"""Deterministic multi-run eval ledger orchestration."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from context_ir.eval_metrics import score_eval_run
from context_ir.eval_oracles import setup_eval_oracle_task
from context_ir.eval_providers import (
    CONTEXT_IR_PROVIDER,
    FILE_ORDER_FLOOR_PROVIDER,
    IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
    LEXICAL_TOP_K_FILES_PROVIDER,
    EvalProviderRequest,
    EvalProviderResult,
    build_context_ir_provider_pack,
    build_file_order_floor_pack,
    build_import_neighborhood_files_pack,
    build_lexical_top_k_files_pack,
)
from context_ir.eval_results import (
    append_eval_run_record_jsonl,
    build_eval_run_record,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ALLOWED_SPEC_FIELDS = frozenset({"plan_id", "cases"})
_ALLOWED_CASE_FIELDS = frozenset(
    {"case_id", "task_path", "query", "budgets", "providers"}
)

EvalProviderBuilder = Callable[[EvalProviderRequest], EvalProviderResult]

_PROVIDER_BUILDERS: dict[str, EvalProviderBuilder] = {
    CONTEXT_IR_PROVIDER: build_context_ir_provider_pack,
    LEXICAL_TOP_K_FILES_PROVIDER: build_lexical_top_k_files_pack,
    IMPORT_NEIGHBORHOOD_FILES_PROVIDER: build_import_neighborhood_files_pack,
    FILE_ORDER_FLOOR_PROVIDER: build_file_order_floor_pack,
}


class EvalRunSpecError(ValueError):
    """Raised when a durable eval run spec violates the runner schema."""


@dataclass(frozen=True)
class EvalRunCase:
    """One deterministic case in a durable multi-run eval plan."""

    case_id: str
    task_path: str
    query: str
    budgets: tuple[int, ...]
    providers: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject malformed case data even when constructed directly."""
        if not self.case_id:
            raise ValueError("case_id must be non-empty")
        if not self.task_path:
            raise ValueError("task_path must be non-empty")
        if not self.query:
            raise ValueError("query must be non-empty")
        if not self.budgets:
            raise ValueError("budgets must be non-empty")
        if any(budget <= 0 for budget in self.budgets):
            raise ValueError("budgets must contain only positive integers")
        if not self.providers:
            raise ValueError("providers must be non-empty")


@dataclass(frozen=True)
class EvalRunSpec:
    """Strict durable JSON run spec for deterministic multi-run execution."""

    plan_id: str
    cases: tuple[EvalRunCase, ...]

    def __post_init__(self) -> None:
        """Reject empty plans and duplicate case identifiers."""
        if not self.plan_id:
            raise ValueError("plan_id must be non-empty")
        if not self.cases:
            raise ValueError("cases must be non-empty")

        seen_case_ids: set[str] = set()
        for case in self.cases:
            if case.case_id in seen_case_ids:
                raise ValueError(f"duplicate case_id '{case.case_id}'")
            seen_case_ids.add(case.case_id)


@dataclass(frozen=True)
class EvalRunCaseExecutionCount:
    """Per-case record-count summary for one executed run spec."""

    case_id: str
    record_count: int


@dataclass(frozen=True)
class EvalRunExecutionResult:
    """Typed execution summary for one deterministic multi-run ledger append."""

    plan_id: str
    output_path: Path
    record_count: int
    written_run_ids: tuple[str, ...]
    case_record_counts: tuple[EvalRunCaseExecutionCount, ...]


def load_eval_run_spec(path: Path | str) -> EvalRunSpec:
    """Load a durable eval run spec JSON file into typed case records."""
    spec_path = Path(path)
    try:
        raw: object = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise EvalRunSpecError(
            f"invalid run spec JSON in {spec_path}: {error}"
        ) from error

    record = _expect_object(raw, path="$")
    _validate_allowed_fields(record, _ALLOWED_SPEC_FIELDS, path="$")
    plan_id = _required_string(record, "plan_id", path="$")
    case_records = _required_list(record, "cases", path="$")
    if not case_records:
        raise EvalRunSpecError("run spec must contain at least one case")

    cases = tuple(
        _parse_case(case_record, path=f"$.cases[{index}]")
        for index, case_record in enumerate(case_records)
    )
    try:
        return EvalRunSpec(plan_id=plan_id, cases=cases)
    except ValueError as error:
        raise EvalRunSpecError(str(error)) from error


def execute_eval_run_spec(
    spec_path: Path | str,
    output_path: Path | str,
    *,
    git_commit: str,
    python_version: str,
    package_version: str,
    spec_version: str = "v1",
) -> EvalRunExecutionResult:
    """Execute one strict run spec and append raw JSONL records for every run."""
    if not git_commit:
        raise ValueError("git_commit must be non-empty")
    if not python_version:
        raise ValueError("python_version must be non-empty")
    if not package_version:
        raise ValueError("package_version must be non-empty")
    if not spec_version:
        raise ValueError("spec_version must be non-empty")

    spec = load_eval_run_spec(spec_path)
    ledger_path = Path(output_path)
    written_run_ids: list[str] = []
    case_record_counts: list[EvalRunCaseExecutionCount] = []
    seen_run_ids: set[str] = set()

    for case in spec.cases:
        setup = setup_eval_oracle_task(_resolve_task_path(case.task_path))
        case_record_count = 0
        repo_root = setup.semantic_program.repo_root
        task_id = setup.task.task_id

        for provider_name in case.providers:
            provider_builder = _provider_builder(provider_name)
            for budget in sorted(case.budgets):
                run_id = _run_id(
                    plan_id=spec.plan_id,
                    case_id=case.case_id,
                    provider_name=provider_name,
                    budget=budget,
                )
                if run_id in seen_run_ids:
                    raise EvalRunSpecError(
                        f"duplicate run_id '{run_id}' generated by run spec"
                    )
                seen_run_ids.add(run_id)

                request = EvalProviderRequest(
                    repo_root=repo_root,
                    task_id=task_id,
                    query=case.query,
                    budget=budget,
                )
                provider_result = provider_builder(request)
                metrics = score_eval_run(setup, provider_result)
                record = build_eval_run_record(
                    setup,
                    provider_result,
                    metrics,
                    run_id=run_id,
                    git_commit=git_commit,
                    python_version=python_version,
                    package_version=package_version,
                    spec_version=spec_version,
                )
                append_eval_run_record_jsonl(ledger_path, record)
                written_run_ids.append(run_id)
                case_record_count += 1

        case_record_counts.append(
            EvalRunCaseExecutionCount(
                case_id=case.case_id,
                record_count=case_record_count,
            )
        )

    return EvalRunExecutionResult(
        plan_id=spec.plan_id,
        output_path=ledger_path,
        record_count=len(written_run_ids),
        written_run_ids=tuple(written_run_ids),
        case_record_counts=tuple(case_record_counts),
    )


def _parse_case(raw: object, *, path: str) -> EvalRunCase:
    """Parse one case JSON object into its typed dataclass."""
    record = _expect_object(raw, path=path)
    _validate_allowed_fields(record, _ALLOWED_CASE_FIELDS, path=path)

    budgets_raw = _required_list(record, "budgets", path=path)
    if not budgets_raw:
        raise EvalRunSpecError(f"{path}.budgets must contain at least one budget")
    providers_raw = _required_list(record, "providers", path=path)
    if not providers_raw:
        raise EvalRunSpecError(f"{path}.providers must contain at least one provider")

    try:
        return EvalRunCase(
            case_id=_required_string(record, "case_id", path=path),
            task_path=_required_repo_relative_path(record, "task_path", path=path),
            query=_required_string(record, "query", path=path),
            budgets=tuple(
                _parse_positive_int(budget, path=f"{path}.budgets[{index}]")
                for index, budget in enumerate(budgets_raw)
            ),
            providers=tuple(
                _parse_provider_name(provider, path=f"{path}.providers[{index}]")
                for index, provider in enumerate(providers_raw)
            ),
        )
    except ValueError as error:
        raise EvalRunSpecError(str(error)) from error


def _provider_builder(provider_name: str) -> EvalProviderBuilder:
    """Return the deterministic provider builder for one accepted provider name."""
    try:
        return _PROVIDER_BUILDERS[provider_name]
    except KeyError as error:
        raise EvalRunSpecError(
            f"provider must be one of {_allowed_provider_names()}"
        ) from error


def _resolve_task_path(task_path: str) -> Path:
    """Resolve one repo-relative task path under the repository root."""
    relative_path = PurePosixPath(task_path)
    if relative_path.is_absolute():
        raise EvalRunSpecError("task_path must be repo-relative")
    if ".." in relative_path.parts:
        raise EvalRunSpecError("task_path must not escape the repository root")

    resolved_path = _PROJECT_ROOT.joinpath(*relative_path.parts)
    if not resolved_path.is_file():
        raise EvalRunSpecError(f"task_path does not exist: {task_path}")
    return resolved_path


def _run_id(
    *,
    plan_id: str,
    case_id: str,
    provider_name: str,
    budget: int,
) -> str:
    """Return the stable deterministic run identifier for one executed run."""
    return f"{plan_id}:{case_id}:{provider_name}:{budget}"


def _validate_allowed_fields(
    record: dict[str, object],
    allowed_fields: frozenset[str],
    *,
    path: str,
) -> None:
    """Reject unknown JSON object fields for one schema node."""
    for key in record:
        if key not in allowed_fields:
            raise EvalRunSpecError(f"{path} contains unknown field '{key}'")


def _expect_object(raw: object, *, path: str) -> dict[str, object]:
    """Return a required JSON object or fail with schema context."""
    if not isinstance(raw, dict):
        raise EvalRunSpecError(f"{path} must be an object")
    return cast(dict[str, object], raw)


def _required_list(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> list[object]:
    """Return a required JSON list field from one schema object."""
    value = record.get(key)
    if not isinstance(value, list):
        raise EvalRunSpecError(f"{path}.{key} must be a list")
    return cast(list[object], value)


def _required_string(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> str:
    """Return a required non-empty string field from one schema object."""
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise EvalRunSpecError(f"{path}.{key} must be a non-empty string")
    return value


def _required_repo_relative_path(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> str:
    """Return a required repo-relative path string from one schema object."""
    value = _required_string(record, key, path=path)
    relative_path = PurePosixPath(value)
    if relative_path.is_absolute():
        raise EvalRunSpecError(f"{path}.{key} must be repo-relative")
    if ".." in relative_path.parts:
        raise EvalRunSpecError(f"{path}.{key} must not escape the repository root")
    return value


def _parse_positive_int(raw: object, *, path: str) -> int:
    """Parse one strictly positive integer JSON value."""
    if type(raw) is not int or raw <= 0:
        raise EvalRunSpecError(f"{path} must be a positive integer")
    return raw


def _parse_provider_name(raw: object, *, path: str) -> str:
    """Parse one accepted provider name from JSON."""
    if not isinstance(raw, str) or not raw:
        raise EvalRunSpecError(f"{path} must be a non-empty string")
    if raw not in _PROVIDER_BUILDERS:
        raise EvalRunSpecError(f"{path} must be one of {_allowed_provider_names()}")
    return raw


def _allowed_provider_names() -> str:
    """Return the accepted provider-name list for schema error messages."""
    return ", ".join(_PROVIDER_BUILDERS)


__all__ = [
    "EvalRunCase",
    "EvalRunCaseExecutionCount",
    "EvalRunExecutionResult",
    "EvalRunSpec",
    "EvalRunSpecError",
    "execute_eval_run_spec",
    "load_eval_run_spec",
]

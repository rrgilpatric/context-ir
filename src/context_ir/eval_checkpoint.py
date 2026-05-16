"""Internal tangible runtime-evidence checkpoint command."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from context_ir import __version__
from context_ir.eval_bundle import EvalBundleArtifact, execute_eval_bundle
from context_ir.eval_providers import (
    CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER,
)
from context_ir.eval_runs import EvalRunCase, load_eval_run_spec
from context_ir.eval_summary import EvalLedgerRecord, load_eval_ledger

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RUN_SPEC_DIR = _PROJECT_ROOT / "evals" / "run_specs"
_RUN_SPEC_FILENAME = "run_spec.json"
_LEDGER_FILENAME = "ledger.jsonl"
_REPORT_FILENAME = "report.md"
_MANIFEST_FILENAME = "manifest.json"
_CHECKPOINT_FILENAME = "checkpoint.md"
_CHECKPOINT_PLAN_ID = "internal_runtime_evidence_checkpoint"
_CHECKPOINT_BUDGET = 100

_SUPPORTED_PROBE_SPECS: tuple[tuple[str, str], ...] = (
    ("oracle_signal_locals_probe", "oracle_signal_locals_probe_matrix.json"),
    ("oracle_signal_globals_probe", "oracle_signal_globals_probe_matrix.json"),
    ("oracle_signal_vars_zero_probe", "oracle_signal_vars_zero_probe_matrix.json"),
    ("oracle_signal_dir_zero_probe", "oracle_signal_dir_zero_probe_matrix.json"),
    ("oracle_signal_hasattr_probe", "oracle_signal_hasattr_probe_matrix.json"),
    ("oracle_signal_exec_probe", "oracle_signal_exec_probe_matrix.json"),
    ("oracle_signal_eval_probe", "oracle_signal_eval_probe_matrix.json"),
    (
        "oracle_signal_metaclass_behavior_probe",
        "oracle_signal_metaclass_behavior_probe_matrix.json",
    ),
)
_SUPPORTED_TASK_IDS = tuple(task_id for task_id, _ in _SUPPORTED_PROBE_SPECS)


class EvalCheckpointError(ValueError):
    """Raised when the internal checkpoint cannot be generated safely."""


@dataclass(frozen=True)
class EvalCheckpointPaths:
    """Deterministic artifact paths for one checkpoint output directory."""

    output_dir: Path
    run_spec_path: Path
    ledger_path: Path
    report_path: Path
    manifest_path: Path
    checkpoint_path: Path


@dataclass(frozen=True)
class EvalCheckpointEvidenceRow:
    """Compact runtime-evidence row rendered into the checkpoint Markdown."""

    task_id: str
    provider_name: str
    budget: int
    normalized_payload: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class EvalCheckpointArtifact:
    """Completed internal checkpoint bundle and extracted evidence rows."""

    paths: EvalCheckpointPaths
    bundle: EvalBundleArtifact
    evidence_rows: tuple[EvalCheckpointEvidenceRow, ...]


def execute_eval_checkpoint(output_dir: Path | str) -> EvalCheckpointArtifact:
    """Generate one internal runtime-evidence checkpoint artifact bundle."""
    paths = _checkpoint_paths(output_dir)
    _require_artifacts_absent(paths)
    run_spec = _build_checkpoint_run_spec()
    _write_generated_run_spec(paths.run_spec_path, run_spec)

    bundle = execute_eval_bundle(
        paths.run_spec_path,
        paths.output_dir,
        git_commit=_current_git_commit(),
        python_version=platform.python_version(),
        package_version=__version__,
    )
    evidence_rows = _build_checkpoint_evidence_rows(paths.ledger_path)
    checkpoint_markdown = _render_checkpoint_markdown(paths, evidence_rows)
    _write_checkpoint_markdown(paths.checkpoint_path, checkpoint_markdown)

    return EvalCheckpointArtifact(
        paths=paths,
        bundle=bundle,
        evidence_rows=evidence_rows,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the internal runtime-evidence checkpoint command."""
    parser = argparse.ArgumentParser(
        description="Generate an internal runtime-evidence checkpoint bundle.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory that will receive the checkpoint artifacts.",
    )
    namespace = parser.parse_args(argv)
    output_dir = cast(Path, namespace.output_dir)

    artifact = execute_eval_checkpoint(output_dir)
    for label, path in _artifact_path_rows(artifact.paths):
        print(f"{label}: {path}")
    return 0


def _checkpoint_paths(output_dir: Path | str) -> EvalCheckpointPaths:
    """Return the fixed artifact paths below one caller-selected directory."""
    directory = Path(output_dir)
    return EvalCheckpointPaths(
        output_dir=directory,
        run_spec_path=directory / _RUN_SPEC_FILENAME,
        ledger_path=directory / _LEDGER_FILENAME,
        report_path=directory / _REPORT_FILENAME,
        manifest_path=directory / _MANIFEST_FILENAME,
        checkpoint_path=directory / _CHECKPOINT_FILENAME,
    )


def _require_artifacts_absent(paths: EvalCheckpointPaths) -> None:
    """Fail closed before any checkpoint artifact can append or overwrite."""
    existing_paths = tuple(
        path for _, path in _artifact_path_rows(paths) if path.exists()
    )
    if existing_paths:
        rendered_paths = ", ".join(path.as_posix() for path in existing_paths)
        raise EvalCheckpointError(
            f"checkpoint target artifact files already exist: {rendered_paths}"
        )


def _build_checkpoint_run_spec() -> dict[str, object]:
    """Build the generated run spec from committed source run specs."""
    cases = [
        _checkpoint_case_from_source_spec(task_id, _RUN_SPEC_DIR / spec_filename)
        for task_id, spec_filename in _SUPPORTED_PROBE_SPECS
    ]
    return {
        "plan_id": _CHECKPOINT_PLAN_ID,
        "cases": [_case_to_json(case) for case in cases],
    }


def _checkpoint_case_from_source_spec(
    expected_task_id: str,
    source_spec_path: Path,
) -> EvalRunCase:
    """Return one default-subprocess checkpoint case from a committed run spec."""
    source_spec = load_eval_run_spec(source_spec_path)
    if len(source_spec.cases) != 1:
        raise EvalCheckpointError(
            f"checkpoint source spec must contain one case: {source_spec_path}"
        )
    source_case = source_spec.cases[0]
    expected_task_path = f"evals/tasks/{expected_task_id}.json"
    if source_case.task_path != expected_task_path:
        raise EvalCheckpointError(
            "checkpoint source spec task_path mismatch for "
            f"{expected_task_id}: {source_case.task_path}"
        )
    return EvalRunCase(
        case_id=source_case.case_id,
        task_path=source_case.task_path,
        query=source_case.query,
        budgets=(_CHECKPOINT_BUDGET,),
        providers=(CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER,),
    )


def _case_to_json(case: EvalRunCase) -> dict[str, object]:
    """Return one run-spec case as strict JSON-safe data."""
    return {
        "case_id": case.case_id,
        "task_path": case.task_path,
        "query": case.query,
        "budgets": list(case.budgets),
        "providers": list(case.providers),
    }


def _write_generated_run_spec(
    run_spec_path: Path,
    run_spec: dict[str, object],
) -> None:
    """Write the generated checkpoint run spec without overwriting an artifact."""
    run_spec_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(run_spec, ensure_ascii=False, indent=2) + "\n"
    try:
        with run_spec_path.open("x", encoding="utf-8") as handle:
            handle.write(payload)
    except FileExistsError as error:
        raise EvalCheckpointError(
            f"checkpoint target artifact file already exists: {run_spec_path}"
        ) from error


def _current_git_commit() -> str:
    """Return the current repository commit for the raw eval ledger metadata."""
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=_PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _build_checkpoint_evidence_rows(
    ledger_path: Path,
) -> tuple[EvalCheckpointEvidenceRow, ...]:
    """Extract exact supported-probe runtime payload rows from the ledger."""
    ledger = load_eval_ledger(ledger_path)
    records_by_task_id = _records_by_task_id(ledger.records)
    return tuple(
        _evidence_row_from_record(_require_record(records_by_task_id, task_id))
        for task_id in _SUPPORTED_TASK_IDS
    )


def _records_by_task_id(
    records: tuple[EvalLedgerRecord, ...],
) -> dict[str, EvalLedgerRecord]:
    """Return one ledger record per expected checkpoint task id."""
    records_by_task_id: dict[str, EvalLedgerRecord] = {}
    for record in records:
        if record.task_id not in _SUPPORTED_TASK_IDS:
            raise EvalCheckpointError(
                f"checkpoint ledger contains unsupported task_id: {record.task_id}"
            )
        if record.task_id in records_by_task_id:
            raise EvalCheckpointError(
                f"checkpoint ledger contains duplicate task_id: {record.task_id}"
            )
        records_by_task_id[record.task_id] = record
    return records_by_task_id


def _require_record(
    records_by_task_id: dict[str, EvalLedgerRecord],
    task_id: str,
) -> EvalLedgerRecord:
    """Return the required ledger row for one exact supported probe."""
    record = records_by_task_id.get(task_id)
    if record is None:
        raise EvalCheckpointError(
            f"checkpoint ledger is missing supported task_id: {task_id}"
        )
    return record


def _evidence_row_from_record(record: EvalLedgerRecord) -> EvalCheckpointEvidenceRow:
    """Build one checkpoint evidence row from one strict ledger record."""
    if record.provider_name != CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER:
        raise EvalCheckpointError(
            f"checkpoint ledger used unexpected provider: {record.provider_name}"
        )
    if record.budget != _CHECKPOINT_BUDGET:
        raise EvalCheckpointError(
            f"checkpoint ledger used unexpected budget: {record.budget}"
        )
    if not record.runtime_provenance_records:
        raise EvalCheckpointError(
            "checkpoint ledger must contain runtime provenance records "
            f"for {record.task_id}"
        )
    payloads = tuple(
        tuple(
            (field.key, field.value) for field in provenance_record.normalized_payload
        )
        for provenance_record in record.runtime_provenance_records
    )
    unique_payloads = tuple(dict.fromkeys(payloads))
    if len(unique_payloads) != 1:
        raise EvalCheckpointError(
            "checkpoint ledger contains conflicting normalized payloads "
            f"for {record.task_id}"
        )
    normalized_payload = unique_payloads[0]
    if not normalized_payload:
        raise EvalCheckpointError(
            f"checkpoint ledger has an empty normalized payload for {record.task_id}"
        )
    return EvalCheckpointEvidenceRow(
        task_id=record.task_id,
        provider_name=record.provider_name,
        budget=record.budget,
        normalized_payload=normalized_payload,
    )


def _render_checkpoint_markdown(
    paths: EvalCheckpointPaths,
    evidence_rows: tuple[EvalCheckpointEvidenceRow, ...],
) -> str:
    """Render the internal checkpoint Markdown artifact."""
    lines = [
        "# Runtime Evidence Checkpoint",
        "",
        (
            "This is an internal checkpoint for tangible runtime-evidence "
            "verification. It is not a public benchmark, benchmark result, or "
            "product claim."
        ),
        "",
        "## Artifacts",
        "",
        "| Artifact | Path |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| {label} | `{path.as_posix()}` |"
        for label, path in _artifact_path_rows(paths)
    )
    lines.extend(
        (
            "",
            "## Evidence",
            "",
            "| Probe | Provider | Budget | Normalized Payload |",
            "| --- | --- | ---: | --- |",
        )
    )
    lines.extend(
        (
            f"| {row.task_id} | {row.provider_name} | {row.budget} | "
            f"`{_render_payload(row.normalized_payload)}` |"
        )
        for row in evidence_rows
    )
    lines.extend(
        (
            "",
            "## Unsupported / Remaining Gap",
            "",
            (
                "This checkpoint only exercises the exact "
                "`context_ir_default_local_python_subprocess` fixtures listed "
                "above at budget 100. It does not widen support for generalized "
                "runtime/provider behavior, additional runtime-probe forms, "
                "compiler semantics, scoring, MCP contracts, schema/config "
                "contracts, dynamic imports, runtime mutation, exec/eval, "
                "metaclass behavior, or reflective builtins beyond these exact "
                "supported probes."
            ),
        )
    )
    return "\n".join(lines) + "\n"


def _render_payload(payload: tuple[tuple[str, str], ...]) -> str:
    """Render one normalized runtime payload as compact deterministic JSON."""
    return json.dumps(
        {key: value for key, value in payload},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _write_checkpoint_markdown(checkpoint_path: Path, markdown: str) -> None:
    """Write checkpoint Markdown without overwriting an artifact."""
    try:
        with checkpoint_path.open("x", encoding="utf-8") as handle:
            handle.write(markdown)
    except FileExistsError as error:
        raise EvalCheckpointError(
            f"checkpoint target artifact file already exists: {checkpoint_path}"
        ) from error


def _artifact_path_rows(paths: EvalCheckpointPaths) -> tuple[tuple[str, Path], ...]:
    """Return artifact labels and paths in checkpoint display order."""
    return (
        ("Generated run spec", paths.run_spec_path),
        ("Raw ledger", paths.ledger_path),
        ("Eval report", paths.report_path),
        ("Manifest", paths.manifest_path),
        ("Checkpoint", paths.checkpoint_path),
    )


if __name__ == "__main__":
    raise SystemExit(main())

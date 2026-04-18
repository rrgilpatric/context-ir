"""Deterministic internal summary rendering for raw eval ledgers."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from math import fsum, isfinite
from pathlib import Path
from typing import cast


class EvalLedgerError(ValueError):
    """Raised when a raw eval ledger cannot be loaded or summarized safely."""


@dataclass(frozen=True)
class EvalLedgerMetrics:
    """Typed metric fields retained from one raw eval ledger row."""

    aggregate_score: float
    edit_coverage: float
    support_coverage: float | None
    representation_adequacy: float
    uncertainty_honesty: float | None
    noise_efficiency: float


@dataclass(frozen=True)
class EvalLedgerRecord:
    """Typed internal representation of one raw JSONL eval ledger row."""

    run_id: str
    task_id: str
    provider_name: str
    budget: int
    budget_compliant: bool
    metrics: EvalLedgerMetrics


@dataclass(frozen=True)
class EvalLedger:
    """Typed raw eval ledger loaded from one JSONL file."""

    source_path: Path
    records: tuple[EvalLedgerRecord, ...]


@dataclass(frozen=True)
class EvalProviderAggregate:
    """Deterministic provider-level aggregate metrics across one ledger."""

    provider_name: str
    record_count: int
    budget_compliance_rate: float
    average_aggregate_score: float
    average_edit_coverage: float
    average_support_coverage: float | None
    average_representation_adequacy: float
    average_uncertainty_honesty: float | None
    average_noise_efficiency: float


@dataclass(frozen=True)
class EvalTaskBudgetProviderResult:
    """Provider comparison metrics for one task and budget slot."""

    run_id: str
    provider_name: str
    budget_compliant: bool
    aggregate_score: float
    edit_coverage: float
    support_coverage: float | None
    representation_adequacy: float
    uncertainty_honesty: float | None
    noise_efficiency: float


@dataclass(frozen=True)
class EvalTaskBudgetResult:
    """Deterministic provider comparison row for one task and budget slot."""

    task_id: str
    budget: int
    provider_results: tuple[EvalTaskBudgetProviderResult, ...]
    winner_provider_names: tuple[str, ...]


@dataclass(frozen=True)
class EvalLedgerSummary:
    """Deterministic rollup summary for one accepted raw eval ledger."""

    record_count: int
    task_ids: tuple[str, ...]
    provider_names: tuple[str, ...]
    budgets: tuple[int, ...]
    provider_aggregates: tuple[EvalProviderAggregate, ...]
    task_budget_results: tuple[EvalTaskBudgetResult, ...]
    budget_violation_run_ids: tuple[str, ...]


def load_eval_ledger(path: Path | str) -> EvalLedger:
    """Load one strict raw JSONL eval ledger into typed immutable records."""
    ledger_path = Path(path)
    records: list[EvalLedgerRecord] = []
    seen_run_ids: set[str] = set()

    for line_number, raw_line in enumerate(
        ledger_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if raw_line.strip() == "":
            raise EvalLedgerError(f"invalid blank line at {ledger_path}:{line_number}")
        try:
            raw = json.loads(
                raw_line,
                parse_constant=_build_non_finite_json_constant_hook(
                    ledger_path=ledger_path,
                    line_number=line_number,
                ),
            )
        except json.JSONDecodeError as error:
            raise EvalLedgerError(
                f"invalid JSON at {ledger_path}:{line_number}: {error.msg}"
            ) from error

        record = _parse_ledger_record(
            raw,
            ledger_path=ledger_path,
            line_number=line_number,
        )
        if record.run_id in seen_run_ids:
            raise EvalLedgerError(
                f"duplicate run_id '{record.run_id}' at {ledger_path}:{line_number}"
            )
        seen_run_ids.add(record.run_id)
        records.append(record)

    if not records:
        raise EvalLedgerError(
            f"eval ledger must contain at least one record: {ledger_path}"
        )

    return EvalLedger(source_path=ledger_path, records=tuple(records))


def build_eval_ledger_summary(ledger: EvalLedger) -> EvalLedgerSummary:
    """Build deterministic provider and task-budget rollups for one ledger."""
    provider_groups: dict[str, list[EvalLedgerRecord]] = {}
    task_budget_groups: dict[tuple[str, int], list[EvalLedgerRecord]] = {}

    for record in ledger.records:
        provider_groups.setdefault(record.provider_name, []).append(record)
        task_budget_groups.setdefault((record.task_id, record.budget), []).append(
            record
        )

    task_ids = tuple(sorted({record.task_id for record in ledger.records}))
    provider_names = tuple(sorted({record.provider_name for record in ledger.records}))
    budgets = tuple(sorted({record.budget for record in ledger.records}))
    provider_aggregates = tuple(
        _build_provider_aggregate(provider_name, provider_groups[provider_name])
        for provider_name in sorted(provider_groups)
    )
    task_budget_results = tuple(
        _build_task_budget_result(
            task_id,
            budget,
            task_budget_groups[(task_id, budget)],
        )
        for task_id, budget in sorted(task_budget_groups)
    )
    budget_violation_run_ids = tuple(
        sorted(
            record.run_id for record in ledger.records if not record.budget_compliant
        )
    )

    return EvalLedgerSummary(
        record_count=len(ledger.records),
        task_ids=task_ids,
        provider_names=provider_names,
        budgets=budgets,
        provider_aggregates=provider_aggregates,
        task_budget_results=task_budget_results,
        budget_violation_run_ids=budget_violation_run_ids,
    )


def render_eval_ledger_summary(summary: EvalLedgerSummary) -> str:
    """Render one deterministic internal-review Markdown summary."""
    lines = [
        "# Eval Summary",
        "",
        f"- Record count: {summary.record_count}",
        f"- Tasks: {_render_string_list(summary.task_ids)}",
        f"- Providers: {_render_string_list(summary.provider_names)}",
        f"- Budgets: {_render_int_list(summary.budgets)}",
        "",
        "## Provider Aggregates",
        "",
    ]
    lines.extend(
        _render_markdown_table(
            (
                "Provider",
                "Records",
                "Budget Compliance",
                "Aggregate Score",
                "Edit Coverage",
                "Support Coverage",
                "Representation Adequacy",
                "Uncertainty Honesty",
                "Noise Efficiency",
            ),
            tuple(
                (
                    aggregate.provider_name,
                    str(aggregate.record_count),
                    _format_metric(aggregate.budget_compliance_rate),
                    _format_metric(aggregate.average_aggregate_score),
                    _format_metric(aggregate.average_edit_coverage),
                    _format_metric(aggregate.average_support_coverage),
                    _format_metric(aggregate.average_representation_adequacy),
                    _format_metric(aggregate.average_uncertainty_honesty),
                    _format_metric(aggregate.average_noise_efficiency),
                )
                for aggregate in summary.provider_aggregates
            ),
            numeric_columns=frozenset({1, 2, 3, 4, 5, 6, 7, 8}),
        )
    )
    lines.extend(("", "## Task Budget Results", ""))
    lines.extend(
        _render_markdown_table(
            ("Task", "Budget", "Winner", "Provider Results"),
            tuple(
                (
                    result.task_id,
                    str(result.budget),
                    _winner_label(result.winner_provider_names),
                    _render_provider_results(result.provider_results),
                )
                for result in summary.task_budget_results
            ),
            numeric_columns=frozenset({1}),
        )
    )

    if summary.budget_violation_run_ids:
        lines.extend(("", "## Budget Violations", ""))
        lines.extend(f"- {run_id}" for run_id in summary.budget_violation_run_ids)

    return "\n".join(lines)


def _parse_ledger_record(
    raw: object,
    *,
    ledger_path: Path,
    line_number: int,
) -> EvalLedgerRecord:
    """Parse one raw JSON object into the typed fields needed for summary."""
    record = _require_object(raw, ledger_path=ledger_path, line_number=line_number)
    metrics_record = _require_object(
        record.get("metrics"),
        ledger_path=ledger_path,
        line_number=line_number,
        field_path="metrics",
    )

    return EvalLedgerRecord(
        run_id=_require_string(
            record,
            "run_id",
            ledger_path=ledger_path,
            line_number=line_number,
        ),
        task_id=_require_string(
            record,
            "task_id",
            ledger_path=ledger_path,
            line_number=line_number,
        ),
        provider_name=_require_string(
            record,
            "provider_name",
            ledger_path=ledger_path,
            line_number=line_number,
        ),
        budget=_require_int(
            record,
            "budget",
            ledger_path=ledger_path,
            line_number=line_number,
        ),
        budget_compliant=_require_bool(
            metrics_record,
            "budget_compliant",
            ledger_path=ledger_path,
            line_number=line_number,
            prefix="metrics",
        ),
        metrics=EvalLedgerMetrics(
            aggregate_score=_require_float(
                metrics_record,
                "aggregate_score",
                ledger_path=ledger_path,
                line_number=line_number,
                prefix="metrics",
            ),
            edit_coverage=_require_float(
                metrics_record,
                "edit_coverage",
                ledger_path=ledger_path,
                line_number=line_number,
                prefix="metrics",
            ),
            support_coverage=_require_optional_float(
                metrics_record,
                "support_coverage",
                ledger_path=ledger_path,
                line_number=line_number,
                prefix="metrics",
            ),
            representation_adequacy=_require_float(
                metrics_record,
                "representation_adequacy",
                ledger_path=ledger_path,
                line_number=line_number,
                prefix="metrics",
            ),
            uncertainty_honesty=_require_optional_float(
                metrics_record,
                "uncertainty_honesty",
                ledger_path=ledger_path,
                line_number=line_number,
                prefix="metrics",
            ),
            noise_efficiency=_require_float(
                metrics_record,
                "noise_efficiency",
                ledger_path=ledger_path,
                line_number=line_number,
                prefix="metrics",
            ),
        ),
    )


def _build_provider_aggregate(
    provider_name: str,
    records: list[EvalLedgerRecord],
) -> EvalProviderAggregate:
    """Aggregate deterministic provider summary metrics across all runs."""
    return EvalProviderAggregate(
        provider_name=provider_name,
        record_count=len(records),
        budget_compliance_rate=_average(
            1.0 if record.budget_compliant else 0.0 for record in records
        ),
        average_aggregate_score=_average(
            record.metrics.aggregate_score for record in records
        ),
        average_edit_coverage=_average(
            record.metrics.edit_coverage for record in records
        ),
        average_support_coverage=_average_optional(
            record.metrics.support_coverage for record in records
        ),
        average_representation_adequacy=_average(
            record.metrics.representation_adequacy for record in records
        ),
        average_uncertainty_honesty=_average_optional(
            record.metrics.uncertainty_honesty for record in records
        ),
        average_noise_efficiency=_average(
            record.metrics.noise_efficiency for record in records
        ),
    )


def _build_task_budget_result(
    task_id: str,
    budget: int,
    records: list[EvalLedgerRecord],
) -> EvalTaskBudgetResult:
    """Build one deterministic task and budget comparison row."""
    provider_results = tuple(
        EvalTaskBudgetProviderResult(
            run_id=record.run_id,
            provider_name=record.provider_name,
            budget_compliant=record.budget_compliant,
            aggregate_score=record.metrics.aggregate_score,
            edit_coverage=record.metrics.edit_coverage,
            support_coverage=record.metrics.support_coverage,
            representation_adequacy=record.metrics.representation_adequacy,
            uncertainty_honesty=record.metrics.uncertainty_honesty,
            noise_efficiency=record.metrics.noise_efficiency,
        )
        for record in sorted(records, key=lambda item: item.provider_name)
    )
    winning_score = max(
        provider_result.aggregate_score for provider_result in provider_results
    )
    winner_provider_names = tuple(
        provider_result.provider_name
        for provider_result in provider_results
        if provider_result.aggregate_score == winning_score
    )
    return EvalTaskBudgetResult(
        task_id=task_id,
        budget=budget,
        provider_results=provider_results,
        winner_provider_names=winner_provider_names,
    )


def _average(values: Iterable[float]) -> float:
    """Return the arithmetic mean for a non-empty finite float sequence."""
    materialized = tuple(values)
    if not materialized:
        raise EvalLedgerError("cannot average an empty value sequence")
    return fsum(materialized) / len(materialized)


def _average_optional(values: Iterable[float | None]) -> float | None:
    """Return the arithmetic mean over non-null values, or ``None``."""
    materialized = tuple(value for value in values if value is not None)
    if not materialized:
        return None
    return fsum(materialized) / len(materialized)


def _render_markdown_table(
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
    *,
    numeric_columns: frozenset[int],
) -> tuple[str, ...]:
    """Render a compact Markdown table with deterministic alignment."""
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = (
        "| "
        + " | ".join(
            "---:" if index in numeric_columns else "---"
            for index, _header in enumerate(headers)
        )
        + " |"
    )
    body_rows = tuple("| " + " | ".join(row) + " |" for row in rows)
    return (header_row, separator_row, *body_rows)


def _winner_label(winner_provider_names: tuple[str, ...]) -> str:
    """Render one deterministic winner label, preserving explicit ties."""
    if len(winner_provider_names) == 1:
        return winner_provider_names[0]
    return f"tie: {', '.join(winner_provider_names)}"


def _render_provider_results(
    provider_results: tuple[EvalTaskBudgetProviderResult, ...],
) -> str:
    """Render deterministic provider metrics for one task and budget row."""
    return "; ".join(
        (
            f"{provider_result.provider_name} "
            f"(agg={_format_metric(provider_result.aggregate_score)}, "
            f"edit={_format_metric(provider_result.edit_coverage)}, "
            f"support={_format_metric(provider_result.support_coverage)}, "
            f"repr={_format_metric(provider_result.representation_adequacy)}, "
            f"honest={_format_metric(provider_result.uncertainty_honesty)}, "
            f"noise={_format_metric(provider_result.noise_efficiency)}, "
            f"budget={'yes' if provider_result.budget_compliant else 'no'})"
        )
        for provider_result in provider_results
    )


def _render_string_list(values: tuple[str, ...]) -> str:
    """Render one deterministic comma-separated string list."""
    if not values:
        return "-"
    return ", ".join(values)


def _render_int_list(values: tuple[int, ...]) -> str:
    """Render one deterministic comma-separated integer list."""
    if not values:
        return "-"
    return ", ".join(str(value) for value in values)


def _format_metric(value: float | None) -> str:
    """Render one score or rate with fixed precision, preserving nulls."""
    if value is None:
        return "-"
    return f"{value:.3f}"


def _require_object(
    raw: object,
    *,
    ledger_path: Path,
    line_number: int,
    field_path: str | None = None,
) -> dict[str, object]:
    """Return one required JSON object or raise with ledger line context."""
    if not isinstance(raw, dict):
        if field_path is None:
            raise EvalLedgerError(
                f"ledger line {line_number} in {ledger_path} must be a JSON object"
            )
        raise EvalLedgerError(
            "required field "
            f"'{field_path}' must be a JSON object at {ledger_path}:{line_number}"
        )
    return cast(dict[str, object], raw)


def _require_string(
    record: dict[str, object],
    key: str,
    *,
    ledger_path: Path,
    line_number: int,
    prefix: str | None = None,
) -> str:
    """Return one required non-empty string field from a ledger object."""
    field_path = _field_path(key, prefix=prefix)
    value = record.get(key)
    if not isinstance(value, str) or value == "":
        raise EvalLedgerError(
            f"missing required field '{field_path}' at {ledger_path}:{line_number}"
        )
    return value


def _require_int(
    record: dict[str, object],
    key: str,
    *,
    ledger_path: Path,
    line_number: int,
    prefix: str | None = None,
) -> int:
    """Return one required integer field from a ledger object."""
    field_path = _field_path(key, prefix=prefix)
    value = record.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise EvalLedgerError(
            f"missing required field '{field_path}' at {ledger_path}:{line_number}"
        )
    return value


def _require_bool(
    record: dict[str, object],
    key: str,
    *,
    ledger_path: Path,
    line_number: int,
    prefix: str | None = None,
) -> bool:
    """Return one required boolean field from a ledger object."""
    field_path = _field_path(key, prefix=prefix)
    value = record.get(key)
    if not isinstance(value, bool):
        raise EvalLedgerError(
            f"missing required field '{field_path}' at {ledger_path}:{line_number}"
        )
    return value


def _require_float(
    record: dict[str, object],
    key: str,
    *,
    ledger_path: Path,
    line_number: int,
    prefix: str | None = None,
) -> float:
    """Return one required numeric field from a ledger object."""
    field_path = _field_path(key, prefix=prefix)
    value = record.get(key)
    return _require_finite_float(
        value,
        field_path=field_path,
        ledger_path=ledger_path,
        line_number=line_number,
    )


def _require_optional_float(
    record: dict[str, object],
    key: str,
    *,
    ledger_path: Path,
    line_number: int,
    prefix: str | None = None,
) -> float | None:
    """Return one required nullable numeric field from a ledger object."""
    field_path = _field_path(key, prefix=prefix)
    value = record.get(key)
    if value is None:
        return None
    return _require_finite_float(
        value,
        field_path=field_path,
        ledger_path=ledger_path,
        line_number=line_number,
    )


def _require_finite_float(
    value: object,
    *,
    field_path: str,
    ledger_path: Path,
    line_number: int,
) -> float:
    """Return one finite numeric value or raise with ledger line context."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvalLedgerError(
            f"missing required field '{field_path}' at {ledger_path}:{line_number}"
        )
    numeric_value = float(value)
    if not isfinite(numeric_value):
        raise EvalLedgerError(
            f"non-finite numeric field '{field_path}' at {ledger_path}:{line_number}"
        )
    return numeric_value


def _build_non_finite_json_constant_hook(
    *,
    ledger_path: Path,
    line_number: int,
) -> Callable[[str], object]:
    """Return one decoder hook that rejects non-finite JSON numeric tokens."""

    def _reject_non_finite_json_constant(constant: str) -> object:
        raise EvalLedgerError(
            f"non-finite numeric token '{constant}' at {ledger_path}:{line_number}"
        )

    return _reject_non_finite_json_constant


def _field_path(key: str, *, prefix: str | None) -> str:
    """Return one human-readable dotted field path."""
    if prefix is None:
        return key
    return f"{prefix}.{key}"

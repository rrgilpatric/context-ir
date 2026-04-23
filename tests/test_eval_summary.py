"""Deterministic internal eval summary tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_runs as eval_runs
import context_ir.eval_summary as eval_summary
import context_ir.semantic_types as semantic_types

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_SPEC_PATH = REPO_ROOT / "evals" / "run_specs" / "oracle_smoke_matrix.json"


def _resolved_selector_record(
    *,
    expected_primary_capability_tier: str | None = "statically_proved",
    expect_attached_runtime_provenance: bool | None = False,
    primary_capability_tier: str | None = "statically_proved",
    has_attached_runtime_provenance: bool | None = False,
) -> dict[str, object]:
    """Return one minimal resolved-selector payload for summary loading tests."""
    return {
        "original_selector": {
            "kind": "symbol",
            "min_detail": "identity",
            "expected_primary_capability_tier": expected_primary_capability_tier,
            "expect_attached_runtime_provenance": (expect_attached_runtime_provenance),
        },
        "primary_capability_tier": primary_capability_tier,
        "has_attached_runtime_provenance": has_attached_runtime_provenance,
    }


def _selected_unit_record(
    *,
    primary_capability_tier: str | None = "statically_proved",
    has_attached_runtime_provenance: bool | None = False,
) -> dict[str, object]:
    """Return one minimal selected-unit payload for summary loading tests."""
    return {
        "primary_capability_tier": primary_capability_tier,
        "has_attached_runtime_provenance": has_attached_runtime_provenance,
    }


def _ledger_record(
    *,
    run_id: str,
    task_id: str = "task_alpha",
    provider_name: str = "provider_alpha",
    budget: int = 100,
    budget_compliant: bool = True,
    aggregate_score: float = 0.5,
    edit_coverage: float = 0.5,
    support_coverage: float | None = 0.5,
    representation_adequacy: float = 0.5,
    uncertainty_honesty: float | None = 0.5,
    noise_efficiency: float = 0.5,
    resolved_selectors: list[dict[str, object]] | None = None,
    selected_units: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Return one minimal raw ledger row for strict summary loading tests."""
    if resolved_selectors is None:
        resolved_selectors = [_resolved_selector_record()]
    if selected_units is None:
        selected_units = [_selected_unit_record()]
    return {
        "run_id": run_id,
        "task_id": task_id,
        "provider_name": provider_name,
        "budget": budget,
        "provider_metadata": {
            "selected_units": selected_units,
        },
        "resolved_selectors": resolved_selectors,
        "metrics": {
            "budget_compliant": budget_compliant,
            "aggregate_score": aggregate_score,
            "edit_coverage": edit_coverage,
            "support_coverage": support_coverage,
            "representation_adequacy": representation_adequacy,
            "uncertainty_honesty": uncertainty_honesty,
            "noise_efficiency": noise_efficiency,
        },
    }


def _write_jsonl(path: Path, rows: list[str]) -> Path:
    """Write raw JSONL rows to one temporary ledger file."""
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _write_ledger_records(
    path: Path,
    records: list[dict[str, object]],
) -> Path:
    """Write JSON objects as one compact JSONL ledger file."""
    return _write_jsonl(
        path,
        [
            json.dumps(record, separators=(",", ":"), sort_keys=True)
            for record in records
        ],
    )


def _execute_smoke_ledger(path: Path) -> Path:
    """Execute the accepted smoke run spec into one temporary ledger path."""
    eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )
    return path


def test_valid_raw_jsonl_ledger_loads_into_typed_records(tmp_path: Path) -> None:
    """A valid raw JSONL ledger becomes typed immutable summary records."""
    ledger_path = _execute_smoke_ledger(tmp_path / "smoke.jsonl")

    ledger = eval_summary.load_eval_ledger(ledger_path)

    assert ledger.source_path == ledger_path
    assert len(ledger.records) == 6
    assert all(
        isinstance(record, eval_summary.EvalLedgerRecord) for record in ledger.records
    )
    first_record = ledger.records[0]
    assert first_record.run_id == (
        "oracle_smoke_matrix:smoke_core_baselines:context_ir:120"
    )
    assert first_record.task_id == "oracle_smoke"
    assert first_record.provider_name == "context_ir"
    assert first_record.budget == 120
    assert isinstance(first_record.metrics, eval_summary.EvalLedgerMetrics)
    assert all(
        isinstance(selector, eval_summary.EvalLedgerResolvedSelector)
        for selector in first_record.resolved_selectors
    )
    assert all(
        isinstance(unit, eval_summary.EvalLedgerSelectedUnit)
        for unit in first_record.selected_units
    )


def test_malformed_json_lines_fail_loudly(tmp_path: Path) -> None:
    """Malformed ledger JSON fails with source line context."""
    ledger_path = _write_jsonl(
        tmp_path / "invalid.jsonl",
        [
            json.dumps(
                _ledger_record(run_id="run-1"),
                separators=(",", ":"),
                sort_keys=True,
            ),
            "{",
        ],
    )

    with pytest.raises(
        eval_summary.EvalLedgerError,
        match=r"invalid JSON .*:2",
    ):
        eval_summary.load_eval_ledger(ledger_path)


def test_blank_lines_fail_loudly(tmp_path: Path) -> None:
    """Blank ledger lines are rejected with their line number."""
    ledger_path = _write_jsonl(
        tmp_path / "blank.jsonl",
        [
            json.dumps(
                _ledger_record(run_id="run-1"),
                separators=(",", ":"),
                sort_keys=True,
            ),
            "",
            json.dumps(
                _ledger_record(run_id="run-2"),
                separators=(",", ":"),
                sort_keys=True,
            ),
        ],
    )

    with pytest.raises(
        eval_summary.EvalLedgerError,
        match=r"blank line .*:2",
    ):
        eval_summary.load_eval_ledger(ledger_path)


def test_duplicate_run_id_fails_loudly(tmp_path: Path) -> None:
    """Duplicate run identifiers are rejected during strict ledger loading."""
    ledger_path = _write_ledger_records(
        tmp_path / "duplicate.jsonl",
        [
            _ledger_record(run_id="run-1"),
            _ledger_record(run_id="run-1", provider_name="provider_beta"),
        ],
    )

    with pytest.raises(
        eval_summary.EvalLedgerError,
        match=r"duplicate run_id 'run-1'",
    ):
        eval_summary.load_eval_ledger(ledger_path)


def test_missing_required_fields_fail_loudly(tmp_path: Path) -> None:
    """Rows missing summary-required fields are rejected."""
    record = _ledger_record(run_id="run-1")
    metrics = cast(dict[str, object], record["metrics"])
    del metrics["aggregate_score"]
    ledger_path = _write_ledger_records(tmp_path / "missing.jsonl", [record])

    with pytest.raises(
        eval_summary.EvalLedgerError,
        match=r"metrics\.aggregate_score",
    ):
        eval_summary.load_eval_ledger(ledger_path)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("aggregate_score", float("nan")),
        ("aggregate_score", float("inf")),
        ("aggregate_score", float("-inf")),
        ("support_coverage", float("nan")),
    ],
    ids=[
        "aggregate_score_nan",
        "aggregate_score_infinity",
        "aggregate_score_negative_infinity",
        "support_coverage_nan",
    ],
)
def test_non_finite_metric_values_fail_loudly(
    tmp_path: Path,
    field_name: str,
    field_value: float,
) -> None:
    """Non-finite metric values are rejected during strict ledger loading."""
    record = _ledger_record(run_id="run-1")
    metrics = cast(dict[str, object], record["metrics"])
    metrics[field_name] = field_value
    ledger_path = _write_ledger_records(tmp_path / "non_finite.jsonl", [record])

    with pytest.raises(
        eval_summary.EvalLedgerError,
        match=r"non-finite numeric (field|token)",
    ):
        eval_summary.load_eval_ledger(ledger_path)


def test_provider_aggregates_are_deterministic_and_average_nullable_metrics(
    tmp_path: Path,
) -> None:
    """Provider aggregates sort by name and average nullable metrics correctly."""
    ledger_path = _write_ledger_records(
        tmp_path / "aggregates.jsonl",
        [
            _ledger_record(
                run_id="run-b-1",
                provider_name="provider_beta",
                aggregate_score=0.2,
                support_coverage=None,
                uncertainty_honesty=0.2,
                noise_efficiency=0.7,
            ),
            _ledger_record(
                run_id="run-a-1",
                provider_name="provider_alpha",
                aggregate_score=0.6,
                support_coverage=None,
                uncertainty_honesty=None,
                noise_efficiency=0.5,
            ),
            _ledger_record(
                run_id="run-a-2",
                provider_name="provider_alpha",
                budget_compliant=False,
                aggregate_score=0.8,
                support_coverage=0.4,
                uncertainty_honesty=1.0,
                noise_efficiency=0.9,
            ),
            _ledger_record(
                run_id="run-b-2",
                provider_name="provider_beta",
                aggregate_score=0.4,
                support_coverage=None,
                uncertainty_honesty=None,
                noise_efficiency=0.9,
            ),
        ],
    )

    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(ledger_path)
    )
    aggregates = {
        aggregate.provider_name: aggregate for aggregate in summary.provider_aggregates
    }

    assert summary.provider_names == ("provider_alpha", "provider_beta")
    assert tuple(aggregates) == ("provider_alpha", "provider_beta")
    assert aggregates["provider_alpha"].record_count == 2
    assert aggregates["provider_alpha"].budget_compliance_rate == pytest.approx(0.5)
    assert aggregates["provider_alpha"].average_aggregate_score == pytest.approx(0.7)
    assert aggregates["provider_alpha"].average_edit_coverage == pytest.approx(0.5)
    assert aggregates["provider_alpha"].average_support_coverage == pytest.approx(0.4)
    assert aggregates[
        "provider_alpha"
    ].average_representation_adequacy == pytest.approx(0.5)
    assert aggregates["provider_alpha"].average_uncertainty_honesty == pytest.approx(
        1.0
    )
    assert aggregates["provider_alpha"].average_noise_efficiency == pytest.approx(0.7)
    assert aggregates["provider_beta"].record_count == 2
    assert aggregates["provider_beta"].budget_compliance_rate == pytest.approx(1.0)
    assert aggregates["provider_beta"].average_aggregate_score == pytest.approx(0.3)
    assert aggregates["provider_beta"].average_edit_coverage == pytest.approx(0.5)
    assert aggregates["provider_beta"].average_support_coverage is None
    assert aggregates["provider_beta"].average_representation_adequacy == pytest.approx(
        0.5
    )
    assert aggregates["provider_beta"].average_uncertainty_honesty == pytest.approx(0.2)
    assert aggregates["provider_beta"].average_noise_efficiency == pytest.approx(0.8)


def test_legacy_scalar_only_ledger_loads_and_renders_empty_accounting(
    tmp_path: Path,
) -> None:
    """Legacy scalar-only rows still load and render deterministic empty accounting."""
    legacy_record = _ledger_record(run_id="run-legacy")
    del legacy_record["provider_metadata"]
    del legacy_record["resolved_selectors"]
    ledger_path = _write_ledger_records(
        tmp_path / "legacy_scalar_only.jsonl",
        [legacy_record],
    )

    ledger = eval_summary.load_eval_ledger(ledger_path)
    summary = eval_summary.build_eval_ledger_summary(ledger)
    rendered = eval_summary.render_eval_ledger_summary(summary)

    assert ledger.records[0].resolved_selectors == ()
    assert ledger.records[0].selected_units == ()
    assert summary.selector_tier_expectation_aggregates == ()
    assert summary.selector_runtime_expectation_aggregates == ()
    assert summary.selected_unit_tier_aggregates == ()
    assert "## Capability-Tier Accounting" in rendered
    assert "### Selector Expectations by Declared Primary Tier" in rendered
    assert "### Selector Runtime Provenance Expectations" in rendered
    assert "### Selected Units by Actual Primary Tier" in rendered
    assert rendered.count("- None") == 3


def test_task_budget_rows_are_sorted_and_preserve_provider_comparisons(
    tmp_path: Path,
) -> None:
    """Task-budget results sort by task then budget and provider name."""
    ledger_path = _write_ledger_records(
        tmp_path / "task_budget.jsonl",
        [
            _ledger_record(
                run_id="run-z-b",
                task_id="task_zeta",
                budget=200,
                provider_name="provider_beta",
                aggregate_score=0.2,
            ),
            _ledger_record(
                run_id="run-a-c",
                task_id="task_alpha",
                budget=100,
                provider_name="provider_charlie",
                aggregate_score=0.3,
            ),
            _ledger_record(
                run_id="run-z-a",
                task_id="task_zeta",
                budget=200,
                provider_name="provider_alpha",
                aggregate_score=0.9,
            ),
            _ledger_record(
                run_id="run-a-a",
                task_id="task_alpha",
                budget=100,
                provider_name="provider_alpha",
                aggregate_score=0.7,
            ),
        ],
    )

    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(ledger_path)
    )

    assert tuple(
        (result.task_id, result.budget) for result in summary.task_budget_results
    ) == (
        ("task_alpha", 100),
        ("task_zeta", 200),
    )
    assert tuple(
        provider_result.provider_name
        for provider_result in summary.task_budget_results[0].provider_results
    ) == ("provider_alpha", "provider_charlie")
    assert tuple(
        provider_result.provider_name
        for provider_result in summary.task_budget_results[1].provider_results
    ) == ("provider_alpha", "provider_beta")
    assert summary.task_budget_results[0].winner_provider_names == ("provider_alpha",)


def test_capability_tier_accounting_is_grouped_deterministically(
    tmp_path: Path,
) -> None:
    """Declared selector tiers and selected-unit tiers roll up deterministically."""
    ledger_path = _write_ledger_records(
        tmp_path / "capability_accounting.jsonl",
        [
            _ledger_record(
                run_id="run-alpha",
                resolved_selectors=[
                    _resolved_selector_record(
                        expected_primary_capability_tier="statically_proved",
                        expect_attached_runtime_provenance=False,
                        primary_capability_tier="statically_proved",
                        has_attached_runtime_provenance=False,
                    ),
                    _resolved_selector_record(
                        expected_primary_capability_tier="unsupported/opaque",
                        expect_attached_runtime_provenance=True,
                        primary_capability_tier="unsupported/opaque",
                        has_attached_runtime_provenance=True,
                    ),
                    _resolved_selector_record(
                        expected_primary_capability_tier="heuristic/frontier",
                        expect_attached_runtime_provenance=False,
                        primary_capability_tier="unsupported/opaque",
                        has_attached_runtime_provenance=True,
                    ),
                ],
                selected_units=[
                    _selected_unit_record(
                        primary_capability_tier="statically_proved",
                        has_attached_runtime_provenance=False,
                    ),
                    _selected_unit_record(
                        primary_capability_tier="unsupported/opaque",
                        has_attached_runtime_provenance=True,
                    ),
                ],
            ),
            _ledger_record(
                run_id="run-beta",
                provider_name="provider_beta",
                resolved_selectors=[
                    _resolved_selector_record(
                        expected_primary_capability_tier="heuristic/frontier",
                        expect_attached_runtime_provenance=False,
                        primary_capability_tier="heuristic/frontier",
                        has_attached_runtime_provenance=False,
                    ),
                ],
                selected_units=[
                    _selected_unit_record(
                        primary_capability_tier="heuristic/frontier",
                        has_attached_runtime_provenance=False,
                    ),
                    _selected_unit_record(
                        primary_capability_tier="unsupported/opaque",
                        has_attached_runtime_provenance=False,
                    ),
                ],
            ),
        ],
    )

    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(ledger_path)
    )

    assert tuple(
        (
            aggregate.expected_primary_capability_tier,
            aggregate.selector_count,
            aggregate.satisfied_count,
        )
        for aggregate in summary.selector_tier_expectation_aggregates
    ) == (
        ("statically_proved", 1, 1),
        ("heuristic/frontier", 2, 1),
        ("unsupported/opaque", 1, 1),
    )
    assert tuple(
        (
            aggregate.expected_attached_runtime_provenance,
            aggregate.selector_count,
            aggregate.satisfied_count,
        )
        for aggregate in summary.selector_runtime_expectation_aggregates
    ) == (
        (True, 1, 1),
        (False, 3, 2),
    )
    assert tuple(
        (
            aggregate.primary_capability_tier,
            aggregate.selected_unit_count,
            aggregate.attached_runtime_provenance_count,
        )
        for aggregate in summary.selected_unit_tier_aggregates
    ) == (
        ("statically_proved", 1, 0),
        ("heuristic/frontier", 1, 0),
        ("unsupported/opaque", 2, 1),
    )


def test_exact_ties_are_preserved_in_summary_and_rendering(tmp_path: Path) -> None:
    """Exact aggregate-score ties are rendered explicitly as ties."""
    ledger_path = _write_ledger_records(
        tmp_path / "tie.jsonl",
        [
            _ledger_record(
                run_id="run-beta",
                provider_name="provider_beta",
                aggregate_score=0.75,
            ),
            _ledger_record(
                run_id="run-alpha",
                provider_name="provider_alpha",
                aggregate_score=0.75,
            ),
        ],
    )

    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(ledger_path)
    )
    rendered = eval_summary.render_eval_ledger_summary(summary)

    assert summary.task_budget_results[0].winner_provider_names == (
        "provider_alpha",
        "provider_beta",
    )
    assert "tie: provider_alpha, provider_beta" in rendered


def test_markdown_rendering_is_deterministic_for_the_accepted_smoke_ledger(
    tmp_path: Path,
) -> None:
    """Independent accepted smoke ledgers render to the same Markdown output."""
    first_summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(_execute_smoke_ledger(tmp_path / "first.jsonl"))
    )
    second_summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(_execute_smoke_ledger(tmp_path / "second.jsonl"))
    )

    assert eval_summary.render_eval_ledger_summary(first_summary) == (
        eval_summary.render_eval_ledger_summary(second_summary)
    )


def test_markdown_includes_internal_accounting_and_task_budget_sections(
    tmp_path: Path,
) -> None:
    """Rendered Markdown includes the required internal summary sections."""
    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(_execute_smoke_ledger(tmp_path / "smoke.jsonl"))
    )
    rendered = eval_summary.render_eval_ledger_summary(summary)

    assert rendered.startswith("# Eval Summary\n")
    assert "## Provider Aggregates" in rendered
    assert "## Capability-Tier Accounting" in rendered
    assert "### Selector Expectations by Declared Primary Tier" in rendered
    assert "### Selector Runtime Provenance Expectations" in rendered
    assert "### Selected Units by Actual Primary Tier" in rendered
    assert "## Task Budget Results" in rendered
    assert "| Provider | Records | Budget Compliance |" in rendered
    assert rendered.count("- None") >= 1
    assert "| Actual Primary Tier | Selected Units | Attached Runtime Provenance |" in (
        rendered
    )
    assert "| Task | Budget | Winner | Provider Results |" in rendered


def test_budget_violations_render_only_when_present(tmp_path: Path) -> None:
    """Budget violations are review-only output and render only when needed."""
    clean_summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(
            _write_ledger_records(
                tmp_path / "clean.jsonl",
                [
                    _ledger_record(run_id="run-clean-1"),
                    _ledger_record(
                        run_id="run-clean-2",
                        provider_name="provider_beta",
                    ),
                ],
            )
        )
    )
    violating_summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(
            _write_ledger_records(
                tmp_path / "violations.jsonl",
                [
                    _ledger_record(run_id="run-violation", budget_compliant=False),
                ],
            )
        )
    )

    clean_rendered = eval_summary.render_eval_ledger_summary(clean_summary)
    violating_rendered = eval_summary.render_eval_ledger_summary(violating_summary)

    assert "## Budget Violations" not in clean_rendered
    assert "## Budget Violations" in violating_rendered
    assert "- run-violation" in violating_rendered


def test_loading_and_summarizing_do_not_mutate_inputs(tmp_path: Path) -> None:
    """Loading and summary rendering treat typed ledger inputs as immutable."""
    ledger = eval_summary.load_eval_ledger(
        _execute_smoke_ledger(tmp_path / "smoke.jsonl")
    )
    ledger_before = copy.deepcopy(ledger)

    summary = eval_summary.build_eval_ledger_summary(ledger)
    summary_before = copy.deepcopy(summary)

    eval_summary.render_eval_ledger_summary(summary)

    assert ledger == ledger_before
    assert summary == summary_before


def test_eval_summary_stays_internal_and_avoids_public_claim_surfaces() -> None:
    """Summary rendering remains internal and does not add public surfaces."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "load_eval_ledger" not in context_ir.__all__
    assert not hasattr(context_ir, "load_eval_ledger")
    assert not hasattr(eval_summary, "export_public_eval_summary")
    assert not hasattr(eval_summary, "render_public_claims")
    assert not hasattr(eval_summary, "publish_eval_report")

    forbidden_fields = {
        "public_claims",
        "claim_gate",
        "readme_path",
        "eval_md_path",
        "published_report",
    }
    summary_fields = set(eval_summary.EvalLedgerSummary.__dataclass_fields__)

    assert forbidden_fields.isdisjoint(summary_fields)

"""Isolated one-argument ``vars`` runtime-backed eval pilot tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import context_ir
import context_ir.eval_providers as eval_providers
import context_ir.eval_report as eval_report
import context_ir.eval_runs as eval_runs
import context_ir.eval_summary as eval_summary
import context_ir.semantic_types as semantic_types
from context_ir.eval_oracles import (
    SymbolOracleSelector,
    UnsupportedOracleSelector,
    load_fixture_vars_runtime_observations,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import CapabilityTier

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_vars_probe"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_vars_probe.json"
RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_vars_probe_matrix.json"
)
PROBE_BUDGETS = (220,)
PROBE_PROVIDERS = (
    eval_providers.CONTEXT_IR_PROVIDER,
    eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
    eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
BASELINE_PROVIDERS = (
    eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
    eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
QUERY = (
    "Fix probe_namespace unsupported vars(obj) returned namespace and keep digest "
    "output aligned"
)
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:7:11"


def _parsed_ledger_records(ledger_path: Path) -> list[dict[str, object]]:
    """Return parsed JSON objects from one JSONL ledger file."""
    return [
        cast(dict[str, object], json.loads(line))
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
    ]


def _record_for(
    records: list[dict[str, object]],
    *,
    provider_name: str,
    budget: int,
) -> dict[str, object]:
    """Return one raw ledger record by provider and budget."""
    return next(
        record
        for record in records
        if record["provider_name"] == provider_name and record["budget"] == budget
    )


def _selected_units(record: dict[str, object]) -> list[dict[str, object]]:
    """Return structured selected-unit metadata from one raw ledger record."""
    provider_metadata = cast(dict[str, object], record["provider_metadata"])
    return cast(list[dict[str, object]], provider_metadata["selected_units"])


def test_vars_probe_task_resolves_expected_selectors_deterministically() -> None:
    """The isolated probe resolves the intended symbol and unsupported selectors."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_vars_probe"
    assert setup.task.fixture_id == "oracle_signal_vars_probe"
    assert len(setup.task.expected_selectors) == 3
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], UnsupportedOracleSelector)
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.probe_namespace",
        "def:main.py:main.render_probe_digest",
        UNSUPPORTED_UNIT_ID,
    ]

    unsupported = setup.resolved_selectors[2]
    assert unsupported.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert unsupported.has_attached_runtime_provenance is True
    assert unsupported.attached_runtime_provenance_record_ids


def test_vars_probe_run_spec_loads_cleanly_through_runner() -> None:
    """The isolated probe run spec stays valid runner input."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_vars_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_vars_probe"
    assert case.task_path == "evals/tasks/oracle_signal_vars_probe.json"
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_vars_probe_fixture_uses_one_argument_returned_namespace_payload() -> None:
    """The fixture preserves the accepted one-argument ``vars(obj)`` branch."""
    observations = load_fixture_vars_runtime_observations(FIXTURE_ROOT)

    assert len(observations) == 1
    assert observations[0].site.snippet == "vars(obj)"
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (("lookup_outcome", "returned_namespace"),)


def test_vars_probe_assets_stay_internal() -> None:
    """The isolated probe remains internal and does not widen public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_vars_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_vars_probe")


def test_vars_probe_run_executes_with_runtime_backed_raw_fields(
    tmp_path: Path,
) -> None:
    """Run execution preserves additive runtime provenance in raw pilot records."""
    ledger_path = tmp_path / "vars_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_vars_probe_matrix"
    assert execution.record_count == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert len(records) == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert {(record["provider_name"], record["budget"]) for record in records} == {
        (provider_name, budget)
        for provider_name in PROBE_PROVIDERS
        for budget in PROBE_BUDGETS
    }

    for provider_name in BASELINE_PROVIDERS:
        baseline_record = _record_for(
            records,
            provider_name=provider_name,
            budget=220,
        )
        assert baseline_record["selected_unit_ids"] == []
        assert _selected_units(baseline_record) == []

    record = _record_for(
        records,
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=220,
    )
    metrics = cast(dict[str, object], record["metrics"])
    runtime_provenance_records = cast(
        list[dict[str, object]],
        record["runtime_provenance_records"],
    )
    unsupported_unit = next(
        unit
        for unit in _selected_units(record)
        if unit["unit_id"] == UNSUPPORTED_UNIT_ID
    )

    assert record["spec_version"] == "v1"
    assert record["provider_name"] == eval_providers.CONTEXT_IR_PROVIDER
    assert UNSUPPORTED_UNIT_ID in cast(list[str], record["selected_unit_ids"])
    assert metrics["uncertainty_honesty"] == 1.0
    assert unsupported_unit["primary_capability_tier"] == "unsupported/opaque"
    assert unsupported_unit["has_attached_runtime_provenance"] is True
    assert cast(
        list[str],
        unsupported_unit["attached_runtime_provenance_record_ids"],
    )
    assert len(runtime_provenance_records) == 1
    assert runtime_provenance_records[0]["normalized_payload"] == {
        "lookup_outcome": "returned_namespace",
    }


def test_vars_probe_summary_surfaces_internal_capability_accounting(
    tmp_path: Path,
) -> None:
    """The accepted pilot renders tier-aware accounting without widening claims."""
    ledger_path = tmp_path / "vars_probe.jsonl"

    eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(ledger_path)
    )
    rendered = eval_summary.render_eval_ledger_summary(summary)

    unsupported_selector_aggregate = next(
        aggregate
        for aggregate in summary.selector_tier_expectation_aggregates
        if aggregate.expected_primary_capability_tier == "unsupported/opaque"
    )
    runtime_expectation_aggregate = next(
        aggregate
        for aggregate in summary.selector_runtime_expectation_aggregates
        if aggregate.expected_attached_runtime_provenance is True
    )
    runtime_outcome_aggregate = next(
        aggregate
        for aggregate in summary.runtime_outcome_aggregates
        if aggregate.payload_key == "lookup_outcome"
        and aggregate.payload_value == "returned_namespace"
    )
    unsupported_selected_unit_aggregate = next(
        aggregate
        for aggregate in summary.selected_unit_tier_aggregates
        if aggregate.primary_capability_tier == "unsupported/opaque"
    )
    provider_unsupported_selected_unit_aggregate = next(
        aggregate
        for aggregate in summary.provider_selected_unit_tier_aggregates
        if aggregate.provider_name == eval_providers.CONTEXT_IR_PROVIDER
        and aggregate.primary_capability_tier == "unsupported/opaque"
    )
    report = eval_report.build_eval_report(ledger_path)

    assert unsupported_selector_aggregate.selector_count == 3
    assert unsupported_selector_aggregate.satisfied_count == 3
    assert runtime_expectation_aggregate.selector_count == 3
    assert runtime_expectation_aggregate.satisfied_count == 3
    assert runtime_outcome_aggregate.runtime_provenance_count == 3
    assert unsupported_selected_unit_aggregate.selected_unit_count == 1
    assert unsupported_selected_unit_aggregate.attached_runtime_provenance_count == 1
    assert provider_unsupported_selected_unit_aggregate.selected_unit_count == 1
    assert (
        provider_unsupported_selected_unit_aggregate.attached_runtime_provenance_count
        == 1
    )

    assert report.markdown_report == rendered
    for markdown in (rendered, report.markdown_report):
        assert "## Capability-Tier Accounting" in markdown
        assert "### Selected Units by Provider" in markdown
        assert "| yes | 3 | 3 |" in markdown
        assert "| lookup_outcome | returned_namespace | 3 |" in markdown
        assert "| unsupported/opaque | 1 | 1 |" in markdown
        assert "| runtime_backed |" not in markdown

"""Isolated dynamic-import runtime-backed eval pilot tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_providers as eval_providers
import context_ir.eval_report as eval_report
import context_ir.eval_runs as eval_runs
import context_ir.eval_summary as eval_summary
import context_ir.runtime_probe_results as runtime_probe_results
import context_ir.semantic_types as semantic_types
import context_ir.tool_facade as tool_facade
from context_ir.eval_oracles import (
    SymbolOracleSelector,
    UnsupportedOracleSelector,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import CapabilityTier, EvidenceOriginKind, ReplayStatus

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_dynamic_import_probe"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_dynamic_import_probe.json"
RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_dynamic_import_probe_matrix.json"
)
PROBE_BUDGETS = (220, 180, 100)
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
    'Fix unsupported dynamic import import_module("plugins.weather") '
    "while keeping probe digest output aligned"
)
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:5:13"
UNSUPPORTED_SITE_ID = "site:call:main.py:5:13"
BUDGET_100_CONTEXT_IR_SELECTED_UNIT_IDS = (
    "def:main.py:main.load_weather_plugin",
    "def:main.py:main.render_probe_digest",
    "frontier:call:main.py:6:11",
)


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


def _resolved_selectors(record: dict[str, object]) -> list[dict[str, object]]:
    """Return structured resolved-selector metadata from one raw ledger record."""
    return cast(list[dict[str, object]], record["resolved_selectors"])


def test_dynamic_import_probe_task_resolves_expected_selectors_deterministically() -> (
    None
):
    """The isolated probe resolves the intended symbol and unsupported selectors."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_dynamic_import_probe"
    assert setup.task.fixture_id == "oracle_signal_dynamic_import_probe"
    assert len(setup.task.expected_selectors) == 3
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], UnsupportedOracleSelector)
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.load_weather_plugin",
        "def:main.py:main.render_probe_digest",
        UNSUPPORTED_UNIT_ID,
    ]

    unsupported = setup.resolved_selectors[2]
    assert unsupported.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert unsupported.has_attached_runtime_provenance is True
    assert unsupported.attached_runtime_provenance_record_ids


def test_dynamic_import_probe_keeps_imported_module_out_of_static_edges() -> None:
    """Runtime evidence does not turn plugins.weather into static proof."""
    setup = setup_eval_oracle_task(TASK_PATH)
    program = setup.semantic_program
    symbols_by_id = program.resolved_symbols
    load_weather_symbol_id = next(
        symbol.symbol_id
        for symbol in symbols_by_id.values()
        if symbol.qualified_name == "main.load_weather_plugin"
    )
    weather_symbol_ids = {
        symbol.symbol_id
        for symbol in symbols_by_id.values()
        if symbol.definition_site.file_path == "plugins/weather.py"
    }

    assert weather_symbol_ids
    assert all(
        resolved_import.target_qualified_name != "plugins.weather"
        for resolved_import in program.resolved_imports
    )
    assert all(
        UNSUPPORTED_UNIT_ID
        not in (dependency.source_symbol_id, dependency.target_symbol_id)
        for dependency in program.proven_dependencies
    )
    assert all(
        dependency.evidence_site_id != UNSUPPORTED_SITE_ID
        for dependency in program.proven_dependencies
    )
    assert all(
        not (
            dependency.source_symbol_id == load_weather_symbol_id
            and dependency.target_symbol_id in weather_symbol_ids
        )
        for dependency in program.proven_dependencies
    )
    assert all(
        selector.resolved_unit_id not in weather_symbol_ids
        for selector in setup.resolved_selectors
    )


def test_dynamic_import_probe_run_spec_loads_cleanly_through_runner() -> None:
    """The isolated probe run spec stays valid runner input."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_dynamic_import_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_dynamic_import_probe"
    assert case.task_path == "evals/tasks/oracle_signal_dynamic_import_probe.json"
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_dynamic_import_probe_assets_stay_internal() -> None:
    """The isolated probe remains internal and does not widen public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_dynamic_import_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_dynamic_import_probe")


def test_dynamic_import_probe_default_local_provider_replays_exact_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default local-Python provider admits only the exact literal fixture."""
    captured_responses: list[
        tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileResponse
    ] = []
    real_dynamic_recompile = eval_providers.tool_facade.recompile_repository_context_with_dynamic_import_local_python_subprocess  # noqa: E501

    def capture_dynamic_import_recompile(
        recompile_request: (
            tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileRequest
        ),
    ) -> tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileResponse:
        response = real_dynamic_recompile(recompile_request)
        captured_responses.append(response)
        return response

    def reject_default_recompile(
        recompile_request: (
            tool_facade.SemanticDefaultLocalPythonSubprocessRecompileRequest
        ),
    ) -> tool_facade.SemanticDefaultLocalPythonSubprocessRecompileResponse:
        del recompile_request
        raise AssertionError("default subprocess facade should not be used")

    monkeypatch.setattr(
        eval_providers.tool_facade,
        "recompile_repository_context_with_dynamic_import_local_python_subprocess",
        capture_dynamic_import_recompile,
    )
    monkeypatch.setattr(
        eval_providers.tool_facade,
        "recompile_repository_context_with_default_local_python_subprocess",
        reject_default_recompile,
    )

    result = eval_providers.build_context_ir_default_local_python_subprocess_pack(
        eval_providers.EvalProviderRequest(
            repo_root=FIXTURE_ROOT,
            task_id="oracle_signal_dynamic_import_probe",
            query=QUERY,
            budget=180,
        )
    )
    unsupported_unit = next(
        unit
        for unit in result.metadata.selected_units
        if unit.unit_id == UNSUPPORTED_UNIT_ID
    )
    static_units = tuple(
        unit
        for unit in result.metadata.selected_units
        if unit.unit_id != UNSUPPORTED_UNIT_ID
    )
    provenance_record = result.runtime_provenance_records[0]
    origin_detail = cast(dict[str, object], json.loads(provenance_record.origin_detail))
    fixture = eval_providers._default_local_python_subprocess_fixture(
        "oracle_signal_dynamic_import_probe"
    )
    previous_response = eval_providers.tool_facade.compile_repository_context(
        tool_facade.SemanticContextRequest(
            repo_root=FIXTURE_ROOT,
            query=QUERY,
            budget=180,
        )
    )
    miss_evidence = semantic_types.SemanticMissEvidence(
        kind=semantic_types.SemanticMissKind.ABSENT_SYMBOL,
        evidence='import_module("plugins.weather")',
    )
    diagnostic = eval_providers.diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    planned_request = (
        eval_providers._require_default_local_python_runtime_probe_request(
            diagnostic,
            fixture,
        )
    )
    weather_symbol_ids = {
        symbol.symbol_id
        for symbol in captured_responses[0].program.resolved_symbols.values()
        if symbol.definition_site.file_path == "plugins/weather.py"
    }
    load_weather_symbol_id = next(
        symbol.symbol_id
        for symbol in captured_responses[0].program.resolved_symbols.values()
        if symbol.qualified_name == "main.load_weather_plugin"
    )

    assert result.provider_name == (
        eval_providers.CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    )
    assert result.task_id == "oracle_signal_dynamic_import_probe"
    assert result.budget == 180
    assert captured_responses[0].compile_budget == 180
    assert result.selected_files == ()
    assert result.warnings == ()
    assert planned_request.subject_id == UNSUPPORTED_UNIT_ID
    assert planned_request.boundary_text == 'import_module("plugins.weather")'
    assert (
        planned_request.family_label is eval_providers.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert planned_request.form_label == "dynamic_import:import_module/1"
    assert planned_request.replay_target_seed == "main.load_weather_plugin"
    assert planned_request.replay_selector_seed == (
        "call:main.load_weather_plugin:dynamic_import:import_module/1@main.py:5:13:5:45"
    )
    assert len(captured_responses) == 1
    runner_attempts = captured_responses[0].runner_attempt_collection.attempts
    runner_results = captured_responses[
        0
    ].runner_attempt_collection.result_batch.results
    assert len(runner_attempts) == 1
    assert len(runner_results) == 1
    assert runner_attempts[0].request == planned_request
    assert runner_attempts[0].outcome is (
        runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    )
    assert runner_attempts[0].observed_replay_inputs == ()
    assert tuple(
        (field.key, field.value) for field in runner_attempts[0].normalized_payload
    ) == (("imported_module", "plugins.weather"),)
    assert isinstance(
        runner_results[0],
        runtime_probe_results.RuntimeProbeObservedResult,
    )
    assert runner_results[0].request == planned_request
    assert tuple(
        (field.key, field.value) for field in runner_results[0].normalized_payload
    ) == (("imported_module", "plugins.weather"),)
    assert len(result.runtime_provenance_records) == 1
    assert origin_detail["normalized_payload"] == {"imported_module": "plugins.weather"}
    assert origin_detail["replay_target"] == "main.load_weather_plugin"
    assert origin_detail["replay_selector"] == (
        "call:main.load_weather_plugin:dynamic_import:import_module/1@main.py:5:13:5:45"
    )
    assert "observed_replay_inputs" not in origin_detail
    assert unsupported_unit.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        unsupported_unit.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported_unit.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported_unit.has_attached_runtime_provenance is True
    assert unsupported_unit.attached_runtime_provenance_record_ids == (
        provenance_record.record_id,
    )
    assert all(
        unit.primary_capability_tier is not CapabilityTier.RUNTIME_BACKED
        for unit in result.metadata.selected_units
    )
    assert all(
        unit.primary_capability_tier
        in {CapabilityTier.STATICALLY_PROVED, CapabilityTier.HEURISTIC_FRONTIER}
        for unit in static_units
    )
    assert all(unit.has_attached_runtime_provenance is False for unit in static_units)
    assert all(
        "plugins/weather.py" not in unit_id and "plugins.weather" not in unit_id
        for unit_id in result.selected_unit_ids
    )
    assert all(
        unit_id not in weather_symbol_ids for unit_id in result.selected_unit_ids
    )
    assert all(
        resolved_import.target_qualified_name != "plugins.weather"
        for resolved_import in captured_responses[0].program.resolved_imports
    )
    assert all(
        dependency.evidence_site_id != UNSUPPORTED_SITE_ID
        for dependency in captured_responses[0].program.proven_dependencies
    )
    assert all(
        not (
            dependency.source_symbol_id == load_weather_symbol_id
            and dependency.target_symbol_id in weather_symbol_ids
        )
        for dependency in captured_responses[0].program.proven_dependencies
    )


def test_dynamic_import_probe_default_local_provider_fails_closed_above_safe_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact literal fixture rejects unsupported budgets instead of capping."""

    def reject_compile(
        compile_request: tool_facade.SemanticContextRequest,
    ) -> tool_facade.SemanticContextResponse:
        del compile_request
        raise AssertionError("unsupported budget should fail before compilation")

    monkeypatch.setattr(
        eval_providers.tool_facade,
        "compile_repository_context",
        reject_compile,
    )

    with pytest.raises(
        ValueError,
        match=(
            "context_ir_default_local_python_subprocess only supports "
            "budget 180 for oracle_signal_dynamic_import_probe"
        ),
    ):
        eval_providers.build_context_ir_default_local_python_subprocess_pack(
            eval_providers.EvalProviderRequest(
                repo_root=FIXTURE_ROOT,
                task_id="oracle_signal_dynamic_import_probe",
                query=QUERY,
                budget=220,
            )
        )


def test_dynamic_import_probe_run_executes_with_runtime_backed_raw_fields(
    tmp_path: Path,
) -> None:
    """Run execution preserves additive runtime provenance in raw pilot records."""
    ledger_path = tmp_path / "dynamic_import_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_dynamic_import_probe_matrix"
    assert execution.record_count == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert len(records) == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert {(record["provider_name"], record["budget"]) for record in records} == {
        (provider_name, budget)
        for provider_name in PROBE_PROVIDERS
        for budget in PROBE_BUDGETS
    }

    for provider_name in BASELINE_PROVIDERS:
        for budget in PROBE_BUDGETS:
            baseline_record = _record_for(
                records,
                provider_name=provider_name,
                budget=budget,
            )
            assert baseline_record["selected_unit_ids"] == []
            assert _selected_units(baseline_record) == []

    for raw_record in records:
        runtime_provenance_records = cast(
            list[dict[str, object]],
            raw_record["runtime_provenance_records"],
        )

        assert len(runtime_provenance_records) == 1
        assert runtime_provenance_records[0]["normalized_payload"] == {
            "imported_module": "plugins.weather"
        }

    record = _record_for(
        records,
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=220,
    )
    metrics = cast(dict[str, object], record["metrics"])
    unsupported_unit = next(
        unit
        for unit in _selected_units(record)
        if unit["unit_id"] == "unsupported:call:main.py:5:13"
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

    budget_100_record = _record_for(
        records,
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=100,
    )
    budget_100_metrics = cast(dict[str, object], budget_100_record["metrics"])
    budget_100_selected_units = _selected_units(budget_100_record)
    budget_100_unsupported_selector = next(
        selector
        for selector in _resolved_selectors(budget_100_record)
        if selector["resolved_unit_id"] == UNSUPPORTED_UNIT_ID
    )

    assert budget_100_record["selected_files"] == []
    assert (
        tuple(cast(list[str], budget_100_record["selected_unit_ids"]))
        == BUDGET_100_CONTEXT_IR_SELECTED_UNIT_IDS
    )
    assert [unit["unit_id"] for unit in budget_100_selected_units] == list(
        BUDGET_100_CONTEXT_IR_SELECTED_UNIT_IDS
    )
    assert all(
        "plugins/weather.py" not in cast(str, unit["unit_id"])
        for unit in budget_100_selected_units
    )
    assert all(
        unit["has_attached_runtime_provenance"] is False
        and unit["attached_runtime_provenance_record_ids"] == []
        for unit in budget_100_selected_units
    )
    assert budget_100_metrics["uncertainty_honesty"] == 0.25
    assert budget_100_metrics["aggregate_score"] == 0.0375
    assert budget_100_metrics["omitted_expected_uncertainty_ids"] == [
        UNSUPPORTED_UNIT_ID
    ]
    assert budget_100_metrics["selected_matched_selector_ids"] == [
        "def:main.py:main.load_weather_plugin",
        "def:main.py:main.render_probe_digest",
    ]
    assert budget_100_metrics["too_shallow_selector_ids"] == [
        "def:main.py:main.load_weather_plugin",
        "def:main.py:main.render_probe_digest",
    ]
    assert UNSUPPORTED_UNIT_ID not in cast(
        list[str], budget_100_record["selected_unit_ids"]
    )
    assert budget_100_unsupported_selector["primary_capability_tier"] == (
        "unsupported/opaque"
    )
    assert budget_100_unsupported_selector["primary_evidence_origin"] == (
        "unsupported_reason_code"
    )
    assert budget_100_unsupported_selector["primary_replay_status"] == (
        "opaque_boundary"
    )
    assert budget_100_unsupported_selector["has_attached_runtime_provenance"] is True
    assert cast(
        list[str],
        budget_100_unsupported_selector["attached_runtime_provenance_record_ids"],
    )


def test_dynamic_import_probe_summary_surfaces_internal_capability_accounting(
    tmp_path: Path,
) -> None:
    """The accepted pilot renders tier-aware accounting without widening claims."""
    ledger_path = tmp_path / "dynamic_import_probe.jsonl"

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

    assert unsupported_selector_aggregate.selector_count == 9
    assert unsupported_selector_aggregate.satisfied_count == 9
    assert runtime_expectation_aggregate.selector_count == 9
    assert runtime_expectation_aggregate.satisfied_count == 9
    assert tuple(
        (
            aggregate.primary_capability_tier,
            aggregate.selected_unit_count,
            aggregate.attached_runtime_provenance_count,
        )
        for aggregate in summary.selected_unit_tier_aggregates
    ) == (
        ("statically_proved", 7, 0),
        ("heuristic/frontier", 3, 0),
        ("unsupported/opaque", 2, 2),
    )
    assert unsupported_selected_unit_aggregate.selected_unit_count == 2
    assert unsupported_selected_unit_aggregate.attached_runtime_provenance_count == 2
    assert tuple(
        (
            aggregate.provider_name,
            aggregate.selected_unit_count,
            aggregate.attached_runtime_provenance_count,
        )
        for aggregate in summary.provider_selected_unit_aggregates
    ) == (
        (eval_providers.CONTEXT_IR_PROVIDER, 12, 2),
        (eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER, 0, 0),
        (eval_providers.LEXICAL_TOP_K_FILES_PROVIDER, 0, 0),
    )
    assert tuple(
        (
            aggregate.provider_name,
            aggregate.primary_capability_tier,
            aggregate.selected_unit_count,
            aggregate.attached_runtime_provenance_count,
        )
        for aggregate in summary.provider_selected_unit_tier_aggregates
    ) == (
        (eval_providers.CONTEXT_IR_PROVIDER, "statically_proved", 7, 0),
        (eval_providers.CONTEXT_IR_PROVIDER, "heuristic/frontier", 3, 0),
        (eval_providers.CONTEXT_IR_PROVIDER, "unsupported/opaque", 2, 2),
    )
    assert provider_unsupported_selected_unit_aggregate.selected_unit_count == 2
    assert (
        provider_unsupported_selected_unit_aggregate.attached_runtime_provenance_count
        == 2
    )
    assert tuple(
        (result.budget, result.winner_provider_names)
        for result in summary.task_budget_results
    ) == (
        (100, (eval_providers.CONTEXT_IR_PROVIDER,)),
        (180, (eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,)),
        (220, (eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,)),
    )

    assert report.markdown_report == rendered
    for markdown in (rendered, report.markdown_report):
        assert "## Capability-Tier Accounting" in markdown
        assert "### Selected Units by Provider" in markdown
        assert "### Selected Units by Provider and Actual Primary Tier" in markdown
        assert "| yes | 9 | 9 |" in markdown
        assert "| unsupported/opaque | 2 | 2 |" in markdown
        assert "| context_ir | 12 | 2 |" in markdown
        assert "| import_neighborhood_files | 0 | 0 |" in markdown
        assert "| lexical_top_k_files | 0 | 0 |" in markdown
        assert "| context_ir | unsupported/opaque | 2 | 2 |" in markdown
        assert "| oracle_signal_dynamic_import_probe | 100 | context_ir |" in markdown
        assert (
            "| oracle_signal_dynamic_import_probe | 180 | import_neighborhood_files |"
        ) in markdown
        assert (
            "| oracle_signal_dynamic_import_probe | 220 | import_neighborhood_files |"
        ) in markdown
        assert "| runtime_backed |" not in markdown

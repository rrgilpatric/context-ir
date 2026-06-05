"""Isolated ``vars(obj)`` raised-TypeError runtime-backed eval pilot tests."""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
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
    load_fixture_vars_runtime_observations,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_vars_type_error_probe"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_vars_type_error_probe.json"
RUN_SPEC_PATH = (
    REPO_ROOT
    / "evals"
    / "run_specs"
    / "oracle_signal_vars_type_error_probe_matrix.json"
)
PROBE_BUDGETS = (220, 100)
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
    "Fix probe_namespace unsupported vars(obj) raised TypeError and keep digest "
    "output aligned"
)
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
UNSUPPORTED_SITE_ID = "site:call:main.py:2:11"
FAILED_LOOKUP_MARKERS = ("__dict__", "builtins.int")


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


def _load_fixture_module() -> ModuleType:
    """Load the isolated fixture module so its digest behavior can be checked."""
    spec = importlib.util.spec_from_file_location(
        "oracle_signal_vars_type_error_probe_fixture",
        FIXTURE_ROOT / "main.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_vars_type_error_probe_task_resolves_expected_selectors() -> None:
    """The raised-TypeError probe resolves the intended unsupported selector."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_vars_type_error_probe"
    assert setup.task.fixture_id == "oracle_signal_vars_type_error_probe"
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
    assert (
        unsupported.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported.has_attached_runtime_provenance is True
    assert unsupported.attached_runtime_provenance_record_ids
    assert all(
        marker not in (symbol.symbol_id, symbol.qualified_name)
        for marker in FAILED_LOOKUP_MARKERS
        for symbol in setup.semantic_program.resolved_symbols.values()
    )
    assert all(
        marker not in (dependency.source_symbol_id, dependency.target_symbol_id)
        for marker in FAILED_LOOKUP_MARKERS
        for dependency in setup.semantic_program.proven_dependencies
    )
    assert all(
        dependency.evidence_site_id != UNSUPPORTED_SITE_ID
        for dependency in setup.semantic_program.proven_dependencies
    )


def test_vars_type_error_probe_run_spec_loads_cleanly() -> None:
    """The raised-TypeError probe run spec stays valid runner input."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_vars_type_error_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_vars_type_error_probe"
    assert case.task_path == "evals/tasks/oracle_signal_vars_type_error_probe.json"
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_vars_type_error_probe_fixture_uses_raised_type_error_payload() -> None:
    """The fixture boundary is exactly ``vars(obj)`` for the TypeError branch."""
    source = (FIXTURE_ROOT / "main.py").read_text(encoding="utf-8")
    observations = load_fixture_vars_runtime_observations(FIXTURE_ROOT)

    assert source.count("vars(obj)") == 1
    assert "vars()" not in source
    assert len(observations) == 1
    assert observations[0].site.snippet == "vars(obj)"
    assert observations[0].site.span.start_line == 2
    assert observations[0].site.span.start_column == 11
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (("lookup_outcome", "raised_type_error"),)


def test_vars_type_error_probe_fixture_digest_is_deterministic() -> None:
    """The fixture catches ``TypeError`` before rendering its digest."""
    module = _load_fixture_module()
    render_probe_digest = cast(Callable[[], str], module.render_probe_digest)

    assert render_probe_digest() == "vars_type_error:raised_type_error"


def test_vars_type_error_probe_assets_stay_internal() -> None:
    """The raised-TypeError probe does not widen public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_vars_type_error_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_vars_type_error_probe")


def test_vars_type_error_probe_default_local_provider_replays_exact_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact provider replays only the raised-TypeError ``vars(obj)`` case."""
    captured_responses: list[
        tool_facade.SemanticDefaultLocalPythonSubprocessRecompileResponse
    ] = []
    original_recompile = (
        tool_facade.recompile_repository_context_with_default_local_python_subprocess
    )

    def capturing_recompile(
        request: tool_facade.SemanticDefaultLocalPythonSubprocessRecompileRequest,
    ) -> tool_facade.SemanticDefaultLocalPythonSubprocessRecompileResponse:
        response = original_recompile(request)
        captured_responses.append(response)
        return response

    monkeypatch.setattr(
        tool_facade,
        "recompile_repository_context_with_default_local_python_subprocess",
        capturing_recompile,
    )

    result = eval_providers.build_context_ir_default_local_python_subprocess_pack(
        eval_providers.EvalProviderRequest(
            repo_root=FIXTURE_ROOT,
            task_id="oracle_signal_vars_type_error_probe",
            query=QUERY,
            budget=100,
        )
    )

    assert len(captured_responses) == 1
    response = captured_responses[0]
    attempt = response.runner_attempt_collection.attempts[0]
    observed_result = response.runner_attempt_collection.result_batch.results[0]
    planned_request = attempt.request
    static_units = tuple(
        unit
        for unit in result.metadata.selected_units
        if unit.unit_id != UNSUPPORTED_UNIT_ID
    )
    boundary = next(
        candidate
        for candidate in response.diagnostic.boundary_classifications
        if candidate.unit_id == UNSUPPORTED_UNIT_ID
    )
    boundary_trace = boundary.trace_summary
    provenance_record = result.runtime_provenance_records[0]
    origin_detail = cast(dict[str, object], json.loads(provenance_record.origin_detail))

    assert result.provider_name == (
        eval_providers.CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    )
    assert result.task_id == "oracle_signal_vars_type_error_probe"
    assert result.budget == 100
    assert result.selected_files == ()
    assert result.warnings == ()
    assert planned_request.subject_id == UNSUPPORTED_UNIT_ID
    assert planned_request.boundary_text == "vars(obj)"
    assert (
        planned_request.family_label
        is eval_providers.RuntimeProbeFamily.REFLECTIVE_BUILTIN
    )
    assert planned_request.form_label == "reflective_builtin:vars/1"
    assert planned_request.replay_target_seed == "main.probe_namespace"
    assert attempt.normalized_payload == (
        runtime_probe_results.RuntimeProbeReplayField(
            key="lookup_outcome",
            value="raised_type_error",
        ),
    )
    assert attempt.observed_replay_inputs == ()
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.normalized_payload == attempt.normalized_payload
    assert tuple(
        (field.key, field.value)
        for field in observed_result.replay_artifact.replay_inputs[-1:]
    ) == (("object_type", "builtins.int"),)
    assert len(result.runtime_provenance_records) == 1
    assert result.runtime_provenance_records == tuple(
        response.program.provenance_records
    )
    assert origin_detail["normalized_payload"] == {
        "lookup_outcome": "raised_type_error",
    }
    assert "observed_replay_inputs" not in origin_detail
    assert provenance_record.subject_kind is (
        semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    )
    assert provenance_record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert boundary.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert boundary.has_attached_runtime_provenance is True
    assert boundary_trace is not None
    assert boundary_trace.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        boundary_trace.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert boundary_trace.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert boundary_trace.has_attached_runtime_provenance is True
    assert boundary_trace.attached_runtime_provenance_record_ids == (
        provenance_record.record_id,
    )
    assert all(
        unit.primary_capability_tier is CapabilityTier.STATICALLY_PROVED
        for unit in static_units
    )
    assert all(unit.has_attached_runtime_provenance is False for unit in static_units)
    assert all(
        unit.primary_capability_tier is not CapabilityTier.RUNTIME_BACKED
        for unit in result.metadata.selected_units
    )
    assert UNSUPPORTED_UNIT_ID not in result.selected_unit_ids
    assert all(
        marker not in unit.detail
        for marker in FAILED_LOOKUP_MARKERS
        for unit in result.metadata.selected_units
    )


def test_vars_type_error_probe_default_local_provider_fails_closed() -> None:
    """Wrong task IDs remain unsupported by the exact subprocess provider."""
    with pytest.raises(ValueError) as exc_info:
        eval_providers.build_context_ir_default_local_python_subprocess_pack(
            eval_providers.EvalProviderRequest(
                repo_root=FIXTURE_ROOT,
                task_id="oracle_signal_vars_type_error_probe_typo",
                query=QUERY,
                budget=100,
            )
        )

    message = str(exc_info.value)
    assert "context_ir_default_local_python_subprocess only supports" in message
    assert "oracle_signal_vars_type_error_probe" in message
    assert "oracle_signal_vars_type_error_probe_typo" not in message
    assert "oracle_signal_vars_probe" not in message
    assert "oracle_signal_setattr_probe" not in message
    assert "oracle_signal_delattr_probe" not in message


def test_vars_type_error_probe_run_preserves_additive_runtime_fields(
    tmp_path: Path,
) -> None:
    """Run execution keeps raised-TypeError provenance selector-additive only."""
    ledger_path = tmp_path / "vars_type_error_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_vars_type_error_probe_matrix"
    assert execution.record_count == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert len(records) == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert {(record["provider_name"], record["budget"]) for record in records} == {
        (provider_name, budget)
        for provider_name in PROBE_PROVIDERS
        for budget in PROBE_BUDGETS
    }

    for budget in PROBE_BUDGETS:
        for provider_name in BASELINE_PROVIDERS:
            baseline_record = _record_for(
                records,
                provider_name=provider_name,
                budget=budget,
            )
            assert baseline_record["selected_unit_ids"] == []
            assert _selected_units(baseline_record) == []

        record = _record_for(
            records,
            provider_name=eval_providers.CONTEXT_IR_PROVIDER,
            budget=budget,
        )
        runtime_provenance_records = cast(
            list[dict[str, object]],
            record["runtime_provenance_records"],
        )
        selected_units = _selected_units(record)
        unsupported_selector = next(
            selector
            for selector in _resolved_selectors(record)
            if selector["resolved_unit_id"] == UNSUPPORTED_UNIT_ID
        )

        assert record["spec_version"] == "v1"
        assert record["provider_name"] == eval_providers.CONTEXT_IR_PROVIDER
        assert record["budget"] == budget
        assert record["selected_unit_ids"] == [
            "def:main.py:main.render_probe_digest",
            "def:main.py:main.probe_namespace",
        ]
        assert unsupported_selector["primary_capability_tier"] == "unsupported/opaque"
        assert unsupported_selector["primary_evidence_origin"] == (
            "unsupported_reason_code"
        )
        assert unsupported_selector["primary_replay_status"] == "opaque_boundary"
        assert unsupported_selector["has_attached_runtime_provenance"] is True
        assert cast(
            list[str],
            unsupported_selector["attached_runtime_provenance_record_ids"],
        )
        assert len(runtime_provenance_records) == 1
        assert runtime_provenance_records[0]["normalized_payload"] == {
            "lookup_outcome": "raised_type_error",
        }
        assert all(
            unit["primary_capability_tier"] == "statically_proved"
            for unit in selected_units
        )
        assert all(
            unit["has_attached_runtime_provenance"] is False for unit in selected_units
        )
        assert all(unit["unit_id"] != UNSUPPORTED_UNIT_ID for unit in selected_units)
        assert all(
            marker not in json.dumps(unit, sort_keys=True)
            for marker in FAILED_LOOKUP_MARKERS
            for unit in selected_units
        )


def test_vars_type_error_probe_summary_keeps_runtime_additive(
    tmp_path: Path,
) -> None:
    """The probe renders tier accounting without runtime-backed promotion."""
    ledger_path = tmp_path / "vars_type_error_probe.jsonl"

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
        and aggregate.payload_value == "raised_type_error"
    )
    statically_proved_selected_unit_aggregate = next(
        aggregate
        for aggregate in summary.selected_unit_tier_aggregates
        if aggregate.primary_capability_tier == "statically_proved"
    )
    provider_statically_proved_selected_unit_aggregate = next(
        aggregate
        for aggregate in summary.provider_selected_unit_tier_aggregates
        if aggregate.provider_name == eval_providers.CONTEXT_IR_PROVIDER
        and aggregate.primary_capability_tier == "statically_proved"
    )
    report = eval_report.build_eval_report(ledger_path)
    expected_record_count = len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    expected_context_ir_symbol_count = len(PROBE_BUDGETS) * 2

    assert unsupported_selector_aggregate.selector_count == expected_record_count
    assert unsupported_selector_aggregate.satisfied_count == expected_record_count
    assert runtime_expectation_aggregate.selector_count == expected_record_count
    assert runtime_expectation_aggregate.satisfied_count == expected_record_count
    assert runtime_outcome_aggregate.runtime_provenance_count == expected_record_count
    assert (
        statically_proved_selected_unit_aggregate.selected_unit_count
        == expected_context_ir_symbol_count
    )
    assert (
        statically_proved_selected_unit_aggregate.attached_runtime_provenance_count == 0
    )
    assert (
        provider_statically_proved_selected_unit_aggregate.selected_unit_count
        == expected_context_ir_symbol_count
    )
    assert (
        provider_statically_proved_selected_unit_aggregate.attached_runtime_provenance_count
        == 0
    )
    assert all(
        aggregate.primary_capability_tier != "unsupported/opaque"
        for aggregate in summary.selected_unit_tier_aggregates
    )

    assert report.markdown_report == rendered
    for markdown in (rendered, report.markdown_report):
        assert "## Capability-Tier Accounting" in markdown
        assert "### Selected Units by Provider" in markdown
        assert (
            f"| yes | {expected_record_count} | {expected_record_count} |" in markdown
        )
        assert (
            f"| lookup_outcome | raised_type_error | {expected_record_count} |"
            in markdown
        )
        assert (
            f"| statically_proved | {expected_context_ir_symbol_count} | 0 |"
            in markdown
        )
        assert "| runtime_backed |" not in markdown

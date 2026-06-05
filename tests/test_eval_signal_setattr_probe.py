"""Isolated ``setattr`` runtime-backed eval pilot tests."""

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
    load_fixture_setattr_runtime_observations,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
    UnresolvedReasonCode,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_setattr_probe"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_setattr_probe.json"
RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_setattr_probe_matrix.json"
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
    "Fix probe_set_attribute unsupported setattr(obj, name, value) returned None "
    "and keep digest output aligned"
)
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:7:4"


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


def test_setattr_probe_task_resolves_expected_selectors_deterministically() -> None:
    """The isolated setattr probe resolves the intended selectors."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_setattr_probe"
    assert setup.task.fixture_id == "oracle_signal_setattr_probe"
    assert len(setup.task.expected_selectors) == 3
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], UnsupportedOracleSelector)
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.probe_set_attribute",
        "def:main.py:main.render_probe_digest",
        UNSUPPORTED_UNIT_ID,
    ]

    selector = setup.task.expected_selectors[2]
    unsupported = setup.resolved_selectors[2]
    assert isinstance(selector, UnsupportedOracleSelector)
    assert selector.reason_code is UnresolvedReasonCode.RUNTIME_MUTATION
    assert (
        selector.expected_primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    )
    assert selector.expect_attached_runtime_provenance is True
    assert unsupported.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        unsupported.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported.has_attached_runtime_provenance is True
    assert unsupported.attached_runtime_provenance_record_ids


def test_setattr_probe_run_spec_loads_budget_matrix() -> None:
    """The setattr probe run spec is one task x two budgets x three providers."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_setattr_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_setattr_probe"
    assert case.task_path == "evals/tasks/oracle_signal_setattr_probe.json"
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_setattr_probe_fixture_uses_returned_none_payload() -> None:
    """The fixture preserves the eval-only ``setattr`` runtime payload."""
    source = (FIXTURE_ROOT / "main.py").read_text(encoding="utf-8")
    observations = load_fixture_setattr_runtime_observations(FIXTURE_ROOT)

    assert source.count("setattr(obj, name, value)") == 1
    assert "delattr(" not in source
    assert "globals(" not in source
    assert "locals(" not in source
    assert "vars(" not in source
    assert len(observations) == 1
    assert observations[0].site.snippet == "setattr(obj, name, value)"
    assert observations[0].site.span.start_line == 7
    assert observations[0].site.span.start_column == 4
    assert tuple(
        (field.key, field.value) for field in observations[0].replay_inputs
    ) == (
        ("object_type", "main.ProbeTarget"),
        ("attribute_name", "flag"),
        ("assigned_value_type", "builtins.str"),
    )
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (("mutation_outcome", "returned_none"),)
    assert observations[0].durable_payload_reference


def test_setattr_probe_default_local_provider_replays_exact_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default local-Python provider admits only the exact name fixture."""
    recompile_requests: list[
        tool_facade.SemanticDefaultLocalPythonSubprocessRecompileRequest
    ] = []
    captured_responses: list[
        tool_facade.SemanticDefaultLocalPythonSubprocessRecompileResponse
    ] = []
    original_recompile = (
        tool_facade.recompile_repository_context_with_default_local_python_subprocess
    )

    def capturing_recompile(
        request: tool_facade.SemanticDefaultLocalPythonSubprocessRecompileRequest,
    ) -> tool_facade.SemanticDefaultLocalPythonSubprocessRecompileResponse:
        recompile_requests.append(request)
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
            task_id="oracle_signal_setattr_probe",
            query=QUERY,
            budget=220,
        )
    )

    assert len(recompile_requests) == 1
    assert len(captured_responses) == 1
    recompile_request = recompile_requests[0]
    response = captured_responses[0]
    attempt = response.runner_attempt_collection.attempts[0]
    observed_result = response.runner_attempt_collection.result_batch.results[0]
    planned_request = attempt.request
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
    boundary = next(
        candidate
        for candidate in response.diagnostic.boundary_classifications
        if candidate.unit_id == UNSUPPORTED_UNIT_ID
    )
    boundary_trace = boundary.trace_summary
    provenance_record = result.runtime_provenance_records[0]
    origin_detail = cast(dict[str, object], json.loads(provenance_record.origin_detail))
    expected_durable_reference = (
        f"artifact://runtime-probe/setattr-value/{planned_request.request_id}.json"
    )

    assert result.provider_name == (
        eval_providers.CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    )
    assert result.task_id == "oracle_signal_setattr_probe"
    assert result.budget == 220
    assert result.selected_files == ()
    assert result.warnings == ()
    assert recompile_request.repository_snapshot_basis.snapshot_kind == "eval_fixture"
    assert recompile_request.repository_snapshot_basis.snapshot_id == (
        "oracle_signal_setattr_probe@default-local-python:v1"
    )
    assert recompile_request.repository_snapshot_basis.is_dirty_worktree is False
    assert planned_request.subject_id == UNSUPPORTED_UNIT_ID
    assert planned_request.boundary_text == "setattr(obj, name, value)"
    assert (
        planned_request.family_label
        is eval_providers.RuntimeProbeFamily.RUNTIME_MUTATION
    )
    assert planned_request.form_label == "runtime_mutation:setattr/3"
    assert planned_request.replay_target_seed == "main.probe_set_attribute"
    assert attempt.normalized_payload == (
        runtime_probe_results.RuntimeProbeReplayField(
            key="mutation_outcome",
            value="returned_none",
        ),
    )
    assert attempt.observed_replay_inputs == ()
    assert attempt.durable_artifact_reference == expected_durable_reference
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.normalized_payload == attempt.normalized_payload
    assert observed_result.durable_artifact_reference == expected_durable_reference
    assert tuple(
        (field.key, field.value)
        for field in observed_result.replay_artifact.replay_inputs[-4:]
    ) == (
        ("object_type", "main.ProbeTarget"),
        ("attribute_name", "flag"),
        ("assigned_value_type", "builtins.str"),
        ("assigned_value_literal", "ready"),
    )
    assert len(result.runtime_provenance_records) == 1
    assert result.runtime_provenance_records == tuple(
        response.program.provenance_records
    )
    assert origin_detail["normalized_payload"] == {"mutation_outcome": "returned_none"}
    assert origin_detail["durable_payload_reference"] == expected_durable_reference
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
        unit.primary_capability_tier is CapabilityTier.STATICALLY_PROVED
        for unit in static_units
    )
    assert all(unit.has_attached_runtime_provenance is False for unit in static_units)
    assert all(
        unit.primary_capability_tier is not CapabilityTier.RUNTIME_BACKED
        for unit in result.metadata.selected_units
    )


def test_setattr_probe_default_local_provider_fails_closed() -> None:
    """Wrong task IDs remain unsupported by the exact subprocess provider."""
    with pytest.raises(ValueError) as exc_info:
        eval_providers.build_context_ir_default_local_python_subprocess_pack(
            eval_providers.EvalProviderRequest(
                repo_root=FIXTURE_ROOT,
                task_id="oracle_signal_setattr_probe_typo",
                query=QUERY,
                budget=220,
            )
        )

    message = str(exc_info.value)
    assert "context_ir_default_local_python_subprocess only supports" in message
    assert "oracle_signal_setattr_probe" in message
    assert "oracle_signal_setattr_probe_typo" not in message
    assert "oracle_signal_vars_probe" in message


def test_setattr_probe_assets_stay_internal() -> None:
    """The isolated setattr probe does not widen public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_setattr_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_setattr_probe")


def test_setattr_probe_run_executes_with_additive_runtime_provenance(
    tmp_path: Path,
) -> None:
    """Run execution preserves unsupported primary truth plus runtime support."""
    ledger_path = tmp_path / "setattr_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_setattr_probe_matrix"
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
        metrics = cast(dict[str, object], record["metrics"])
        runtime_provenance_records = cast(
            list[dict[str, object]],
            record["runtime_provenance_records"],
        )
        unsupported_selector = next(
            selector
            for selector in _resolved_selectors(record)
            if selector["resolved_unit_id"] == UNSUPPORTED_UNIT_ID
        )
        unsupported_unit = next(
            unit
            for unit in _selected_units(record)
            if unit["unit_id"] == UNSUPPORTED_UNIT_ID
        )

        assert record["spec_version"] == "v1"
        assert record["provider_name"] == eval_providers.CONTEXT_IR_PROVIDER
        assert record["budget"] == budget
        assert UNSUPPORTED_UNIT_ID in cast(list[str], record["selected_unit_ids"])
        assert metrics["uncertainty_honesty"] == 1.0
        assert unsupported_selector["primary_capability_tier"] == "unsupported/opaque"
        assert unsupported_selector["primary_evidence_origin"] == (
            "unsupported_reason_code"
        )
        assert unsupported_selector["primary_replay_status"] == "opaque_boundary"
        assert unsupported_selector["has_attached_runtime_provenance"] is True
        assert unsupported_unit["primary_capability_tier"] == "unsupported/opaque"
        assert unsupported_unit["primary_evidence_origin"] == "unsupported_reason_code"
        assert unsupported_unit["primary_replay_status"] == "opaque_boundary"
        assert unsupported_unit["has_attached_runtime_provenance"] is True
        assert cast(
            list[str],
            unsupported_unit["attached_runtime_provenance_record_ids"],
        )
        assert len(runtime_provenance_records) == 1
        assert runtime_provenance_records[0]["normalized_payload"] == {
            "mutation_outcome": "returned_none",
        }


def test_setattr_probe_summary_surfaces_internal_capability_accounting(
    tmp_path: Path,
) -> None:
    """The accepted pilot renders tier-aware accounting without widening claims."""
    ledger_path = tmp_path / "setattr_probe.jsonl"

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
        if aggregate.payload_key == "mutation_outcome"
        and aggregate.payload_value == "returned_none"
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

    expected_record_count = len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    expected_context_ir_count = len(PROBE_BUDGETS)

    assert unsupported_selector_aggregate.selector_count == expected_record_count
    assert unsupported_selector_aggregate.satisfied_count == expected_record_count
    assert runtime_expectation_aggregate.selector_count == expected_record_count
    assert runtime_expectation_aggregate.satisfied_count == expected_record_count
    assert runtime_outcome_aggregate.runtime_provenance_count == expected_record_count
    assert (
        unsupported_selected_unit_aggregate.selected_unit_count
        == expected_context_ir_count
    )
    assert (
        unsupported_selected_unit_aggregate.attached_runtime_provenance_count
        == expected_context_ir_count
    )
    assert (
        provider_unsupported_selected_unit_aggregate.selected_unit_count
        == expected_context_ir_count
    )
    assert (
        provider_unsupported_selected_unit_aggregate.attached_runtime_provenance_count
        == expected_context_ir_count
    )

    assert report.markdown_report == rendered

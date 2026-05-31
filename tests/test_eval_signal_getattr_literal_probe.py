"""Direct-literal ``getattr`` runtime-backed eval pilot tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_providers as eval_providers
import context_ir.eval_runs as eval_runs
import context_ir.runtime_probe_results as runtime_probe_results
import context_ir.semantic_types as semantic_types
import context_ir.tool_facade as tool_facade
from context_ir.eval_oracles import (
    SymbolOracleSelector,
    UnsupportedOracleSelector,
    load_fixture_getattr_runtime_observations,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
    UnresolvedReasonCode,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_getattr_literal_probe"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_getattr_literal_probe.json"
RUN_SPEC_PATH = (
    REPO_ROOT
    / "evals"
    / "run_specs"
    / "oracle_signal_getattr_literal_probe_matrix.json"
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
EXPECTED_BASELINE_SELECTED_FILES = {
    (eval_providers.LEXICAL_TOP_K_FILES_PROVIDER, 100): [],
    (eval_providers.LEXICAL_TOP_K_FILES_PROVIDER, 220): ["main.py"],
    (eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER, 100): [],
    (eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER, 220): ["main.py"],
}
QUERY = (
    'Fix probe_literal_attribute unsupported getattr(obj, "bit_length") '
    "and keep digest output aligned"
)
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
UNSUPPORTED_SITE_ID = "site:call:main.py:2:11"
CONTEXT_IR_SELECTED_UNIT_IDS = (
    "def:main.py:main.probe_literal_attribute",
    "def:main.py:main.render_probe_digest",
    UNSUPPORTED_UNIT_ID,
)
UNSUPPORTED_LITERAL_SIBLING_TASK_IDS = (
    "oracle_signal_setattr_literal_probe",
    "oracle_signal_delattr_literal_probe",
    "oracle_signal_dynamic_import_root_literal_probe",
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


def test_getattr_literal_probe_fixture_uses_only_direct_literal_shape() -> None:
    """The fixture preserves exactly ``getattr(obj, "bit_length")``."""
    source = (FIXTURE_ROOT / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    observations = load_fixture_getattr_runtime_observations(FIXTURE_ROOT)

    getattr_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
    ]
    forbidden_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"hasattr", "setattr", "delattr", "vars", "dir"}
    ]
    name_assignments = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "name"
            for target in node.targets
        )
    ]
    name_loads = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Name) and node.id == "name"
    ]
    call = getattr_calls[0]

    assert source.count('getattr(obj, "bit_length")') == 1
    assert "getattr(obj, name)" not in source
    assert 'getattr(obj, "bit_length", ' not in source
    assert "hasattr(" not in source
    assert "setattr(" not in source
    assert "delattr(" not in source
    assert "vars(" not in source
    assert "dir(" not in source
    assert len(getattr_calls) == 1
    assert len(call.args) == 2
    assert call.keywords == []
    assert isinstance(call.args[0], ast.Name)
    assert call.args[0].id == "obj"
    assert isinstance(call.args[1], ast.Constant)
    assert call.args[1].value == "bit_length"
    assert name_assignments == []
    assert name_loads == []
    assert forbidden_calls == []
    assert len(observations) == 1
    assert observations[0].site.site_id == UNSUPPORTED_SITE_ID
    assert observations[0].site.snippet == 'getattr(obj, "bit_length")'
    assert observations[0].site.span.start_line == 2
    assert observations[0].site.span.start_column == 11
    assert observations[0].site.span.end_line == 2
    assert observations[0].site.span.end_column == 37
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (("lookup_outcome", "returned_value"),)
    assert observations[0].durable_payload_reference


def test_getattr_literal_probe_resolves_without_static_attribute_proof() -> None:
    """Runtime evidence stays additive and does not prove ``bit_length`` statically."""
    setup = setup_eval_oracle_task(TASK_PATH)
    program = setup.semantic_program
    unsupported_construct = next(
        construct
        for construct in program.unsupported_constructs
        if construct.construct_id == UNSUPPORTED_UNIT_ID
    )

    assert setup.task.task_id == "oracle_signal_getattr_literal_probe"
    assert setup.task.fixture_id == "oracle_signal_getattr_literal_probe"
    assert len(setup.task.expected_selectors) == 3
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], UnsupportedOracleSelector)
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.probe_literal_attribute",
        "def:main.py:main.render_probe_digest",
        UNSUPPORTED_UNIT_ID,
    ]
    assert unsupported_construct.reason_code is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert unsupported_construct.site.snippet == 'getattr(obj, "bit_length")'

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
        "bit_length" not in (symbol.symbol_id, symbol.qualified_name)
        for symbol in program.resolved_symbols.values()
    )
    assert all(
        "bit_length" not in (dependency.source_symbol_id, dependency.target_symbol_id)
        for dependency in program.proven_dependencies
    )
    assert all(
        dependency.evidence_site_id != UNSUPPORTED_SITE_ID
        for dependency in program.proven_dependencies
    )


def test_getattr_literal_probe_default_local_provider_replays_exact_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default local-Python provider admits only the exact literal fixture."""
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
            task_id="oracle_signal_getattr_literal_probe",
            query=QUERY,
            budget=220,
        )
    )

    assert len(captured_responses) == 1
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
    provenance_record = result.runtime_provenance_records[0]
    origin_detail = cast(dict[str, object], json.loads(provenance_record.origin_detail))

    assert result.provider_name == (
        eval_providers.CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    )
    assert result.task_id == "oracle_signal_getattr_literal_probe"
    assert result.budget == 220
    assert result.selected_files == ()
    assert result.selected_unit_ids == CONTEXT_IR_SELECTED_UNIT_IDS
    assert result.warnings == ()
    assert planned_request.subject_id == UNSUPPORTED_UNIT_ID
    assert planned_request.boundary_text == 'getattr(obj, "bit_length")'
    assert (
        planned_request.family_label
        is eval_providers.RuntimeProbeFamily.REFLECTIVE_BUILTIN
    )
    assert planned_request.form_label == "reflective_builtin:getattr/2"
    assert planned_request.replay_target_seed == "main.probe_literal_attribute"
    assert attempt.normalized_payload == (
        runtime_probe_results.RuntimeProbeReplayField(
            key="lookup_outcome",
            value="returned_value",
        ),
    )
    assert attempt.observed_replay_inputs == ()
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.normalized_payload == attempt.normalized_payload
    assert tuple(
        (field.key, field.value)
        for field in observed_result.replay_artifact.replay_inputs[-2:]
    ) == (("object_type", "builtins.int"), ("attribute_name", "bit_length"))
    assert len(result.runtime_provenance_records) == 1
    assert origin_detail["normalized_payload"] == {"lookup_outcome": "returned_value"}
    assert "observed_replay_inputs" not in origin_detail
    assert "returned_value_summary" not in origin_detail
    assert "returned_type_summary" not in origin_detail
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
    assert all("bit_length" not in unit_id for unit_id in result.selected_unit_ids)
    assert all(
        "bit_length" not in (symbol_id, symbol.qualified_name)
        for symbol_id, symbol in response.program.resolved_symbols.items()
    )
    assert all(
        "bit_length" not in dependency.source_symbol_id
        and "bit_length" not in dependency.target_symbol_id
        for dependency in response.program.proven_dependencies
    )
    assert all(
        "returned_value" not in unit.detail
        and "returned_type" not in unit.detail
        and "builtins.builtin_function_or_method" not in unit.detail
        for unit in result.metadata.selected_units
    )


def test_getattr_literal_probe_default_local_provider_rejects_wrong_plan_fields() -> (
    None
):
    """The provider fails closed when the planned probe identity drifts."""
    previous_response = eval_providers.tool_facade.compile_repository_context(
        tool_facade.SemanticContextRequest(
            repo_root=FIXTURE_ROOT,
            query=QUERY,
            budget=220,
        )
    )
    fixture = eval_providers._default_local_python_subprocess_fixture(
        "oracle_signal_getattr_literal_probe"
    )
    miss_evidence = semantic_types.SemanticMissEvidence(
        kind=semantic_types.SemanticMissKind.ABSENT_SYMBOL,
        evidence='getattr(obj, "bit_length")',
    )
    diagnostic = eval_providers.diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    assert len(plan.requests) == 1
    object.__setattr__(plan.requests[0], "form_label", "reflective_builtin:getattr/3")

    with pytest.raises(ValueError, match="wrong form"):
        eval_providers._require_default_local_python_runtime_probe_request(
            diagnostic,
            fixture,
        )


@pytest.mark.parametrize("task_id", UNSUPPORTED_LITERAL_SIBLING_TASK_IDS)
def test_getattr_literal_probe_default_local_provider_rejects_literal_siblings(
    task_id: str,
) -> None:
    """Literal sibling tasks remain outside this exact provider slice."""
    sibling_fixture_root = REPO_ROOT / "evals" / "fixtures" / task_id

    with pytest.raises(ValueError, match="only supports"):
        eval_providers.build_context_ir_default_local_python_subprocess_pack(
            eval_providers.EvalProviderRequest(
                repo_root=sibling_fixture_root,
                task_id=task_id,
                query=QUERY,
                budget=220,
            )
        )


def test_getattr_literal_probe_run_spec_loads_two_budget_matrix() -> None:
    """The run spec stays at 1 task x 2 budgets x 3 providers."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_getattr_literal_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_getattr_literal_probe"
    assert case.task_path == "evals/tasks/oracle_signal_getattr_literal_probe.json"
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_getattr_literal_probe_assets_stay_internal() -> None:
    """The direct-literal pilot remains internal and does not widen exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_getattr_literal_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_getattr_literal_probe")


def test_getattr_literal_probe_run_preserves_additive_runtime_boundary(
    tmp_path: Path,
) -> None:
    """The matrix locks selected units, baselines, and additive provenance."""
    ledger_path = tmp_path / "getattr_literal_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_getattr_literal_probe_matrix"
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
            assert (
                baseline_record["selected_files"]
                == EXPECTED_BASELINE_SELECTED_FILES[(provider_name, budget)]
            )
            assert baseline_record["selected_unit_ids"] == []
            assert _selected_units(baseline_record) == []

    for budget in PROBE_BUDGETS:
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
        selected_units = _selected_units(record)
        selected_unit_ids = cast(list[str], record["selected_unit_ids"])
        unsupported_selector = next(
            selector
            for selector in _resolved_selectors(record)
            if selector["resolved_unit_id"] == UNSUPPORTED_UNIT_ID
        )
        unsupported_unit = next(
            unit for unit in selected_units if unit["unit_id"] == UNSUPPORTED_UNIT_ID
        )

        assert record["spec_version"] == "v1"
        assert record["provider_name"] == eval_providers.CONTEXT_IR_PROVIDER
        assert record["budget"] == budget
        assert record["selected_files"] == []
        assert tuple(selected_unit_ids) == CONTEXT_IR_SELECTED_UNIT_IDS
        assert metrics["uncertainty_honesty"] == 1.0
        assert all(
            "bit_length" not in cast(str, unit["unit_id"]) for unit in selected_units
        )
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
            "lookup_outcome": "returned_value"
        }

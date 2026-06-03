"""Isolated metaclass behavior runtime-backed eval pilot tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_providers as eval_providers
import context_ir.eval_runs as eval_runs
import context_ir.runtime_probe_execution as runtime_probe_execution
import context_ir.runtime_probe_requests as runtime_probe_requests
import context_ir.runtime_probe_results as runtime_probe_results
import context_ir.semantic_types as semantic_types
from context_ir.eval_metrics import score_eval_run
from context_ir.eval_oracles import (
    SymbolOracleSelector,
    UnsupportedOracleSelector,
    load_fixture_metaclass_behavior_runtime_observations,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
    SemanticDiagnosticBoundaryKind,
    SemanticMissEvidence,
    SemanticMissKind,
    SemanticSubjectKind,
    UnresolvedReasonCode,
)
from context_ir.tool_facade import (
    SemanticContextRequest,
    SemanticContextResponse,
    SemanticDefaultLocalPythonSubprocessRecompileRequest,
    SemanticDefaultLocalPythonSubprocessRecompileResponse,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (
    REPO_ROOT / "evals" / "fixtures" / "oracle_signal_metaclass_behavior_probe"
)
TASK_PATH = (
    REPO_ROOT / "evals" / "tasks" / "oracle_signal_metaclass_behavior_probe.json"
)
RUN_SPEC_PATH = (
    REPO_ROOT
    / "evals"
    / "run_specs"
    / "oracle_signal_metaclass_behavior_probe_matrix.json"
)
PROBE_BUDGETS = (220, 100)
PROBE_PROVIDERS = (
    eval_providers.CONTEXT_IR_PROVIDER,
    eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
    eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER = (
    eval_providers.CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
)
BASELINE_PROVIDERS = (
    eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
    eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
QUERY = (
    "Fix Example metaclass=Meta class creation behavior and keep digest output aligned"
)
EXAMPLE_UNIT_ID = "def:main.py:main.Example"
BASE_UNIT_ID = "def:main.py:main.Base"
METACLASS_SYMBOL_UNIT_ID = "def:main.py:main.Meta"
UNSUPPORTED_UNIT_ID = "unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1"
METACLASS_SITE_ID = "site:metaclass:main.py:9:20:def:main.py:main.Example:1"
METACLASS_FRONTIER_UNIT_ID = "frontier:base:main.py:5:11:def:main.py:main.Meta:1"
RUNTIME_PAYLOAD = (
    ("class_creation_outcome", "created_class"),
    ("created_class_qualified_name", "main.Example"),
    ("selected_metaclass_qualified_name", "main.Meta"),
)
CONTEXT_IR_SELECTED_UNIT_IDS_BY_BUDGET = {
    100: (
        EXAMPLE_UNIT_ID,
        UNSUPPORTED_UNIT_ID,
        METACLASS_FRONTIER_UNIT_ID,
    ),
    220: (
        EXAMPLE_UNIT_ID,
        BASE_UNIT_ID,
        UNSUPPORTED_UNIT_ID,
        METACLASS_FRONTIER_UNIT_ID,
    ),
}


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


def _runtime_observation_fields_are_empty(
    request: SemanticContextRequest,
) -> bool:
    """Return whether an initial compile request carries no runtime fixtures."""
    return (
        request.dynamic_import_runtime_observations is None
        and request.eval_runtime_observations is None
        and request.exec_runtime_observations is None
        and request.hasattr_runtime_observations is None
        and request.getattr_runtime_observations is None
        and request.vars_runtime_observations is None
        and request.globals_runtime_observations is None
        and request.locals_runtime_observations is None
        and request.metaclass_behavior_runtime_observations is None
        and request.setattr_runtime_observations is None
        and request.delattr_runtime_observations is None
        and request.dir_runtime_observations is None
    )


def _single_provider_run_spec_path(
    tmp_path: Path,
    *,
    provider_name: str,
    budget: int,
) -> Path:
    """Return a temporary metaclass probe run spec for one provider and budget."""
    spec_record = cast(
        dict[str, object],
        json.loads(RUN_SPEC_PATH.read_text(encoding="utf-8")),
    )
    case_records = cast(list[object], spec_record["cases"])
    case_record = cast(dict[str, object], case_records[0])
    case_record["providers"] = [provider_name]
    case_record["budgets"] = [budget]
    spec_path = tmp_path / "metaclass_behavior_probe_single_provider.json"
    spec_path.write_text(json.dumps(spec_record), encoding="utf-8")
    return spec_path


def _probe_field(
    key: str,
    value: str,
) -> runtime_probe_results.RuntimeProbeReplayField:
    """Return one runtime probe replay field."""
    return runtime_probe_results.RuntimeProbeReplayField(key=key, value=value)


def _fixture_root_runner_environment() -> tuple[
    runtime_probe_results.RuntimeProbeReplayField,
    ...,
]:
    """Return local-Python runner environment fields for the fixture root."""
    source_root = Path(context_ir.__file__).resolve().parents[1]
    return (
        _probe_field("repository_root", str(FIXTURE_ROOT)),
        _probe_field("working_directory", str(FIXTURE_ROOT)),
        _probe_field("python_path_entry", str(source_root)),
    )


def _assert_context_ir_metaclass_record(
    record: dict[str, object],
    *,
    budget: int,
    expected_selected_unit_ids: tuple[str, ...],
) -> None:
    """Assert one context_ir metaclass behavior ledger record."""
    metrics = cast(dict[str, object], record["metrics"])
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
    unsupported_unit = next(
        unit for unit in selected_units if unit["unit_id"] == UNSUPPORTED_UNIT_ID
    )

    assert record["spec_version"] == "v1"
    assert record["provider_name"] == eval_providers.CONTEXT_IR_PROVIDER
    assert record["budget"] == budget
    assert tuple(cast(list[str], record["selected_unit_ids"])) == (
        expected_selected_unit_ids
    )
    assert METACLASS_SYMBOL_UNIT_ID not in expected_selected_unit_ids
    assert all(unit["unit_id"] != METACLASS_SYMBOL_UNIT_ID for unit in selected_units)
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
        "class_creation_outcome": "created_class",
        "created_class_qualified_name": "main.Example",
        "selected_metaclass_qualified_name": "main.Meta",
    }


def test_metaclass_behavior_probe_task_resolves_expected_selectors() -> None:
    """The isolated metaclass probe resolves the intended selectors."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_metaclass_behavior_probe"
    assert setup.task.fixture_id == "oracle_signal_metaclass_behavior_probe"
    assert len(setup.task.expected_selectors) == 3
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], UnsupportedOracleSelector)
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.Example",
        "def:main.py:main.render_probe_digest",
        UNSUPPORTED_UNIT_ID,
    ]

    selector = setup.task.expected_selectors[2]
    unsupported = setup.resolved_selectors[2]
    assert isinstance(selector, UnsupportedOracleSelector)
    assert selector.reason_code is UnresolvedReasonCode.METACLASS_BEHAVIOR
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
    assert all(
        selector.resolved_unit_id != METACLASS_SYMBOL_UNIT_ID
        for selector in setup.resolved_selectors
    )
    assert all(
        METACLASS_SYMBOL_UNIT_ID
        not in (dependency.source_symbol_id, dependency.target_symbol_id)
        for dependency in setup.semantic_program.proven_dependencies
    )
    assert all(
        dependency.evidence_site_id != METACLASS_SITE_ID
        for dependency in setup.semantic_program.proven_dependencies
    )


def test_metaclass_behavior_probe_run_spec_loads_budget_matrix() -> None:
    """The metaclass probe run spec is one task x two budgets x three providers."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_metaclass_behavior_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_metaclass_behavior_probe"
    assert case.task_path == "evals/tasks/oracle_signal_metaclass_behavior_probe.json"
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_metaclass_behavior_probe_fixture_uses_created_class_payload() -> None:
    """The fixture preserves eval-only created-class metaclass provenance."""
    source = (FIXTURE_ROOT / "main.py").read_text(encoding="utf-8")
    observations = load_fixture_metaclass_behavior_runtime_observations(FIXTURE_ROOT)

    assert source.count("metaclass=Meta") == 1
    assert "metaclass=Holder.Meta" not in source
    assert len(observations) == 1
    assert observations[0].site.snippet == "metaclass=Meta"
    assert observations[0].site.span.start_line == 9
    assert observations[0].site.span.start_column == 20
    assert tuple(
        (field.key, field.value) for field in observations[0].replay_inputs
    ) == (("declared_base_qualified_name", "main.Base"),)
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (
        ("class_creation_outcome", "created_class"),
        ("created_class_qualified_name", "main.Example"),
        ("selected_metaclass_qualified_name", "main.Meta"),
    )
    assert observations[0].durable_payload_reference


def test_metaclass_behavior_probe_assets_stay_internal() -> None:
    """The isolated metaclass probe does not widen public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_metaclass_behavior_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_metaclass_behavior_probe")


def test_metaclass_behavior_probe_default_subprocess_provider_owns_runtime_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact provider replays metaclass behavior through subprocess."""
    setup = setup_eval_oracle_task(TASK_PATH)
    setup_runtime_record_ids = {
        record.record_id for record in setup.semantic_program.provenance_records
    }
    compile_requests: list[SemanticContextRequest] = []
    recompile_requests: list[SemanticDefaultLocalPythonSubprocessRecompileRequest] = []
    recompile_responses: list[
        SemanticDefaultLocalPythonSubprocessRecompileResponse
    ] = []

    original_compile = eval_providers.tool_facade.compile_repository_context
    original_recompile = eval_providers.tool_facade.recompile_repository_context_with_default_local_python_subprocess  # noqa: E501

    def spying_compile(request: SemanticContextRequest) -> SemanticContextResponse:
        compile_requests.append(request)
        return original_compile(request)

    def spying_recompile(
        request: SemanticDefaultLocalPythonSubprocessRecompileRequest,
    ) -> SemanticDefaultLocalPythonSubprocessRecompileResponse:
        recompile_requests.append(request)
        response = original_recompile(request)
        recompile_responses.append(response)
        return response

    original_run = runtime_probe_execution.subprocess.run
    subprocess_invocations: list[tuple[str, ...]] = []

    def spying_run(*args: object, **kwargs: object) -> object:
        argv = args[0]
        if isinstance(argv, tuple | list):
            subprocess_invocations.append(tuple(str(part) for part in argv))
        else:
            subprocess_invocations.append((str(argv),))
        return original_run(*args, **kwargs)

    monkeypatch.setattr(
        eval_providers.tool_facade,
        "compile_repository_context",
        spying_compile,
    )
    monkeypatch.setattr(
        eval_providers.tool_facade,
        "recompile_repository_context_with_default_local_python_subprocess",
        spying_recompile,
    )
    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", spying_run)

    provider_result = (
        eval_providers.build_context_ir_default_local_python_subprocess_pack(
            eval_providers.EvalProviderRequest(
                repo_root=FIXTURE_ROOT,
                task_id="oracle_signal_metaclass_behavior_probe",
                query=QUERY,
                budget=100,
            )
        )
    )

    recompile_request = recompile_requests[0]
    recompile_response = recompile_responses[0]
    plan = recompile_request.diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    planned_request = plan.requests[0]
    attempts = recompile_response.runner_attempt_collection.attempts
    results = recompile_response.runner_attempt_collection.result_batch.results
    observed_result = results[0]
    unsupported_unit = next(
        unit
        for unit in provider_result.metadata.selected_units
        if unit.unit_id == UNSUPPORTED_UNIT_ID
    )
    boundary = next(
        candidate
        for candidate in recompile_response.diagnostic.boundary_classifications
        if candidate.unit_id == UNSUPPORTED_UNIT_ID
    )
    selected_trace = next(
        selection.trace_summary
        for selection in recompile_response.compile_result.optimization.selections
        if selection.unit_id == UNSUPPORTED_UNIT_ID
    )
    provenance_record = provider_result.runtime_provenance_records[0]
    provenance_detail = cast(
        dict[str, object],
        json.loads(provenance_record.origin_detail),
    )

    assert compile_requests
    assert _runtime_observation_fields_are_empty(compile_requests[0])
    assert tuple(recompile_request.previous_response.program.provenance_records) == ()
    assert recompile_request.miss_evidence == SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence="metaclass=Meta",
    )
    assert recompile_request.diagnostic.planned_runtime_probe_requests == (
        plan.requests
    )
    assert len(plan.requests) == 1
    assert planned_request.subject_id == UNSUPPORTED_UNIT_ID
    assert planned_request.family_label is (
        runtime_probe_requests.RuntimeProbeFamily.METACLASS_BEHAVIOR
    )
    assert planned_request.form_label == "metaclass_behavior:keyword"
    assert planned_request.boundary_text == "metaclass=Meta"
    assert planned_request.replay_target_seed == "main.Example"
    assert recompile_request.delta_budget == 0
    assert recompile_request.python_executable == sys.executable
    assert recompile_request.runner_environment == _fixture_root_runner_environment()
    assert all(
        Path(field.value).is_absolute()
        for field in recompile_request.runner_environment
    )
    assert subprocess_invocations == [
        (sys.executable, "-m", "context_ir.runtime_probe_worker"),
    ]
    assert len(attempts) == 1
    assert len(results) == 1
    assert attempts[0].request is planned_request
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.request is planned_request
    assert (
        tuple((field.key, field.value) for field in observed_result.normalized_payload)
        == RUNTIME_PAYLOAD
    )
    assert provider_result.provider_name == DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    assert provider_result.runtime_provenance_records == tuple(
        recompile_response.program.provenance_records
    )
    assert len(provider_result.runtime_provenance_records) == 1
    assert provenance_record.record_id not in setup_runtime_record_ids
    assert provenance_detail["normalized_payload"] == {
        "class_creation_outcome": "created_class",
        "created_class_qualified_name": "main.Example",
        "selected_metaclass_qualified_name": "main.Meta",
    }
    assert boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert boundary.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert boundary.has_attached_runtime_provenance is True
    assert selected_trace is not None
    assert selected_trace.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        selected_trace.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert selected_trace.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert selected_trace.has_attached_runtime_provenance is True
    assert provenance_record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert provenance_record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert provenance_record.evidence_origin is (
        EvidenceOriginKind.RUNTIME_PROBE_IDENTITY
    )
    assert provenance_record.replay_status is ReplayStatus.REPRODUCIBLE_RUNTIME
    assert unsupported_unit.primary_capability_tier is (
        CapabilityTier.UNSUPPORTED_OPAQUE
    )
    assert unsupported_unit.primary_evidence_origin is (
        EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported_unit.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported_unit.has_attached_runtime_provenance is True
    assert unsupported_unit.attached_runtime_provenance_record_ids == (
        provenance_record.record_id,
    )
    assert UNSUPPORTED_UNIT_ID in provider_result.selected_unit_ids
    assert METACLASS_SYMBOL_UNIT_ID not in provider_result.selected_unit_ids
    assert all(
        unit.unit_id != METACLASS_SYMBOL_UNIT_ID
        for unit in provider_result.metadata.selected_units
    )

    metrics = score_eval_run(setup, provider_result)

    assert metrics.uncertainty_honesty == 1.0
    assert UNSUPPORTED_UNIT_ID in metrics.selected_matched_selector_ids


def test_metaclass_behavior_probe_default_subprocess_provider_fails_closed() -> None:
    """The exact subprocess provider is not a generalized eval provider."""
    with pytest.raises(
        ValueError,
        match=(
            "context_ir_default_local_python_subprocess only supports "
            "oracle_signal_locals_probe, oracle_signal_globals_probe, "
            "oracle_signal_vars_zero_probe, oracle_signal_dir_zero_probe, "
            "oracle_signal_hasattr_probe, oracle_signal_hasattr_false_probe, "
            "oracle_signal_hasattr_literal_probe, "
            "oracle_signal_getattr_probe, "
            "oracle_signal_getattr_attribute_error_probe, "
            "oracle_signal_getattr_literal_probe, "
            "oracle_signal_dynamic_import_root_literal_probe, "
            "oracle_signal_dynamic_import_root_probe, "
            "oracle_signal_dynamic_import_root_alias_probe, "
            "oracle_signal_dynamic_import_builtin_probe, "
            "oracle_signal_dynamic_import_builtins_attr_probe, "
            "oracle_signal_dynamic_import_builtins_alias_probe, "
            "oracle_signal_dynamic_import_imported_name_probe, "
            "oracle_signal_dynamic_import_imported_alias_probe, "
            "oracle_signal_dynamic_import_probe, "
            "oracle_signal_setattr_literal_probe, "
            "oracle_signal_delattr_literal_probe, oracle_signal_exec_probe, "
            "oracle_signal_eval_probe, or "
            "oracle_signal_metaclass_behavior_probe"
        ),
    ):
        eval_providers.build_context_ir_default_local_python_subprocess_pack(
            eval_providers.EvalProviderRequest(
                repo_root=FIXTURE_ROOT,
                task_id="oracle_smoke",
                query=QUERY,
                budget=100,
            )
        )


def test_metaclass_behavior_probe_default_subprocess_provider_runs_via_run_spec_name(
    tmp_path: Path,
) -> None:
    """Run-spec provider dispatch uses a temporary single-provider spec."""
    spec_path = _single_provider_run_spec_path(
        tmp_path,
        provider_name=DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER,
        budget=100,
    )
    ledger_path = tmp_path / "metaclass_probe_default_subprocess.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        spec_path,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    record = records[0]
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
    selector_record_ids = tuple(
        cast(list[str], unsupported_selector["attached_runtime_provenance_record_ids"])
    )
    selected_unit_record_ids = tuple(
        cast(list[str], unsupported_unit["attached_runtime_provenance_record_ids"])
    )
    runtime_record_ids = {
        cast(str, provenance_record["record_id"])
        for provenance_record in runtime_provenance_records
    }

    assert execution.record_count == 1
    assert record["provider_name"] == DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    assert METACLASS_SYMBOL_UNIT_ID not in cast(list[str], record["selected_unit_ids"])
    assert all(
        unit["unit_id"] != METACLASS_SYMBOL_UNIT_ID for unit in _selected_units(record)
    )
    assert metrics["uncertainty_honesty"] == 1.0
    assert unsupported_unit["primary_capability_tier"] == "unsupported/opaque"
    assert unsupported_unit["primary_evidence_origin"] == "unsupported_reason_code"
    assert unsupported_unit["primary_replay_status"] == "opaque_boundary"
    assert unsupported_unit["has_attached_runtime_provenance"] is True
    assert len(selector_record_ids) == 1
    assert len(selected_unit_record_ids) == 1
    assert selected_unit_record_ids != selector_record_ids
    assert selected_unit_record_ids[0] in runtime_record_ids
    assert selector_record_ids[0] in runtime_record_ids
    assert len(runtime_provenance_records) == 2
    assert all(
        provenance_record["normalized_payload"]
        == {
            "class_creation_outcome": "created_class",
            "created_class_qualified_name": "main.Example",
            "selected_metaclass_qualified_name": "main.Meta",
        }
        for provenance_record in runtime_provenance_records
    )


def test_metaclass_behavior_probe_run_preserves_unsupported_primary_truth(
    tmp_path: Path,
) -> None:
    """Run execution preserves unsupported primary truth plus runtime support."""
    ledger_path = tmp_path / "metaclass_behavior_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_metaclass_behavior_probe_matrix"
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

    record_220 = _record_for(
        records,
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=220,
    )
    _assert_context_ir_metaclass_record(
        record_220,
        budget=220,
        expected_selected_unit_ids=CONTEXT_IR_SELECTED_UNIT_IDS_BY_BUDGET[220],
    )
    record_100 = _record_for(
        records,
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=100,
    )
    _assert_context_ir_metaclass_record(
        record_100,
        budget=100,
        expected_selected_unit_ids=CONTEXT_IR_SELECTED_UNIT_IDS_BY_BUDGET[100],
    )

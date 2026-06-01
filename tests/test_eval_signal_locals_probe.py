"""Isolated ``locals()`` runtime-backed eval pilot tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_providers as eval_providers
import context_ir.eval_report as eval_report
import context_ir.eval_results as eval_results
import context_ir.eval_runs as eval_runs
import context_ir.eval_summary as eval_summary
import context_ir.runtime_probe_execution as runtime_probe_execution
import context_ir.runtime_probe_requests as runtime_probe_requests
import context_ir.runtime_probe_results as runtime_probe_results
import context_ir.semantic_types as semantic_types
from context_ir.eval_metrics import score_eval_run
from context_ir.eval_oracles import (
    SymbolOracleSelector,
    UnsupportedOracleSelector,
    load_eval_oracle_task,
    load_fixture_locals_runtime_observations,
    resolve_eval_oracle_task,
    setup_eval_oracle_task,
)
from context_ir.semantic_diagnostics import diagnose_semantic_miss
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
    RepositorySnapshotBasis,
    SemanticDiagnosticBoundaryKind,
    SemanticDiagnosticUnitStatus,
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
    compile_repository_context,
    recompile_repository_context_with_default_local_python_subprocess,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_locals_probe"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_locals_probe.json"
RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_locals_probe_matrix.json"
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
    "Fix probe_local_namespace unsupported locals() returned namespace and keep digest "
    "output aligned"
)
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:3:11"
RUNTIME_PAYLOAD = (("lookup_outcome", "returned_namespace"),)


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
    """Return a temporary locals-probe run spec for one provider and budget."""
    spec_record = cast(
        dict[str, object],
        json.loads(RUN_SPEC_PATH.read_text(encoding="utf-8")),
    )
    case_records = cast(list[object], spec_record["cases"])
    case_record = cast(dict[str, object], case_records[0])
    case_record["providers"] = [provider_name]
    case_record["budgets"] = [budget]
    spec_path = tmp_path / "locals_probe_single_provider.json"
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


def _runner_runtime_assumptions() -> tuple[
    runtime_probe_results.RuntimeProbeReplayField,
    ...,
]:
    """Return explicit runtime assumptions for subprocess fixture replay."""
    return (
        _probe_field("python_version", "test"),
        _probe_field("dependency_mode", "offline-fixture"),
    )


def _runner_assumptions() -> tuple[
    runtime_probe_results.RuntimeProbeReplayField,
    ...,
]:
    """Return explicit runner assumptions for subprocess fixture replay."""
    return (
        _probe_field("network", "disabled"),
        _probe_field("filesystem_mode", "read_only_fixture"),
    )


def test_locals_probe_task_resolves_expected_selectors_deterministically() -> None:
    """The isolated locals probe resolves the intended selectors."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_locals_probe"
    assert setup.task.fixture_id == "oracle_signal_locals_probe"
    assert len(setup.task.expected_selectors) == 3
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], UnsupportedOracleSelector)
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.probe_local_namespace",
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


def test_locals_probe_run_spec_loads_budget_matrix() -> None:
    """The locals probe run spec is one task x two budgets x three providers."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_locals_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_locals_probe"
    assert case.task_path == "evals/tasks/oracle_signal_locals_probe.json"
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_locals_probe_fixture_uses_namespace_payload() -> None:
    """The fixture preserves the eval-only ``locals()`` runtime payload."""
    source = (FIXTURE_ROOT / "main.py").read_text(encoding="utf-8")
    observations = load_fixture_locals_runtime_observations(FIXTURE_ROOT)

    assert source.count("locals()") == 1
    assert len(observations) == 1
    assert observations[0].site.snippet == "locals()"
    assert observations[0].site.span.start_line == 3
    assert observations[0].site.span.start_column == 11
    assert observations[0].replay_inputs == ()
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (("lookup_outcome", "returned_namespace"),)


def test_locals_probe_assets_stay_internal() -> None:
    """The isolated locals probe does not widen public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_locals_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_locals_probe")


def test_locals_probe_default_subprocess_replay_adds_runtime_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The local-Python subprocess facade replays the eval fixture through worker."""
    previous_response = compile_repository_context(
        SemanticContextRequest(
            repo_root=FIXTURE_ROOT,
            query=QUERY,
            budget=100,
        )
    )
    unsupported = next(
        construct
        for construct in previous_response.program.unsupported_constructs
        if construct.construct_id == UNSUPPORTED_UNIT_ID
    )
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence="locals()",
    )
    diagnostic = diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    plan = diagnostic.planned_runtime_probe_request_plan

    assert tuple(previous_response.program.provenance_records) == ()
    assert unsupported.construct_text == "locals()"
    assert plan is not None
    assert diagnostic.planned_runtime_probe_requests == plan.requests
    assert len(plan.requests) == 1
    request = plan.requests[0]
    assert request.subject_id == UNSUPPORTED_UNIT_ID
    assert request.family_label is (
        runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION
    )
    assert request.form_label == "runtime_mutation:locals/0"
    assert request.boundary_text == "locals()"

    original_run = runtime_probe_execution.subprocess.run
    subprocess_invocations: list[tuple[str, ...]] = []

    def spying_run(*args: object, **kwargs: object) -> object:
        argv = args[0]
        if isinstance(argv, tuple | list):
            subprocess_invocations.append(tuple(str(part) for part in argv))
        else:
            subprocess_invocations.append((str(argv),))
        return original_run(*args, **kwargs)

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", spying_run)

    response = recompile_repository_context_with_default_local_python_subprocess(
        SemanticDefaultLocalPythonSubprocessRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            miss_evidence=miss_evidence,
            delta_budget=160,
            python_executable=sys.executable,
            invocation_contract_revision=(
                "runtime-probe-local-python-subprocess:test.1"
            ),
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
            repository_snapshot_basis=RepositorySnapshotBasis(
                snapshot_kind="git_commit",
                snapshot_id="oracle-signal-locals-probe-test",
                is_dirty_worktree=False,
            ),
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=_runner_runtime_assumptions(),
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_fixture_root_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    )

    collection = response.runner_attempt_collection
    observed_result = collection.result_batch.results[0]
    admission = response.observation_application.admissions[0]
    boundary = next(
        candidate
        for candidate in response.diagnostic.boundary_classifications
        if candidate.unit_id == UNSUPPORTED_UNIT_ID
    )
    selected_trace = next(
        selection.trace_summary
        for selection in response.compile_result.optimization.selections
        if selection.unit_id == UNSUPPORTED_UNIT_ID
    )
    provenance_record = next(
        record
        for record in response.program.provenance_records
        if record.subject_id == UNSUPPORTED_UNIT_ID
    )

    assert subprocess_invocations == [
        (sys.executable, "-m", "context_ir.runtime_probe_worker"),
    ]
    assert (
        collection.runner_request_batch
        is response.runner_request_preparation.runner_request_batch
    )
    assert collection.attempts[0].request is request
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.request is request
    assert (
        tuple((field.key, field.value) for field in observed_result.normalized_payload)
        == RUNTIME_PAYLOAD
    )
    assert (
        tuple(
            (field.key, field.value)
            for field in admission.observation.normalized_payload
        )
        == RUNTIME_PAYLOAD
    )
    assert admission.request is request
    assert response.non_proof_results == ()
    assert boundary.status is SemanticDiagnosticUnitStatus.TOO_SHALLOW
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

    runtime_free_setup = resolve_eval_oracle_task(
        load_eval_oracle_task(TASK_PATH),
        FIXTURE_ROOT,
    )
    selected_units = tuple(
        eval_providers._selected_unit_metadata(record)
        for record in response.compile_result.optimization.selections
    )
    warning_details = tuple(
        eval_providers._provider_warning_metadata(warning)
        for warning in response.compile_result.optimization.warnings
    )
    provider_metadata = eval_providers.EvalProviderMetadata(
        selected_units=selected_units,
        warning_details=warning_details,
        unresolved_unit_ids=tuple(
            access.access_id for access in response.program.unresolved_frontier
        ),
        unsupported_unit_ids=tuple(
            construct.construct_id
            for construct in response.program.unsupported_constructs
        ),
        syntax_diagnostic_ids=tuple(
            diagnostic.diagnostic_id
            for diagnostic in response.program.syntax.diagnostics
        ),
        semantic_diagnostic_ids=tuple(
            diagnostic.diagnostic_id for diagnostic in response.program.diagnostics
        ),
    )
    provider_result = eval_providers.EvalProviderResult(
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        provider_algorithm_version=eval_providers.PROVIDER_ALGORITHM_VERSION,
        provider_config=eval_providers.EvalProviderConfig(),
        task_id=runtime_free_setup.task.task_id,
        query=QUERY,
        budget=response.compile_budget,
        document=response.compile_result.document,
        total_tokens=response.compile_total_tokens,
        selected_files=(),
        omitted_candidate_files=(),
        selected_unit_ids=tuple(unit.unit_id for unit in selected_units),
        omitted_unit_ids=response.compile_result.omitted_unit_ids,
        warnings=tuple(warning.code for warning in warning_details),
        metadata=provider_metadata,
        runtime_provenance_records=tuple(response.program.provenance_records),
    )
    payload = eval_results.eval_run_record_to_json(
        eval_results.build_eval_run_record(
            runtime_free_setup,
            provider_result,
            score_eval_run(runtime_free_setup, provider_result),
            run_id="locals-provider-owned-runtime",
            git_commit="abc1234",
            python_version="3.11.9",
            package_version=context_ir.__version__,
        )
    )

    assert tuple(runtime_free_setup.semantic_program.provenance_records) == ()
    assert payload["runtime_provenance_records"] == [
        {
            "record_id": provenance_record.record_id,
            "normalized_payload": {"lookup_outcome": "returned_namespace"},
        }
    ]


def test_locals_probe_default_subprocess_provider_owns_runtime_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact provider replays locals() through subprocess-owned provenance."""
    setup = setup_eval_oracle_task(TASK_PATH)
    setup_runtime_record_ids = {
        record.record_id for record in setup.semantic_program.provenance_records
    }
    compile_requests: list[SemanticContextRequest] = []
    recompile_requests: list[SemanticDefaultLocalPythonSubprocessRecompileRequest] = []

    original_compile = compile_repository_context
    original_recompile = (
        recompile_repository_context_with_default_local_python_subprocess
    )

    def spying_compile(request: SemanticContextRequest) -> SemanticContextResponse:
        compile_requests.append(request)
        return original_compile(request)

    def spying_recompile(
        request: SemanticDefaultLocalPythonSubprocessRecompileRequest,
    ) -> SemanticDefaultLocalPythonSubprocessRecompileResponse:
        recompile_requests.append(request)
        return original_recompile(request)

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
                task_id="oracle_signal_locals_probe",
                query=QUERY,
                budget=100,
            )
        )
    )
    unsupported_unit = next(
        unit
        for unit in provider_result.metadata.selected_units
        if unit.unit_id == UNSUPPORTED_UNIT_ID
    )
    provenance_record = provider_result.runtime_provenance_records[0]
    provenance_detail = cast(
        dict[str, object],
        json.loads(provenance_record.origin_detail),
    )

    assert compile_requests
    assert _runtime_observation_fields_are_empty(compile_requests[0])
    assert recompile_requests
    assert recompile_requests[0].delta_budget == 0
    assert recompile_requests[0].python_executable == sys.executable
    assert recompile_requests[0].runner_environment == (
        _fixture_root_runner_environment()
    )
    assert recompile_requests[0].invocation_contract_revision == (
        eval_providers._DEFAULT_LOCAL_PYTHON_INVOCATION_CONTRACT_REVISION
    )
    assert recompile_requests[0].completion_contract_revision == (
        eval_providers._DEFAULT_LOCAL_PYTHON_COMPLETION_CONTRACT_REVISION
    )
    assert recompile_requests[0].probe_contract_revision == (
        eval_providers._DEFAULT_LOCAL_PYTHON_PROBE_CONTRACT_REVISION
    )
    assert recompile_requests[0].runner_contract_revision == (
        eval_providers._DEFAULT_LOCAL_PYTHON_RUNNER_CONTRACT_REVISION
    )
    assert subprocess_invocations == [
        (sys.executable, "-m", "context_ir.runtime_probe_worker"),
    ]
    assert provider_result.provider_name == DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    assert len(provider_result.runtime_provenance_records) == 1
    assert provenance_record.record_id not in setup_runtime_record_ids
    assert provenance_detail["normalized_payload"] == {
        "lookup_outcome": "returned_namespace",
    }
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

    metrics = score_eval_run(setup, provider_result)

    assert metrics.uncertainty_honesty == 1.0
    assert UNSUPPORTED_UNIT_ID in metrics.selected_matched_selector_ids


def test_locals_probe_default_subprocess_provider_fails_closed_for_other_tasks() -> (
    None
):
    """The exact subprocess provider is not a generalized eval provider."""
    with pytest.raises(
        ValueError,
        match=(
            "context_ir_default_local_python_subprocess only supports "
            "oracle_signal_locals_probe, oracle_signal_globals_probe, "
            "oracle_signal_vars_zero_probe, oracle_signal_dir_zero_probe, "
            "oracle_signal_hasattr_probe, oracle_signal_hasattr_literal_probe, "
            "oracle_signal_getattr_literal_probe, "
            "oracle_signal_dynamic_import_root_literal_probe, "
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


def test_locals_probe_default_subprocess_provider_runs_via_run_spec_name(
    tmp_path: Path,
) -> None:
    """Run-spec provider dispatch preserves provider-owned runtime provenance."""
    spec_path = _single_provider_run_spec_path(
        tmp_path,
        provider_name=DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER,
        budget=100,
    )
    ledger_path = tmp_path / "locals_probe_default_subprocess.jsonl"

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
        == {"lookup_outcome": "returned_namespace"}
        for provenance_record in runtime_provenance_records
    )


def test_locals_probe_run_executes_with_additive_runtime_provenance(
    tmp_path: Path,
) -> None:
    """Run execution preserves unsupported primary truth plus runtime support."""
    ledger_path = tmp_path / "locals_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_locals_probe_matrix"
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
        assert unsupported_unit["primary_evidence_origin"] == (
            "unsupported_reason_code"
        )
        assert unsupported_unit["primary_replay_status"] == "opaque_boundary"
        assert unsupported_unit["has_attached_runtime_provenance"] is True
        assert cast(
            list[str],
            unsupported_unit["attached_runtime_provenance_record_ids"],
        )
        assert len(runtime_provenance_records) == 1
        assert runtime_provenance_records[0]["normalized_payload"] == {
            "lookup_outcome": "returned_namespace",
        }


def test_locals_probe_summary_surfaces_internal_capability_accounting(
    tmp_path: Path,
) -> None:
    """The accepted pilot renders tier-aware accounting without widening claims."""
    ledger_path = tmp_path / "locals_probe.jsonl"

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
    for markdown in (rendered, report.markdown_report):
        assert "## Capability-Tier Accounting" in markdown
        assert "### Selected Units by Provider" in markdown
        assert "| yes | 6 | 6 |" in markdown
        assert "| lookup_outcome | returned_namespace | 6 |" in markdown
        assert "| unsupported/opaque | 2 | 2 |" in markdown
        assert "| runtime_backed |" not in markdown

"""Tests for runtime observation application composed with semantic recompile."""

from __future__ import annotations

import hashlib
import sys
import textwrap
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import context_ir
import context_ir.runtime_acquisition as runtime_acquisition
import context_ir.runtime_observation_admission as runtime_observation_admission
import context_ir.runtime_observation_recompile as runtime_observation_recompile
import context_ir.runtime_probe_execution as runtime_probe_execution
import context_ir.runtime_probe_requests as runtime_probe_requests
import context_ir.runtime_probe_results as runtime_probe_results
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.runtime_observation_recompile import (
    RuntimeObservationRecompileApplication,
    RuntimeProbeResultBatchRecompileApplication,
    RuntimeProbeRunnerCallableRecompileApplication,
    apply_default_local_python_subprocess_for_diagnostic_and_recompile,
    apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile,
    apply_runtime_observations_for_diagnostic_and_recompile,
    apply_runtime_probe_result_batch_for_diagnostic_and_recompile,
    apply_runtime_probe_runner_for_diagnostic_and_recompile,
)
from context_ir.semantic_compiler import compile_semantic_context
from context_ir.semantic_diagnostics import (
    diagnose_semantic_miss,
    recompile_semantic_context,
)
from context_ir.semantic_types import (
    CapabilityTier,
    RepositorySnapshotBasis,
    RuntimeAttachmentLink,
    SemanticCompileResult,
    SemanticDiagnosticBoundary,
    SemanticDiagnosticBoundaryKind,
    SemanticDiagnosticResult,
    SemanticDiagnosticUnitStatus,
    SemanticMissEvidence,
    SemanticMissKind,
    SemanticProgram,
    SemanticRecompileResult,
    SemanticSubjectKind,
    SourceSite,
    SourceSpan,
)


def _semantic_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted semantic pipeline through dependency/frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _write_dynamic_import_program(tmp_path: Path) -> None:
    """Write a fixture with one attachable dynamic-import boundary."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(name: str) -> None:
                importlib.import_module(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_local_python_dynamic_import_program(tmp_path: Path) -> None:
    """Write a replay target importable by the local-Python worker subprocess."""
    (tmp_path / "plugins").mkdir()
    (tmp_path / "plugins" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "plugins" / "recompile_subprocess.py").write_text(
        "VALUE = 'runtime probe subprocess fixture'\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run() -> None:
                importlib.import_module("plugins.recompile_subprocess")
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_local_python_locals_program(tmp_path: Path) -> None:
    """Write a replay target with one attachable locals/0 boundary."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            MODULE_VALUE = object()

            def run() -> object:
                local_value = object()
                namespace = locals()
                assert type(namespace) is dict
                assert namespace["local_value"] is local_value
                assert "MODULE_VALUE" not in namespace
                assert "namespace" not in namespace
                return namespace
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_mixed_runtime_program(tmp_path: Path) -> None:
    """Write a fixture with several attachable runtime probe boundaries."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(obj: object, name: str, source: str) -> None:
                importlib.import_module(name)
                getattr(obj, name)
                exec(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _runtime_recompile_fixture(
    tmp_path: Path,
) -> tuple[
    SemanticProgram,
    SemanticCompileResult,
    SemanticMissEvidence,
    SemanticDiagnosticResult,
    runtime_probe_requests.RuntimeProbeRequestPlan,
    runtime_probe_requests.RuntimeProbeRequest,
    runtime_acquisition.DynamicImportRuntimeObservation,
    str,
]:
    """Build the common diagnostic-gated runtime recompile fixture."""
    _write_dynamic_import_program(tmp_path)
    program = _semantic_program(tmp_path)
    unsupported_id = _unsupported_id_for(program, "importlib.import_module(name)")
    previous_result = compile_semantic_context(
        program,
        "dynamic import",
        budget=32,
    )
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence="importlib.import_module(name)",
    )
    diagnostic = diagnose_semantic_miss(previous_result, miss_evidence, program)

    assert diagnostic.omitted_unit_ids == (unsupported_id,)
    assert len(diagnostic.planned_runtime_probe_requests) == 1
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    request = diagnostic.planned_runtime_probe_requests[0]
    observation = _dynamic_import_runtime_observation(request.source_site)
    return (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        plan,
        request,
        observation,
        unsupported_id,
    )


def _runtime_recompile_multi_request_fixture(
    tmp_path: Path,
) -> tuple[
    SemanticProgram,
    SemanticCompileResult,
    SemanticMissEvidence,
    SemanticDiagnosticResult,
    runtime_probe_requests.RuntimeProbeRequestPlan,
]:
    """Build a diagnostic/recompile fixture with several planned requests."""
    _write_mixed_runtime_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(
        program,
        "runtime boundary",
        budget=48,
    )
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.EDIT_TO_OMITTED_PATH,
        evidence="main.py",
    )
    diagnostic = diagnose_semantic_miss(previous_result, miss_evidence, program)
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    assert [request.boundary_text for request in plan.requests] == [
        "importlib.import_module(name)",
        "getattr(obj, name)",
        "exec(source)",
    ]
    return program, previous_result, miss_evidence, diagnostic, plan


def _unsupported_id_for(program: SemanticProgram, construct_text: str) -> str:
    """Return the unsupported-construct ID for ``construct_text``."""
    return next(
        construct.construct_id
        for construct in program.unsupported_constructs
        if construct.construct_text == construct_text
    )


def _boundary_for(
    result: SemanticDiagnosticResult,
    unit_id: str,
) -> SemanticDiagnosticBoundary:
    """Return the diagnostic boundary classification for ``unit_id``."""
    return next(
        boundary
        for boundary in result.boundary_classifications
        if boundary.unit_id == unit_id
    )


def _snapshot_basis() -> RepositorySnapshotBasis:
    """Return stable snapshot metadata for test observations."""
    return RepositorySnapshotBasis(
        snapshot_kind="git_commit",
        snapshot_id="abc123def456",
        is_dirty_worktree=False,
    )


def _attachment_links(site: SourceSite) -> tuple[RuntimeAttachmentLink, ...]:
    """Return stable attachment metadata for one test observation."""
    return (
        RuntimeAttachmentLink(
            attachment_id=f"attachment:{site.site_id}:trace",
            attachment_role="trace",
            description="runtime trace",
        ),
    )


def _probe_field(
    key: str = "runtime_input",
    value: str = "runtime-value",
) -> runtime_probe_results.RuntimeProbeReplayField:
    """Return one runtime probe replay/result field."""
    return runtime_probe_results.RuntimeProbeReplayField(key=key, value=value)


def _runner_runtime_assumptions() -> tuple[
    runtime_probe_results.RuntimeProbeReplayField, ...
]:
    """Return explicit runtime assumptions for runner-callable bridge tests."""
    return (
        _probe_field("python_version", "3.11"),
        _probe_field("dependency_mode", "offline-fixture"),
    )


def _runner_environment() -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return explicit environment fields for runner-callable bridge tests."""
    return (
        _probe_field("python_version", "3.11"),
        _probe_field("platform", "linux-x86_64"),
    )


def _runner_assumptions() -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return explicit runner assumptions for runner-callable bridge tests."""
    return (
        _probe_field("network", "disabled"),
        _probe_field("filesystem_mode", "read_only_fixture"),
    )


def _local_python_runner_environment(
    working_directory: Path,
) -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return local-Python subprocess environment fields for a temp repo."""
    source_root = Path(context_ir.__file__).resolve().parents[1]
    return (
        _probe_field("repository_root", str(working_directory)),
        _probe_field("working_directory", str(working_directory)),
        _probe_field("python_path_entry", str(source_root)),
    )


def _probe_execution_attempt(
    runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    *,
    outcome: runtime_probe_results.RuntimeProbeResultOutcome = (
        runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    ),
    normalized_payload: tuple[runtime_probe_results.RuntimeProbeReplayField, ...] = (),
    durable_artifact_reference: str | None = None,
    failure_summary: str | None = None,
    failure_detail_fields: tuple[
        runtime_probe_results.RuntimeProbeReplayField, ...
    ] = (),
) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
    """Return one runner attempt tied to the supplied runner request."""
    return runtime_probe_execution.RuntimeProbeExecutionAttempt(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        outcome=outcome,
        normalized_payload=normalized_payload,
        durable_artifact_reference=durable_artifact_reference,
        failure_summary=failure_summary,
        failure_detail_fields=failure_detail_fields,
    )


def _probe_fields_from_runtime_fields(
    fields: tuple[runtime_acquisition._RuntimeObservationField, ...],
) -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Convert existing typed observation fields into probe result fields."""
    return tuple(_probe_field(field.key, field.value) for field in fields)


def _runtime_fields_from_probe_fields(
    fields: tuple[runtime_probe_results.RuntimeProbeReplayField, ...],
) -> tuple[runtime_acquisition._RuntimeObservationField, ...]:
    """Convert probe result fields into the existing typed observation shape."""
    return tuple(
        runtime_acquisition._RuntimeObservationField(
            key=field.key,
            value=field.value,
        )
        for field in fields
    )


def _replay_inputs_for_result(
    request: runtime_probe_requests.RuntimeProbeRequest,
    observation: runtime_observation_admission.RuntimeObservation,
) -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return non-empty replay inputs for an observed result contract."""
    replay_inputs = _probe_fields_from_runtime_fields(observation.replay_inputs)
    if replay_inputs:
        return replay_inputs
    return (_probe_field("request_id", request.request_id),)


def _replay_artifact_for_result(
    request: runtime_probe_requests.RuntimeProbeRequest,
    observation: runtime_observation_admission.RuntimeObservation,
) -> runtime_probe_results.RuntimeProbeReplayArtifact:
    """Build a replay artifact that mirrors an existing typed observation."""
    return runtime_probe_results.RuntimeProbeReplayArtifact(
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=_replay_inputs_for_result(request, observation),
        runtime_assumptions=(
            _probe_field("python_version", "3.11"),
            _probe_field("platform", "test"),
        ),
    )


def _observed_probe_result_for_observation(
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
    request: runtime_probe_requests.RuntimeProbeRequest,
    observation: runtime_observation_admission.RuntimeObservation,
) -> runtime_probe_results.RuntimeProbeObservedResult:
    """Build an observed probe result carrying an existing observation's data."""
    return runtime_probe_results.RuntimeProbeObservedResult(
        plan_id=plan.plan_id,
        request_id=request.request_id,
        request=request,
        replay_artifact=_replay_artifact_for_result(request, observation),
        normalized_payload=_probe_fields_from_runtime_fields(
            observation.normalized_payload
        ),
        durable_artifact_reference=observation.durable_payload_reference,
    )


def _non_proof_probe_result(
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
    request: runtime_probe_requests.RuntimeProbeRequest,
) -> runtime_probe_results.RuntimeProbeNonProofResult:
    """Build a failed probe result for non-proof preservation tests."""
    return runtime_probe_results.RuntimeProbeNonProofResult(
        plan_id=plan.plan_id,
        request_id=request.request_id,
        request=request,
        outcome=runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        failure_summary="probe exceeded timeout",
        failure_detail_fields=(_probe_field("timeout_seconds", "30"),),
    )


def _expected_probe_result_attachment_link(
    result: runtime_probe_results.RuntimeProbeObservedResult,
) -> RuntimeAttachmentLink:
    """Return the deterministic attachment link expected from the result bridge."""
    if result.durable_artifact_reference is None:
        attachment_identity = f"{result.plan_id}:{result.request_id}"
        description = "inline runtime probe result payload"
    else:
        attachment_identity = result.durable_artifact_reference
        description = "durable runtime probe result artifact"
    attachment_digest = hashlib.sha256(attachment_identity.encode("utf-8")).hexdigest()[
        :24
    ]
    return RuntimeAttachmentLink(
        attachment_id=f"runtime_probe_result:{attachment_digest}",
        attachment_role="runtime_probe_result",
        description=description,
    )


def _assert_observation_copied_probe_result(
    observation: runtime_observation_admission.RuntimeObservation,
    result: runtime_probe_results.RuntimeProbeObservedResult,
) -> None:
    """Assert the bridge copied the proof-bearing result contract fields."""
    assert observation.site == result.request.source_site
    assert observation.probe_identifier == result.replay_artifact.probe_identifier
    assert (
        observation.probe_contract_revision
        == result.replay_artifact.probe_contract_revision
    )
    assert (
        observation.repository_snapshot_basis
        == result.replay_artifact.repository_snapshot_basis
    )
    assert observation.attachment_links == (
        _expected_probe_result_attachment_link(result),
    )
    assert observation.replay_target == result.replay_artifact.replay_target
    assert observation.replay_selector == result.replay_artifact.replay_selector
    assert observation.replay_inputs == _runtime_fields_from_probe_fields(
        result.replay_artifact.replay_inputs
    )
    assert observation.runtime_assumptions == _runtime_fields_from_probe_fields(
        result.replay_artifact.runtime_assumptions
    )
    assert observation.normalized_payload == _runtime_fields_from_probe_fields(
        result.normalized_payload
    )
    assert observation.durable_payload_reference == result.durable_artifact_reference


def _dynamic_import_runtime_observation(
    site: SourceSite,
) -> runtime_acquisition.DynamicImportRuntimeObservation:
    """Create one admissible dynamic-import observation."""
    return runtime_acquisition.DynamicImportRuntimeObservation(
        site=site,
        probe_identifier="probe:dynamic-import",
        probe_contract_revision="2026-05-05.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:dynamic_import",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="imported_module",
                value="pkg.dynamic",
            ),
        ),
    )


def _exec_runtime_observation(
    site: SourceSite,
) -> runtime_acquisition.ExecRuntimeObservation:
    """Create one exec observation for mismatch and duplicate-site tests."""
    return runtime_acquisition.ExecRuntimeObservation(
        site=site,
        probe_identifier="probe:exec",
        probe_contract_revision="2026-05-05.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:exec",
        replay_inputs=(
            runtime_acquisition._RuntimeObservationField(
                key="source_shape",
                value="literal_statement",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="source_sha256",
                value=hashlib.sha256(b"pass").hexdigest(),
            ),
        ),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="execution_outcome",
                value="completed",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="statement_kind",
                value="pass",
            ),
        ),
        durable_payload_reference=f"artifact://exec-result/{site.site_id}.json",
    )


def _unplanned_site() -> SourceSite:
    """Return a source site that is not present in the diagnostic request plan."""
    return SourceSite(
        site_id="site:unplanned",
        file_path="main.py",
        span=SourceSpan(
            start_line=99,
            start_column=0,
            end_line=99,
            end_column=12,
        ),
        snippet="missing()",
    )


def _program_state(
    program: SemanticProgram,
) -> tuple[object, object, object, object, object, object]:
    """Return semantic program fields that must remain unchanged."""
    return (
        dict(program.resolved_symbols),
        list(program.proven_dependencies),
        list(program.unresolved_frontier),
        list(program.unsupported_constructs),
        list(program.provenance_records),
        list(program.diagnostics),
    )


def _previous_result_state(
    previous_result: SemanticCompileResult,
) -> tuple[object, object, object, object]:
    """Return compile result fields relevant to mutation checks."""
    return (
        previous_result.optimization,
        previous_result.document,
        previous_result.compile_context,
        previous_result.omitted_unit_ids,
    )


def _diagnostic_state(
    diagnostic: SemanticDiagnosticResult,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    str,
    tuple[SemanticDiagnosticBoundary, ...],
    tuple[runtime_probe_requests.RuntimeProbeRequest, ...],
    runtime_probe_requests.RuntimeProbeRequestPlan | None,
]:
    """Return diagnostic fields that should not change during composition."""
    return (
        diagnostic.grounded_unit_ids,
        diagnostic.omitted_unit_ids,
        diagnostic.too_shallow_unit_ids,
        diagnostic.sufficiently_represented_unit_ids,
        diagnostic.recommended_expansions,
        diagnostic.reason,
        diagnostic.boundary_classifications,
        diagnostic.planned_runtime_probe_requests,
        diagnostic.planned_runtime_probe_request_plan,
    )


def _plan_state(
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
) -> tuple[
    tuple[runtime_probe_requests.RuntimeProbeRequest, ...],
    tuple[str, ...],
    str,
]:
    """Return runtime request-plan fields that should remain stable."""
    return (plan.requests, plan.request_ids, plan.plan_id)


def _request_state(
    request: runtime_probe_requests.RuntimeProbeRequest,
) -> tuple[
    str,
    SemanticSubjectKind,
    str,
    SourceSite,
    str,
    runtime_probe_requests.RuntimeProbeRequestStatus,
]:
    """Return runtime request fields that should remain stable."""
    return (
        request.request_id,
        request.subject_kind,
        request.subject_id,
        request.source_site,
        request.boundary_text,
        request.status,
    )


def _observation_state(
    observation: runtime_acquisition.DynamicImportRuntimeObservation,
) -> tuple[object, ...]:
    """Return runtime observation fields that should remain stable."""
    return (
        observation.site,
        observation.probe_identifier,
        observation.probe_contract_revision,
        observation.repository_snapshot_basis,
        observation.attachment_links,
        observation.replay_target,
        observation.replay_selector,
        observation.replay_inputs,
        observation.runtime_assumptions,
        observation.normalized_payload,
        observation.durable_payload_reference,
    )


def _observed_result_state(
    result: runtime_probe_results.RuntimeProbeObservedResult,
) -> tuple[object, ...]:
    """Return observed probe result fields that should remain stable."""
    return (
        result.plan_id,
        result.request_id,
        result.request,
        result.replay_artifact,
        result.normalized_payload,
        result.durable_artifact_reference,
        result.outcome,
    )


def _non_proof_result_state(
    result: runtime_probe_results.RuntimeProbeNonProofResult,
) -> tuple[object, ...]:
    """Return non-proof probe result fields that should remain stable."""
    return (
        result.plan_id,
        result.request_id,
        result.request,
        result.outcome,
        result.failure_summary,
        result.replay_artifact,
        result.failure_detail_fields,
    )


def _batch_state(
    batch: runtime_probe_results.RuntimeProbeResultBatch,
) -> tuple[object, ...]:
    """Return result batch fields that should remain stable."""
    return (batch.plan_id, batch.results)


def test_runtime_observation_recompile_applies_and_recompiles_updated_program(
    tmp_path: Path,
) -> None:
    """The helper applies admitted observations, then recompiles the update."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        plan,
        request,
        observation,
        unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)
    original_program_state = _program_state(program)
    previous_state = _previous_result_state(previous_result)
    diagnostic_before = _diagnostic_state(diagnostic)
    plan_before = _plan_state(plan)
    request_before = _request_state(request)
    observation_before = _observation_state(observation)

    result = apply_runtime_observations_for_diagnostic_and_recompile(
        program,
        diagnostic,
        (observation,),
        previous_result,
        miss_evidence,
        delta_budget=160,
    )
    application = result.observation_application
    recompile_result = result.recompile_result
    recompile_boundary = _boundary_for(recompile_result.diagnostic, unsupported_id)
    selected_trace = next(
        selection.trace_summary
        for selection in recompile_result.compile_result.optimization.selections
        if selection.unit_id == unsupported_id
    )

    assert isinstance(
        result,
        RuntimeObservationRecompileApplication,
    )
    assert isinstance(application.updated_program, SemanticProgram)
    assert isinstance(recompile_result, SemanticRecompileResult)
    assert application.diagnostic is diagnostic
    assert application.admissions[0].request is request
    assert application.admissions[0].observation is observation
    assert application.updated_program is not program
    assert recompile_result.diagnostic.planned_runtime_probe_requests == ()
    assert recompile_result.diagnostic.planned_runtime_probe_request_plan == (
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )
    assert recompile_boundary.status is SemanticDiagnosticUnitStatus.OMITTED
    assert recompile_boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert (
        recompile_boundary.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    )
    assert recompile_boundary.has_attached_runtime_provenance is True
    assert selected_trace is not None
    assert selected_trace.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert selected_trace.has_attached_runtime_provenance is True
    assert selected_trace.attached_runtime_provenance_record_ids == tuple(
        record.record_id for record in application.updated_program.provenance_records
    )
    assert unsupported_id in recompile_result.newly_selected_unit_ids
    assert _program_state(program) == original_program_state
    assert _previous_result_state(previous_result) == previous_state
    assert _diagnostic_state(diagnostic) == diagnostic_before
    assert _plan_state(plan) == plan_before
    assert _request_state(request) == request_before
    assert _observation_state(observation) == observation_before


def test_runtime_probe_result_batch_recompile_admits_observed_and_recompiles(
    tmp_path: Path,
) -> None:
    """Observed result batches bridge into attachment before semantic recompile."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        plan,
        request,
        observation,
        unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)
    observed = _observed_probe_result_for_observation(plan, request, observation)
    batch = runtime_probe_results.RuntimeProbeResultBatch(
        plan_id=plan.plan_id,
        results=(observed,),
    )
    original_program_state = _program_state(program)
    previous_state = _previous_result_state(previous_result)
    diagnostic_before = _diagnostic_state(diagnostic)
    plan_before = _plan_state(plan)
    request_before = _request_state(request)
    observation_before = _observation_state(observation)
    observed_before = _observed_result_state(observed)
    batch_before = _batch_state(batch)

    result = apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
        program,
        diagnostic,
        batch,
        previous_result,
        miss_evidence,
        delta_budget=160,
    )
    application = result.observation_application
    recompile_result = result.recompile_result
    admitted_observation = application.admissions[0].observation
    recompile_boundary = _boundary_for(recompile_result.diagnostic, unsupported_id)
    selected_trace = next(
        selection.trace_summary
        for selection in recompile_result.compile_result.optimization.selections
        if selection.unit_id == unsupported_id
    )

    assert isinstance(result, RuntimeProbeResultBatchRecompileApplication)
    assert isinstance(application.updated_program, SemanticProgram)
    assert isinstance(recompile_result, SemanticRecompileResult)
    assert result.result_batch_admission.non_proof_results == ()
    assert result.non_proof_results == ()
    assert application.diagnostic is diagnostic
    assert application.admissions == result.result_batch_admission.admissions
    assert application.admissions[0].request is request
    assert application.admissions[0].request_id == request.request_id
    assert application.updated_program is not program
    assert isinstance(
        admitted_observation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    )
    assert admitted_observation is not observation
    _assert_observation_copied_probe_result(admitted_observation, observed)
    assert recompile_boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert recompile_boundary.has_attached_runtime_provenance is True
    assert selected_trace is not None
    assert selected_trace.has_attached_runtime_provenance is True
    assert selected_trace.attached_runtime_provenance_record_ids == tuple(
        record.record_id for record in application.updated_program.provenance_records
    )
    assert unsupported_id in recompile_result.newly_selected_unit_ids
    assert _program_state(program) == original_program_state
    assert _previous_result_state(previous_result) == previous_state
    assert _diagnostic_state(diagnostic) == diagnostic_before
    assert _plan_state(plan) == plan_before
    assert _request_state(request) == request_before
    assert _observation_state(observation) == observation_before
    assert _observed_result_state(observed) == observed_before
    assert _batch_state(batch) == batch_before


def test_runtime_probe_result_batch_recompile_preserves_non_proof_only_batch(
    tmp_path: Path,
) -> None:
    """Non-proof-only batches remain separate and recompile the original program."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        plan,
        request,
        _observation,
        unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)
    non_proof = _non_proof_probe_result(plan, request)
    batch = runtime_probe_results.RuntimeProbeResultBatch(
        plan_id=plan.plan_id,
        results=(non_proof,),
    )
    non_proof_before = _non_proof_result_state(non_proof)
    batch_before = _batch_state(batch)

    result = apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
        program,
        diagnostic,
        batch,
        previous_result,
        miss_evidence,
        delta_budget=96,
    )
    expected_recompile = recompile_semantic_context(
        previous_result,
        miss_evidence,
        delta_budget=96,
        program=program,
    )
    boundary = _boundary_for(result.recompile_result.diagnostic, unsupported_id)

    assert result.result_batch_admission.admissions == ()
    assert result.result_batch_admission.non_proof_results == (non_proof,)
    assert result.non_proof_results == (non_proof,)
    assert all(
        non_proof_result.is_admissible_runtime_backed_proof is False
        for non_proof_result in result.non_proof_results
    )
    assert result.observation_application.diagnostic is diagnostic
    assert result.observation_application.admissions == ()
    assert result.observation_application.updated_program is program
    assert result.recompile_result.diagnostic == expected_recompile.diagnostic
    assert result.recompile_result.newly_selected_unit_ids == (
        expected_recompile.newly_selected_unit_ids
    )
    assert boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
    )
    assert program.provenance_records == []
    assert _non_proof_result_state(non_proof) == non_proof_before
    assert _batch_state(batch) == batch_before

    with pytest.raises(FrozenInstanceError):
        result.non_proof_results = ()


def test_runtime_probe_result_batch_recompile_preserves_plan_order_for_partial_batches(
    tmp_path: Path,
) -> None:
    """Partial mixed batches are admitted by plan order, never result order."""
    program, previous_result, miss_evidence, diagnostic, plan = (
        _runtime_recompile_multi_request_fixture(tmp_path)
    )
    dynamic_observation = _dynamic_import_runtime_observation(
        plan.requests[0].source_site
    )
    exec_observation = _exec_runtime_observation(plan.requests[2].source_site)
    observed_dynamic = _observed_probe_result_for_observation(
        plan,
        plan.requests[0],
        dynamic_observation,
    )
    observed_exec = _observed_probe_result_for_observation(
        plan,
        plan.requests[2],
        exec_observation,
    )
    non_proof_getattr = _non_proof_probe_result(plan, plan.requests[1])
    batch = runtime_probe_results.RuntimeProbeResultBatch(
        plan_id=plan.plan_id,
        results=(observed_exec, non_proof_getattr, observed_dynamic),
    )

    result = apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
        program,
        diagnostic,
        batch,
        previous_result,
        miss_evidence,
        delta_budget=96,
    )

    assert [
        admission.request_id for admission in result.result_batch_admission.admissions
    ] == [
        plan.request_ids[0],
        plan.request_ids[2],
    ]
    assert [
        admission.request.boundary_text
        for admission in result.observation_application.admissions
    ] == [
        "importlib.import_module(name)",
        "exec(source)",
    ]
    assert result.observation_application.admissions == (
        result.result_batch_admission.admissions
    )
    assert result.non_proof_results == (non_proof_getattr,)
    assert result.result_batch_admission.non_proof_results == (non_proof_getattr,)
    assert len(result.observation_application.updated_program.provenance_records) == 2
    assert {
        record.subject_id
        for record in result.observation_application.updated_program.provenance_records
    } == {plan.requests[0].subject_id, plan.requests[2].subject_id}
    _assert_observation_copied_probe_result(
        result.observation_application.admissions[0].observation,
        observed_dynamic,
    )
    _assert_observation_copied_probe_result(
        result.observation_application.admissions[1].observation,
        observed_exec,
    )
    assert all(
        non_proof_result.is_admissible_runtime_backed_proof is False
        for non_proof_result in result.non_proof_results
    )


def test_runtime_probe_runner_callable_recompile_collects_and_recompiles(
    tmp_path: Path,
) -> None:
    """Runner-callable bridge preserves preparation, attempt, and result identity."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        plan,
        request,
        observation,
        unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)
    runtime_assumptions = _runner_runtime_assumptions()
    runner_environment = _runner_environment()
    runner_assumptions = _runner_assumptions()
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []
    returned_attempts: list[runtime_probe_execution.RuntimeProbeExecutionAttempt] = []
    embedded_batches: list[tuple[str, ...]] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        attempt = _probe_execution_attempt(
            runner_request,
            normalized_payload=_probe_fields_from_runtime_fields(
                observation.normalized_payload
            ),
            durable_artifact_reference=observation.durable_payload_reference,
        )
        returned_attempts.append(attempt)
        return attempt

    def embed_fn(texts: list[str]) -> list[list[float]]:
        embedded_batches.append(tuple(texts))
        return [[1.0, 0.0] for _text in texts]

    result = apply_runtime_probe_runner_for_diagnostic_and_recompile(
        program,
        diagnostic,
        previous_result,
        miss_evidence,
        delta_budget=160,
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision="runtime-probe-contract:test.1",
        runtime_assumptions=runtime_assumptions,
        runner_contract_revision="runtime-probe-runner:test.1",
        timeout_seconds=30,
        runner_environment=runner_environment,
        runner_assumptions=runner_assumptions,
        runner=runner,
        embed_fn=embed_fn,
    )
    preparation = result.runner_request_preparation
    collection = result.runner_attempt_collection
    recompile_application = result.result_batch_recompile_application
    observed_result = collection.result_batch.results[0]
    recompile_boundary = _boundary_for(
        recompile_application.recompile_result.diagnostic,
        unsupported_id,
    )

    assert isinstance(result, RuntimeProbeRunnerCallableRecompileApplication)
    assert preparation.diagnostic is diagnostic
    assert preparation.request_plan is plan
    assert preparation.execution_input_batch.request_ids == plan.request_ids
    assert preparation.runner_request_batch.request_ids == plan.request_ids
    assert preparation.execution_input_batch.inputs[0].request is request
    assert preparation.runner_request_batch.runner_requests[0].request is request
    assert (
        preparation.execution_input_batch.inputs[0].replay_artifact.runtime_assumptions
        is runtime_assumptions
    )
    assert preparation.runner_request_batch.runner_environment is runner_environment
    assert preparation.runner_request_batch.runner_assumptions is runner_assumptions
    assert collection.runner_request_batch is preparation.runner_request_batch
    assert tuple(calls) == preparation.runner_request_batch.runner_requests
    assert collection.attempts == tuple(returned_attempts)
    assert collection.attempts[0] is returned_attempts[0]
    assert collection.result_batch.plan_id == plan.plan_id
    assert observed_result.request is request
    assert (
        observed_result.replay_artifact
        is preparation.runner_request_batch.runner_requests[0].replay_artifact
    )
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert recompile_application.result_batch_admission.non_proof_results == ()
    assert recompile_application.non_proof_results == ()
    assert recompile_application.observation_application.diagnostic is diagnostic
    assert recompile_application.observation_application.admissions[0].request is (
        request
    )
    assert recompile_application.observation_application.updated_program is not program
    _assert_observation_copied_probe_result(
        recompile_application.observation_application.admissions[0].observation,
        observed_result,
    )
    assert recompile_boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert (
        unsupported_id in recompile_application.recompile_result.newly_selected_unit_ids
    )
    assert embedded_batches

    with pytest.raises(FrozenInstanceError):
        result.runner_attempt_collection = collection


def test_runtime_probe_runner_callable_recompile_uses_local_python_worker_subprocess(
    tmp_path: Path,
) -> None:
    """Real local-Python worker attempts flow through admission and recompile."""
    _write_local_python_dynamic_import_program(tmp_path)
    program = _semantic_program(tmp_path)
    boundary_text = 'importlib.import_module("plugins.recompile_subprocess")'
    unsupported_id = _unsupported_id_for(program, boundary_text)
    previous_result = compile_semantic_context(
        program,
        "dynamic import",
        budget=32,
    )
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence=boundary_text,
    )
    diagnostic = diagnose_semantic_miss(previous_result, miss_evidence, program)
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    assert diagnostic.omitted_unit_ids == (unsupported_id,)
    assert len(plan.requests) == 1
    request = plan.requests[0]
    assert request.boundary_text == boundary_text
    assert (
        request.family_label is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert request.form_label == "dynamic_import:importlib.import_module/1"
    assert request.replay_target_seed == "main.run"

    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (
            runtime_probe_execution.make_runtime_probe_local_python_subprocess_handler_entry(
                family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
                form_label="dynamic_import:importlib.import_module/1",
                python_executable=sys.executable,
                module_name="context_ir.runtime_probe_worker",
                invocation_contract_revision=(
                    "runtime-probe-local-python-subprocess:test.1"
                ),
                completion_contract_revision=(
                    "runtime-probe-local-python-completion:test.1"
                ),
            ),
        )
    )
    result = apply_runtime_probe_runner_for_diagnostic_and_recompile(
        program,
        diagnostic,
        previous_result,
        miss_evidence,
        delta_budget=160,
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision="runtime-probe-contract:test.1",
        runtime_assumptions=_runner_runtime_assumptions(),
        runner_contract_revision="runtime-probe-runner:test.1",
        timeout_seconds=30,
        runner_environment=_local_python_runner_environment(tmp_path),
        runner_assumptions=_runner_assumptions(),
        runner=dispatching_runner,
    )
    collection = result.runner_attempt_collection
    recompile_application = result.result_batch_recompile_application
    attempt = collection.attempts[0]
    observed_result = collection.result_batch.results[0]
    admission = recompile_application.observation_application.admissions[0]
    recompiled_boundary = _boundary_for(
        recompile_application.recompile_result.diagnostic,
        unsupported_id,
    )
    expected_payload = (
        _probe_field("imported_module", "plugins.recompile_subprocess"),
    )

    assert collection.runner_request_batch.request_ids == plan.request_ids
    assert collection.runner_request_batch.runner_requests[0].request is request
    assert attempt.request is request
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == expected_payload
    assert attempt.failure_summary is None
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.request is request
    assert observed_result.normalized_payload == expected_payload
    assert observed_result.is_admissible_runtime_backed_proof is True
    assert admission.request is request
    assert admission.request_id == observed_result.request_id
    assert admission.observation.normalized_payload == (
        _runtime_fields_from_probe_fields(expected_payload)
    )
    _assert_observation_copied_probe_result(
        admission.observation,
        observed_result,
    )
    assert recompile_application.result_batch_admission.non_proof_results == ()
    assert recompile_application.non_proof_results == ()
    assert recompile_application.observation_application.updated_program is not program
    assert recompiled_boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert recompiled_boundary.has_attached_runtime_provenance is True
    assert (
        unsupported_id in recompile_application.recompile_result.newly_selected_unit_ids
    )


def test_dynamic_import_local_python_subprocess_recompile_helper_uses_default_worker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The internal helper composes the default worker runner with recompile."""
    _write_local_python_dynamic_import_program(tmp_path)
    program = _semantic_program(tmp_path)
    boundary_text = 'importlib.import_module("plugins.recompile_subprocess")'
    unsupported_id = _unsupported_id_for(program, boundary_text)
    previous_result = compile_semantic_context(
        program,
        "dynamic import",
        budget=32,
    )
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence=boundary_text,
    )
    diagnostic = diagnose_semantic_miss(previous_result, miss_evidence, program)
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    assert diagnostic.omitted_unit_ids == (unsupported_id,)
    assert len(plan.requests) == 1
    request = plan.requests[0]
    assert request.boundary_text == boundary_text
    assert (
        request.family_label is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert request.form_label == "dynamic_import:importlib.import_module/1"
    assert request.replay_target_seed == "main.run"

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

    result = apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile(
        program,
        diagnostic,
        previous_result,
        miss_evidence,
        delta_budget=160,
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision="runtime-probe-contract:test.1",
        runtime_assumptions=_runner_runtime_assumptions(),
        runner_contract_revision="runtime-probe-runner:test.1",
        timeout_seconds=30,
        runner_environment=_local_python_runner_environment(tmp_path),
        runner_assumptions=_runner_assumptions(),
    )
    collection = result.runner_attempt_collection
    recompile_application = result.result_batch_recompile_application
    attempt = collection.attempts[0]
    observed_result = collection.result_batch.results[0]
    admission = recompile_application.observation_application.admissions[0]
    recompiled_boundary = _boundary_for(
        recompile_application.recompile_result.diagnostic,
        unsupported_id,
    )
    expected_payload = (
        _probe_field("imported_module", "plugins.recompile_subprocess"),
    )

    assert subprocess_invocations == [
        (sys.executable, "-m", "context_ir.runtime_probe_worker"),
    ]
    assert isinstance(result, RuntimeProbeRunnerCallableRecompileApplication)
    assert collection.runner_request_batch.request_ids == plan.request_ids
    assert collection.runner_request_batch.runner_requests[0].request is request
    assert attempt.request is request
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == expected_payload
    assert attempt.failure_summary is None
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.request is request
    assert observed_result.normalized_payload == expected_payload
    assert observed_result.is_admissible_runtime_backed_proof is True
    assert admission.request is request
    assert admission.request_id == observed_result.request_id
    assert admission.observation.normalized_payload == (
        _runtime_fields_from_probe_fields(expected_payload)
    )
    _assert_observation_copied_probe_result(
        admission.observation,
        observed_result,
    )
    assert recompile_application.result_batch_admission.non_proof_results == ()
    assert recompile_application.non_proof_results == ()
    assert recompile_application.observation_application.updated_program is not program
    assert recompiled_boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert recompiled_boundary.has_attached_runtime_provenance is True
    assert (
        unsupported_id in recompile_application.recompile_result.newly_selected_unit_ids
    )


def test_default_local_python_subprocess_recompile_helper_observes_locals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default helper composes the real worker for non-dynamic forms."""
    _write_local_python_locals_program(tmp_path)
    program = _semantic_program(tmp_path)
    boundary_text = "locals()"
    unsupported_id = _unsupported_id_for(program, boundary_text)
    previous_result = compile_semantic_context(
        program,
        "runtime mutation",
        budget=32,
    )
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence=boundary_text,
    )
    diagnostic = diagnose_semantic_miss(previous_result, miss_evidence, program)
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    assert diagnostic.omitted_unit_ids == (unsupported_id,)
    assert len(plan.requests) == 1
    request = plan.requests[0]
    assert request.boundary_text == boundary_text
    assert (
        request.family_label
        is runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION
    )
    assert request.form_label == "runtime_mutation:locals/0"
    assert request.replay_target_seed == "main.run"

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

    result = apply_default_local_python_subprocess_for_diagnostic_and_recompile(
        program,
        diagnostic,
        previous_result,
        miss_evidence,
        delta_budget=160,
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision="runtime-probe-contract:test.1",
        runtime_assumptions=_runner_runtime_assumptions(),
        runner_contract_revision="runtime-probe-runner:test.1",
        timeout_seconds=30,
        runner_environment=_local_python_runner_environment(tmp_path),
        runner_assumptions=_runner_assumptions(),
    )
    collection = result.runner_attempt_collection
    recompile_application = result.result_batch_recompile_application
    attempt = collection.attempts[0]
    observed_result = collection.result_batch.results[0]
    admission = recompile_application.observation_application.admissions[0]
    recompiled_boundary = _boundary_for(
        recompile_application.recompile_result.diagnostic,
        unsupported_id,
    )
    expected_payload = (_probe_field("lookup_outcome", "returned_namespace"),)

    assert subprocess_invocations == [
        (sys.executable, "-m", "context_ir.runtime_probe_worker"),
    ]
    assert isinstance(result, RuntimeProbeRunnerCallableRecompileApplication)
    assert collection.runner_request_batch.request_ids == plan.request_ids
    assert collection.runner_request_batch.runner_requests[0].request is request
    assert attempt.request is request
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == expected_payload
    assert attempt.failure_summary is None
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.request is request
    assert observed_result.normalized_payload == expected_payload
    assert observed_result.is_admissible_runtime_backed_proof is True
    assert admission.request is request
    assert admission.request_id == observed_result.request_id
    assert admission.observation.normalized_payload == (
        _runtime_fields_from_probe_fields(expected_payload)
    )
    _assert_observation_copied_probe_result(
        admission.observation,
        observed_result,
    )
    assert recompile_application.result_batch_admission.non_proof_results == ()
    assert recompile_application.non_proof_results == ()
    assert recompile_application.observation_application.updated_program is not program
    assert recompiled_boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert recompiled_boundary.has_attached_runtime_provenance is True
    assert (
        unsupported_id in recompile_application.recompile_result.newly_selected_unit_ids
    )


def test_runtime_probe_runner_callable_recompile_preserves_non_proof_results(
    tmp_path: Path,
) -> None:
    """Runner non-proof results stay separate through result-batch recompile."""
    program, previous_result, miss_evidence, diagnostic, plan = (
        _runtime_recompile_multi_request_fixture(tmp_path)
    )
    dynamic_observation = _dynamic_import_runtime_observation(
        plan.requests[0].source_site
    )

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        if runner_request.request is not plan.requests[0]:
            return _probe_execution_attempt(
                runner_request,
                outcome=runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
                failure_summary="probe exceeded timeout",
                failure_detail_fields=(_probe_field("timeout_seconds", "30"),),
            )
        return _probe_execution_attempt(
            runner_request,
            normalized_payload=_probe_fields_from_runtime_fields(
                dynamic_observation.normalized_payload
            ),
        )

    result = apply_runtime_probe_runner_for_diagnostic_and_recompile(
        program,
        diagnostic,
        previous_result,
        miss_evidence,
        delta_budget=96,
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision="runtime-probe-contract:test.1",
        runtime_assumptions=_runner_runtime_assumptions(),
        runner_contract_revision="runtime-probe-runner:test.1",
        timeout_seconds=30,
        runner_environment=_runner_environment(),
        runner_assumptions=_runner_assumptions(),
        runner=runner,
    )
    result_batch = result.runner_attempt_collection.result_batch
    recompile_application = result.result_batch_recompile_application
    non_proof_result = result_batch.results[1]

    assert isinstance(
        non_proof_result,
        runtime_probe_results.RuntimeProbeNonProofResult,
    )
    assert [
        admission.request_id
        for admission in recompile_application.result_batch_admission.admissions
    ] == [
        plan.request_ids[0],
    ]
    assert recompile_application.non_proof_results == (
        non_proof_result,
        result_batch.results[2],
    )
    assert recompile_application.non_proof_results[0] is non_proof_result
    assert recompile_application.non_proof_results[1] is result_batch.results[2]
    assert (
        recompile_application.result_batch_admission.non_proof_results[0]
        is non_proof_result
    )
    assert all(
        non_proof.is_admissible_runtime_backed_proof is False
        for non_proof in recompile_application.non_proof_results
    )
    _assert_observation_copied_probe_result(
        recompile_application.observation_application.admissions[0].observation,
        result_batch.results[0],
    )


def test_runtime_probe_runner_callable_recompile_supports_empty_plan(
    tmp_path: Path,
) -> None:
    """Empty planned request batches do not invoke the runner callable."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        _plan,
        _request,
        _observation,
        _unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)
    empty_plan = runtime_probe_requests.build_runtime_probe_request_plan(())
    empty_diagnostic = replace(
        diagnostic,
        planned_runtime_probe_requests=(),
        planned_runtime_probe_request_plan=empty_plan,
    )
    was_called = False

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        nonlocal was_called
        was_called = True
        return _probe_execution_attempt(
            runner_request,
            normalized_payload=(_probe_field("observed_module", "pkg.dynamic"),),
        )

    result = apply_runtime_probe_runner_for_diagnostic_and_recompile(
        program,
        empty_diagnostic,
        previous_result,
        miss_evidence,
        delta_budget=96,
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision="runtime-probe-contract:test.1",
        runtime_assumptions=_runner_runtime_assumptions(),
        runner_contract_revision="runtime-probe-runner:test.1",
        timeout_seconds=30,
        runner_environment=_runner_environment(),
        runner_assumptions=_runner_assumptions(),
        runner=runner,
    )
    recompile_application = result.result_batch_recompile_application
    expected_recompile = recompile_semantic_context(
        previous_result,
        miss_evidence,
        delta_budget=96,
        program=program,
    )

    assert was_called is False
    assert result.runner_request_preparation.diagnostic is empty_diagnostic
    assert result.runner_request_preparation.request_plan is empty_plan
    assert result.runner_attempt_collection.attempts == ()
    assert result.runner_attempt_collection.result_batch.results == ()
    assert recompile_application.non_proof_results == ()
    assert recompile_application.observation_application.diagnostic is empty_diagnostic
    assert recompile_application.observation_application.admissions == ()
    assert recompile_application.observation_application.updated_program is program
    assert recompile_application.recompile_result.diagnostic == (
        expected_recompile.diagnostic
    )
    assert recompile_application.recompile_result.newly_selected_unit_ids == (
        expected_recompile.newly_selected_unit_ids
    )


def test_runtime_probe_runner_callable_recompile_propagates_runner_exceptions(
    tmp_path: Path,
) -> None:
    """Runner exceptions propagate without being converted to probe results."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        _plan,
        request,
        _observation,
        _unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        raise RuntimeError("runner failed")

    with pytest.raises(RuntimeError, match="runner failed"):
        apply_runtime_probe_runner_for_diagnostic_and_recompile(
            program,
            diagnostic,
            previous_result,
            miss_evidence,
            delta_budget=96,
            repository_snapshot_basis=_snapshot_basis(),
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=_runner_runtime_assumptions(),
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
            runner=runner,
        )

    assert len(calls) == 1
    assert calls[0].request is request


def test_runtime_probe_result_batch_recompile_propagates_admission_and_recompile_gates(
    tmp_path: Path,
) -> None:
    """The batch helper lets existing admission and recompile validators fail."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        plan,
        request,
        observation,
        _unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)
    observed = _observed_probe_result_for_observation(plan, request, observation)
    batch = runtime_probe_results.RuntimeProbeResultBatch(
        plan_id=plan.plan_id,
        results=(observed,),
    )

    missing_plan = replace(diagnostic, planned_runtime_probe_request_plan=None)
    with pytest.raises(ValueError, match="planned_runtime_probe_request_plan"):
        apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
            program,
            missing_plan,
            batch,
            previous_result,
            miss_evidence,
            delta_budget=96,
        )

    wrong_plan_batch = runtime_probe_results.RuntimeProbeResultBatch(
        plan_id="runtime_probe_request_plan:other",
        results=(),
    )
    with pytest.raises(ValueError, match="plan_id must match request plan"):
        apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
            program,
            diagnostic,
            wrong_plan_batch,
            previous_result,
            miss_evidence,
            delta_budget=96,
        )

    duplicate_batch = runtime_probe_results.RuntimeProbeResultBatch(
        plan_id=plan.plan_id,
        results=(observed,),
    )
    object.__setattr__(duplicate_batch, "results", (observed, observed))
    with pytest.raises(ValueError, match="duplicate runtime probe result request_id"):
        apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
            program,
            diagnostic,
            duplicate_batch,
            previous_result,
            miss_evidence,
            delta_budget=96,
        )

    with pytest.raises(ValueError, match="delta_budget must be >= 0"):
        apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
            program,
            diagnostic,
            batch,
            previous_result,
            miss_evidence,
            delta_budget=-1,
        )

    previous_without_context = replace(previous_result, compile_context=None)
    with pytest.raises(ValueError, match="compile_context"):
        apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
            program,
            diagnostic,
            batch,
            previous_without_context,
            miss_evidence,
            delta_budget=96,
        )


def test_runtime_probe_result_batch_recompile_helper_is_internal() -> None:
    """The recompile bridges stay off root and wildcard public surfaces."""
    assert (
        "apply_runtime_probe_result_batch_for_diagnostic_and_recompile"
        not in runtime_observation_recompile.__all__
    )
    assert (
        "RuntimeProbeResultBatchRecompileApplication"
        not in runtime_observation_recompile.__all__
    )
    assert (
        "apply_runtime_probe_result_batch_for_diagnostic_and_recompile"
        not in context_ir.__all__
    )
    assert "RuntimeProbeResultBatchRecompileApplication" not in context_ir.__all__
    assert not hasattr(
        context_ir,
        "apply_runtime_probe_result_batch_for_diagnostic_and_recompile",
    )
    assert not hasattr(context_ir, "RuntimeProbeResultBatchRecompileApplication")
    assert (
        "apply_runtime_probe_runner_for_diagnostic_and_recompile"
        not in runtime_observation_recompile.__all__
    )
    assert (
        "RuntimeProbeRunnerCallableRecompileApplication"
        not in runtime_observation_recompile.__all__
    )
    assert (
        "apply_runtime_probe_runner_for_diagnostic_and_recompile"
        not in context_ir.__all__
    )
    assert "RuntimeProbeRunnerCallableRecompileApplication" not in context_ir.__all__
    assert not hasattr(
        context_ir,
        "apply_runtime_probe_runner_for_diagnostic_and_recompile",
    )
    assert not hasattr(
        context_ir,
        "RuntimeProbeRunnerCallableRecompileApplication",
    )
    helper_name = (
        "apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile"
    )
    assert helper_name not in runtime_observation_recompile.__all__
    assert helper_name not in context_ir.__all__
    assert not hasattr(context_ir, helper_name)
    helper_name = "apply_default_local_python_subprocess_for_diagnostic_and_recompile"
    assert helper_name not in runtime_observation_recompile.__all__
    assert helper_name not in context_ir.__all__
    assert not hasattr(context_ir, helper_name)


def test_runtime_observation_recompile_empty_observations_recompile_original_program(
    tmp_path: Path,
) -> None:
    """Empty observations preserve existing empty application behavior."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        _plan,
        _request,
        _observation,
        unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)

    result = apply_runtime_observations_for_diagnostic_and_recompile(
        program,
        diagnostic,
        (),
        previous_result,
        miss_evidence,
        delta_budget=96,
    )
    expected_recompile = recompile_semantic_context(
        previous_result,
        miss_evidence,
        delta_budget=96,
        program=program,
    )
    boundary = _boundary_for(result.recompile_result.diagnostic, unsupported_id)

    assert result.observation_application.diagnostic is diagnostic
    assert result.observation_application.admissions == ()
    assert result.observation_application.updated_program is program
    assert result.recompile_result.diagnostic == expected_recompile.diagnostic
    assert result.recompile_result.newly_selected_unit_ids == (
        expected_recompile.newly_selected_unit_ids
    )
    assert boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
    )
    assert result.recompile_result.diagnostic.planned_runtime_probe_requests == (
        diagnostic.planned_runtime_probe_requests
    )
    assert program.provenance_records == []


def test_runtime_observation_recompile_forwards_embed_fn(tmp_path: Path) -> None:
    """The composition helper forwards optional embeddings to recompile scoring."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        _plan,
        _request,
        _observation,
        _unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)
    embedded_batches: list[tuple[str, ...]] = []

    def embed_fn(texts: list[str]) -> list[list[float]]:
        embedded_batches.append(tuple(texts))
        return [[1.0, 0.0] for _text in texts]

    apply_runtime_observations_for_diagnostic_and_recompile(
        program,
        diagnostic,
        (),
        previous_result,
        miss_evidence,
        delta_budget=96,
        embed_fn=embed_fn,
    )

    assert embedded_batches
    assert embedded_batches[0][0] == "dynamic import"


def test_runtime_observation_recompile_propagates_application_gates(
    tmp_path: Path,
) -> None:
    """Invalid observations fail through existing application gates."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        _plan,
        request,
        observation,
        _unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)

    missing_plan = replace(diagnostic, planned_runtime_probe_request_plan=None)
    with pytest.raises(ValueError, match="planned_runtime_probe_request_plan"):
        apply_runtime_observations_for_diagnostic_and_recompile(
            program,
            missing_plan,
            (observation,),
            previous_result,
            miss_evidence,
            delta_budget=96,
        )

    with pytest.raises(ValueError, match="not present in request plan"):
        apply_runtime_observations_for_diagnostic_and_recompile(
            program,
            diagnostic,
            (_dynamic_import_runtime_observation(_unplanned_site()),),
            previous_result,
            miss_evidence,
            delta_budget=96,
        )

    with pytest.raises(ValueError, match="share the same source site"):
        apply_runtime_observations_for_diagnostic_and_recompile(
            program,
            diagnostic,
            (
                observation,
                _exec_runtime_observation(request.source_site),
            ),
            previous_result,
            miss_evidence,
            delta_budget=96,
        )

    with pytest.raises(ValueError, match="does not match planned request family/form"):
        apply_runtime_observations_for_diagnostic_and_recompile(
            program,
            diagnostic,
            (_exec_runtime_observation(request.source_site),),
            previous_result,
            miss_evidence,
            delta_budget=96,
        )


def test_runtime_observation_recompile_propagates_recompile_gates(
    tmp_path: Path,
) -> None:
    """Recompile preconditions still fail through the composed helper."""
    (
        program,
        previous_result,
        miss_evidence,
        diagnostic,
        _plan,
        _request,
        observation,
        _unsupported_id,
    ) = _runtime_recompile_fixture(tmp_path)

    with pytest.raises(ValueError, match="delta_budget must be >= 0"):
        apply_runtime_observations_for_diagnostic_and_recompile(
            program,
            diagnostic,
            (observation,),
            previous_result,
            miss_evidence,
            delta_budget=-1,
        )

    previous_without_context = replace(previous_result, compile_context=None)
    with pytest.raises(ValueError, match="compile_context"):
        apply_runtime_observations_for_diagnostic_and_recompile(
            program,
            diagnostic,
            (),
            previous_without_context,
            miss_evidence,
            delta_budget=96,
        )

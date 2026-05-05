"""Tests for runtime observation application composed with semantic recompile."""

from __future__ import annotations

import textwrap
from dataclasses import replace
from pathlib import Path

import pytest

import context_ir.runtime_acquisition as runtime_acquisition
import context_ir.runtime_probe_requests as runtime_probe_requests
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.runtime_observation_recompile import (
    RuntimeObservationRecompileApplication,
    apply_runtime_observations_for_diagnostic_and_recompile,
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
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="execution_outcome",
                value="completed",
            ),
        ),
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

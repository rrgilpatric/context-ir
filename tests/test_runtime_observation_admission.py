"""Tests for runtime observation admission against planned probe requests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

import context_ir.runtime_acquisition as runtime_acquisition
import context_ir.runtime_observation_admission as runtime_observation_admission
import context_ir.runtime_probe_requests as runtime_probe_requests
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_types import (
    CapabilityTier,
    RepositorySnapshotBasis,
    RuntimeAttachmentLink,
    SemanticDiagnosticBoundary,
    SemanticDiagnosticBoundaryKind,
    SemanticDiagnosticResult,
    SemanticDiagnosticUnitStatus,
    SemanticProgram,
    SourceSite,
    SourceSpan,
)


def _derived_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted semantic pipeline through frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _runtime_plan(
    tmp_path: Path,
) -> tuple[SemanticProgram, runtime_probe_requests.RuntimeProbeRequestPlan]:
    """Build a small runtime probe request plan with three planned requests."""
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
    program = _derived_program(tmp_path)
    requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    plan = runtime_probe_requests.build_runtime_probe_request_plan(requests)

    assert [request.boundary_text for request in plan.requests] == [
        "importlib.import_module(name)",
        "getattr(obj, name)",
        "exec(source)",
    ]
    return program, plan


def _diagnostic_for_plan(
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
) -> SemanticDiagnosticResult:
    """Build a diagnostic whose attached plan is the runtime admission boundary."""
    subject_ids = tuple(request.subject_id for request in plan.requests)
    boundaries = tuple(
        SemanticDiagnosticBoundary(
            unit_id=subject_id,
            status=SemanticDiagnosticUnitStatus.OMITTED,
            boundary_kind=(
                SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
            ),
            primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            has_attached_runtime_provenance=False,
        )
        for subject_id in subject_ids
    )
    return SemanticDiagnosticResult(
        grounded_unit_ids=subject_ids,
        omitted_unit_ids=subject_ids,
        too_shallow_unit_ids=(),
        sufficiently_represented_unit_ids=(),
        recommended_expansions=(),
        reason="Test diagnostic with an attached runtime request plan.",
        boundary_classifications=boundaries,
        planned_runtime_probe_requests=plan.requests,
        planned_runtime_probe_request_plan=plan,
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


def _dynamic_import_observation(
    site: SourceSite,
) -> runtime_acquisition.DynamicImportRuntimeObservation:
    """Create one typed dynamic-import runtime observation."""
    return runtime_acquisition.DynamicImportRuntimeObservation(
        site=site,
        probe_identifier="probe:dynamic-import",
        probe_contract_revision="2026-05-04.1",
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


def _getattr_observation(
    site: SourceSite,
) -> runtime_acquisition.GetattrRuntimeObservation:
    """Create one typed getattr runtime observation."""
    return runtime_acquisition.GetattrRuntimeObservation(
        site=site,
        probe_identifier="probe:getattr",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:getattr",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value="returned_value",
            ),
        ),
    )


def _exec_observation(site: SourceSite) -> runtime_acquisition.ExecRuntimeObservation:
    """Create one typed exec runtime observation."""
    return runtime_acquisition.ExecRuntimeObservation(
        site=site,
        probe_identifier="probe:exec",
        probe_contract_revision="2026-05-04.1",
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
    """Return a source site that is not present in the test request plan."""
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


def test_full_plan_with_matching_observations_returns_admissions_in_plan_order(
    tmp_path: Path,
) -> None:
    """Matching observations are admitted deterministically by request-plan order."""
    _program, plan = _runtime_plan(tmp_path)
    exec_observation = _exec_observation(plan.requests[2].source_site)
    dynamic_observation = _dynamic_import_observation(plan.requests[0].source_site)
    getattr_observation = _getattr_observation(plan.requests[1].source_site)

    admissions = runtime_observation_admission.admit_runtime_observations_for_plan(
        plan,
        (exec_observation, dynamic_observation, getattr_observation),
    )

    assert [admission.request.boundary_text for admission in admissions] == [
        "importlib.import_module(name)",
        "getattr(obj, name)",
        "exec(source)",
    ]
    assert [admission.request_id for admission in admissions] == list(plan.request_ids)
    assert [admission.plan_id for admission in admissions] == [plan.plan_id] * 3
    assert admissions[0].request is plan.requests[0]
    assert admissions[1].request is plan.requests[1]
    assert admissions[2].request is plan.requests[2]
    assert admissions[0].observation is dynamic_observation
    assert admissions[1].observation is getattr_observation
    assert admissions[2].observation is exec_observation


def test_diagnostic_helper_preserves_plan_order_and_admission_ids(
    tmp_path: Path,
) -> None:
    """Diagnostic admission delegates to the attached plan in deterministic order."""
    _program, plan = _runtime_plan(tmp_path)
    diagnostic = _diagnostic_for_plan(plan)
    exec_observation = _exec_observation(plan.requests[2].source_site)
    dynamic_observation = _dynamic_import_observation(plan.requests[0].source_site)
    getattr_observation = _getattr_observation(plan.requests[1].source_site)

    admissions = (
        runtime_observation_admission.admit_runtime_observations_for_diagnostic(
            diagnostic,
            (exec_observation, dynamic_observation, getattr_observation),
        )
    )

    assert [admission.request.boundary_text for admission in admissions] == [
        "importlib.import_module(name)",
        "getattr(obj, name)",
        "exec(source)",
    ]
    assert [admission.request_id for admission in admissions] == list(plan.request_ids)
    assert [admission.plan_id for admission in admissions] == [plan.plan_id] * 3
    assert admissions[0].request is plan.requests[0]
    assert admissions[1].request is plan.requests[1]
    assert admissions[2].request is plan.requests[2]
    assert admissions[0].observation is dynamic_observation
    assert admissions[1].observation is getattr_observation
    assert admissions[2].observation is exec_observation


def test_partial_observations_do_not_require_every_planned_request(
    tmp_path: Path,
) -> None:
    """Planned requests without matching observations are skipped, not rejected."""
    _program, plan = _runtime_plan(tmp_path)
    dynamic_observation = _dynamic_import_observation(plan.requests[0].source_site)
    exec_observation = _exec_observation(plan.requests[2].source_site)

    admissions = runtime_observation_admission.admit_runtime_observations_for_plan(
        plan,
        (exec_observation, dynamic_observation),
    )

    assert [admission.request.boundary_text for admission in admissions] == [
        "importlib.import_module(name)",
        "exec(source)",
    ]
    assert admissions[0].observation is dynamic_observation
    assert admissions[1].observation is exec_observation


def test_empty_plan_and_empty_observations_return_empty_admissions() -> None:
    """Empty request plans preserve the empty admission contract."""
    plan = runtime_probe_requests.build_runtime_probe_request_plan(())

    admissions = runtime_observation_admission.admit_runtime_observations_for_plan(
        plan,
        (),
    )

    assert admissions == ()
    assert plan.requests == ()
    assert plan.request_ids == ()


def test_empty_diagnostic_plan_returns_empty_admissions() -> None:
    """Diagnostic admission preserves the plan-level empty admission contract."""
    plan = runtime_probe_requests.build_runtime_probe_request_plan(())
    diagnostic = _diagnostic_for_plan(plan)

    admissions = (
        runtime_observation_admission.admit_runtime_observations_for_diagnostic(
            diagnostic,
            (),
        )
    )

    assert admissions == ()
    assert plan.requests == ()
    assert plan.request_ids == ()


def test_diagnostic_helper_requires_attached_runtime_probe_request_plan() -> None:
    """Diagnostic admission rejects diagnostics without an attached plan."""
    diagnostic = SemanticDiagnosticResult(
        grounded_unit_ids=(),
        omitted_unit_ids=(),
        too_shallow_unit_ids=(),
        sufficiently_represented_unit_ids=(),
        recommended_expansions=(),
        reason="No attached runtime plan.",
    )

    with pytest.raises(ValueError, match="planned_runtime_probe_request_plan"):
        runtime_observation_admission.admit_runtime_observations_for_diagnostic(
            diagnostic,
            (),
        )


def test_unmatched_observation_source_site_raises_value_error(
    tmp_path: Path,
) -> None:
    """Observations outside the request plan are rejected before admission."""
    _program, plan = _runtime_plan(tmp_path)
    observation = _dynamic_import_observation(_unplanned_site())

    with pytest.raises(ValueError, match="not present in request plan"):
        runtime_observation_admission.admit_runtime_observations_for_plan(
            plan,
            (observation,),
        )


def test_diagnostic_helper_unmatched_observation_raises_through_plan_admission(
    tmp_path: Path,
) -> None:
    """Diagnostic admission reuses plan-level unmatched-observation rejection."""
    _program, plan = _runtime_plan(tmp_path)
    diagnostic = _diagnostic_for_plan(plan)
    observation = _dynamic_import_observation(_unplanned_site())

    with pytest.raises(ValueError, match="not present in request plan"):
        runtime_observation_admission.admit_runtime_observations_for_diagnostic(
            diagnostic,
            (observation,),
        )


def test_duplicate_observation_source_sites_raise_value_error(
    tmp_path: Path,
) -> None:
    """Duplicate observation source sites are ambiguous and rejected."""
    _program, plan = _runtime_plan(tmp_path)
    first_observation = _dynamic_import_observation(plan.requests[0].source_site)
    second_observation = _getattr_observation(plan.requests[0].source_site)

    with pytest.raises(ValueError, match="share the same source site"):
        runtime_observation_admission.admit_runtime_observations_for_plan(
            plan,
            (first_observation, second_observation),
        )


def test_diagnostic_helper_duplicate_observations_raise_through_plan_admission(
    tmp_path: Path,
) -> None:
    """Diagnostic admission reuses plan-level duplicate-observation rejection."""
    _program, plan = _runtime_plan(tmp_path)
    diagnostic = _diagnostic_for_plan(plan)
    first_observation = _dynamic_import_observation(plan.requests[0].source_site)
    second_observation = _getattr_observation(plan.requests[0].source_site)

    with pytest.raises(ValueError, match="share the same source site"):
        runtime_observation_admission.admit_runtime_observations_for_diagnostic(
            diagnostic,
            (first_observation, second_observation),
        )


def test_request_and_observation_object_identity_is_preserved(
    tmp_path: Path,
) -> None:
    """Admissions retain the original request and observation objects."""
    _program, plan = _runtime_plan(tmp_path)
    observation = _getattr_observation(plan.requests[1].source_site)

    admissions = runtime_observation_admission.admit_runtime_observations_for_plan(
        plan,
        (observation,),
    )

    assert len(admissions) == 1
    [admission] = admissions
    assert admission.request is plan.requests[1]
    assert admission.observation is observation
    assert admission.request_id == plan.request_ids[1]
    assert admission.plan_id == plan.plan_id


def test_admission_does_not_mutate_program_plan_or_requests(
    tmp_path: Path,
) -> None:
    """Admission is a read model and leaves semantic/request inputs unchanged."""
    program, plan = _runtime_plan(tmp_path)
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)
    original_requests = plan.requests
    original_request_ids = plan.request_ids
    original_plan_id = plan.plan_id
    original_request_statuses = tuple(request.status for request in plan.requests)
    observation = _dynamic_import_observation(plan.requests[0].source_site)

    admissions = runtime_observation_admission.admit_runtime_observations_for_plan(
        plan,
        (observation,),
    )

    assert len(admissions) == 1
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records
    assert program.provenance_records == []
    assert plan.requests == original_requests
    assert plan.request_ids == original_request_ids
    assert plan.plan_id == original_plan_id
    assert (
        tuple(request.status for request in plan.requests) == original_request_statuses
    )
    assert all(
        request.status
        is runtime_probe_requests.RuntimeProbeRequestStatus.PLANNED_NOT_EXECUTED
        for request in plan.requests
    )
    assert (
        tuple(request.request_id for request in plan.requests) == original_request_ids
    )


def test_diagnostic_helper_does_not_mutate_inputs(tmp_path: Path) -> None:
    """Diagnostic admission is a read model over diagnostics, plans, and inputs."""
    _program, plan = _runtime_plan(tmp_path)
    diagnostic = _diagnostic_for_plan(plan)
    observation = _dynamic_import_observation(plan.requests[0].source_site)
    original_diagnostic_state = (
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
    original_plan_state = (
        plan.requests,
        plan.request_ids,
        plan.plan_id,
        tuple(request.request_id for request in plan.requests),
        tuple(request.status for request in plan.requests),
    )
    original_request_state = tuple(
        (
            request.request_id,
            request.subject_id,
            request.source_site,
            request.boundary_text,
            request.status,
        )
        for request in plan.requests
    )
    original_observation_state = (
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

    admissions = (
        runtime_observation_admission.admit_runtime_observations_for_diagnostic(
            diagnostic,
            (observation,),
        )
    )

    assert len(admissions) == 1
    assert (
        diagnostic.grounded_unit_ids,
        diagnostic.omitted_unit_ids,
        diagnostic.too_shallow_unit_ids,
        diagnostic.sufficiently_represented_unit_ids,
        diagnostic.recommended_expansions,
        diagnostic.reason,
        diagnostic.boundary_classifications,
        diagnostic.planned_runtime_probe_requests,
        diagnostic.planned_runtime_probe_request_plan,
    ) == original_diagnostic_state
    assert (
        plan.requests,
        plan.request_ids,
        plan.plan_id,
        tuple(request.request_id for request in plan.requests),
        tuple(request.status for request in plan.requests),
    ) == original_plan_state
    assert (
        tuple(
            (
                request.request_id,
                request.subject_id,
                request.source_site,
                request.boundary_text,
                request.status,
            )
            for request in plan.requests
        )
        == original_request_state
    )
    assert (
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
    ) == original_observation_state
    assert admissions[0].request is plan.requests[0]
    assert admissions[0].observation is observation


def test_diagnostic_helper_has_no_request_or_plan_id_drift(
    tmp_path: Path,
) -> None:
    """Diagnostic admission reports the plan's existing IDs without recomputing."""
    _program, plan = _runtime_plan(tmp_path)
    diagnostic = _diagnostic_for_plan(plan)
    observations = (
        _dynamic_import_observation(plan.requests[0].source_site),
        _getattr_observation(plan.requests[1].source_site),
        _exec_observation(plan.requests[2].source_site),
    )
    original_plan_id = plan.plan_id
    original_request_ids = plan.request_ids

    admissions = (
        runtime_observation_admission.admit_runtime_observations_for_diagnostic(
            diagnostic,
            observations,
        )
    )

    assert diagnostic.planned_runtime_probe_request_plan is plan
    assert plan.plan_id == original_plan_id
    assert plan.request_ids == original_request_ids
    assert plan.request_ids == tuple(request.request_id for request in plan.requests)
    assert tuple(admission.plan_id for admission in admissions) == (
        original_plan_id,
    ) * len(admissions)
    assert tuple(admission.request_id for admission in admissions) == (
        original_request_ids
    )

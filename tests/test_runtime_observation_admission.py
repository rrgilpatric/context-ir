"""Tests for runtime observation admission against planned probe requests."""

from __future__ import annotations

import hashlib
import textwrap
from dataclasses import replace
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
    SemanticSubjectKind,
    SourceSite,
    SourceSpan,
    UnresolvedReasonCode,
)

_RUNTIME_OBSERVATION_COMPATIBILITY_CASES = (
    (
        runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        "dynamic_import:any_supported_form/9",
        runtime_acquisition.DynamicImportRuntimeObservation,
        runtime_acquisition.ExecRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        "reflective_builtin:hasattr/2",
        runtime_acquisition.HasattrRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        "reflective_builtin:getattr/2",
        runtime_acquisition.GetattrRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        "reflective_builtin:getattr/3",
        runtime_acquisition.GetattrRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        "reflective_builtin:vars/0",
        runtime_acquisition.VarsRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        "reflective_builtin:vars/1",
        runtime_acquisition.VarsRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        "reflective_builtin:dir/0",
        runtime_acquisition.DirRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        "reflective_builtin:dir/1",
        runtime_acquisition.DirRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        "runtime_mutation:globals/0",
        runtime_acquisition.GlobalsRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        "runtime_mutation:locals/0",
        runtime_acquisition.LocalsRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        "runtime_mutation:setattr/3",
        runtime_acquisition.SetattrRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        "runtime_mutation:delattr/2",
        runtime_acquisition.DelattrRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL,
        "exec_or_eval:exec/1",
        runtime_acquisition.ExecRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL,
        "exec_or_eval:eval/1",
        runtime_acquisition.EvalRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.METACLASS_BEHAVIOR,
        "metaclass_behavior:keyword",
        runtime_acquisition.MetaclassBehaviorRuntimeObservation,
        runtime_acquisition.DynamicImportRuntimeObservation,
    ),
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


def _all_family_runtime_plan(
    tmp_path: Path,
) -> tuple[SemanticProgram, runtime_probe_requests.RuntimeProbeRequestPlan]:
    """Build a runtime probe request plan covering every current observation type."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            class Meta(type):
                pass

            class Example(metaclass=Meta):
                pass

            def run(
                obj: object,
                name: str,
                source: str,
                value: object,
            ) -> None:
                importlib.import_module(name)
                hasattr(obj, name)
                getattr(obj, name)
                vars(obj)
                dir(obj)
                globals()
                locals()
                setattr(obj, name, value)
                delattr(obj, name)
                eval(source)
                exec(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    plan = runtime_probe_requests.build_runtime_probe_request_plan(requests)

    assert {request.form_label for request in plan.requests} == {
        "dynamic_import:importlib.import_module/1",
        "reflective_builtin:hasattr/2",
        "reflective_builtin:getattr/2",
        "reflective_builtin:vars/1",
        "reflective_builtin:dir/1",
        "runtime_mutation:globals/0",
        "runtime_mutation:locals/0",
        "runtime_mutation:setattr/3",
        "runtime_mutation:delattr/2",
        "exec_or_eval:eval/1",
        "exec_or_eval:exec/1",
        "metaclass_behavior:keyword",
    }
    return program, plan


def _runtime_plan_admissions(
    tmp_path: Path,
) -> tuple[
    SemanticProgram,
    runtime_probe_requests.RuntimeProbeRequestPlan,
    tuple[runtime_observation_admission.RuntimeObservationAdmission, ...],
]:
    """Build a small valid admission batch for attachment validation tests."""
    program, plan = _runtime_plan(tmp_path)
    observations = (
        _dynamic_import_observation(plan.requests[0].source_site),
        _getattr_observation(plan.requests[1].source_site),
        _exec_observation(plan.requests[2].source_site),
    )
    admissions = runtime_observation_admission.admit_runtime_observations_for_plan(
        plan,
        observations,
    )
    return program, plan, admissions


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


def _eval_observation(site: SourceSite) -> runtime_acquisition.EvalRuntimeObservation:
    """Create one typed eval runtime observation."""
    return runtime_acquisition.EvalRuntimeObservation(
        site=site,
        probe_identifier="probe:eval",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:eval",
        replay_inputs=(
            runtime_acquisition._RuntimeObservationField(
                key="source_shape",
                value="literal_expression",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="source_sha256",
                value=hashlib.sha256(b'"runtime-value"').hexdigest(),
            ),
        ),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="evaluation_outcome",
                value="returned_value",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="result_type",
                value="builtins.str",
            ),
        ),
        durable_payload_reference=f"artifact://eval-result/{site.site_id}.json",
    )


def _hasattr_observation(
    site: SourceSite,
) -> runtime_acquisition.HasattrRuntimeObservation:
    """Create one typed hasattr runtime observation."""
    return runtime_acquisition.HasattrRuntimeObservation(
        site=site,
        probe_identifier="probe:hasattr",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:hasattr",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="attribute_present",
                value="true",
            ),
        ),
    )


def _vars_observation(site: SourceSite) -> runtime_acquisition.VarsRuntimeObservation:
    """Create one typed vars runtime observation."""
    return runtime_acquisition.VarsRuntimeObservation(
        site=site,
        probe_identifier="probe:vars",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:vars",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value="returned_namespace",
            ),
        ),
    )


def _dir_observation(site: SourceSite) -> runtime_acquisition.DirRuntimeObservation:
    """Create one typed dir runtime observation."""
    return runtime_acquisition.DirRuntimeObservation(
        site=site,
        probe_identifier="probe:dir",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:dir",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="listing_entry_count",
                value="3",
            ),
        ),
        durable_payload_reference=f"artifact://dir-listing/{site.site_id}.json",
    )


def _globals_observation(
    site: SourceSite,
) -> runtime_acquisition.GlobalsRuntimeObservation:
    """Create one typed globals runtime observation."""
    return runtime_acquisition.GlobalsRuntimeObservation(
        site=site,
        probe_identifier="probe:globals",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:globals",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value="returned_namespace",
            ),
        ),
    )


def _locals_observation(
    site: SourceSite,
) -> runtime_acquisition.LocalsRuntimeObservation:
    """Create one typed locals runtime observation."""
    return runtime_acquisition.LocalsRuntimeObservation(
        site=site,
        probe_identifier="probe:locals",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:locals",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value="returned_namespace",
            ),
        ),
    )


def _setattr_observation(
    site: SourceSite,
) -> runtime_acquisition.SetattrRuntimeObservation:
    """Create one typed setattr runtime observation."""
    return runtime_acquisition.SetattrRuntimeObservation(
        site=site,
        probe_identifier="probe:setattr",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:setattr",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="mutation_outcome",
                value="returned_none",
            ),
        ),
        durable_payload_reference=f"artifact://passed-value/{site.site_id}.json",
    )


def _delattr_observation(
    site: SourceSite,
) -> runtime_acquisition.DelattrRuntimeObservation:
    """Create one typed delattr runtime observation."""
    return runtime_acquisition.DelattrRuntimeObservation(
        site=site,
        probe_identifier="probe:delattr",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector="call:main.run:delattr",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="mutation_outcome",
                value="deleted_attribute",
            ),
        ),
    )


def _metaclass_observation(
    site: SourceSite,
) -> runtime_acquisition.MetaclassBehaviorRuntimeObservation:
    """Create one typed metaclass runtime observation."""
    return runtime_acquisition.MetaclassBehaviorRuntimeObservation(
        site=site,
        probe_identifier="probe:metaclass",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.Example",
        replay_selector="class:main.Example:metaclass",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="class_creation_outcome",
                value="created_class",
            ),
        ),
        durable_payload_reference=(
            f"artifact://metaclass-selection/{site.site_id}.json"
        ),
    )


def _runtime_observation_for_class(
    site: SourceSite,
    observation_class: type[runtime_observation_admission.RuntimeObservation],
    probe_name: str,
) -> runtime_observation_admission.RuntimeObservation:
    """Create one typed runtime observation for compatibility-matrix tests."""
    return observation_class(
        site=site,
        probe_identifier=f"probe:{probe_name}",
        probe_contract_revision="2026-05-04.1",
        repository_snapshot_basis=_snapshot_basis(),
        attachment_links=_attachment_links(site),
        replay_target="main.run",
        replay_selector=f"call:main.run:{probe_name}",
    )


def _attachable_observation_for_request(
    request: runtime_probe_requests.RuntimeProbeRequest,
) -> runtime_observation_admission.RuntimeObservation:
    """Create one attachable observation matching a planned request."""
    site = request.source_site
    form_label = request.form_label
    if request.family_label is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT:
        return _dynamic_import_observation(site)
    if form_label == "reflective_builtin:hasattr/2":
        return _hasattr_observation(site)
    if form_label in {
        "reflective_builtin:getattr/2",
        "reflective_builtin:getattr/3",
    }:
        return _getattr_observation(site)
    if form_label in {
        "reflective_builtin:vars/0",
        "reflective_builtin:vars/1",
    }:
        return _vars_observation(site)
    if form_label in {
        "reflective_builtin:dir/0",
        "reflective_builtin:dir/1",
    }:
        return _dir_observation(site)
    if form_label == "runtime_mutation:globals/0":
        return _globals_observation(site)
    if form_label == "runtime_mutation:locals/0":
        return _locals_observation(site)
    if form_label == "runtime_mutation:setattr/3":
        return _setattr_observation(site)
    if form_label == "runtime_mutation:delattr/2":
        return _delattr_observation(site)
    if form_label == "exec_or_eval:eval/1":
        return _eval_observation(site)
    if form_label == "exec_or_eval:exec/1":
        return _exec_observation(site)
    if form_label == "metaclass_behavior:keyword":
        return _metaclass_observation(site)
    raise ValueError(f"unsupported attachable request form: {form_label}")


def _source_site_for_form(form_label: str) -> SourceSite:
    """Return a stable synthetic source site for one planned request form."""
    site_fragment = form_label.replace(":", "_").replace("/", "_")
    return SourceSite(
        site_id=f"site:{site_fragment}",
        file_path="main.py",
        span=SourceSpan(
            start_line=1,
            start_column=0,
            end_line=1,
            end_column=len(form_label),
        ),
        snippet=form_label,
    )


def _reason_code_for_family(
    family_label: runtime_probe_requests.RuntimeProbeFamily,
) -> UnresolvedReasonCode:
    """Return the unresolved reason code that corresponds to a request family."""
    if family_label is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT:
        return UnresolvedReasonCode.DYNAMIC_IMPORT
    if family_label is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        return UnresolvedReasonCode.REFLECTIVE_BUILTIN
    if family_label is runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION:
        return UnresolvedReasonCode.RUNTIME_MUTATION
    if family_label is runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL:
        return UnresolvedReasonCode.EXEC_OR_EVAL
    if family_label is runtime_probe_requests.RuntimeProbeFamily.METACLASS_BEHAVIOR:
        return UnresolvedReasonCode.METACLASS_BEHAVIOR
    raise ValueError(f"unsupported runtime probe family: {family_label.value}")


def _planned_request_for_form(
    *,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
    source_site: SourceSite,
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Build one planned request for compatibility-matrix tests."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:{source_site.site_id}",
        source_site=source_site,
        reason_code=_reason_code_for_family(family_label),
        boundary_text=form_label,
        family_label=family_label,
        form_label=form_label,
        replay_target_seed="main.run",
        replay_selector_seed=f"call:main.run:{form_label}",
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


@pytest.mark.parametrize(
    ("family_label", "form_label", "observation_class", "_wrong_observation_class"),
    _RUNTIME_OBSERVATION_COMPATIBILITY_CASES,
)
def test_matching_observation_type_is_admitted_for_each_request_family_form(
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
    observation_class: type[runtime_observation_admission.RuntimeObservation],
    _wrong_observation_class: type[runtime_observation_admission.RuntimeObservation],
) -> None:
    """Every currently mapped request family/form admits only its typed observation."""
    source_site = _source_site_for_form(form_label)
    request = _planned_request_for_form(
        family_label=family_label,
        form_label=form_label,
        source_site=source_site,
    )
    plan = runtime_probe_requests.build_runtime_probe_request_plan((request,))
    observation = _runtime_observation_for_class(
        source_site,
        observation_class,
        form_label,
    )

    admissions = runtime_observation_admission.admit_runtime_observations_for_plan(
        plan,
        (observation,),
    )

    assert len(admissions) == 1
    [admission] = admissions
    assert admission.request is request
    assert admission.observation is observation
    assert admission.request_id == request.request_id
    assert admission.plan_id == plan.plan_id


@pytest.mark.parametrize(
    ("family_label", "form_label", "_observation_class", "wrong_observation_class"),
    _RUNTIME_OBSERVATION_COMPATIBILITY_CASES,
)
def test_mismatched_observation_type_is_rejected_for_request_family_form(
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
    _observation_class: type[runtime_observation_admission.RuntimeObservation],
    wrong_observation_class: type[runtime_observation_admission.RuntimeObservation],
) -> None:
    """A source-site match is not enough when the observation type is wrong."""
    source_site = _source_site_for_form(form_label)
    request = _planned_request_for_form(
        family_label=family_label,
        form_label=form_label,
        source_site=source_site,
    )
    plan = runtime_probe_requests.build_runtime_probe_request_plan((request,))
    observation = _runtime_observation_for_class(
        source_site,
        wrong_observation_class,
        "wrong-type",
    )

    with pytest.raises(ValueError, match="does not match planned request family/form"):
        runtime_observation_admission.admit_runtime_observations_for_plan(
            plan,
            (observation,),
        )


def test_unmapped_request_form_rejects_observation_even_when_family_matches() -> None:
    """Unknown planned forms are not admitted through family-level fallback."""
    source_site = _source_site_for_form("reflective_builtin:getattr/1")
    request = _planned_request_for_form(
        family_label=runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:getattr/1",
        source_site=source_site,
    )
    plan = runtime_probe_requests.build_runtime_probe_request_plan((request,))
    observation = _runtime_observation_for_class(
        source_site,
        runtime_acquisition.GetattrRuntimeObservation,
        "getattr",
    )

    with pytest.raises(ValueError, match="does not match planned request family/form"):
        runtime_observation_admission.admit_runtime_observations_for_plan(
            plan,
            (observation,),
        )


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


def test_attach_admitted_runtime_observations_empty_batch_returns_input_program(
    tmp_path: Path,
) -> None:
    """Empty admitted batches leave the semantic program object unchanged."""
    program, _plan = _runtime_plan(tmp_path)

    updated_program = (
        runtime_observation_admission.attach_admitted_runtime_observations(
            program,
            (),
        )
    )

    assert updated_program is program
    assert program.provenance_records == []


def test_attach_admitted_runtime_observations_routes_all_current_families(
    tmp_path: Path,
) -> None:
    """Already-admitted observations attach through all existing family helpers."""
    program, plan = _all_family_runtime_plan(tmp_path)
    observations = tuple(
        _attachable_observation_for_request(request) for request in plan.requests
    )
    admissions = runtime_observation_admission.admit_runtime_observations_for_plan(
        plan,
        reversed(observations),
    )
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)
    original_admission_state = tuple(
        (
            admission.plan_id,
            admission.request_id,
            admission.request,
            admission.observation,
        )
        for admission in admissions
    )
    original_request_state = tuple(
        (
            admission.request.request_id,
            admission.request.source_site,
            admission.request.form_label,
            admission.request.status,
        )
        for admission in admissions
    )
    original_observation_state = tuple(
        (
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
        for observation in observations
    )

    updated_program = (
        runtime_observation_admission.attach_admitted_runtime_observations(
            program,
            reversed(admissions),
        )
    )

    assert updated_program is not program
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records
    assert program.provenance_records == []
    assert len(updated_program.provenance_records) == len(admissions)
    assert {record.subject_id for record in updated_program.provenance_records} == {
        admission.request.subject_id for admission in admissions
    }
    assert all(
        record.capability_tier is CapabilityTier.RUNTIME_BACKED
        for record in updated_program.provenance_records
    )
    assert (
        tuple(
            (
                admission.plan_id,
                admission.request_id,
                admission.request,
                admission.observation,
            )
            for admission in admissions
        )
        == original_admission_state
    )
    assert (
        tuple(
            (
                admission.request.request_id,
                admission.request.source_site,
                admission.request.form_label,
                admission.request.status,
            )
            for admission in admissions
        )
        == original_request_state
    )
    assert (
        tuple(
            (
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
            for observation in observations
        )
        == original_observation_state
    )


def test_attach_admitted_runtime_observations_rejects_multiple_plan_ids(
    tmp_path: Path,
) -> None:
    """Non-empty attachment batches must describe one admitted request plan."""
    program, _plan, admissions = _runtime_plan_admissions(tmp_path)
    drifted_admission = replace(admissions[1], plan_id="runtime_probe_plan:other")

    with pytest.raises(ValueError, match="exactly one plan_id"):
        runtime_observation_admission.attach_admitted_runtime_observations(
            program,
            (admissions[0], drifted_admission),
        )


def test_attach_admitted_runtime_observations_rejects_request_id_drift(
    tmp_path: Path,
) -> None:
    """Attachment revalidates that each admission still matches its request ID."""
    program, _plan, admissions = _runtime_plan_admissions(tmp_path)
    drifted_admission = replace(admissions[0], request_id="runtime_probe:drifted")

    with pytest.raises(ValueError, match="request_id must match"):
        runtime_observation_admission.attach_admitted_runtime_observations(
            program,
            (drifted_admission,),
        )


def test_attach_admitted_runtime_observations_rejects_source_site_drift(
    tmp_path: Path,
) -> None:
    """Attachment revalidates request and observation source-site identity."""
    program, _plan, admissions = _runtime_plan_admissions(tmp_path)
    drifted_admission = replace(
        admissions[0],
        observation=_dynamic_import_observation(_unplanned_site()),
    )

    with pytest.raises(ValueError, match="source site must match"):
        runtime_observation_admission.attach_admitted_runtime_observations(
            program,
            (drifted_admission,),
        )


def test_attach_admitted_runtime_observations_rejects_incompatible_observation(
    tmp_path: Path,
) -> None:
    """Attachment reuses the request/observation family-form compatibility guard."""
    program, _plan, admissions = _runtime_plan_admissions(tmp_path)
    drifted_admission = replace(
        admissions[0],
        observation=_exec_observation(admissions[0].request.source_site),
    )

    with pytest.raises(ValueError, match="does not match planned request family/form"):
        runtime_observation_admission.attach_admitted_runtime_observations(
            program,
            (drifted_admission,),
        )


def test_attach_admitted_runtime_observations_rejects_duplicate_request_ids(
    tmp_path: Path,
) -> None:
    """An admission batch cannot attach the same admitted request twice."""
    program, _plan, admissions = _runtime_plan_admissions(tmp_path)

    with pytest.raises(ValueError, match="duplicate.*request_id"):
        runtime_observation_admission.attach_admitted_runtime_observations(
            program,
            (admissions[0], admissions[0]),
        )


def test_attach_admitted_runtime_observations_rejects_duplicate_source_sites(
    tmp_path: Path,
) -> None:
    """Different admissions for the same source site are ambiguous."""
    program, _plan = _runtime_plan(tmp_path)
    source_site = _source_site_for_form("reflective_builtin:duplicate")
    first_request = _planned_request_for_form(
        family_label=runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:hasattr/2",
        source_site=source_site,
    )
    second_request = _planned_request_for_form(
        family_label=runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:getattr/2",
        source_site=source_site,
    )
    first_admission = runtime_observation_admission.RuntimeObservationAdmission(
        plan_id="runtime_probe_request_plan:test",
        request_id=first_request.request_id,
        request=first_request,
        observation=_hasattr_observation(source_site),
    )
    second_admission = runtime_observation_admission.RuntimeObservationAdmission(
        plan_id="runtime_probe_request_plan:test",
        request_id=second_request.request_id,
        request=second_request,
        observation=_getattr_observation(source_site),
    )

    with pytest.raises(ValueError, match="duplicate.*source site"):
        runtime_observation_admission.attach_admitted_runtime_observations(
            program,
            (first_admission, second_admission),
        )

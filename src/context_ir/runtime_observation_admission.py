"""Runtime observation admission for planned probe request boundaries."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeAlias, TypedDict, assert_never

import context_ir.runtime_acquisition as runtime_acquisition
from context_ir.runtime_probe_requests import (
    RuntimeProbeFamily,
    RuntimeProbeRequest,
    RuntimeProbeRequestPlan,
    index_runtime_probe_request_plan_by_source_site,
)
from context_ir.runtime_probe_results import (
    RuntimeProbeNonProofResult,
    RuntimeProbeObservedResult,
    RuntimeProbeReplayField,
    RuntimeProbeResult,
    RuntimeProbeResultBatch,
)
from context_ir.semantic_types import (
    RepositorySnapshotBasis,
    RuntimeAttachmentLink,
    SemanticDiagnosticResult,
    SemanticProgram,
    SourceSite,
)

_SourceSiteIdentity: TypeAlias = tuple[str, int, int, int, int]

_REFLECTIVE_GETATTR_FORMS = frozenset(
    {
        "reflective_builtin:getattr/2",
        "reflective_builtin:getattr/3",
    }
)
_REFLECTIVE_VARS_FORMS = frozenset(
    {
        "reflective_builtin:vars/0",
        "reflective_builtin:vars/1",
    }
)
_REFLECTIVE_DIR_FORMS = frozenset(
    {
        "reflective_builtin:dir/0",
        "reflective_builtin:dir/1",
    }
)

RuntimeObservation: TypeAlias = (
    runtime_acquisition.DynamicImportRuntimeObservation
    | runtime_acquisition.EvalRuntimeObservation
    | runtime_acquisition.ExecRuntimeObservation
    | runtime_acquisition.HasattrRuntimeObservation
    | runtime_acquisition.GetattrRuntimeObservation
    | runtime_acquisition.DirRuntimeObservation
    | runtime_acquisition.VarsRuntimeObservation
    | runtime_acquisition.GlobalsRuntimeObservation
    | runtime_acquisition.LocalsRuntimeObservation
    | runtime_acquisition.SetattrRuntimeObservation
    | runtime_acquisition.DelattrRuntimeObservation
    | runtime_acquisition.MetaclassBehaviorRuntimeObservation
)


@dataclass(frozen=True)
class RuntimeObservationAdmission:
    """Accepted pairing between a planned probe request and a runtime observation."""

    plan_id: str
    request_id: str
    request: RuntimeProbeRequest
    observation: RuntimeObservation


@dataclass(frozen=True)
class RuntimeProbeResultBatchAdmission:
    """Internal bridge result for one runtime probe result batch admission."""

    admissions: tuple[RuntimeObservationAdmission, ...]
    non_proof_results: tuple[RuntimeProbeNonProofResult, ...]


@dataclass(frozen=True)
class RuntimeObservationApplication:
    """Result of applying admitted runtime observations for one diagnostic."""

    diagnostic: SemanticDiagnosticResult
    admissions: tuple[RuntimeObservationAdmission, ...]
    updated_program: SemanticProgram


@dataclass(frozen=True)
class _RuntimeObservationFields:
    """Common typed observation fields copied from an observed probe result."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[runtime_acquisition._RuntimeObservationField, ...]
    runtime_assumptions: tuple[runtime_acquisition._RuntimeObservationField, ...]
    normalized_payload: tuple[runtime_acquisition._RuntimeObservationField, ...]
    durable_payload_reference: str | None


class _RuntimeObservationKwargs(TypedDict):
    """Keyword arguments shared by every typed runtime observation dataclass."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[runtime_acquisition._RuntimeObservationField, ...]
    runtime_assumptions: tuple[runtime_acquisition._RuntimeObservationField, ...]
    normalized_payload: tuple[runtime_acquisition._RuntimeObservationField, ...]
    durable_payload_reference: str | None


def admit_runtime_probe_result_batch_for_plan(
    plan: RuntimeProbeRequestPlan,
    batch: RuntimeProbeResultBatch,
) -> RuntimeProbeResultBatchAdmission:
    """Admit proof-bearing observed probe results and preserve non-proof results."""
    results_by_request_id = _index_runtime_probe_result_batch_for_plan(plan, batch)

    admissions: list[RuntimeObservationAdmission] = []
    non_proof_results: list[RuntimeProbeNonProofResult] = []
    for request, request_id in zip(plan.requests, plan.request_ids, strict=True):
        result = results_by_request_id.get(request_id)
        if result is None:
            continue
        if isinstance(result, RuntimeProbeObservedResult):
            observation = _runtime_observation_from_probe_observed_result(result)
            if not _runtime_observation_matches_request(request, observation):
                raise ValueError(
                    "runtime probe observed result does not match planned request "
                    f"family/form: {request.form_label}"
                )
            admissions.append(
                RuntimeObservationAdmission(
                    plan_id=plan.plan_id,
                    request_id=request_id,
                    request=request,
                    observation=observation,
                )
            )
            continue
        non_proof_results.append(result)

    return RuntimeProbeResultBatchAdmission(
        admissions=tuple(admissions),
        non_proof_results=tuple(non_proof_results),
    )


def admit_runtime_observations_for_plan(
    plan: RuntimeProbeRequestPlan,
    observations: Iterable[RuntimeObservation],
) -> tuple[RuntimeObservationAdmission, ...]:
    """Admit observations whose source sites are present in a planned request plan."""
    requests_by_source_site = index_runtime_probe_request_plan_by_source_site(plan)
    observations_by_source_site = _index_runtime_observations_by_source_site(
        observations
    )

    for source_site_identity in observations_by_source_site:
        if source_site_identity not in requests_by_source_site:
            raise ValueError(
                "runtime observation source site is not present in request plan"
            )

    admissions: list[RuntimeObservationAdmission] = []
    for request, request_id in zip(plan.requests, plan.request_ids, strict=True):
        source_site_identity = runtime_acquisition._source_site_identity(
            request.source_site
        )
        observation = observations_by_source_site.get(source_site_identity)
        if observation is None:
            continue
        if not _runtime_observation_matches_request(request, observation):
            raise ValueError(
                "runtime observation type does not match planned request "
                f"family/form: {request.form_label}"
            )
        admissions.append(
            RuntimeObservationAdmission(
                plan_id=plan.plan_id,
                request_id=request_id,
                request=request,
                observation=observation,
            )
        )
    return tuple(admissions)


def admit_runtime_observations_for_diagnostic(
    diagnostic: SemanticDiagnosticResult,
    observations: Iterable[RuntimeObservation],
) -> tuple[RuntimeObservationAdmission, ...]:
    """Admit observations against a diagnostic's attached runtime request plan."""
    plan = diagnostic.planned_runtime_probe_request_plan
    if plan is None:
        raise ValueError(
            "planned_runtime_probe_request_plan is required for runtime observation "
            "admission"
        )
    return admit_runtime_observations_for_plan(plan, observations)


def apply_runtime_observations_for_diagnostic(
    program: SemanticProgram,
    diagnostic: SemanticDiagnosticResult,
    observations: Iterable[RuntimeObservation],
) -> RuntimeObservationApplication:
    """Admit and attach runtime observations gated by a diagnostic request plan."""
    admissions = admit_runtime_observations_for_diagnostic(diagnostic, observations)
    updated_program = attach_admitted_runtime_observations(program, admissions)
    return RuntimeObservationApplication(
        diagnostic=diagnostic,
        admissions=admissions,
        updated_program=updated_program,
    )


def attach_admitted_runtime_observations(
    program: SemanticProgram,
    admissions: Iterable[RuntimeObservationAdmission],
) -> SemanticProgram:
    """Attach already-admitted observations through family-specific helpers."""
    ordered_admissions = tuple(admissions)
    if not ordered_admissions:
        return program

    _validate_runtime_observation_admissions(ordered_admissions)

    dynamic_import_observations: list[
        runtime_acquisition.DynamicImportRuntimeObservation
    ] = []
    eval_observations: list[runtime_acquisition.EvalRuntimeObservation] = []
    exec_observations: list[runtime_acquisition.ExecRuntimeObservation] = []
    hasattr_observations: list[runtime_acquisition.HasattrRuntimeObservation] = []
    getattr_observations: list[runtime_acquisition.GetattrRuntimeObservation] = []
    dir_observations: list[runtime_acquisition.DirRuntimeObservation] = []
    vars_observations: list[runtime_acquisition.VarsRuntimeObservation] = []
    globals_observations: list[runtime_acquisition.GlobalsRuntimeObservation] = []
    locals_observations: list[runtime_acquisition.LocalsRuntimeObservation] = []
    setattr_observations: list[runtime_acquisition.SetattrRuntimeObservation] = []
    delattr_observations: list[runtime_acquisition.DelattrRuntimeObservation] = []
    metaclass_observations: list[
        runtime_acquisition.MetaclassBehaviorRuntimeObservation
    ] = []

    for admission in ordered_admissions:
        observation = admission.observation
        if isinstance(
            observation,
            runtime_acquisition.DynamicImportRuntimeObservation,
        ):
            dynamic_import_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.EvalRuntimeObservation):
            eval_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.ExecRuntimeObservation):
            exec_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.HasattrRuntimeObservation):
            hasattr_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.GetattrRuntimeObservation):
            getattr_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.DirRuntimeObservation):
            dir_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.VarsRuntimeObservation):
            vars_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.GlobalsRuntimeObservation):
            globals_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.LocalsRuntimeObservation):
            locals_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.SetattrRuntimeObservation):
            setattr_observations.append(observation)
        elif isinstance(observation, runtime_acquisition.DelattrRuntimeObservation):
            delattr_observations.append(observation)
        elif isinstance(
            observation,
            runtime_acquisition.MetaclassBehaviorRuntimeObservation,
        ):
            metaclass_observations.append(observation)
        else:
            assert_never(observation)

    updated_program = runtime_acquisition.attach_dynamic_import_runtime_provenance(
        program,
        tuple(dynamic_import_observations),
    )
    updated_program = runtime_acquisition.attach_eval_runtime_provenance(
        updated_program,
        tuple(eval_observations),
    )
    updated_program = runtime_acquisition.attach_exec_runtime_provenance(
        updated_program,
        tuple(exec_observations),
    )
    updated_program = runtime_acquisition.attach_hasattr_runtime_provenance(
        updated_program,
        tuple(hasattr_observations),
    )
    updated_program = runtime_acquisition.attach_getattr_runtime_provenance(
        updated_program,
        tuple(getattr_observations),
    )
    updated_program = runtime_acquisition.attach_dir_runtime_provenance(
        updated_program,
        tuple(dir_observations),
    )
    updated_program = runtime_acquisition.attach_vars_runtime_provenance(
        updated_program,
        tuple(vars_observations),
    )
    updated_program = runtime_acquisition.attach_globals_runtime_provenance(
        updated_program,
        tuple(globals_observations),
    )
    updated_program = runtime_acquisition.attach_locals_runtime_provenance(
        updated_program,
        tuple(locals_observations),
    )
    updated_program = runtime_acquisition.attach_setattr_runtime_provenance(
        updated_program,
        tuple(setattr_observations),
    )
    updated_program = runtime_acquisition.attach_delattr_runtime_provenance(
        updated_program,
        tuple(delattr_observations),
    )
    return runtime_acquisition.attach_metaclass_behavior_runtime_provenance(
        updated_program,
        tuple(metaclass_observations),
    )


def _index_runtime_probe_result_batch_for_plan(
    plan: RuntimeProbeRequestPlan,
    batch: RuntimeProbeResultBatch,
) -> dict[str, RuntimeProbeResult]:
    """Return probe results keyed by request ID after plan/request validation."""
    if batch.plan_id != plan.plan_id:
        raise ValueError("runtime probe result batch plan_id must match request plan")

    index_runtime_probe_request_plan_by_source_site(plan)
    requests_by_id = {
        request_id: request
        for request, request_id in zip(plan.requests, plan.request_ids, strict=True)
    }

    results_by_request_id: dict[str, RuntimeProbeResult] = {}
    for result in batch.results:
        if result.plan_id != plan.plan_id:
            raise ValueError("runtime probe result plan_id must match request plan")
        if result.request_id in results_by_request_id:
            raise ValueError("duplicate runtime probe result request_id")
        request = requests_by_id.get(result.request_id)
        if request is None:
            raise ValueError(
                "runtime probe result request_id is not present in request plan"
            )
        _validate_runtime_probe_result_matches_request_plan(
            request=request,
            result=result,
        )
        results_by_request_id[result.request_id] = result
    return results_by_request_id


def _validate_runtime_probe_result_matches_request_plan(
    *,
    request: RuntimeProbeRequest,
    result: RuntimeProbeResult,
) -> None:
    """Reject result contracts whose carried request drifted from the plan."""
    if result.request_id != result.request.request_id:
        raise ValueError(
            "runtime probe result request_id must match carried request.request_id"
        )
    request_source_site_identity = runtime_acquisition._source_site_identity(
        request.source_site
    )
    result_source_site_identity = runtime_acquisition._source_site_identity(
        result.request.source_site
    )
    if request_source_site_identity != result_source_site_identity:
        raise ValueError(
            "runtime probe result source site must match planned request source site"
        )
    if (
        request.family_label is not result.request.family_label
        or request.form_label != result.request.form_label
    ):
        raise ValueError("runtime probe result family/form must match planned request")
    if result.request != request:
        raise ValueError(
            "runtime probe result carried request must match planned request"
        )


def _runtime_observation_from_probe_observed_result(
    result: RuntimeProbeObservedResult,
) -> RuntimeObservation:
    """Convert one observed probe result into the existing typed observation path."""
    fields = _runtime_observation_fields_from_probe_observed_result(result)
    request = result.request
    if request.family_label is RuntimeProbeFamily.DYNAMIC_IMPORT:
        return runtime_acquisition.DynamicImportRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    if request.family_label is RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        return _reflective_builtin_runtime_observation_from_probe_result(
            request.form_label,
            fields,
        )
    if request.family_label is RuntimeProbeFamily.RUNTIME_MUTATION:
        return _runtime_mutation_runtime_observation_from_probe_result(
            request.form_label,
            fields,
        )
    if request.family_label is RuntimeProbeFamily.EXEC_OR_EVAL:
        return _exec_or_eval_runtime_observation_from_probe_result(
            request.form_label,
            fields,
        )
    if (
        request.family_label is RuntimeProbeFamily.METACLASS_BEHAVIOR
        and request.form_label == "metaclass_behavior:keyword"
    ):
        return runtime_acquisition.MetaclassBehaviorRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    raise ValueError(
        "runtime probe observed result does not match planned request "
        f"family/form: {request.form_label}"
    )


def _runtime_observation_fields_from_probe_observed_result(
    result: RuntimeProbeObservedResult,
) -> _RuntimeObservationFields:
    """Copy replay, payload, artifact, and attachment data from a proof result."""
    replay_artifact = result.replay_artifact
    return _RuntimeObservationFields(
        site=result.request.source_site,
        probe_identifier=replay_artifact.probe_identifier,
        probe_contract_revision=replay_artifact.probe_contract_revision,
        repository_snapshot_basis=replay_artifact.repository_snapshot_basis,
        attachment_links=(_runtime_attachment_link_from_probe_result(result),),
        replay_target=replay_artifact.replay_target,
        replay_selector=replay_artifact.replay_selector,
        replay_inputs=_runtime_observation_fields_from_probe_fields(
            replay_artifact.replay_inputs
        ),
        runtime_assumptions=_runtime_observation_fields_from_probe_fields(
            replay_artifact.runtime_assumptions
        ),
        normalized_payload=_runtime_observation_fields_from_probe_fields(
            result.normalized_payload
        ),
        durable_payload_reference=result.durable_artifact_reference,
    )


def _runtime_observation_kwargs(
    fields: _RuntimeObservationFields,
) -> _RuntimeObservationKwargs:
    """Return shared constructor kwargs for typed runtime observations."""
    return {
        "site": fields.site,
        "probe_identifier": fields.probe_identifier,
        "probe_contract_revision": fields.probe_contract_revision,
        "repository_snapshot_basis": fields.repository_snapshot_basis,
        "attachment_links": fields.attachment_links,
        "replay_target": fields.replay_target,
        "replay_selector": fields.replay_selector,
        "replay_inputs": fields.replay_inputs,
        "runtime_assumptions": fields.runtime_assumptions,
        "normalized_payload": fields.normalized_payload,
        "durable_payload_reference": fields.durable_payload_reference,
    }


def _runtime_observation_fields_from_probe_fields(
    fields: tuple[RuntimeProbeReplayField, ...],
) -> tuple[runtime_acquisition._RuntimeObservationField, ...]:
    """Convert probe replay/result fields into the typed observation field shape."""
    return tuple(
        runtime_acquisition._RuntimeObservationField(
            key=field.key,
            value=field.value,
        )
        for field in fields
    )


def _runtime_attachment_link_from_probe_result(
    result: RuntimeProbeObservedResult,
) -> RuntimeAttachmentLink:
    """Derive a stable attachment link without adding a new proof surface."""
    if result.durable_artifact_reference is None:
        attachment_identity = f"{result.plan_id}:{result.request_id}"
        description = "inline runtime probe result payload"
    else:
        attachment_identity = result.durable_artifact_reference.strip()
        description = "durable runtime probe result artifact"
    attachment_digest = hashlib.sha256(attachment_identity.encode("utf-8")).hexdigest()[
        :24
    ]
    return RuntimeAttachmentLink(
        attachment_id=f"runtime_probe_result:{attachment_digest}",
        attachment_role="runtime_probe_result",
        description=description,
    )


def _reflective_builtin_runtime_observation_from_probe_result(
    form_label: str,
    fields: _RuntimeObservationFields,
) -> RuntimeObservation:
    """Build a reflective-builtin typed observation for a result form."""
    if form_label == "reflective_builtin:hasattr/2":
        return runtime_acquisition.HasattrRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    if form_label in _REFLECTIVE_GETATTR_FORMS:
        return runtime_acquisition.GetattrRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    if form_label in _REFLECTIVE_VARS_FORMS:
        return runtime_acquisition.VarsRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    if form_label in _REFLECTIVE_DIR_FORMS:
        return runtime_acquisition.DirRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    raise ValueError(
        "runtime probe observed result does not match planned request "
        f"family/form: {form_label}"
    )


def _runtime_mutation_runtime_observation_from_probe_result(
    form_label: str,
    fields: _RuntimeObservationFields,
) -> RuntimeObservation:
    """Build a runtime-mutation typed observation for a result form."""
    if form_label == "runtime_mutation:globals/0":
        return runtime_acquisition.GlobalsRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    if form_label == "runtime_mutation:locals/0":
        return runtime_acquisition.LocalsRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    if form_label == "runtime_mutation:setattr/3":
        return runtime_acquisition.SetattrRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    if form_label == "runtime_mutation:delattr/2":
        return runtime_acquisition.DelattrRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    raise ValueError(
        "runtime probe observed result does not match planned request "
        f"family/form: {form_label}"
    )


def _exec_or_eval_runtime_observation_from_probe_result(
    form_label: str,
    fields: _RuntimeObservationFields,
) -> RuntimeObservation:
    """Build an exec/eval typed observation for a result form."""
    if form_label == "exec_or_eval:exec/1":
        return runtime_acquisition.ExecRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    if form_label == "exec_or_eval:eval/1":
        return runtime_acquisition.EvalRuntimeObservation(
            **_runtime_observation_kwargs(fields)
        )
    raise ValueError(
        "runtime probe observed result does not match planned request "
        f"family/form: {form_label}"
    )


def _validate_runtime_observation_admissions(
    admissions: tuple[RuntimeObservationAdmission, ...],
) -> None:
    """Reject admitted batches whose request, plan, or source-site identities drift."""
    plan_ids = {admission.plan_id for admission in admissions}
    if len(plan_ids) != 1:
        raise ValueError(
            "runtime observation admissions must belong to exactly one plan_id"
        )

    request_ids: set[str] = set()
    source_site_identities: set[_SourceSiteIdentity] = set()
    for admission in admissions:
        if admission.request_id != admission.request.request_id:
            raise ValueError(
                "runtime observation admission request_id must match request.request_id"
            )
        if admission.request_id in request_ids:
            raise ValueError("duplicate runtime observation admission request_id")
        request_ids.add(admission.request_id)

        request_source_site_identity = runtime_acquisition._source_site_identity(
            admission.request.source_site
        )
        observation_source_site_identity = runtime_acquisition._source_site_identity(
            admission.observation.site
        )
        if request_source_site_identity != observation_source_site_identity:
            raise ValueError(
                "runtime observation admission source site must match request "
                "source site"
            )
        if request_source_site_identity in source_site_identities:
            raise ValueError("duplicate runtime observation admission source site")
        source_site_identities.add(request_source_site_identity)

        if not _runtime_observation_matches_request(
            admission.request,
            admission.observation,
        ):
            raise ValueError(
                "runtime observation type does not match planned request "
                f"family/form: {admission.request.form_label}"
            )


def _index_runtime_observations_by_source_site(
    observations: Iterable[RuntimeObservation],
) -> dict[_SourceSiteIdentity, RuntimeObservation]:
    """Return typed runtime observations keyed by source-site identity."""
    observations_by_source_site: dict[_SourceSiteIdentity, RuntimeObservation] = {}
    for observation in observations:
        source_site_identity = runtime_acquisition._source_site_identity(
            observation.site
        )
        if source_site_identity in observations_by_source_site:
            raise ValueError("multiple runtime observations share the same source site")
        observations_by_source_site[source_site_identity] = observation
    return observations_by_source_site


def _runtime_observation_matches_request(
    request: RuntimeProbeRequest,
    observation: RuntimeObservation,
) -> bool:
    """Return whether a typed observation is compatible with a planned request."""
    if request.family_label is RuntimeProbeFamily.DYNAMIC_IMPORT:
        return request.form_label.startswith("dynamic_import:") and isinstance(
            observation,
            runtime_acquisition.DynamicImportRuntimeObservation,
        )
    if request.family_label is RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        return _reflective_builtin_observation_matches_request(
            request.form_label,
            observation,
        )
    if request.family_label is RuntimeProbeFamily.RUNTIME_MUTATION:
        return _runtime_mutation_observation_matches_request(
            request.form_label,
            observation,
        )
    if request.family_label is RuntimeProbeFamily.EXEC_OR_EVAL:
        return _exec_or_eval_observation_matches_request(
            request.form_label,
            observation,
        )
    if request.family_label is RuntimeProbeFamily.METACLASS_BEHAVIOR:
        return request.form_label == "metaclass_behavior:keyword" and isinstance(
            observation,
            runtime_acquisition.MetaclassBehaviorRuntimeObservation,
        )
    return False


def _reflective_builtin_observation_matches_request(
    form_label: str,
    observation: RuntimeObservation,
) -> bool:
    """Return whether a reflective-builtin observation matches the request form."""
    if form_label == "reflective_builtin:hasattr/2":
        return isinstance(observation, runtime_acquisition.HasattrRuntimeObservation)
    if form_label in _REFLECTIVE_GETATTR_FORMS:
        return isinstance(observation, runtime_acquisition.GetattrRuntimeObservation)
    if form_label in _REFLECTIVE_VARS_FORMS:
        return isinstance(observation, runtime_acquisition.VarsRuntimeObservation)
    if form_label in _REFLECTIVE_DIR_FORMS:
        return isinstance(observation, runtime_acquisition.DirRuntimeObservation)
    return False


def _runtime_mutation_observation_matches_request(
    form_label: str,
    observation: RuntimeObservation,
) -> bool:
    """Return whether a runtime-mutation observation matches the request form."""
    if form_label == "runtime_mutation:globals/0":
        return isinstance(observation, runtime_acquisition.GlobalsRuntimeObservation)
    if form_label == "runtime_mutation:locals/0":
        return isinstance(observation, runtime_acquisition.LocalsRuntimeObservation)
    if form_label == "runtime_mutation:setattr/3":
        return isinstance(observation, runtime_acquisition.SetattrRuntimeObservation)
    if form_label == "runtime_mutation:delattr/2":
        return isinstance(observation, runtime_acquisition.DelattrRuntimeObservation)
    return False


def _exec_or_eval_observation_matches_request(
    form_label: str,
    observation: RuntimeObservation,
) -> bool:
    """Return whether an exec/eval observation matches the request form."""
    if form_label == "exec_or_eval:exec/1":
        return isinstance(observation, runtime_acquisition.ExecRuntimeObservation)
    if form_label == "exec_or_eval:eval/1":
        return isinstance(observation, runtime_acquisition.EvalRuntimeObservation)
    return False


__all__ = [
    "RuntimeObservation",
    "RuntimeObservationAdmission",
    "RuntimeObservationApplication",
    "admit_runtime_observations_for_diagnostic",
    "admit_runtime_observations_for_plan",
    "apply_runtime_observations_for_diagnostic",
]

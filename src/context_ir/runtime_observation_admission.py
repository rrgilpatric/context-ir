"""Runtime observation admission for planned probe request boundaries."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeAlias

import context_ir.runtime_acquisition as runtime_acquisition
from context_ir.runtime_probe_requests import (
    RuntimeProbeFamily,
    RuntimeProbeRequest,
    RuntimeProbeRequestPlan,
    index_runtime_probe_request_plan_by_source_site,
)
from context_ir.semantic_types import SemanticDiagnosticResult

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
    "admit_runtime_observations_for_diagnostic",
    "admit_runtime_observations_for_plan",
]

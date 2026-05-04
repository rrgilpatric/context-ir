"""Runtime observation admission for planned probe request boundaries."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeAlias

import context_ir.runtime_acquisition as runtime_acquisition
from context_ir.runtime_probe_requests import (
    RuntimeProbeRequest,
    RuntimeProbeRequestPlan,
    index_runtime_probe_request_plan_by_source_site,
)

_SourceSiteIdentity: TypeAlias = tuple[str, int, int, int, int]

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
        admissions.append(
            RuntimeObservationAdmission(
                plan_id=plan.plan_id,
                request_id=request_id,
                request=request,
                observation=observation,
            )
        )
    return tuple(admissions)


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


__all__ = [
    "RuntimeObservation",
    "RuntimeObservationAdmission",
    "admit_runtime_observations_for_plan",
]

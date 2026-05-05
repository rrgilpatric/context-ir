"""Internal materialization of planned runtime probe execution inputs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TypeAlias

import context_ir.runtime_acquisition as runtime_acquisition
from context_ir.runtime_probe_requests import (
    RuntimeProbeFamily,
    RuntimeProbeRequest,
    RuntimeProbeRequestPlan,
    build_runtime_probe_request_plan,
)
from context_ir.runtime_probe_results import (
    RuntimeProbeReplayArtifact,
    RuntimeProbeReplayField,
)
from context_ir.semantic_types import RepositorySnapshotBasis

_RUNTIME_PROBE_EXECUTION_INPUT_BATCH_CONTRACT_VERSION = (
    "runtime_probe_execution_input_batch:v1"
)

_SourceSiteIdentity: TypeAlias = tuple[str, int, int, int, int]


@dataclass(frozen=True)
class RuntimeProbeExecutionInput:
    """Internal, non-executing work item for one planned runtime probe request."""

    plan_id: str
    request_id: str
    request: RuntimeProbeRequest
    source_site_identity: _SourceSiteIdentity
    family_label: RuntimeProbeFamily
    form_label: str
    replay_target_seed: str
    replay_selector_seed: str
    replay_artifact: RuntimeProbeReplayArtifact

    def __post_init__(self) -> None:
        """Reject materialized execution inputs that drift from their request."""
        if not self.plan_id.strip():
            raise ValueError("plan_id must be non-empty")
        if not self.request_id.strip():
            raise ValueError("request_id must be non-empty")
        if self.request_id != self.request.request_id:
            raise ValueError(
                "runtime probe execution input request_id must match request.request_id"
            )
        if self.source_site_identity != runtime_acquisition._source_site_identity(
            self.request.source_site
        ):
            raise ValueError(
                "runtime probe execution input source site must match request "
                "source site"
            )
        if self.family_label is not self.request.family_label:
            raise ValueError(
                "runtime probe execution input family_label must match request"
            )
        if self.form_label != self.request.form_label:
            raise ValueError(
                "runtime probe execution input form_label must match request"
            )
        if self.replay_target_seed != self.request.replay_target_seed:
            raise ValueError(
                "runtime probe execution input replay target must match request"
            )
        if self.replay_selector_seed != self.request.replay_selector_seed:
            raise ValueError(
                "runtime probe execution input replay selector must match request"
            )

        replay_artifact = self.replay_artifact
        if replay_artifact.probe_identifier != _runtime_probe_identifier(
            plan_id=self.plan_id,
            request_id=self.request_id,
            request=self.request,
        ):
            raise ValueError(
                "runtime probe execution input probe_identifier must match "
                "planned request identity"
            )
        if replay_artifact.replay_target != self.replay_target_seed:
            raise ValueError(
                "runtime probe execution input replay_artifact target must match "
                "request seed"
            )
        if replay_artifact.replay_selector != self.replay_selector_seed:
            raise ValueError(
                "runtime probe execution input replay_artifact selector must match "
                "request seed"
            )
        if replay_artifact.replay_inputs != _replay_inputs_for_request(
            plan_id=self.plan_id,
            request_id=self.request_id,
            request=self.request,
        ):
            raise ValueError(
                "runtime probe execution input replay_inputs must match planned "
                "request identity"
            )
        if not replay_artifact.runtime_assumptions:
            raise ValueError(
                "runtime probe execution inputs require runtime_assumptions"
            )


@dataclass(frozen=True)
class RuntimeProbeExecutionInputBatch:
    """Ordered internal execution-input batch for one runtime request plan."""

    plan_id: str
    request_ids: tuple[str, ...]
    inputs: tuple[RuntimeProbeExecutionInput, ...]
    contract_version: str = field(
        default=_RUNTIME_PROBE_EXECUTION_INPUT_BATCH_CONTRACT_VERSION,
        init=False,
    )

    def __post_init__(self) -> None:
        """Reject batches whose request order or plan identity has drifted."""
        if not self.plan_id.strip():
            raise ValueError("plan_id must be non-empty")
        input_request_ids = tuple(input_item.request_id for input_item in self.inputs)
        if self.request_ids != input_request_ids:
            raise ValueError(
                "runtime probe execution input batch request_ids must match inputs"
            )

        seen_request_ids: set[str] = set()
        for input_item in self.inputs:
            if input_item.plan_id != self.plan_id:
                raise ValueError(
                    "runtime probe execution input batch plan_id must match inputs"
                )
            if input_item.request_id in seen_request_ids:
                raise ValueError("duplicate runtime probe execution input request_id")
            seen_request_ids.add(input_item.request_id)


def materialize_runtime_probe_execution_input_batch(
    plan: RuntimeProbeRequestPlan,
    *,
    repository_snapshot_basis: RepositorySnapshotBasis,
    probe_contract_revision: str,
    runtime_assumptions: Iterable[RuntimeProbeReplayField],
) -> RuntimeProbeExecutionInputBatch:
    """Materialize replay-ready, non-executing inputs for a planned probe batch."""
    _validate_request_plan(plan)
    if not probe_contract_revision.strip():
        raise ValueError("probe_contract_revision must be non-empty")
    assumptions = tuple(runtime_assumptions)
    if not assumptions:
        raise ValueError("runtime probe execution inputs require runtime_assumptions")

    inputs = tuple(
        _materialize_runtime_probe_execution_input(
            plan_id=plan.plan_id,
            request_id=request_id,
            request=request,
            repository_snapshot_basis=repository_snapshot_basis,
            probe_contract_revision=probe_contract_revision,
            runtime_assumptions=assumptions,
        )
        for request, request_id in zip(plan.requests, plan.request_ids, strict=True)
    )
    return RuntimeProbeExecutionInputBatch(
        plan_id=plan.plan_id,
        request_ids=plan.request_ids,
        inputs=inputs,
    )


def _materialize_runtime_probe_execution_input(
    *,
    plan_id: str,
    request_id: str,
    request: RuntimeProbeRequest,
    repository_snapshot_basis: RepositorySnapshotBasis,
    probe_contract_revision: str,
    runtime_assumptions: tuple[RuntimeProbeReplayField, ...],
) -> RuntimeProbeExecutionInput:
    """Build one typed work item without executing or observing a probe."""
    return RuntimeProbeExecutionInput(
        plan_id=plan_id,
        request_id=request_id,
        request=request,
        source_site_identity=runtime_acquisition._source_site_identity(
            request.source_site
        ),
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        replay_artifact=RuntimeProbeReplayArtifact(
            probe_identifier=_runtime_probe_identifier(
                plan_id=plan_id,
                request_id=request_id,
                request=request,
            ),
            probe_contract_revision=probe_contract_revision,
            repository_snapshot_basis=repository_snapshot_basis,
            replay_target=request.replay_target_seed,
            replay_selector=request.replay_selector_seed,
            replay_inputs=_replay_inputs_for_request(
                plan_id=plan_id,
                request_id=request_id,
                request=request,
            ),
            runtime_assumptions=runtime_assumptions,
        ),
    )


def _validate_request_plan(plan: RuntimeProbeRequestPlan) -> None:
    """Reject request-plan envelopes that drifted after construction."""
    expected_plan = build_runtime_probe_request_plan(plan.requests)
    if plan.request_ids != expected_plan.request_ids:
        raise ValueError("runtime probe execution plan request_ids must match requests")
    if plan.plan_id != expected_plan.plan_id:
        raise ValueError("runtime probe execution plan_id must match requests")


def _runtime_probe_identifier(
    *,
    plan_id: str,
    request_id: str,
    request: RuntimeProbeRequest,
) -> str:
    """Return a stable execution-input identity for one planned probe request."""
    serialized_identity = json.dumps(
        (
            ("plan_id", plan_id),
            ("request_id", request_id),
            (
                "source_site_identity",
                runtime_acquisition._source_site_identity(request.source_site),
            ),
            ("family_label", request.family_label.value),
            ("form_label", request.form_label),
            ("replay_target_seed", request.replay_target_seed),
            ("replay_selector_seed", request.replay_selector_seed),
        ),
        separators=(",", ":"),
    )
    digest = hashlib.sha256(serialized_identity.encode("utf-8")).hexdigest()
    return f"runtime_probe_execution_input:{digest}"


def _replay_inputs_for_request(
    *,
    plan_id: str,
    request_id: str,
    request: RuntimeProbeRequest,
) -> tuple[RuntimeProbeReplayField, ...]:
    """Return replay/debug identity fields copied from one planned request."""
    span = request.source_site.span
    return (
        RuntimeProbeReplayField(key="plan_id", value=plan_id),
        RuntimeProbeReplayField(key="request_id", value=request_id),
        RuntimeProbeReplayField(key="subject_kind", value=request.subject_kind.value),
        RuntimeProbeReplayField(key="subject_id", value=request.subject_id),
        RuntimeProbeReplayField(
            key="source_site_id",
            value=request.source_site.site_id,
        ),
        RuntimeProbeReplayField(
            key="source_file_path",
            value=request.source_site.file_path,
        ),
        RuntimeProbeReplayField(
            key="source_start_line",
            value=str(span.start_line),
        ),
        RuntimeProbeReplayField(
            key="source_start_column",
            value=str(span.start_column),
        ),
        RuntimeProbeReplayField(key="source_end_line", value=str(span.end_line)),
        RuntimeProbeReplayField(
            key="source_end_column",
            value=str(span.end_column),
        ),
        RuntimeProbeReplayField(key="reason_code", value=request.reason_code.value),
        RuntimeProbeReplayField(key="boundary_text", value=request.boundary_text),
        RuntimeProbeReplayField(
            key="family_label",
            value=request.family_label.value,
        ),
        RuntimeProbeReplayField(key="form_label", value=request.form_label),
        RuntimeProbeReplayField(
            key="replay_target_seed",
            value=request.replay_target_seed,
        ),
        RuntimeProbeReplayField(
            key="replay_selector_seed",
            value=request.replay_selector_seed,
        ),
    )


__all__ = [
    "RuntimeProbeExecutionInput",
    "RuntimeProbeExecutionInputBatch",
    "materialize_runtime_probe_execution_input_batch",
]

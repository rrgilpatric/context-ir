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
    RuntimeProbeNonProofResult,
    RuntimeProbeObservedResult,
    RuntimeProbeReplayArtifact,
    RuntimeProbeReplayField,
    RuntimeProbeResult,
    RuntimeProbeResultBatch,
    RuntimeProbeResultOutcome,
)
from context_ir.semantic_types import RepositorySnapshotBasis

_RUNTIME_PROBE_EXECUTION_INPUT_BATCH_CONTRACT_VERSION = (
    "runtime_probe_execution_input_batch:v1"
)
_NON_PROOF_ATTEMPT_OUTCOMES = frozenset(
    {
        RuntimeProbeResultOutcome.CRASHED,
        RuntimeProbeResultOutcome.TIMED_OUT,
        RuntimeProbeResultOutcome.MISSING_ENVIRONMENT,
        RuntimeProbeResultOutcome.SETUP_FAILED,
    }
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


@dataclass(frozen=True)
class RuntimeProbeExecutionAttempt:
    """Internal normalized runner output for one non-executing probe input."""

    plan_id: str
    request_id: str
    request: RuntimeProbeRequest
    execution_input: RuntimeProbeExecutionInput
    outcome: RuntimeProbeResultOutcome
    normalized_payload: tuple[RuntimeProbeReplayField, ...] = ()
    durable_artifact_reference: str | None = None
    failure_summary: str | None = None
    failure_detail_fields: tuple[RuntimeProbeReplayField, ...] = ()

    def __post_init__(self) -> None:
        """Reject attempts whose normalized result metadata cannot be trusted."""
        if self.plan_id != self.execution_input.plan_id:
            raise ValueError(
                "runtime probe execution attempt plan_id must match execution input"
            )
        if self.request_id != self.execution_input.request_id:
            raise ValueError(
                "runtime probe execution attempt request_id must match execution input"
            )
        if self.request is not self.execution_input.request:
            raise ValueError(
                "runtime probe execution attempt request must be execution input "
                "request"
            )

        _validate_optional_reference(
            self.durable_artifact_reference,
            field_name="durable_artifact_reference",
        )
        _validate_replay_fields(
            self.normalized_payload,
            field_name="normalized_payload",
        )
        _validate_replay_fields(
            self.failure_detail_fields,
            field_name="failure_detail_fields",
        )

        if self.outcome is RuntimeProbeResultOutcome.OBSERVED:
            _validate_observed_attempt_metadata(self)
            return
        if self.outcome in _NON_PROOF_ATTEMPT_OUTCOMES:
            _validate_non_proof_attempt_metadata(self)
            return
        raise ValueError("runtime probe execution attempt outcome is not supported")


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


def assemble_runtime_probe_result_batch_from_execution_attempts(
    input_batch: RuntimeProbeExecutionInputBatch,
    attempts: Iterable[RuntimeProbeExecutionAttempt],
) -> RuntimeProbeResultBatch:
    """Convert a complete typed attempt set into an ordered result batch."""
    attempts_by_request_id = _index_execution_attempts_for_input_batch(
        input_batch,
        attempts,
    )
    results = tuple(
        _runtime_probe_result_from_attempt(attempts_by_request_id[request_id])
        for request_id in input_batch.request_ids
    )
    return RuntimeProbeResultBatch(plan_id=input_batch.plan_id, results=results)


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


def _index_execution_attempts_for_input_batch(
    input_batch: RuntimeProbeExecutionInputBatch,
    attempts: Iterable[RuntimeProbeExecutionAttempt],
) -> dict[str, RuntimeProbeExecutionAttempt]:
    """Return attempts keyed by request ID after validating batch completeness."""
    inputs_by_request_id = {
        input_item.request_id: input_item for input_item in input_batch.inputs
    }
    attempts_by_request_id: dict[str, RuntimeProbeExecutionAttempt] = {}

    for attempt in attempts:
        if attempt.request_id in attempts_by_request_id:
            raise ValueError("duplicate runtime probe execution attempt request_id")
        input_item = inputs_by_request_id.get(attempt.request_id)
        if input_item is None:
            raise ValueError(
                "runtime probe execution attempt request_id is not present in "
                "input batch"
            )
        if attempt.plan_id != input_batch.plan_id:
            raise ValueError(
                "runtime probe execution attempt plan_id must match input batch"
            )
        if attempt.execution_input is not input_item:
            raise ValueError(
                "runtime probe execution attempt input must be the planned batch input"
            )
        if attempt.request is not input_item.request:
            raise ValueError(
                "runtime probe execution attempt request must be the planned batch "
                "request"
            )
        attempts_by_request_id[attempt.request_id] = attempt

    missing_request_ids = tuple(
        request_id
        for request_id in input_batch.request_ids
        if request_id not in attempts_by_request_id
    )
    if missing_request_ids:
        raise ValueError(
            "missing runtime probe execution attempt for input batch request_id"
        )
    return attempts_by_request_id


def _runtime_probe_result_from_attempt(
    attempt: RuntimeProbeExecutionAttempt,
) -> RuntimeProbeResult:
    """Build the externally admitted result contract for one normalized attempt."""
    if attempt.outcome is RuntimeProbeResultOutcome.OBSERVED:
        return RuntimeProbeObservedResult(
            plan_id=attempt.plan_id,
            request_id=attempt.request_id,
            request=attempt.request,
            replay_artifact=attempt.execution_input.replay_artifact,
            normalized_payload=attempt.normalized_payload,
            durable_artifact_reference=attempt.durable_artifact_reference,
        )

    if attempt.outcome in _NON_PROOF_ATTEMPT_OUTCOMES:
        failure_summary = attempt.failure_summary
        if failure_summary is None:
            raise ValueError("non-proof runtime probe attempts require failure_summary")
        return RuntimeProbeNonProofResult(
            plan_id=attempt.plan_id,
            request_id=attempt.request_id,
            request=attempt.request,
            outcome=attempt.outcome,
            failure_summary=failure_summary,
            replay_artifact=attempt.execution_input.replay_artifact,
            failure_detail_fields=attempt.failure_detail_fields,
        )

    raise ValueError("runtime probe execution attempt outcome is not supported")


def _validate_observed_attempt_metadata(
    attempt: RuntimeProbeExecutionAttempt,
) -> None:
    """Reject observed attempts that carry only failure or empty proof metadata."""
    if attempt.failure_summary is not None or attempt.failure_detail_fields:
        raise ValueError(
            "observed runtime probe execution attempts cannot carry failure metadata"
        )
    if not attempt.normalized_payload and attempt.durable_artifact_reference is None:
        raise ValueError(
            "observed runtime probe execution attempts require normalized_payload "
            "or durable_artifact_reference"
        )


def _validate_non_proof_attempt_metadata(
    attempt: RuntimeProbeExecutionAttempt,
) -> None:
    """Reject failed attempts that omit failure metadata or carry proof metadata."""
    if not attempt.failure_summary or not attempt.failure_summary.strip():
        raise ValueError("non-proof runtime probe attempts require failure_summary")
    if attempt.normalized_payload or attempt.durable_artifact_reference is not None:
        raise ValueError(
            "non-proof runtime probe execution attempts cannot carry proof metadata"
        )


def _validate_replay_fields(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    field_name: str,
) -> None:
    """Reject replay fields whose frozen values have been tampered blank."""
    for replay_field in fields:
        if not replay_field.key.strip() or not replay_field.value.strip():
            raise ValueError(f"{field_name} must not contain blank fields")


def _validate_optional_reference(reference: str | None, *, field_name: str) -> None:
    """Reject blank optional artifact references."""
    if reference is not None and not reference.strip():
        raise ValueError(f"{field_name} must be non-empty when provided")


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
    "RuntimeProbeExecutionAttempt",
    "RuntimeProbeExecutionInput",
    "RuntimeProbeExecutionInputBatch",
    "assemble_runtime_probe_result_batch_from_execution_attempts",
    "materialize_runtime_probe_execution_input_batch",
]

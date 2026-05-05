"""Runtime probe execution result and replay artifact contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

from context_ir.runtime_probe_requests import RuntimeProbeRequest
from context_ir.semantic_types import RepositorySnapshotBasis


class RuntimeProbeResultOutcome(Enum):
    """Execution outcomes for runtime probe runner results."""

    OBSERVED = "observed"
    CRASHED = "crashed"
    TIMED_OUT = "timed_out"
    MISSING_ENVIRONMENT = "missing_environment"
    SETUP_FAILED = "setup_failed"


@dataclass(frozen=True)
class RuntimeProbeReplayField:
    """Typed key/value field used in replay contracts and result payloads."""

    key: str
    value: str

    def __post_init__(self) -> None:
        """Reject incomplete replay field metadata."""
        if not self.key.strip():
            raise ValueError("runtime probe replay field key must be non-empty")
        if not self.value.strip():
            raise ValueError("runtime probe replay field value must be non-empty")


@dataclass(frozen=True)
class RuntimeProbeReplayArtifact:
    """Replay metadata required to reproduce one runtime probe attempt."""

    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[RuntimeProbeReplayField, ...]
    runtime_assumptions: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject incomplete replay identity and selector metadata."""
        if not self.probe_identifier.strip():
            raise ValueError("probe_identifier must be non-empty")
        if not self.probe_contract_revision.strip():
            raise ValueError("probe_contract_revision must be non-empty")
        if not self.replay_target.strip():
            raise ValueError("replay_target must be non-empty")
        if not self.replay_selector.strip():
            raise ValueError("replay_selector must be non-empty")


@dataclass(frozen=True)
class RuntimeProbeObservedResult:
    """Observed runtime probe result that can later feed proof admission."""

    plan_id: str
    request_id: str
    request: RuntimeProbeRequest
    replay_artifact: RuntimeProbeReplayArtifact
    normalized_payload: tuple[RuntimeProbeReplayField, ...] = ()
    durable_artifact_reference: str | None = None
    outcome: RuntimeProbeResultOutcome = field(
        default=RuntimeProbeResultOutcome.OBSERVED,
        init=False,
    )

    def __post_init__(self) -> None:
        """Reject observed results whose identity or proof metadata is incomplete."""
        _validate_plan_and_request_identity(
            plan_id=self.plan_id,
            request_id=self.request_id,
            request=self.request,
        )
        if not self.replay_artifact.replay_inputs:
            raise ValueError("observed runtime probe results require replay_inputs")
        if not self.replay_artifact.runtime_assumptions:
            raise ValueError(
                "observed runtime probe results require runtime_assumptions"
            )
        _validate_optional_reference(
            self.durable_artifact_reference,
            field_name="durable_artifact_reference",
        )
        if not self.normalized_payload and self.durable_artifact_reference is None:
            raise ValueError(
                "observed runtime probe results require normalized_payload or "
                "durable_artifact_reference"
            )

    @property
    def is_admissible_runtime_backed_proof(self) -> bool:
        """Return whether this result can later be considered proof-bearing."""
        return True


@dataclass(frozen=True)
class RuntimeProbeNonProofResult:
    """Runtime probe result for failed attempts that are not proof-bearing."""

    plan_id: str
    request_id: str
    request: RuntimeProbeRequest
    outcome: RuntimeProbeResultOutcome
    failure_summary: str
    replay_artifact: RuntimeProbeReplayArtifact | None = None
    failure_detail_fields: tuple[RuntimeProbeReplayField, ...] = ()

    def __post_init__(self) -> None:
        """Reject non-proof results that look like successful observations."""
        _validate_plan_and_request_identity(
            plan_id=self.plan_id,
            request_id=self.request_id,
            request=self.request,
        )
        if self.outcome is RuntimeProbeResultOutcome.OBSERVED:
            raise ValueError("non-proof runtime probe results cannot be observed")
        if not self.failure_summary.strip():
            raise ValueError("failure_summary must be non-empty")

    @property
    def is_admissible_runtime_backed_proof(self) -> bool:
        """Return whether this failed result can be admitted as runtime proof."""
        return False


RuntimeProbeResult: TypeAlias = RuntimeProbeObservedResult | RuntimeProbeNonProofResult


@dataclass(frozen=True)
class RuntimeProbeResultBatch:
    """Ordered runtime probe result batch for one planned request plan."""

    plan_id: str
    results: tuple[RuntimeProbeResult, ...]

    def __post_init__(self) -> None:
        """Reject result batches with drifted plan or duplicate request identities."""
        if not self.plan_id.strip():
            raise ValueError("plan_id must be non-empty")
        request_ids: set[str] = set()
        for result in self.results:
            if result.plan_id != self.plan_id:
                raise ValueError(
                    "runtime probe result batch plan_id must match results"
                )
            if result.request_id in request_ids:
                raise ValueError("duplicate runtime probe result request_id")
            request_ids.add(result.request_id)


def _validate_plan_and_request_identity(
    *,
    plan_id: str,
    request_id: str,
    request: RuntimeProbeRequest,
) -> None:
    """Reject result identity fields that drift from the planned request."""
    if not plan_id.strip():
        raise ValueError("plan_id must be non-empty")
    if not request_id.strip():
        raise ValueError("request_id must be non-empty")
    if request_id != request.request_id:
        raise ValueError(
            "runtime probe result request_id must match request.request_id"
        )


def _validate_optional_reference(reference: str | None, *, field_name: str) -> None:
    """Reject blank optional artifact references."""
    if reference is not None and not reference.strip():
        raise ValueError(f"{field_name} must be non-empty when provided")


__all__ = [
    "RuntimeProbeNonProofResult",
    "RuntimeProbeObservedResult",
    "RuntimeProbeReplayArtifact",
    "RuntimeProbeReplayField",
    "RuntimeProbeResult",
    "RuntimeProbeResultBatch",
    "RuntimeProbeResultOutcome",
]

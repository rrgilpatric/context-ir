"""Tests for runtime probe execution result contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import context_ir
import context_ir.runtime_probe_requests as runtime_probe_requests
import context_ir.runtime_probe_results as runtime_probe_results
from context_ir.semantic_types import (
    RepositorySnapshotBasis,
    SemanticSubjectKind,
    SourceSite,
    SourceSpan,
    UnresolvedReasonCode,
)


def _source_site(start_line: int = 3) -> SourceSite:
    """Return a stable source site for a synthetic runtime probe request."""
    return SourceSite(
        site_id=f"site:main.py:{start_line}:4",
        file_path="main.py",
        span=SourceSpan(
            start_line=start_line,
            start_column=4,
            end_line=start_line,
            end_column=28,
        ),
        snippet="importlib.import_module(name)",
    )


def _request(start_line: int = 3) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned runtime probe request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:main.py:{start_line}:4",
        source_site=_source_site(start_line),
        reason_code=UnresolvedReasonCode.DYNAMIC_IMPORT,
        boundary_text="importlib.import_module(name)",
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        replay_target_seed="main.run",
        replay_selector_seed=(
            f"call:main.run:dynamic_import@main.py:{start_line}:4:{start_line}:28"
        ),
    )


def _plan(
    *requests: runtime_probe_requests.RuntimeProbeRequest,
) -> runtime_probe_requests.RuntimeProbeRequestPlan:
    """Build a request plan around supplied synthetic probe requests."""
    return runtime_probe_requests.build_runtime_probe_request_plan(requests)


def _field(
    key: str = "imported_module", value: str = "plugins.weather"
) -> runtime_probe_results.RuntimeProbeReplayField:
    """Return one typed replay/result field."""
    return runtime_probe_results.RuntimeProbeReplayField(key=key, value=value)


def _snapshot_basis() -> RepositorySnapshotBasis:
    """Return stable repository snapshot metadata for replay artifacts."""
    return RepositorySnapshotBasis(
        snapshot_kind="git_commit",
        snapshot_id="abc123def456",
        is_dirty_worktree=False,
    )


def _replay_artifact(
    *,
    replay_inputs: tuple[runtime_probe_results.RuntimeProbeReplayField, ...]
    | None = None,
    runtime_assumptions: tuple[runtime_probe_results.RuntimeProbeReplayField, ...]
    | None = None,
) -> runtime_probe_results.RuntimeProbeReplayArtifact:
    """Return a complete replay artifact for observed probe results."""
    inputs = replay_inputs
    if inputs is None:
        inputs = (_field("module_name", "plugins.weather"),)
    assumptions = runtime_assumptions
    if assumptions is None:
        assumptions = (_field("python_version", "3.11"),)
    return runtime_probe_results.RuntimeProbeReplayArtifact(
        probe_identifier="probe:dynamic-import",
        probe_contract_revision="runtime-probe-contract:2026-05-05.1",
        repository_snapshot_basis=_snapshot_basis(),
        replay_target="main.run",
        replay_selector="call:main.run:dynamic_import",
        replay_inputs=inputs,
        runtime_assumptions=assumptions,
    )


def _observed_result(
    request: runtime_probe_requests.RuntimeProbeRequest,
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
    *,
    replay_artifact: runtime_probe_results.RuntimeProbeReplayArtifact | None = None,
) -> runtime_probe_results.RuntimeProbeObservedResult:
    """Return one observed runtime probe result for a planned request."""
    artifact = replay_artifact
    if artifact is None:
        artifact = _replay_artifact()
    return runtime_probe_results.RuntimeProbeObservedResult(
        plan_id=plan.plan_id,
        request_id=request.request_id,
        request=request,
        replay_artifact=artifact,
        normalized_payload=(_field(),),
    )


def test_observed_result_preserves_request_and_plan_identities() -> None:
    """Observed results keep request IDs, plan IDs, request identity, and replay."""
    request = _request()
    plan = _plan(request)
    replay_artifact = _replay_artifact()

    result = runtime_probe_results.RuntimeProbeObservedResult(
        plan_id=plan.plan_id,
        request_id=request.request_id,
        request=request,
        replay_artifact=replay_artifact,
        normalized_payload=(_field(),),
    )

    assert result.plan_id == plan.plan_id
    assert result.request_id == request.request_id
    assert result.request is request
    assert result.replay_artifact is replay_artifact
    assert result.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert result.is_admissible_runtime_backed_proof is True
    assert result.replay_artifact.probe_identifier == "probe:dynamic-import"
    assert result.replay_artifact.probe_contract_revision == (
        "runtime-probe-contract:2026-05-05.1"
    )
    assert result.replay_artifact.repository_snapshot_basis == _snapshot_basis()
    assert result.replay_artifact.replay_target == "main.run"
    assert result.replay_artifact.replay_selector == "call:main.run:dynamic_import"
    assert result.replay_artifact.replay_inputs == (
        _field("module_name", "plugins.weather"),
    )
    assert result.replay_artifact.runtime_assumptions == (
        _field("python_version", "3.11"),
    )
    assert result.normalized_payload == (_field(),)


def test_observed_result_accepts_durable_artifact_reference_without_payload() -> None:
    """Observed proof can cite a durable artifact instead of inline payload."""
    request = _request()
    plan = _plan(request)

    result = runtime_probe_results.RuntimeProbeObservedResult(
        plan_id=plan.plan_id,
        request_id=request.request_id,
        request=request,
        replay_artifact=_replay_artifact(),
        durable_artifact_reference=(
            "artifact://runtime-probe-results/dynamic-import/main-run.json"
        ),
    )

    assert result.normalized_payload == ()
    assert result.durable_artifact_reference == (
        "artifact://runtime-probe-results/dynamic-import/main-run.json"
    )
    assert result.is_admissible_runtime_backed_proof is True


def test_observed_result_requires_payload_or_durable_artifact_reference() -> None:
    """Observed results cannot be proof-bearing without durable outcome evidence."""
    request = _request()
    plan = _plan(request)

    with pytest.raises(ValueError, match="normalized_payload or durable"):
        runtime_probe_results.RuntimeProbeObservedResult(
            plan_id=plan.plan_id,
            request_id=request.request_id,
            request=request,
            replay_artifact=_replay_artifact(),
        )


@pytest.mark.parametrize(
    ("replay_inputs", "runtime_assumptions", "message"),
    (
        ((), (_field("python_version", "3.11"),), "replay_inputs"),
        ((_field("module_name", "plugins.weather"),), (), "runtime_assumptions"),
    ),
)
def test_observed_result_requires_replay_inputs_and_runtime_assumptions(
    replay_inputs: tuple[runtime_probe_results.RuntimeProbeReplayField, ...],
    runtime_assumptions: tuple[runtime_probe_results.RuntimeProbeReplayField, ...],
    message: str,
) -> None:
    """Observed results must carry material replay inputs and assumptions."""
    request = _request()
    plan = _plan(request)

    with pytest.raises(ValueError, match=message):
        _observed_result(
            request,
            plan,
            replay_artifact=_replay_artifact(
                replay_inputs=replay_inputs,
                runtime_assumptions=runtime_assumptions,
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "message"),
    (
        ("probe_identifier", "probe_identifier"),
        ("probe_contract_revision", "probe_contract_revision"),
        ("replay_target", "replay_target"),
        ("replay_selector", "replay_selector"),
    ),
)
def test_replay_artifact_requires_identity_and_selector_metadata(
    field_name: str,
    message: str,
) -> None:
    """Replay artifacts reject missing probe identity and replay selector metadata."""
    kwargs = {
        "probe_identifier": "probe:dynamic-import",
        "probe_contract_revision": "runtime-probe-contract:2026-05-05.1",
        "repository_snapshot_basis": _snapshot_basis(),
        "replay_target": "main.run",
        "replay_selector": "call:main.run:dynamic_import",
        "replay_inputs": (_field("module_name", "plugins.weather"),),
        "runtime_assumptions": (_field("python_version", "3.11"),),
    }
    kwargs[field_name] = " "

    with pytest.raises(ValueError, match=message):
        runtime_probe_results.RuntimeProbeReplayArtifact(**kwargs)


@pytest.mark.parametrize(
    "outcome",
    (
        runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        runtime_probe_results.RuntimeProbeResultOutcome.MISSING_ENVIRONMENT,
        runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
    ),
)
def test_non_proof_outcomes_are_not_admissible_runtime_backed_proof(
    outcome: runtime_probe_results.RuntimeProbeResultOutcome,
) -> None:
    """Runner failures are representable without becoming runtime-backed proof."""
    request = _request()
    plan = _plan(request)

    result = runtime_probe_results.RuntimeProbeNonProofResult(
        plan_id=plan.plan_id,
        request_id=request.request_id,
        request=request,
        outcome=outcome,
        failure_summary=f"runner outcome: {outcome.value}",
        replay_artifact=_replay_artifact(),
        failure_detail_fields=(_field("exit_code", "1"),),
    )

    assert result.plan_id == plan.plan_id
    assert result.request_id == request.request_id
    assert result.request is request
    assert result.outcome is outcome
    assert result.is_admissible_runtime_backed_proof is False
    assert result.replay_artifact is not None
    assert result.failure_detail_fields == (_field("exit_code", "1"),)


def test_non_proof_result_rejects_observed_outcome() -> None:
    """The failure result type cannot be used to smuggle observed proof."""
    request = _request()
    plan = _plan(request)

    with pytest.raises(ValueError, match="cannot be observed"):
        runtime_probe_results.RuntimeProbeNonProofResult(
            plan_id=plan.plan_id,
            request_id=request.request_id,
            request=request,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            failure_summary="not actually failed",
        )


def test_results_reject_request_identity_drift() -> None:
    """Result request IDs must match the carried RuntimeProbeRequest object."""
    request = _request()
    plan = _plan(request)

    with pytest.raises(ValueError, match="request.request_id"):
        runtime_probe_results.RuntimeProbeObservedResult(
            plan_id=plan.plan_id,
            request_id="runtime_probe:wrong",
            request=request,
            replay_artifact=_replay_artifact(),
            normalized_payload=(_field(),),
        )


def test_result_batch_preserves_plan_identity_and_rejects_duplicates() -> None:
    """Batches group mixed proof and non-proof results under one request plan ID."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    plan = _plan(first_request, second_request)
    observed = _observed_result(first_request, plan)
    non_proof = runtime_probe_results.RuntimeProbeNonProofResult(
        plan_id=plan.plan_id,
        request_id=second_request.request_id,
        request=second_request,
        outcome=runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        failure_summary="probe exceeded timeout",
    )

    batch = runtime_probe_results.RuntimeProbeResultBatch(
        plan_id=plan.plan_id,
        results=(observed, non_proof),
    )

    assert batch.plan_id == plan.plan_id
    assert batch.results == (observed, non_proof)

    with pytest.raises(ValueError, match="duplicate runtime probe result request_id"):
        runtime_probe_results.RuntimeProbeResultBatch(
            plan_id=plan.plan_id,
            results=(observed, observed),
        )
    with pytest.raises(ValueError, match="plan_id must match"):
        runtime_probe_results.RuntimeProbeResultBatch(
            plan_id="runtime_probe_request_plan:other",
            results=(observed,),
        )


def test_runtime_probe_result_contract_is_frozen_and_module_local() -> None:
    """The new contract remains frozen and absent from package-root exports."""
    request = _request()
    plan = _plan(request)
    result = _observed_result(request, plan)

    with pytest.raises(FrozenInstanceError):
        result.plan_id = "runtime_probe_request_plan:mutated"

    assert "RuntimeProbeObservedResult" in runtime_probe_results.__all__
    assert "RuntimeProbeObservedResult" not in context_ir.__all__
    assert not hasattr(context_ir, "RuntimeProbeObservedResult")

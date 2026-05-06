"""Tests for internal runtime probe execution input materialization."""

from __future__ import annotations

import textwrap
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import context_ir
import context_ir.runtime_probe_execution as runtime_probe_execution
import context_ir.runtime_probe_requests as runtime_probe_requests
import context_ir.runtime_probe_results as runtime_probe_results
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.runtime_probe_execution import (
    assemble_runtime_probe_result_batch_from_execution_attempts,
)
from context_ir.semantic_types import (
    RepositorySnapshotBasis,
    SemanticProgram,
    SemanticSubjectKind,
    SourceSite,
    SourceSpan,
    UnresolvedReasonCode,
)

_EXPECTED_REPLAY_INPUT_KEYS = (
    "plan_id",
    "request_id",
    "subject_kind",
    "subject_id",
    "source_site_id",
    "source_file_path",
    "source_start_line",
    "source_start_column",
    "source_end_line",
    "source_end_column",
    "reason_code",
    "boundary_text",
    "family_label",
    "form_label",
    "replay_target_seed",
    "replay_selector_seed",
)

_EXPECTED_CURRENT_FORMS = {
    "dynamic_import:importlib.import_module/1",
    "dynamic_import:load_module/1",
    "dynamic_import:builtins.__import__/1",
    "dynamic_import:__import__/1",
    "reflective_builtin:getattr/2",
    "reflective_builtin:getattr/3",
    "reflective_builtin:hasattr/2",
    "reflective_builtin:vars/1",
    "reflective_builtin:vars/0",
    "reflective_builtin:dir/1",
    "reflective_builtin:dir/0",
    "runtime_mutation:globals/0",
    "runtime_mutation:locals/0",
    "runtime_mutation:setattr/3",
    "runtime_mutation:delattr/2",
    "exec_or_eval:exec/1",
    "exec_or_eval:eval/1",
    "metaclass_behavior:keyword",
}


def _derived_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted semantic pipeline through frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _write_runtime_probe_program(tmp_path: Path) -> None:
    """Write source that exercises every currently planned probe family/form."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import builtins
            import importlib
            from importlib import import_module as load_module

            class Meta(type):
                pass

            class Example(metaclass=Meta):
                pass

            def run(
                obj: object,
                name: str,
                value: object,
                source: str,
                default: object,
            ) -> None:
                importlib.import_module(name)
                load_module(name)
                builtins.__import__(name)
                __import__(name)
                getattr(obj, name)
                getattr(obj, name, default)
                hasattr(obj, name)
                vars(obj)
                vars()
                dir(obj)
                dir()
                globals()
                locals()
                setattr(obj, name, value)
                delattr(obj, name)
                exec(source)
                eval(source)
            """
        ).lstrip(),
        encoding="utf-8",
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


def _snapshot_basis() -> RepositorySnapshotBasis:
    """Return stable repository snapshot metadata for replay artifacts."""
    return RepositorySnapshotBasis(
        snapshot_kind="git_commit",
        snapshot_id="abc123def456",
        is_dirty_worktree=False,
    )


def _field(
    key: str = "python_version",
    value: str = "3.11",
) -> runtime_probe_results.RuntimeProbeReplayField:
    """Return one typed replay/runtime assumption field."""
    return runtime_probe_results.RuntimeProbeReplayField(key=key, value=value)


def _runtime_assumptions() -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return the explicit runtime assumptions for materialized input tests."""
    return (
        _field("python_version", "3.11"),
        _field("dependency_mode", "offline-fixture"),
    )


def _source_site_identity(
    request: runtime_probe_requests.RuntimeProbeRequest,
) -> tuple[str, int, int, int, int]:
    """Return the stable source-site identity for one planned request."""
    span = request.source_site.span
    return (
        request.source_site.file_path,
        span.start_line,
        span.start_column,
        span.end_line,
        span.end_column,
    )


def _materialized_batch(
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
) -> runtime_probe_execution.RuntimeProbeExecutionInputBatch:
    """Return a materialized execution-input batch for validation tests."""
    return runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
        plan,
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision="runtime-probe-contract:test.1",
        runtime_assumptions=_runtime_assumptions(),
    )


def _runner_environment() -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return explicit environment fields for non-executing runner requests."""
    return (
        _field("python_version", "3.11"),
        _field("platform", "linux-x86_64"),
    )


def _runner_assumptions() -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return explicit assumption fields for non-executing runner requests."""
    return (
        _field("network", "disabled"),
        _field("filesystem_mode", "read_only_fixture"),
    )


def _runner_request_batch(
    input_batch: runtime_probe_execution.RuntimeProbeExecutionInputBatch,
) -> runtime_probe_execution.RuntimeProbeRunnerRequestBatch:
    """Return a runner-request batch for a materialized input batch."""
    return runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
        input_batch,
        runner_contract_revision="runtime-probe-runner:test.1",
        timeout_seconds=30,
        runner_environment=_runner_environment(),
        runner_assumptions=_runner_assumptions(),
    )


def _execution_attempt(
    input_item: runtime_probe_execution.RuntimeProbeExecutionInput,
    *,
    outcome: runtime_probe_results.RuntimeProbeResultOutcome = (
        runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    ),
    normalized_payload: tuple[runtime_probe_results.RuntimeProbeReplayField, ...] = (),
    durable_artifact_reference: str | None = None,
    failure_summary: str | None = None,
    failure_detail_fields: tuple[
        runtime_probe_results.RuntimeProbeReplayField, ...
    ] = (),
) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
    """Return one normalized executor-output attempt tied to an input item."""
    return runtime_probe_execution.RuntimeProbeExecutionAttempt(
        plan_id=input_item.plan_id,
        request_id=input_item.request_id,
        request=input_item.request,
        execution_input=input_item,
        outcome=outcome,
        normalized_payload=normalized_payload,
        durable_artifact_reference=durable_artifact_reference,
        failure_summary=failure_summary,
        failure_detail_fields=failure_detail_fields,
    )


def _assemble_result_batch(
    input_batch: runtime_probe_execution.RuntimeProbeExecutionInputBatch,
    attempts: tuple[runtime_probe_execution.RuntimeProbeExecutionAttempt, ...],
) -> runtime_probe_results.RuntimeProbeResultBatch:
    """Assemble execution attempts through the public module-local helper."""
    return assemble_runtime_probe_result_batch_from_execution_attempts(
        input_batch,
        attempts,
    )


def test_materialize_runtime_probe_execution_inputs_preserves_plan_order_and_replay(
    tmp_path: Path,
) -> None:
    """Materialized inputs are replay-ready work items for all current forms."""
    _write_runtime_probe_program(tmp_path)
    program = _derived_program(tmp_path)
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)
    requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    plan = runtime_probe_requests.build_runtime_probe_request_plan(requests)
    original_plan_requests = plan.requests
    original_plan_request_ids = plan.request_ids
    original_plan_id = plan.plan_id
    snapshot_basis = _snapshot_basis()
    assumptions = _runtime_assumptions()

    first_batch = (
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            plan,
            repository_snapshot_basis=snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=assumptions,
        )
    )
    second_batch = (
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            plan,
            repository_snapshot_basis=snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=assumptions,
        )
    )

    assert first_batch == second_batch
    assert first_batch.contract_version == "runtime_probe_execution_input_batch:v1"
    assert first_batch.plan_id == plan.plan_id
    assert first_batch.request_ids == plan.request_ids
    assert tuple(input_item.request for input_item in first_batch.inputs) == requests
    assert [input_item.request_id for input_item in first_batch.inputs] == list(
        plan.request_ids
    )
    assert {input_item.form_label for input_item in first_batch.inputs} == (
        _EXPECTED_CURRENT_FORMS
    )
    assert {input_item.family_label for input_item in first_batch.inputs} == set(
        runtime_probe_requests.RuntimeProbeFamily
    )

    for input_item, request, request_id in zip(
        first_batch.inputs,
        plan.requests,
        plan.request_ids,
        strict=True,
    ):
        replay_artifact = input_item.replay_artifact
        replay_inputs = replay_artifact.replay_inputs
        replay_input_values = {field.key: field.value for field in replay_inputs}
        span = request.source_site.span

        assert input_item.plan_id == plan.plan_id
        assert input_item.request_id == request_id
        assert input_item.request is request
        assert input_item.source_site_identity == _source_site_identity(request)
        assert input_item.family_label is request.family_label
        assert input_item.form_label == request.form_label
        assert input_item.replay_target_seed == request.replay_target_seed
        assert input_item.replay_selector_seed == request.replay_selector_seed
        assert replay_artifact.probe_identifier.startswith(
            "runtime_probe_execution_input:"
        )
        assert replay_artifact.probe_contract_revision == (
            "runtime-probe-contract:test.1"
        )
        assert replay_artifact.repository_snapshot_basis is snapshot_basis
        assert replay_artifact.replay_target == request.replay_target_seed
        assert replay_artifact.replay_selector == request.replay_selector_seed
        assert replay_artifact.runtime_assumptions == assumptions
        assert (
            tuple(field.key for field in replay_inputs) == _EXPECTED_REPLAY_INPUT_KEYS
        )
        assert len(replay_input_values) == len(_EXPECTED_REPLAY_INPUT_KEYS)
        assert replay_input_values["plan_id"] == plan.plan_id
        assert replay_input_values["request_id"] == request_id
        assert replay_input_values["subject_kind"] == request.subject_kind.value
        assert replay_input_values["subject_id"] == request.subject_id
        assert replay_input_values["source_site_id"] == request.source_site.site_id
        assert replay_input_values["source_file_path"] == request.source_site.file_path
        assert replay_input_values["source_start_line"] == str(span.start_line)
        assert replay_input_values["source_start_column"] == str(span.start_column)
        assert replay_input_values["source_end_line"] == str(span.end_line)
        assert replay_input_values["source_end_column"] == str(span.end_column)
        assert replay_input_values["reason_code"] == request.reason_code.value
        assert replay_input_values["boundary_text"] == request.boundary_text
        assert replay_input_values["family_label"] == request.family_label.value
        assert replay_input_values["form_label"] == request.form_label
        assert replay_input_values["replay_target_seed"] == request.replay_target_seed
        assert (
            replay_input_values["replay_selector_seed"] == request.replay_selector_seed
        )

    assert plan.requests == original_plan_requests
    assert plan.request_ids == original_plan_request_ids
    assert plan.plan_id == original_plan_id
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records


def test_materialize_runtime_probe_runner_requests_preserves_order_and_identities() -> (
    None
):
    """Runner handoff requests preserve the replay-ready execution inputs exactly."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    plan = _plan(first_request, second_request, third_request)
    input_batch = _materialized_batch(plan)
    original_inputs = input_batch.inputs
    runner_environment = _runner_environment()
    runner_assumptions = _runner_assumptions()

    first_batch = (
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )
    )
    second_batch = (
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )
    )

    assert first_batch == second_batch
    assert first_batch.contract_version == "runtime_probe_runner_request_batch:v1"
    assert first_batch.plan_id == input_batch.plan_id
    assert first_batch.request_ids == input_batch.request_ids
    assert first_batch.runner_contract_revision == "runtime-probe-runner:test.1"
    assert first_batch.timeout_seconds == 30
    assert first_batch.runner_environment == runner_environment
    assert first_batch.runner_assumptions == runner_assumptions
    assert input_batch.inputs is original_inputs
    assert (
        tuple(
            runner_request.execution_input
            for runner_request in first_batch.runner_requests
        )
        == input_batch.inputs
    )
    assert [
        runner_request.request_id for runner_request in first_batch.runner_requests
    ] == list(input_batch.request_ids)

    for runner_request, input_item in zip(
        first_batch.runner_requests,
        input_batch.inputs,
        strict=True,
    ):
        assert runner_request.plan_id == input_batch.plan_id
        assert runner_request.request_id == input_item.request_id
        assert runner_request.request is input_item.request
        assert runner_request.execution_input is input_item
        assert runner_request.replay_artifact is input_item.replay_artifact
        assert runner_request.runner_contract_revision == "runtime-probe-runner:test.1"
        assert runner_request.timeout_seconds == 30
        assert runner_request.runner_environment == runner_environment
        assert runner_request.runner_assumptions == runner_assumptions


def test_materialize_runtime_probe_runner_requests_supports_empty_input_batch() -> None:
    """Empty execution-input batches materialize to empty runner-request batches."""
    input_batch = _materialized_batch(
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )

    runner_batch = _runner_request_batch(input_batch)

    assert runner_batch.plan_id == input_batch.plan_id
    assert runner_batch.request_ids == ()
    assert runner_batch.runner_requests == ()


def test_materialize_runtime_probe_runner_requests_rejects_bad_runner_metadata() -> (
    None
):
    """Runner handoff metadata must be explicit, non-blank, and bounded."""
    input_batch = _materialized_batch(_plan(_request()))
    blank_environment = _field("platform", "linux-x86_64")
    object.__setattr__(blank_environment, "value", " ")
    blank_assumption = _field("network", "disabled")
    object.__setattr__(blank_assumption, "key", " ")

    with pytest.raises(ValueError, match="runner_contract_revision"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision=" ",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="timeout_seconds"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=0,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="runner_environment"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="runner_assumptions"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=(),
        )
    with pytest.raises(ValueError, match="runner_environment"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=(blank_environment,),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="runner_assumptions"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=(blank_assumption,),
        )


def test_materialize_runtime_probe_runner_requests_rejects_input_batch_drift() -> None:
    """Runner materialization revalidates execution-input batch completeness."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    drifted_batch = _materialized_batch(_plan(first_request, second_request))
    object.__setattr__(drifted_batch, "request_ids", ("runtime_probe:wrong",))
    duplicate_batch = _materialized_batch(_plan(first_request, second_request))
    object.__setattr__(
        duplicate_batch,
        "request_ids",
        (duplicate_batch.inputs[0].request_id, duplicate_batch.inputs[0].request_id),
    )
    object.__setattr__(
        duplicate_batch,
        "inputs",
        (duplicate_batch.inputs[0], duplicate_batch.inputs[0]),
    )

    with pytest.raises(ValueError, match="request_ids must match inputs"):
        _runner_request_batch(drifted_batch)
    with pytest.raises(ValueError, match="duplicate runtime probe execution"):
        _runner_request_batch(duplicate_batch)


def test_materialize_runtime_probe_runner_requests_rejects_blank_replay_tampering() -> (
    None
):
    """Runner handoff requests reject replay fields blanked after construction."""
    blank_replay_input_batch = _materialized_batch(_plan(_request(start_line=3)))
    blank_replay_input = blank_replay_input_batch.inputs[0]
    blank_replay_input_field = blank_replay_input.replay_artifact.replay_inputs[0]
    object.__setattr__(blank_replay_input_field, "value", " ")
    blank_assumption_batch = _materialized_batch(_plan(_request(start_line=4)))
    blank_assumption_input = blank_assumption_batch.inputs[0]
    blank_assumption_field = blank_assumption_input.replay_artifact.runtime_assumptions[
        0
    ]
    object.__setattr__(blank_assumption_field, "key", " ")

    with pytest.raises(ValueError, match="replay_inputs"):
        _runner_request_batch(blank_replay_input_batch)
    with pytest.raises(ValueError, match="runtime_assumptions"):
        _runner_request_batch(blank_assumption_batch)


def test_runtime_probe_runner_request_rejects_plan_input_and_replay_drift() -> None:
    """Runner requests must point at the exact input and replay artifact objects."""
    request = _request()
    plan = _plan(request)
    input_batch = _materialized_batch(plan)
    input_item = input_batch.inputs[0]
    equivalent_input = _materialized_batch(plan).inputs[0]

    with pytest.raises(ValueError, match="plan_id must match execution input"):
        runtime_probe_execution.RuntimeProbeRunnerRequest(
            plan_id="runtime_probe_request_plan:wrong",
            request_id=input_item.request_id,
            request=input_item.request,
            execution_input=input_item,
            replay_artifact=input_item.replay_artifact,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="request_id must match execution input"):
        runtime_probe_execution.RuntimeProbeRunnerRequest(
            plan_id=input_item.plan_id,
            request_id="runtime_probe:wrong",
            request=input_item.request,
            execution_input=input_item,
            replay_artifact=input_item.replay_artifact,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="request must be execution input request"):
        runtime_probe_execution.RuntimeProbeRunnerRequest(
            plan_id=input_item.plan_id,
            request_id=input_item.request_id,
            request=_request(start_line=8),
            execution_input=input_item,
            replay_artifact=input_item.replay_artifact,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="replay_artifact"):
        runtime_probe_execution.RuntimeProbeRunnerRequest(
            plan_id=input_item.plan_id,
            request_id=input_item.request_id,
            request=input_item.request,
            execution_input=equivalent_input,
            replay_artifact=input_item.replay_artifact,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )


def test_runtime_probe_runner_request_batch_rejects_order_and_duplicate_drift() -> None:
    """Runner-request batches reject plan, order, and duplicate identity drift."""
    input_batch = _materialized_batch(_plan(_request()))
    runner_request = _runner_request_batch(input_batch).runner_requests[0]

    with pytest.raises(ValueError, match="plan_id must match requests"):
        runtime_probe_execution.RuntimeProbeRunnerRequestBatch(
            plan_id="runtime_probe_request_plan:wrong",
            request_ids=(runner_request.request_id,),
            runner_requests=(runner_request,),
            runner_contract_revision=runner_request.runner_contract_revision,
            timeout_seconds=runner_request.timeout_seconds,
            runner_environment=runner_request.runner_environment,
            runner_assumptions=runner_request.runner_assumptions,
        )
    with pytest.raises(ValueError, match="request_ids must match requests"):
        runtime_probe_execution.RuntimeProbeRunnerRequestBatch(
            plan_id=runner_request.plan_id,
            request_ids=("runtime_probe:wrong",),
            runner_requests=(runner_request,),
            runner_contract_revision=runner_request.runner_contract_revision,
            timeout_seconds=runner_request.timeout_seconds,
            runner_environment=runner_request.runner_environment,
            runner_assumptions=runner_request.runner_assumptions,
        )
    with pytest.raises(ValueError, match="timeout_seconds must match requests"):
        runtime_probe_execution.RuntimeProbeRunnerRequestBatch(
            plan_id=runner_request.plan_id,
            request_ids=(runner_request.request_id,),
            runner_requests=(runner_request,),
            runner_contract_revision=runner_request.runner_contract_revision,
            timeout_seconds=runner_request.timeout_seconds + 1,
            runner_environment=runner_request.runner_environment,
            runner_assumptions=runner_request.runner_assumptions,
        )
    with pytest.raises(ValueError, match="duplicate runtime probe runner request_id"):
        runtime_probe_execution.RuntimeProbeRunnerRequestBatch(
            plan_id=runner_request.plan_id,
            request_ids=(runner_request.request_id, runner_request.request_id),
            runner_requests=(runner_request, runner_request),
            runner_contract_revision=runner_request.runner_contract_revision,
            timeout_seconds=runner_request.timeout_seconds,
            runner_environment=runner_request.runner_environment,
            runner_assumptions=runner_request.runner_assumptions,
        )


def test_assemble_runtime_probe_result_batch_preserves_order_and_identities() -> None:
    """Complete attempts become results in input-batch order without mutation."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    plan = _plan(first_request, second_request, third_request)
    batch = _materialized_batch(plan)
    original_batch_inputs = batch.inputs
    first_payload = (_field("observed_module", "plugins.weather"),)
    first_attempt = _execution_attempt(
        batch.inputs[0],
        normalized_payload=first_payload,
    )
    second_attempt = _execution_attempt(
        batch.inputs[1],
        durable_artifact_reference=(
            "artifact://runtime-probe-results/dynamic-import/main-run.json"
        ),
    )
    third_attempt = _execution_attempt(
        batch.inputs[2],
        outcome=runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        failure_summary="probe exceeded timeout",
        failure_detail_fields=(_field("timeout_seconds", "30"),),
    )

    result_batch = _assemble_result_batch(
        batch,
        (third_attempt, second_attempt, first_attempt),
    )

    assert result_batch.plan_id == batch.plan_id
    assert tuple(result.request_id for result in result_batch.results) == (
        batch.request_ids
    )
    assert batch.inputs == original_batch_inputs
    assert first_attempt.execution_input is batch.inputs[0]
    assert second_attempt.execution_input is batch.inputs[1]
    assert third_attempt.execution_input is batch.inputs[2]

    first_result = result_batch.results[0]
    assert isinstance(first_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert first_result.plan_id == batch.plan_id
    assert first_result.request_id == batch.inputs[0].request_id
    assert first_result.request is batch.inputs[0].request
    assert first_result.replay_artifact is batch.inputs[0].replay_artifact
    assert first_result.normalized_payload == first_payload
    assert first_result.durable_artifact_reference is None
    assert first_result.is_admissible_runtime_backed_proof is True

    second_result = result_batch.results[1]
    assert isinstance(second_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert second_result.request is batch.inputs[1].request
    assert second_result.replay_artifact is batch.inputs[1].replay_artifact
    assert second_result.normalized_payload == ()
    assert second_result.durable_artifact_reference == (
        "artifact://runtime-probe-results/dynamic-import/main-run.json"
    )
    assert second_result.is_admissible_runtime_backed_proof is True

    third_result = result_batch.results[2]
    assert isinstance(third_result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert third_result.request is batch.inputs[2].request
    assert third_result.replay_artifact is batch.inputs[2].replay_artifact
    assert (
        third_result.outcome
        is runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT
    )
    assert third_result.failure_summary == "probe exceeded timeout"
    assert third_result.failure_detail_fields == (_field("timeout_seconds", "30"),)
    assert third_result.is_admissible_runtime_backed_proof is False


@pytest.mark.parametrize(
    "outcome",
    (
        runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        runtime_probe_results.RuntimeProbeResultOutcome.MISSING_ENVIRONMENT,
        runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
    ),
)
def test_assemble_runtime_probe_result_batch_preserves_all_non_proof_outcomes(
    outcome: runtime_probe_results.RuntimeProbeResultOutcome,
) -> None:
    """Every failed execution outcome remains non-proof in result assembly."""
    request = _request()
    batch = _materialized_batch(_plan(request))
    attempt = _execution_attempt(
        batch.inputs[0],
        outcome=outcome,
        failure_summary=f"runner reported {outcome.value}",
    )

    result_batch = _assemble_result_batch(
        batch,
        (attempt,),
    )

    result = result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert result.outcome is outcome
    assert result.is_admissible_runtime_backed_proof is False


def test_assemble_runtime_probe_result_batch_supports_empty_input_batch() -> None:
    """Empty input batches assemble deterministically into empty result batches."""
    empty_plan = runtime_probe_requests.build_runtime_probe_request_plan(())
    batch = _materialized_batch(empty_plan)

    result_batch = _assemble_result_batch(
        batch,
        (),
    )

    assert result_batch.plan_id == batch.plan_id
    assert result_batch.results == ()


def test_assemble_runtime_probe_result_batch_rejects_incomplete_attempt_sets() -> None:
    """Attempt assembly requires exactly one attempt for every batch input."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    batch = _materialized_batch(_plan(first_request, second_request))
    planned_attempt = _execution_attempt(
        batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    duplicate_attempt = _execution_attempt(
        batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.forecast"),),
    )
    unplanned_batch = _materialized_batch(_plan(_request(start_line=8)))
    unplanned_attempt = _execution_attempt(
        unplanned_batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.unplanned"),),
    )

    with pytest.raises(ValueError, match="missing runtime probe execution attempt"):
        _assemble_result_batch(
            batch,
            (planned_attempt,),
        )
    with pytest.raises(ValueError, match="duplicate runtime probe execution attempt"):
        _assemble_result_batch(
            batch,
            (planned_attempt, duplicate_attempt),
        )
    with pytest.raises(ValueError, match="not present in input batch"):
        _assemble_result_batch(
            batch,
            (planned_attempt, unplanned_attempt),
        )


def test_assemble_runtime_probe_result_batch_rejects_plan_and_input_drift() -> None:
    """Attempts must point at the exact planned batch input object."""
    request = _request()
    plan = _plan(request)
    batch = _materialized_batch(plan)
    equivalent_batch = _materialized_batch(plan)
    wrong_input_attempt = _execution_attempt(
        equivalent_batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    drifted_attempt = _execution_attempt(
        batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(drifted_attempt, "plan_id", "runtime_probe_request_plan:wrong")

    with pytest.raises(ValueError, match="planned batch input"):
        _assemble_result_batch(
            batch,
            (wrong_input_attempt,),
        )
    with pytest.raises(ValueError, match="plan_id must match input batch"):
        _assemble_result_batch(
            batch,
            (drifted_attempt,),
        )


def test_runtime_probe_execution_attempt_rejects_plan_input_drift() -> None:
    """Attempt records cannot drift from the execution input they cite."""
    request = _request()
    batch = _materialized_batch(_plan(request))
    input_item = batch.inputs[0]

    with pytest.raises(ValueError, match="plan_id must match execution input"):
        runtime_probe_execution.RuntimeProbeExecutionAttempt(
            plan_id="runtime_probe_request_plan:wrong",
            request_id=input_item.request_id,
            request=input_item.request,
            execution_input=input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )
    with pytest.raises(ValueError, match="request_id must match execution input"):
        runtime_probe_execution.RuntimeProbeExecutionAttempt(
            plan_id=input_item.plan_id,
            request_id="runtime_probe:wrong",
            request=input_item.request,
            execution_input=input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )
    with pytest.raises(ValueError, match="request must be execution input request"):
        runtime_probe_execution.RuntimeProbeExecutionAttempt(
            plan_id=input_item.plan_id,
            request_id=input_item.request_id,
            request=_request(start_line=8),
            execution_input=input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )


def test_runtime_probe_execution_attempt_rejects_observed_failure_metadata() -> None:
    """Observed attempts need proof metadata and cannot carry failure-only fields."""
    request = _request()
    input_item = _materialized_batch(_plan(request)).inputs[0]

    with pytest.raises(ValueError, match="cannot carry failure metadata"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
            failure_summary="runner crashed after observing payload",
        )
    with pytest.raises(ValueError, match="normalized_payload or durable"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            failure_summary=None,
        )


def test_runtime_probe_execution_attempt_rejects_failure_without_summary() -> None:
    """Failure outcomes need a concrete failure summary and cannot carry proof."""
    request = _request()
    input_item = _materialized_batch(_plan(request)).inputs[0]

    with pytest.raises(ValueError, match="failure_summary"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        )
    with pytest.raises(ValueError, match="failure_summary"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
            failure_summary=" ",
        )
    with pytest.raises(ValueError, match="cannot carry proof metadata"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
            failure_summary="runner crashed",
        )


def test_runtime_probe_execution_attempt_rejects_blank_references_and_details() -> None:
    """Attempt metadata rejects blank durable references and tampered detail fields."""
    request = _request()
    input_item = _materialized_batch(_plan(request)).inputs[0]
    blank_detail = _field("exit_code", "1")
    object.__setattr__(blank_detail, "value", " ")

    with pytest.raises(ValueError, match="durable_artifact_reference"):
        _execution_attempt(
            input_item,
            durable_artifact_reference=" ",
        )
    with pytest.raises(ValueError, match="failure_detail_fields"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
            failure_summary="runner crashed",
            failure_detail_fields=(blank_detail,),
        )


def test_materialize_runtime_probe_execution_inputs_supports_empty_plan() -> None:
    """Empty request plans materialize to empty ordered input batches."""
    plan = runtime_probe_requests.build_runtime_probe_request_plan(())

    batch = _materialized_batch(plan)

    assert batch.plan_id == plan.plan_id
    assert batch.request_ids == ()
    assert batch.inputs == ()


def test_materialize_runtime_probe_execution_inputs_rejects_empty_assumptions() -> None:
    """Execution inputs must carry explicit runtime assumptions."""
    request = _request()
    plan = _plan(request)

    with pytest.raises(ValueError, match="runtime_assumptions"):
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            plan,
            repository_snapshot_basis=_snapshot_basis(),
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=(),
        )


def test_materialize_runtime_probe_execution_inputs_rejects_blank_probe_metadata() -> (
    None
):
    """Execution inputs reject blank probe contract metadata."""
    request = _request()
    plan = _plan(request)
    empty_plan = runtime_probe_requests.build_runtime_probe_request_plan(())

    with pytest.raises(ValueError, match="probe_contract_revision"):
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            plan,
            repository_snapshot_basis=_snapshot_basis(),
            probe_contract_revision=" ",
            runtime_assumptions=_runtime_assumptions(),
        )
    with pytest.raises(ValueError, match="probe_contract_revision"):
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            empty_plan,
            repository_snapshot_basis=_snapshot_basis(),
            probe_contract_revision=" ",
            runtime_assumptions=_runtime_assumptions(),
        )


def test_materialize_runtime_probe_execution_inputs_rejects_plan_request_drift() -> (
    None
):
    """Materialization revalidates request-plan envelopes before building inputs."""
    request = _request()
    plan = _plan(request)
    object.__setattr__(plan, "request_ids", ("runtime_probe:wrong",))

    with pytest.raises(ValueError, match="request_ids must match requests"):
        _materialized_batch(plan)


def test_materialize_runtime_probe_execution_inputs_rejects_duplicate_request_ids() -> (
    None
):
    """Materialization refuses tampered plans with duplicate request identities."""
    request = _request()
    plan = _plan(request)
    object.__setattr__(plan, "requests", (request, request))
    object.__setattr__(plan, "request_ids", (request.request_id, request.request_id))

    with pytest.raises(ValueError, match="duplicate runtime probe request_id"):
        _materialized_batch(plan)


def test_runtime_probe_execution_input_rejects_request_identity_drift() -> None:
    """A work item cannot carry a request ID that differs from its request object."""
    request = _request()
    plan = _plan(request)
    input_item = _materialized_batch(plan).inputs[0]

    with pytest.raises(ValueError, match="request_id must match request.request_id"):
        runtime_probe_execution.RuntimeProbeExecutionInput(
            plan_id=input_item.plan_id,
            request_id="runtime_probe:wrong",
            request=request,
            source_site_identity=input_item.source_site_identity,
            family_label=input_item.family_label,
            form_label=input_item.form_label,
            replay_target_seed=input_item.replay_target_seed,
            replay_selector_seed=input_item.replay_selector_seed,
            replay_artifact=input_item.replay_artifact,
        )


def test_runtime_probe_execution_input_rejects_replay_metadata_drift() -> None:
    """Replay artifacts must retain the planned request identity fields."""
    request = _request()
    plan = _plan(request)
    input_item = _materialized_batch(plan).inputs[0]
    replay_artifact = input_item.replay_artifact
    drifted_replay_artifact = runtime_probe_results.RuntimeProbeReplayArtifact(
        probe_identifier=replay_artifact.probe_identifier,
        probe_contract_revision=replay_artifact.probe_contract_revision,
        repository_snapshot_basis=replay_artifact.repository_snapshot_basis,
        replay_target="other.target",
        replay_selector=replay_artifact.replay_selector,
        replay_inputs=replay_artifact.replay_inputs,
        runtime_assumptions=replay_artifact.runtime_assumptions,
    )

    with pytest.raises(ValueError, match="replay_artifact target"):
        runtime_probe_execution.RuntimeProbeExecutionInput(
            plan_id=input_item.plan_id,
            request_id=input_item.request_id,
            request=request,
            source_site_identity=input_item.source_site_identity,
            family_label=input_item.family_label,
            form_label=input_item.form_label,
            replay_target_seed=input_item.replay_target_seed,
            replay_selector_seed=input_item.replay_selector_seed,
            replay_artifact=drifted_replay_artifact,
        )


def test_runtime_probe_execution_input_batch_rejects_input_plan_mismatch() -> None:
    """Ordered batches reject plan, request-order, and duplicate-input drift."""
    request = _request()
    plan = _plan(request)
    input_item = _materialized_batch(plan).inputs[0]

    with pytest.raises(ValueError, match="plan_id must match inputs"):
        runtime_probe_execution.RuntimeProbeExecutionInputBatch(
            plan_id="runtime_probe_request_plan:other",
            request_ids=(input_item.request_id,),
            inputs=(input_item,),
        )

    with pytest.raises(ValueError, match="request_ids must match inputs"):
        runtime_probe_execution.RuntimeProbeExecutionInputBatch(
            plan_id=input_item.plan_id,
            request_ids=("runtime_probe:wrong",),
            inputs=(input_item,),
        )

    with pytest.raises(ValueError, match="duplicate runtime probe execution"):
        runtime_probe_execution.RuntimeProbeExecutionInputBatch(
            plan_id=input_item.plan_id,
            request_ids=(input_item.request_id, input_item.request_id),
            inputs=(input_item, input_item),
        )


def test_runtime_probe_execution_contracts_are_frozen_and_module_local() -> None:
    """Execution records stay frozen and absent from package-root exports."""
    request = _request()
    plan = _plan(request)
    input_item = _materialized_batch(plan).inputs[0]
    runner_batch = _runner_request_batch(_materialized_batch(plan))
    runner_request = runner_batch.runner_requests[0]
    attempt = _execution_attempt(
        input_item,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )

    with pytest.raises(FrozenInstanceError):
        input_item.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        runner_request.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        runner_batch.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        attempt.plan_id = "runtime_probe_request_plan:mutated"

    assert "RuntimeProbeExecutionAttempt" in runtime_probe_execution.__all__
    assert "RuntimeProbeExecutionInput" in runtime_probe_execution.__all__
    assert "RuntimeProbeExecutionInputBatch" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerRequest" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerRequestBatch" in runtime_probe_execution.__all__
    assert "assemble_runtime_probe_result_batch_from_execution_attempts" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_execution_input_batch" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_runner_request_batch" in (
        runtime_probe_execution.__all__
    )
    assert "RuntimeProbeExecutionAttempt" not in context_ir.__all__
    assert "RuntimeProbeExecutionInput" not in context_ir.__all__
    assert "RuntimeProbeExecutionInputBatch" not in context_ir.__all__
    assert "RuntimeProbeRunnerRequest" not in context_ir.__all__
    assert "RuntimeProbeRunnerRequestBatch" not in context_ir.__all__
    assert "assemble_runtime_probe_result_batch_from_execution_attempts" not in (
        context_ir.__all__
    )
    assert "materialize_runtime_probe_execution_input_batch" not in context_ir.__all__
    assert "materialize_runtime_probe_runner_request_batch" not in context_ir.__all__
    assert not hasattr(context_ir, "RuntimeProbeExecutionAttempt")
    assert not hasattr(context_ir, "RuntimeProbeExecutionInput")
    assert not hasattr(context_ir, "RuntimeProbeExecutionInputBatch")
    assert not hasattr(context_ir, "RuntimeProbeRunnerRequest")
    assert not hasattr(context_ir, "RuntimeProbeRunnerRequestBatch")
    assert not hasattr(
        context_ir,
        "assemble_runtime_probe_result_batch_from_execution_attempts",
    )
    assert not hasattr(context_ir, "materialize_runtime_probe_execution_input_batch")
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_runner_request_batch",
    )

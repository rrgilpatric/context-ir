"""Tests for internal runtime probe execution input materialization."""

from __future__ import annotations

import os
import subprocess
import textwrap
from dataclasses import FrozenInstanceError, replace
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
    assemble_runtime_probe_result_batch_from_runner_request_attempts,
    collect_runtime_probe_execution_attempts_from_runner_requests,
    execute_runtime_probe_local_python_subprocess_invocation,
    materialize_runtime_probe_local_python_process_completion,
    materialize_runtime_probe_local_python_process_completion_attempt,
    materialize_runtime_probe_local_python_subprocess_exception_attempt,
    materialize_runtime_probe_local_python_subprocess_invocation,
)
from context_ir.semantic_types import (
    CapabilityTier,
    RepositorySnapshotBasis,
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


def _local_python_runner_environment() -> tuple[
    runtime_probe_results.RuntimeProbeReplayField,
    ...,
]:
    """Return local-Python environment fields for context derivation tests."""
    return (
        _field("python_version", "3.11"),
        _field("repository_root", "/workspace/context-ir"),
        _field("platform", "linux-x86_64"),
        _field("python_path_entry", "/workspace/context-ir/src"),
        _field("working_directory", "/workspace/context-ir"),
        _field("python_path_entry", "/workspace/context-ir/tests/fixtures"),
        _field("python_path_entry", "/opt/context-ir/support"),
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


def _local_python_runner_request(
    runner_environment: tuple[
        runtime_probe_results.RuntimeProbeReplayField,
        ...,
    ]
    | None = None,
    *,
    timeout_seconds: int = 30,
) -> runtime_probe_execution.RuntimeProbeRunnerRequest:
    """Return one runner request carrying local-Python environment metadata."""
    runner_batch = (
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            _materialized_batch(_plan(_request())),
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=timeout_seconds,
            runner_environment=(
                _local_python_runner_environment()
                if runner_environment is None
                else runner_environment
            ),
            runner_assumptions=_runner_assumptions(),
        )
    )
    return runner_batch.runner_requests[0]


def _local_python_subprocess_invocation(
    runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest | None = None,
    *,
    python_executable: str = "/workspace/context-ir/.venv/bin/python",
    module_name: str = "context_ir.runtime_probe_worker",
    module_argv: tuple[str, ...] = ("--request", "runtime-probe-request.json"),
    invocation_contract_revision: str = "runtime-probe-local-python-subprocess:test.1",
) -> runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation:
    """Return one frozen, non-executing local-Python subprocess invocation."""
    selected_runner_request = (
        _local_python_runner_request() if runner_request is None else runner_request
    )
    return materialize_runtime_probe_local_python_subprocess_invocation(
        selected_runner_request,
        python_executable=python_executable,
        module_name=module_name,
        invocation_contract_revision=invocation_contract_revision,
        module_argv=module_argv,
    )


def _local_python_process_completion(
    invocation: runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation
    | None = None,
    *,
    returncode: int = 0,
    stdout_text: str = '{"status":"ok"}\n',
    stderr_text: str = "",
    completion_contract_revision: str = (
        "runtime-probe-local-python-process-completion:test.1"
    ),
) -> runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion:
    """Return one frozen raw local-Python process completion."""
    selected_invocation = (
        _local_python_subprocess_invocation() if invocation is None else invocation
    )
    return materialize_runtime_probe_local_python_process_completion(
        selected_invocation,
        returncode=returncode,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        completion_contract_revision=completion_contract_revision,
    )


def _diagnostic_for_plan(
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
) -> SemanticDiagnosticResult:
    """Return a diagnostic with the supplied runtime request plan attached."""
    boundaries = tuple(
        SemanticDiagnosticBoundary(
            unit_id=request.subject_id,
            status=SemanticDiagnosticUnitStatus.OMITTED,
            boundary_kind=(
                SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
            ),
            primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            has_attached_runtime_provenance=False,
        )
        for request in plan.requests
    )
    planned_subject_ids = tuple(request.subject_id for request in plan.requests)
    return SemanticDiagnosticResult(
        grounded_unit_ids=planned_subject_ids,
        omitted_unit_ids=planned_subject_ids,
        too_shallow_unit_ids=(),
        sufficiently_represented_unit_ids=(),
        recommended_expansions=(),
        reason="Test diagnostic with an attached runtime request plan.",
        boundary_classifications=boundaries,
        planned_runtime_probe_requests=plan.requests,
        planned_runtime_probe_request_plan=plan,
    )


def _prepare_runner_requests(
    diagnostic: SemanticDiagnosticResult,
    *,
    probe_contract_revision: str = "runtime-probe-contract:test.1",
    runtime_assumptions: tuple[
        runtime_probe_results.RuntimeProbeReplayField,
        ...,
    ]
    | None = None,
    runner_contract_revision: str = "runtime-probe-runner:test.1",
    timeout_seconds: int = 30,
    runner_environment: tuple[
        runtime_probe_results.RuntimeProbeReplayField,
        ...,
    ]
    | None = None,
    runner_assumptions: tuple[
        runtime_probe_results.RuntimeProbeReplayField,
        ...,
    ]
    | None = None,
) -> runtime_probe_execution.RuntimeProbeDiagnosticRunnerRequestPreparation:
    """Prepare the diagnostic-gated runner request boundary for tests."""
    return runtime_probe_execution.prepare_runtime_probe_runner_requests_for_diagnostic(
        diagnostic,
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision=probe_contract_revision,
        runtime_assumptions=(
            _runtime_assumptions()
            if runtime_assumptions is None
            else runtime_assumptions
        ),
        runner_contract_revision=runner_contract_revision,
        timeout_seconds=timeout_seconds,
        runner_environment=(
            _runner_environment() if runner_environment is None else runner_environment
        ),
        runner_assumptions=(
            _runner_assumptions() if runner_assumptions is None else runner_assumptions
        ),
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


def _assemble_runner_request_result_batch(
    runner_request_batch: runtime_probe_execution.RuntimeProbeRunnerRequestBatch,
    attempts: tuple[runtime_probe_execution.RuntimeProbeExecutionAttempt, ...],
) -> runtime_probe_results.RuntimeProbeResultBatch:
    """Assemble attempts through the runner-request gate."""
    return assemble_runtime_probe_result_batch_from_runner_request_attempts(
        runner_request_batch,
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


def test_derive_local_python_environment_context_preserves_runner_metadata() -> None:
    """Local-Python context derivation preserves path order and replay metadata."""
    runner_request = _local_python_runner_request()

    context = (
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )
    )

    assert isinstance(
        context,
        runtime_probe_execution.RuntimeProbeLocalPythonEnvironmentContext,
    )
    assert context.repository_root == "/workspace/context-ir"
    assert context.working_directory == "/workspace/context-ir"
    assert context.python_path_entries == (
        "/workspace/context-ir/src",
        "/workspace/context-ir/tests/fixtures",
        "/opt/context-ir/support",
    )
    assert context.runner_contract_revision == (runner_request.runner_contract_revision)
    assert context.timeout_seconds == runner_request.timeout_seconds
    assert context.runner_environment is runner_request.runner_environment
    assert context.runner_assumptions is runner_request.runner_assumptions

    with pytest.raises(FrozenInstanceError):
        context.repository_root = "/tmp/context-ir"


def test_derive_local_python_environment_context_revalidates_runner_request() -> None:
    """Context derivation rejects runner requests that drift after construction."""
    runner_request = _local_python_runner_request()
    object.__setattr__(runner_request, "request_id", "runtime_probe:wrong")

    with pytest.raises(ValueError, match="request_id must match execution input"):
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )


def test_materialize_local_python_subprocess_invocation_is_deterministic() -> None:
    """Local-Python subprocess contracts are frozen execution-free request specs."""
    runner_request = _local_python_runner_request()
    module_argv = (
        "--plan-id",
        runner_request.plan_id,
        "--request-id",
        runner_request.request_id,
    )

    first_invocation = _local_python_subprocess_invocation(
        runner_request,
        module_argv=module_argv,
    )
    second_invocation = _local_python_subprocess_invocation(
        runner_request,
        module_argv=module_argv,
    )

    assert first_invocation == second_invocation
    assert isinstance(
        first_invocation,
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation,
    )
    assert first_invocation.runner_request is runner_request
    assert first_invocation.environment_context == (
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )
    )
    assert first_invocation.python_executable == (
        "/workspace/context-ir/.venv/bin/python"
    )
    assert first_invocation.argv == (
        "/workspace/context-ir/.venv/bin/python",
        "-m",
        "context_ir.runtime_probe_worker",
        "--plan-id",
        runner_request.plan_id,
        "--request-id",
        runner_request.request_id,
    )
    assert first_invocation.working_directory == "/workspace/context-ir"
    assert first_invocation.python_path_entries == (
        "/workspace/context-ir/src",
        "/workspace/context-ir/tests/fixtures",
        "/opt/context-ir/support",
    )
    assert first_invocation.timeout_seconds == runner_request.timeout_seconds
    assert first_invocation.invocation_contract_revision == (
        "runtime-probe-local-python-subprocess:test.1"
    )
    assert first_invocation.request_replay_payload_fields is (
        runner_request.replay_artifact.replay_inputs
    )
    assert (
        tuple(field.key for field in first_invocation.request_replay_payload_fields)
        == _EXPECTED_REPLAY_INPUT_KEYS
    )

    with pytest.raises(FrozenInstanceError):
        first_invocation.python_executable = "/tmp/python"


def test_materialize_local_python_subprocess_invocation_revalidates_runner() -> None:
    """Invocation materialization rejects runner requests that drifted in memory."""
    runner_request = _local_python_runner_request()
    object.__setattr__(runner_request, "request_id", "runtime_probe:wrong")

    with pytest.raises(ValueError, match="request_id must match execution input"):
        _local_python_subprocess_invocation(runner_request)


@pytest.mark.parametrize(
    ("python_executable", "error_match"),
    (
        ("workspace/context-ir/.venv/bin/python", "python_executable.*absolute"),
        (" /workspace/context-ir/.venv/bin/python", "python_executable.*malformed"),
        ("/workspace/context-ir/.venv/bin/python\nbad", "python_executable.*malformed"),
    ),
)
def test_materialize_local_python_subprocess_invocation_rejects_bad_executable(
    python_executable: str,
    error_match: str,
) -> None:
    """Python executable metadata must be absolute and shell-token safe."""
    with pytest.raises(ValueError, match=error_match):
        _local_python_subprocess_invocation(
            python_executable=python_executable,
        )


@pytest.mark.parametrize(
    ("module_name", "module_argv", "error_match"),
    (
        (" ", (), "module name"),
        (" context_ir.worker", (), "module name is malformed"),
        ("context_ir.runtime-probe-worker", (), "dotted identifier"),
        ("context_ir.worker", ("",), "module_argv"),
        ("context_ir.worker", ("--payload\nbad",), "module_argv.*malformed"),
    ),
)
def test_materialize_local_python_subprocess_invocation_rejects_bad_module_or_argv(
    module_name: str,
    module_argv: tuple[str, ...],
    error_match: str,
) -> None:
    """Module names and argv tokens are validated before any future execution."""
    with pytest.raises(ValueError, match=error_match):
        _local_python_subprocess_invocation(
            module_name=module_name,
            module_argv=module_argv,
        )


@pytest.mark.parametrize(
    "invocation_contract_revision",
    ("", " \t\n"),
)
def test_materialize_local_python_subprocess_invocation_rejects_blank_revision(
    invocation_contract_revision: str,
) -> None:
    """Invocation materialization rejects blank contract revisions."""
    with pytest.raises(ValueError, match="invocation_contract_revision"):
        _local_python_subprocess_invocation(
            invocation_contract_revision=invocation_contract_revision,
        )


def test_local_python_subprocess_invocation_preserves_path_order_and_timeout() -> None:
    """Invocation contracts keep Python path ordering and timeout metadata intact."""
    runner_request = _local_python_runner_request(timeout_seconds=47)

    invocation = _local_python_subprocess_invocation(runner_request)

    assert invocation.python_path_entries == (
        "/workspace/context-ir/src",
        "/workspace/context-ir/tests/fixtures",
        "/opt/context-ir/support",
    )
    assert invocation.timeout_seconds == 47
    assert invocation.timeout_seconds == invocation.environment_context.timeout_seconds


def test_local_python_subprocess_invocation_rejects_contract_drift() -> None:
    """The frozen invocation type revalidates path, argv, and replay identities."""
    invocation = _local_python_subprocess_invocation()
    other_runner_request = _local_python_runner_request(
        runner_environment=(
            _field("python_version", "3.11"),
            _field("repository_root", "/workspace/context-ir"),
            _field("platform", "linux-x86_64"),
            _field("python_path_entry", "/workspace/context-ir/src"),
            _field("working_directory", "/workspace/other"),
        )
    )
    other_context = (
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            other_runner_request
        )
    )

    with pytest.raises(ValueError, match="environment_context"):
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation(
            runner_request=invocation.runner_request,
            environment_context=other_context,
            python_executable=invocation.python_executable,
            argv=invocation.argv,
            working_directory=invocation.working_directory,
            python_path_entries=invocation.python_path_entries,
            timeout_seconds=invocation.timeout_seconds,
            invocation_contract_revision=invocation.invocation_contract_revision,
            request_replay_payload_fields=invocation.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="argv executable"):
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation(
            runner_request=invocation.runner_request,
            environment_context=invocation.environment_context,
            python_executable=invocation.python_executable,
            argv=("/workspace/other/python", *invocation.argv[1:]),
            working_directory=invocation.working_directory,
            python_path_entries=invocation.python_path_entries,
            timeout_seconds=invocation.timeout_seconds,
            invocation_contract_revision=invocation.invocation_contract_revision,
            request_replay_payload_fields=invocation.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="replay payload fields"):
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation(
            runner_request=invocation.runner_request,
            environment_context=invocation.environment_context,
            python_executable=invocation.python_executable,
            argv=invocation.argv,
            working_directory=invocation.working_directory,
            python_path_entries=invocation.python_path_entries,
            timeout_seconds=invocation.timeout_seconds,
            invocation_contract_revision=invocation.invocation_contract_revision,
            request_replay_payload_fields=(
                _field("plan_id", invocation.runner_request.plan_id),
            ),
        )


def test_materialize_local_python_process_completion_preserves_raw_fields() -> None:
    """Raw local-Python process completions preserve process fields verbatim."""
    runner_request = _local_python_runner_request(timeout_seconds=47)
    module_argv = (
        "--plan-id",
        runner_request.plan_id,
        "--request-id",
        runner_request.request_id,
    )
    invocation = _local_python_subprocess_invocation(
        runner_request,
        module_argv=module_argv,
    )

    first_completion = _local_python_process_completion(
        invocation,
        returncode=17,
        stdout_text="",
        stderr_text="warning: fixture used\nline 2\n",
    )
    second_completion = _local_python_process_completion(
        invocation,
        returncode=17,
        stdout_text="",
        stderr_text="warning: fixture used\nline 2\n",
    )

    assert first_completion == second_completion
    assert isinstance(
        first_completion,
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion,
    )
    assert first_completion.invocation is invocation
    assert first_completion.invocation_identity.startswith(
        "runtime_probe_local_python_subprocess_invocation:"
    )
    assert first_completion.argv is invocation.argv
    assert first_completion.working_directory == invocation.working_directory
    assert first_completion.python_path_entries is invocation.python_path_entries
    assert first_completion.timeout_seconds == 47
    assert first_completion.returncode == 17
    assert first_completion.stdout_text == ""
    assert first_completion.stderr_text == "warning: fixture used\nline 2\n"
    assert first_completion.completion_contract_revision == (
        "runtime-probe-local-python-process-completion:test.1"
    )
    assert first_completion.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )

    with pytest.raises(FrozenInstanceError):
        first_completion.returncode = 0


def test_materialize_local_python_process_completion_revalidates_invocation() -> None:
    """Completion materialization rejects invocation contracts drifted in memory."""
    argv_drifted_invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        argv_drifted_invocation,
        "argv",
        ("/workspace/other/python", *argv_drifted_invocation.argv[1:]),
    )
    request_drifted_invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        request_drifted_invocation.runner_request,
        "request_id",
        "runtime_probe:wrong",
    )

    with pytest.raises(ValueError, match="argv executable"):
        _local_python_process_completion(argv_drifted_invocation)
    with pytest.raises(ValueError, match="request_id must match execution input"):
        _local_python_process_completion(request_drifted_invocation)


def test_execute_local_python_subprocess_invocation_preserves_raw_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The execution boundary captures raw process fields without interpretation."""
    invocation = _local_python_subprocess_invocation()
    monkeypatch.setenv("CONTEXT_IR_RUNTIME_PROBE_TEST", "ambient-preserved")
    monkeypatch.setenv("PYTHONPATH", "/ambient/path")
    calls: list[dict[str, object]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(
            {
                "args": args,
                "cwd": cwd,
                "env": env,
                "timeout": timeout,
                "shell": shell,
                "capture_output": capture_output,
                "text": text,
                "check": check,
            }
        )
        return subprocess.CompletedProcess(
            args=args,
            returncode=23,
            stdout="raw stdout\n",
            stderr="raw stderr\n",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    completion = execute_runtime_probe_local_python_subprocess_invocation(
        invocation,
        completion_contract_revision=(
            "runtime-probe-local-python-process-completion:test.1"
        ),
    )

    assert len(calls) == 1
    call = calls[0]
    child_environment = call["env"]
    assert call["args"] is invocation.argv
    assert call["cwd"] == invocation.working_directory
    assert call["timeout"] == invocation.timeout_seconds
    assert call["shell"] is False
    assert call["capture_output"] is True
    assert call["text"] is True
    assert call["check"] is False
    assert isinstance(child_environment, dict)
    assert child_environment is not os.environ
    assert child_environment["CONTEXT_IR_RUNTIME_PROBE_TEST"] == "ambient-preserved"
    assert child_environment["PYTHONPATH"] == os.pathsep.join(
        invocation.python_path_entries
    )
    assert os.environ["PYTHONPATH"] == "/ambient/path"
    assert completion == _local_python_process_completion(
        invocation,
        returncode=23,
        stdout_text="raw stdout\n",
        stderr_text="raw stderr\n",
    )


def test_execute_local_python_subprocess_invocation_revalidates_before_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invocation drift is rejected before reaching the subprocess boundary."""
    invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        invocation,
        "argv",
        ("/workspace/other/python", *invocation.argv[1:]),
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, timeout, shell, capture_output, text, check
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="argv executable"):
        execute_runtime_probe_local_python_subprocess_invocation(
            invocation,
            completion_contract_revision=(
                "runtime-probe-local-python-process-completion:test.1"
            ),
        )

    assert calls == []


@pytest.mark.parametrize(
    ("completion_contract_revision", "error_match"),
    (
        ("", "completion_contract_revision"),
        (
            " runtime-probe-local-python-process-completion:test.1",
            "completion_contract_revision.*malformed",
        ),
    ),
)
def test_execute_subprocess_rejects_bad_completion_revision_before_run(
    monkeypatch: pytest.MonkeyPatch,
    completion_contract_revision: str,
    error_match: str,
) -> None:
    """Completion revision metadata is validated before subprocess execution."""
    invocation = _local_python_subprocess_invocation()
    calls: list[tuple[str, ...]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, timeout, shell, capture_output, text, check
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match=error_match):
        execute_runtime_probe_local_python_subprocess_invocation(
            invocation,
            completion_contract_revision=completion_contract_revision,
        )

    assert calls == []


def test_execute_local_python_subprocess_invocation_propagates_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Subprocess exceptions stay raw for later execution-attempt mapping slices."""
    invocation = _local_python_subprocess_invocation()

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, shell, capture_output, text, check
        raise subprocess.TimeoutExpired(cmd=args, timeout=timeout)

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(subprocess.TimeoutExpired):
        execute_runtime_probe_local_python_subprocess_invocation(
            invocation,
            completion_contract_revision=(
                "runtime-probe-local-python-process-completion:test.1"
            ),
        )


def test_materialize_local_python_timeout_attempt_is_sanitized() -> None:
    """Timeout exceptions become deterministic non-proof attempts without raw data."""
    invocation = _local_python_subprocess_invocation()
    exception = subprocess.TimeoutExpired(
        cmd=invocation.argv,
        timeout=invocation.timeout_seconds,
        output="raw stdout proof payload /private/tmp/runtime-probe",
        stderr="raw stderr traceback pid=12345",
    )

    attempt = materialize_runtime_probe_local_python_subprocess_exception_attempt(
        invocation,
        exception,
    )

    runner_request = invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "local Python subprocess timed out; recorded as timed_out"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_subprocess_timeout"),
        _field("normalized_outcome", "timed_out"),
        _field("exception_type", "subprocess.TimeoutExpired"),
        _field("timeout_seconds", str(invocation.timeout_seconds)),
    )
    failure_text = "\n".join(
        (
            attempt.failure_summary,
            *(field.value for field in attempt.failure_detail_fields),
        )
    )
    assert "raw stdout" not in failure_text
    assert "raw stderr" not in failure_text
    assert "/private/tmp" not in failure_text
    assert "pid=12345" not in failure_text
    assert "traceback" not in failure_text
    assert invocation.working_directory not in failure_text


def test_materialize_local_python_exception_attempt_is_sanitized() -> None:
    """Generic local subprocess exceptions default to sanitized crashed attempts."""
    invocation = _local_python_subprocess_invocation()
    exception = RuntimeError(
        "raw stderr traceback pid=12345 from /private/tmp/runtime-probe"
    )

    attempt = materialize_runtime_probe_local_python_subprocess_exception_attempt(
        invocation,
        exception,
    )

    runner_request = invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "local Python subprocess raised RuntimeError; recorded as crashed"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_subprocess_exception"),
        _field("normalized_outcome", "crashed"),
        _field("exception_type", "builtins.RuntimeError"),
    )
    failure_text = "\n".join(
        (
            attempt.failure_summary,
            *(field.value for field in attempt.failure_detail_fields),
        )
    )
    assert "raw stderr" not in failure_text
    assert "traceback" not in failure_text
    assert "pid=12345" not in failure_text
    assert "/private/tmp" not in failure_text
    assert invocation.working_directory not in failure_text


def test_materialize_nonzero_local_python_completion_attempt_is_non_proof() -> None:
    """Nonzero completions become non-proof attempts without parsing raw output."""
    completion = _local_python_process_completion(
        returncode=17,
        stdout_text='{"observed_module":"plugins.weather"}\n',
        stderr_text="Traceback raw stderr pid=12345 /private/tmp/runtime-probe\n",
    )

    attempt = materialize_runtime_probe_local_python_process_completion_attempt(
        completion
    )

    runner_request = completion.invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "local Python subprocess exited with returncode 17; recorded as crashed"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_process_completion"),
        _field("normalized_outcome", "crashed"),
        _field("returncode", "17"),
    )
    result_batch = _assemble_result_batch(
        runtime_probe_execution.RuntimeProbeExecutionInputBatch(
            plan_id=runner_request.plan_id,
            request_ids=(runner_request.request_id,),
            inputs=(runner_request.execution_input,),
        ),
        (attempt,),
    )
    result = result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert result.is_admissible_runtime_backed_proof is False

    failure_text = "\n".join(
        (
            attempt.failure_summary,
            *(field.value for field in attempt.failure_detail_fields),
        )
    )
    assert "observed_module" not in failure_text
    assert "raw stderr" not in failure_text
    assert "pid=12345" not in failure_text
    assert "/private/tmp" not in failure_text
    assert completion.stdout_text not in failure_text
    assert completion.stderr_text not in failure_text


def test_nonzero_local_python_completion_attempt_supports_configured_outcome() -> None:
    """Nonzero completions can be mapped to a configured non-proof outcome."""
    setup_failed = runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    completion = _local_python_process_completion(
        returncode=64,
        stdout_text='{"observed_module":"plugins.weather"}\n',
        stderr_text="missing setup variable from raw stderr\n",
    )

    attempt = materialize_runtime_probe_local_python_process_completion_attempt(
        completion,
        outcome=setup_failed,
    )

    runner_request = completion.invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is setup_failed
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "local Python subprocess exited with returncode 64; recorded as setup_failed"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_process_completion"),
        _field("normalized_outcome", "setup_failed"),
        _field("returncode", "64"),
    )


def test_nonzero_local_python_completion_attempt_rejects_observed_outcome() -> None:
    """Nonzero completion failure materialization cannot produce proof outcomes."""
    completion = _local_python_process_completion(returncode=17)

    with pytest.raises(ValueError, match="non-proof outcome"):
        materialize_runtime_probe_local_python_process_completion_attempt(
            completion,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
        )


def test_materialize_zero_returncode_completion_attempt_rejects_deferred_success() -> (
    None
):
    """Zero-returncode completions are not interpreted by the failure boundary."""
    completion = _local_python_process_completion(
        returncode=0,
        stdout_text='{"observed_module":"plugins.weather"}\n',
        stderr_text="",
    )

    with pytest.raises(ValueError, match="deferred"):
        materialize_runtime_probe_local_python_process_completion_attempt(completion)


def test_materialize_local_python_failure_attempts_revalidate_carried_contracts() -> (
    None
):
    """Local-Python failure materializers revalidate carried request contracts."""
    invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        invocation.runner_request,
        "plan_id",
        "runtime_probe_request_plan:wrong",
    )

    with pytest.raises(ValueError, match="plan_id"):
        materialize_runtime_probe_local_python_subprocess_exception_attempt(
            invocation,
            RuntimeError("local failure"),
        )

    completion = _local_python_process_completion(returncode=5)
    object.__setattr__(completion, "returncode", True)

    with pytest.raises(ValueError, match="returncode"):
        materialize_runtime_probe_local_python_process_completion_attempt(completion)


@pytest.mark.parametrize(
    ("primitive_overrides", "error_match"),
    (
        ({"returncode": True}, "returncode"),
        ({"returncode": "0"}, "returncode"),
        ({"stdout_text": b""}, "stdout_text"),
        ({"stderr_text": None}, "stderr_text"),
        ({"completion_contract_revision": ""}, "completion_contract_revision"),
        (
            {"completion_contract_revision": " runtime-probe-completion:test.1"},
            "completion_contract_revision.*malformed",
        ),
        (
            {"completion_contract_revision": "runtime-probe-completion:test.1\nbad"},
            "completion_contract_revision.*malformed",
        ),
    ),
)
def test_materialize_local_python_process_completion_rejects_bad_primitives(
    primitive_overrides: dict[str, object],
    error_match: str,
) -> None:
    """Raw completion materialization requires typed primitive fields."""
    invocation = _local_python_subprocess_invocation()
    primitives: dict[str, object] = {
        "returncode": 0,
        "stdout_text": "",
        "stderr_text": "",
        "completion_contract_revision": (
            "runtime-probe-local-python-process-completion:test.1"
        ),
    }
    primitives.update(primitive_overrides)

    with pytest.raises(ValueError, match=error_match):
        materialize_runtime_probe_local_python_process_completion(
            invocation,
            returncode=primitives["returncode"],
            stdout_text=primitives["stdout_text"],
            stderr_text=primitives["stderr_text"],
            completion_contract_revision=primitives["completion_contract_revision"],
        )


def test_local_python_process_completion_rejects_contract_drift() -> None:
    """The frozen completion type rechecks invocation and copied metadata."""
    completion = _local_python_process_completion()

    with pytest.raises(ValueError, match="invocation_identity"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity="runtime_probe_local_python_subprocess_invocation:wrong",
            argv=completion.argv,
            working_directory=completion.working_directory,
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="argv"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=(*completion.argv, "--mutated"),
            working_directory=completion.working_directory,
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="working_directory"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=completion.argv,
            working_directory="/workspace/other",
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="python_path_entries"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=completion.argv,
            working_directory=completion.working_directory,
            python_path_entries=("/workspace/other/src",),
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="timeout_seconds"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=completion.argv,
            working_directory=completion.working_directory,
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds + 1,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="replay payload fields"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=completion.argv,
            working_directory=completion.working_directory,
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=(
                _field("plan_id", completion.invocation.runner_request.plan_id),
            ),
        )


@pytest.mark.parametrize(
    ("runner_environment", "error_match"),
    (
        (
            tuple(
                field
                for field in _local_python_runner_environment()
                if field.key != "repository_root"
            ),
            "repository_root",
        ),
        (
            tuple(
                field
                for field in _local_python_runner_environment()
                if field.key != "working_directory"
            ),
            "working_directory",
        ),
        (
            _local_python_runner_environment()
            + (_field("repository_root", "/workspace/other"),),
            "duplicate singleton",
        ),
        (
            _local_python_runner_environment() + (_field("platform", "darwin-arm64"),),
            "duplicate singleton",
        ),
    ),
)
def test_derive_local_python_environment_context_rejects_singleton_metadata_drift(
    runner_environment: tuple[runtime_probe_results.RuntimeProbeReplayField, ...],
    error_match: str,
) -> None:
    """Local-Python context derivation requires unique singleton metadata."""
    runner_request = _local_python_runner_request(
        runner_environment=runner_environment,
    )

    with pytest.raises(ValueError, match=error_match):
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )


@pytest.mark.parametrize(
    ("field_key", "bad_value", "error_match"),
    (
        ("repository_root", " ", "runner_environment"),
        ("repository_root", "workspace/context-ir", "absolute"),
        ("working_directory", "workspace/context-ir", "absolute"),
        ("python_path_entry", "src", "absolute"),
        ("python_path_entry", "/workspace/context-ir/src\nbad", "malformed"),
        ("working_directory", " /workspace/context-ir", "malformed"),
        ("repository_root", "/workspace/context-ir\x00bad", "malformed"),
    ),
)
def test_derive_local_python_environment_context_rejects_bad_path_metadata(
    field_key: str,
    bad_value: str,
    error_match: str,
) -> None:
    """Local-Python path metadata must be non-blank, absolute, and parseable."""
    runner_request = _local_python_runner_request()
    field = next(
        field for field in runner_request.runner_environment if field.key == field_key
    )
    object.__setattr__(field, "value", bad_value)

    with pytest.raises(ValueError, match=error_match):
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )


def test_prepare_runtime_probe_runner_requests_for_diagnostic_preserves_boundary() -> (
    None
):
    """Diagnostic preparation preserves the planned input and runner identities."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    plan = _plan(first_request, second_request, third_request)
    diagnostic = _diagnostic_for_plan(plan)
    snapshot_basis = _snapshot_basis()
    runtime_assumptions = _runtime_assumptions()
    runner_environment = _runner_environment()
    runner_assumptions = _runner_assumptions()

    preparation = (
        runtime_probe_execution.prepare_runtime_probe_runner_requests_for_diagnostic(
            diagnostic,
            repository_snapshot_basis=snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=runtime_assumptions,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )
    )

    input_batch = preparation.execution_input_batch
    runner_batch = preparation.runner_request_batch
    assert preparation.diagnostic is diagnostic
    assert preparation.request_plan is plan
    assert input_batch.plan_id == plan.plan_id
    assert runner_batch.plan_id == plan.plan_id
    assert input_batch.request_ids == plan.request_ids
    assert runner_batch.request_ids == plan.request_ids
    assert [input_item.request_id for input_item in input_batch.inputs] == list(
        plan.request_ids
    )
    assert [
        runner_request.request_id for runner_request in runner_batch.runner_requests
    ] == list(plan.request_ids)
    assert runner_batch.runner_contract_revision == "runtime-probe-runner:test.1"
    assert runner_batch.timeout_seconds == 30
    assert runner_batch.runner_environment is runner_environment
    assert runner_batch.runner_assumptions is runner_assumptions

    for request, input_item, runner_request in zip(
        plan.requests,
        input_batch.inputs,
        runner_batch.runner_requests,
        strict=True,
    ):
        assert input_item.request is request
        assert input_item.plan_id == plan.plan_id
        assert input_item.request_id == request.request_id
        assert input_item.replay_artifact.repository_snapshot_basis is snapshot_basis
        assert input_item.replay_artifact.runtime_assumptions is runtime_assumptions
        assert runner_request.request is request
        assert runner_request.execution_input is input_item
        assert runner_request.replay_artifact is input_item.replay_artifact
        assert runner_request.runner_environment is runner_environment
        assert runner_request.runner_assumptions is runner_assumptions


def test_prepare_runtime_probe_runner_requests_for_diagnostic_rejects_plan_drift() -> (
    None
):
    """Diagnostic preparation rejects missing, detached, or drifted request plans."""
    request = _request()
    plan = _plan(request)
    diagnostic = _diagnostic_for_plan(plan)
    missing_plan = replace(diagnostic, planned_runtime_probe_request_plan=None)
    drifted_diagnostic = _diagnostic_for_plan(plan)
    object.__setattr__(drifted_diagnostic, "planned_runtime_probe_requests", ())
    identity_drifted_diagnostic = _diagnostic_for_plan(plan)
    object.__setattr__(
        identity_drifted_diagnostic,
        "planned_runtime_probe_requests",
        (_request(),),
    )
    drifted_plan = _plan(request)
    object.__setattr__(drifted_plan, "request_ids", ("runtime_probe:wrong",))
    drifted_plan_diagnostic = _diagnostic_for_plan(drifted_plan)
    preparation = _prepare_runner_requests(diagnostic)
    equivalent_plan = _plan(request)

    with pytest.raises(ValueError, match="planned_runtime_probe_request_plan"):
        _prepare_runner_requests(missing_plan)
    with pytest.raises(ValueError, match="requests must match"):
        _prepare_runner_requests(drifted_diagnostic)
    with pytest.raises(ValueError, match="request identities"):
        _prepare_runner_requests(identity_drifted_diagnostic)
    with pytest.raises(ValueError, match="request_ids must match requests"):
        _prepare_runner_requests(drifted_plan_diagnostic)
    with pytest.raises(ValueError, match="request_plan must be diagnostic"):
        runtime_probe_execution.RuntimeProbeDiagnosticRunnerRequestPreparation(
            diagnostic=diagnostic,
            request_plan=equivalent_plan,
            execution_input_batch=preparation.execution_input_batch,
            runner_request_batch=preparation.runner_request_batch,
        )


def test_prepare_runner_requests_for_diagnostic_rejects_bad_metadata() -> None:
    """Diagnostic preparation propagates input and runner metadata validation."""
    diagnostic = _diagnostic_for_plan(_plan(_request()))

    with pytest.raises(ValueError, match="probe_contract_revision"):
        _prepare_runner_requests(diagnostic, probe_contract_revision=" ")
    with pytest.raises(ValueError, match="runtime_assumptions"):
        _prepare_runner_requests(diagnostic, runtime_assumptions=())
    with pytest.raises(ValueError, match="runner_contract_revision"):
        _prepare_runner_requests(diagnostic, runner_contract_revision=" ")
    with pytest.raises(ValueError, match="timeout_seconds"):
        _prepare_runner_requests(diagnostic, timeout_seconds=0)
    with pytest.raises(ValueError, match="runner_environment"):
        _prepare_runner_requests(diagnostic, runner_environment=())
    with pytest.raises(ValueError, match="runner_assumptions"):
        _prepare_runner_requests(diagnostic, runner_assumptions=())


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


def test_assemble_runner_request_results_preserves_order_and_identities() -> None:
    """Runner-request-gated attempts become results in runner-request order."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    plan = _plan(first_request, second_request, third_request)
    input_batch = _materialized_batch(plan)
    runner_batch = _runner_request_batch(input_batch)
    original_runner_requests = runner_batch.runner_requests
    first_payload = (_field("observed_module", "plugins.weather"),)
    first_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=first_payload,
    )
    second_attempt = _execution_attempt(
        runner_batch.runner_requests[1].execution_input,
        durable_artifact_reference=(
            "artifact://runtime-probe-results/dynamic-import/main-run.json"
        ),
    )
    third_attempt = _execution_attempt(
        runner_batch.runner_requests[2].execution_input,
        outcome=runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        failure_summary="probe process exited non-zero",
        failure_detail_fields=(_field("exit_code", "1"),),
    )

    result_batch = _assemble_runner_request_result_batch(
        runner_batch,
        (third_attempt, first_attempt, second_attempt),
    )

    assert result_batch.plan_id == runner_batch.plan_id
    assert tuple(result.request_id for result in result_batch.results) == (
        runner_batch.request_ids
    )
    assert runner_batch.runner_requests is original_runner_requests

    for result, runner_request in zip(
        result_batch.results,
        runner_batch.runner_requests,
        strict=True,
    ):
        assert result.plan_id == runner_request.plan_id
        assert result.request_id == runner_request.request_id
        assert result.request is runner_request.request
        assert result.replay_artifact is runner_request.replay_artifact
        assert result.replay_artifact is runner_request.execution_input.replay_artifact

    first_result = result_batch.results[0]
    assert isinstance(first_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert first_result.normalized_payload == first_payload
    assert first_result.durable_artifact_reference is None
    assert first_result.is_admissible_runtime_backed_proof is True

    second_result = result_batch.results[1]
    assert isinstance(second_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert second_result.normalized_payload == ()
    assert second_result.durable_artifact_reference == (
        "artifact://runtime-probe-results/dynamic-import/main-run.json"
    )
    assert second_result.is_admissible_runtime_backed_proof is True

    third_result = result_batch.results[2]
    assert isinstance(third_result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert (
        third_result.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    )
    assert third_result.failure_summary == "probe process exited non-zero"
    assert third_result.failure_detail_fields == (_field("exit_code", "1"),)
    assert third_result.is_admissible_runtime_backed_proof is False


def test_assemble_runner_request_results_supports_empty_batch() -> None:
    """Empty runner-request batches assemble into empty result batches."""
    input_batch = _materialized_batch(
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )
    runner_batch = _runner_request_batch(input_batch)

    result_batch = _assemble_runner_request_result_batch(runner_batch, ())

    assert result_batch.plan_id == runner_batch.plan_id
    assert result_batch.results == ()


def test_assemble_runner_request_results_rejects_incomplete_attempt_sets() -> None:
    """Runner-request assembly requires exactly one attempt per runner request."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request))
    )
    planned_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    duplicate_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.forecast"),),
    )
    unplanned_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=8)))
    )
    unplanned_attempt = _execution_attempt(
        unplanned_runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.unplanned"),),
    )

    with pytest.raises(ValueError, match="missing runtime probe execution attempt"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (planned_attempt,),
        )
    with pytest.raises(ValueError, match="duplicate runtime probe execution attempt"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (planned_attempt, duplicate_attempt),
        )
    with pytest.raises(ValueError, match="not present in runner request batch"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (planned_attempt, unplanned_attempt),
        )


def test_assemble_runner_request_results_rejects_attempt_identity_drift() -> None:
    """Runner-request assembly rejects plan, request, and execution-input drift."""
    request = _request()
    plan = _plan(request)
    runner_batch = _runner_request_batch(_materialized_batch(plan))
    equivalent_input = _materialized_batch(plan).inputs[0]
    wrong_input_attempt = _execution_attempt(
        equivalent_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    plan_drifted_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(
        plan_drifted_attempt,
        "plan_id",
        "runtime_probe_request_plan:wrong",
    )
    request_drifted_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(request_drifted_attempt, "request", _request(start_line=8))

    with pytest.raises(ValueError, match="runner request execution input"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (wrong_input_attempt,),
        )
    with pytest.raises(ValueError, match="plan_id must match execution input"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (plan_drifted_attempt,),
        )
    with pytest.raises(ValueError, match="request must be execution input request"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (request_drifted_attempt,),
        )


def test_assemble_runner_request_results_rejects_runner_request_drift() -> None:
    """Runner-request assembly revalidates the authorized runner-request batch."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    input_batch = _materialized_batch(_plan(first_request, second_request))
    runner_batch = _runner_request_batch(input_batch)
    object.__setattr__(
        runner_batch,
        "runner_requests",
        tuple(reversed(runner_batch.runner_requests)),
    )
    attempts = tuple(
        _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )
        for runner_request in runner_batch.runner_requests
    )

    with pytest.raises(ValueError, match="request_ids must match requests"):
        _assemble_runner_request_result_batch(runner_batch, attempts)


def test_assemble_runner_request_results_rejects_bad_attempt_metadata() -> None:
    """Runner-request assembly revalidates normalized attempt metadata."""
    blank_payload_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=3)))
    )
    blank_payload_field = _field("observed_module", "plugins.weather")
    blank_payload_attempt = _execution_attempt(
        blank_payload_runner_batch.runner_requests[0].execution_input,
        normalized_payload=(blank_payload_field,),
    )
    object.__setattr__(blank_payload_field, "value", " ")

    malformed_payload_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=4)))
    )
    malformed_payload_attempt = _execution_attempt(
        malformed_payload_runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(
        malformed_payload_attempt,
        "normalized_payload",
        (("observed_module", "plugins.weather"),),
    )

    blank_failure_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=5)))
    )
    blank_failure_attempt = _execution_attempt(
        blank_failure_runner_batch.runner_requests[0].execution_input,
        outcome=runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        failure_summary="probe exceeded timeout",
    )
    object.__setattr__(blank_failure_attempt, "failure_summary", " ")

    malformed_outcome_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=6)))
    )
    malformed_outcome_attempt = _execution_attempt(
        malformed_outcome_runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(malformed_outcome_attempt, "outcome", "observed")

    with pytest.raises(ValueError, match="normalized_payload"):
        _assemble_runner_request_result_batch(
            blank_payload_runner_batch,
            (blank_payload_attempt,),
        )
    with pytest.raises(ValueError, match="normalized_payload"):
        _assemble_runner_request_result_batch(
            malformed_payload_runner_batch,
            (malformed_payload_attempt,),
        )
    with pytest.raises(ValueError, match="failure_summary"):
        _assemble_runner_request_result_batch(
            blank_failure_runner_batch,
            (blank_failure_attempt,),
        )
    with pytest.raises(ValueError, match="outcome is not supported"):
        _assemble_runner_request_result_batch(
            malformed_outcome_runner_batch,
            (malformed_outcome_attempt,),
        )


def test_collect_runtime_probe_runner_attempts_invokes_runner_once_in_order() -> None:
    """Runner-callable collection preserves request, attempt, and result identities."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request, third_request))
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []
    returned_attempts: list[runtime_probe_execution.RuntimeProbeExecutionAttempt] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        attempt = _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(
                _field("observed_request_id", runner_request.request_id),
            ),
        )
        returned_attempts.append(attempt)
        return attempt

    collection = collect_runtime_probe_execution_attempts_from_runner_requests(
        runner_batch,
        runner,
    )

    assert isinstance(
        collection,
        runtime_probe_execution.RuntimeProbeRunnerAttemptCollection,
    )
    assert collection.runner_request_batch is runner_batch
    assert tuple(calls) == runner_batch.runner_requests
    assert all(
        call is runner_request
        for call, runner_request in zip(
            calls,
            runner_batch.runner_requests,
            strict=True,
        )
    )
    assert collection.attempts == tuple(returned_attempts)
    assert all(
        attempt is returned_attempt
        for attempt, returned_attempt in zip(
            collection.attempts,
            returned_attempts,
            strict=True,
        )
    )
    assert collection.result_batch.plan_id == runner_batch.plan_id
    assert tuple(result.request_id for result in collection.result_batch.results) == (
        runner_batch.request_ids
    )

    for attempt, result, runner_request in zip(
        collection.attempts,
        collection.result_batch.results,
        runner_batch.runner_requests,
        strict=True,
    ):
        assert attempt.request_id == runner_request.request_id
        assert attempt.request is runner_request.request
        assert attempt.execution_input is runner_request.execution_input
        assert attempt.execution_input.replay_artifact is runner_request.replay_artifact
        assert result.request_id == runner_request.request_id
        assert result.request is runner_request.request
        assert result.replay_artifact is runner_request.replay_artifact


def test_collect_runtime_probe_runner_attempts_supports_empty_batch() -> None:
    """Empty runner-request batches do not invoke the runner callable."""
    input_batch = _materialized_batch(
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )
    runner_batch = _runner_request_batch(input_batch)
    was_called = False

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        nonlocal was_called
        was_called = True
        return _execution_attempt(runner_request.execution_input)

    collection = collect_runtime_probe_execution_attempts_from_runner_requests(
        runner_batch,
        runner,
    )

    assert was_called is False
    assert collection.runner_request_batch is runner_batch
    assert collection.attempts == ()
    assert collection.result_batch.plan_id == runner_batch.plan_id
    assert collection.result_batch.results == ()


def test_collect_runtime_probe_runner_attempts_revalidates_batch_before_runner() -> (
    None
):
    """Tampered runner-request batches fail before any runner invocation."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request))
    )
    object.__setattr__(
        runner_batch,
        "runner_requests",
        tuple(reversed(runner_batch.runner_requests)),
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        return _execution_attempt(runner_request.execution_input)

    with pytest.raises(ValueError, match="request_ids must match requests"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            runner,
        )

    assert calls == []


def test_collect_runtime_probe_runner_attempts_rejects_untyped_runner_output() -> None:
    """Runner-callable collection accepts only typed execution attempts."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> object:
        return {
            "plan_id": runner_request.plan_id,
            "request_id": runner_request.request_id,
        }

    with pytest.raises(ValueError, match="typed runtime probe execution attempts"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            runner,
        )


def test_collect_runtime_probe_runner_attempts_propagates_runner_exceptions() -> None:
    """Runner exceptions propagate without being synthesized into results."""
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=3), _request(start_line=4)))
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        raise RuntimeError("runner failed")

    with pytest.raises(RuntimeError, match="runner failed"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            runner,
        )

    assert calls == [runner_batch.runner_requests[0]]


def test_dispatching_runtime_probe_runner_dispatches_by_family_and_form() -> None:
    """Dispatching runners select handlers by the request's family/form key."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]
    returned_attempt = _execution_attempt(
        runner_request.execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []
    wrong_key_calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def wrong_key_handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        wrong_key_calls.append(runner_request)
        return _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(_field("observed_module", "wrong"),),
        )

    def handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        return returned_attempt

    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=(
                    runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN
                ),
                form_label=runner_request.request.form_label,
                handler=wrong_key_handler,
            ),
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=runner_request.request.family_label,
                form_label="dynamic_import:other_form/1",
                handler=wrong_key_handler,
            ),
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=runner_request.request.family_label,
                form_label=runner_request.request.form_label,
                handler=handler,
            ),
        )
    )

    attempt = dispatching_runner(runner_request)

    assert isinstance(
        dispatching_runner,
        runtime_probe_execution.RuntimeProbeDispatchingRunner,
    )
    assert attempt is returned_attempt
    assert calls == [runner_request]
    assert wrong_key_calls == []


def test_dispatching_runtime_probe_runner_materializes_missing_handler_attempts() -> (
    None
):
    """Missing dispatch handlers produce deterministic non-proof attempts."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]
    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        ()
    )

    attempt = dispatching_runner(runner_request)
    collection = collect_runtime_probe_execution_attempts_from_runner_requests(
        runner_batch,
        dispatching_runner,
    )

    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.execution_input.replay_artifact is runner_request.replay_artifact
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "runtime probe runner has no handler for dynamic_import form "
        "dynamic_import:importlib.import_module/1; recorded as setup_failed"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", "dynamic_import"),
        _field("form_label", "dynamic_import:importlib.import_module/1"),
        _field("missing_handler_outcome", "setup_failed"),
    )

    result = collection.result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert result.request is runner_request.request
    assert result.replay_artifact is runner_request.replay_artifact
    assert (
        result.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert result.is_admissible_runtime_backed_proof is False


@pytest.mark.parametrize(
    "outcome",
    (
        runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        runtime_probe_results.RuntimeProbeResultOutcome.MISSING_ENVIRONMENT,
        runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
    ),
)
def test_dispatching_runtime_probe_runner_supports_non_proof_missing_outcomes(
    outcome: runtime_probe_results.RuntimeProbeResultOutcome,
) -> None:
    """Missing-handler attempts can be configured to any non-proof outcome."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (),
        missing_handler_outcome=outcome,
    )

    attempt = dispatching_runner(runner_batch.runner_requests[0])

    assert attempt.outcome is outcome
    assert attempt.failure_detail_fields[-1] == _field(
        "missing_handler_outcome",
        outcome.value,
    )


def test_dispatching_runtime_probe_runner_rejects_bad_dispatch_metadata() -> None:
    """Dispatch tables reject ambiguous keys and proof-bearing miss outcomes."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]

    def handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        return _execution_attempt(runner_request.execution_input)

    entry = runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
        family_label=runner_request.request.family_label,
        form_label=runner_request.request.form_label,
        handler=handler,
    )

    with pytest.raises(ValueError, match="form_label"):
        runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
            family_label=runner_request.request.family_label,
            form_label=" ",
            handler=handler,
        )
    with pytest.raises(ValueError, match="duplicate runtime probe runner handler key"):
        runtime_probe_execution.make_dispatching_runtime_probe_runner(
            (
                entry,
                runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                    family_label=runner_request.request.family_label,
                    form_label=runner_request.request.form_label,
                    handler=handler,
                ),
            )
        )
    with pytest.raises(ValueError, match="non-proof outcome"):
        runtime_probe_execution.make_dispatching_runtime_probe_runner(
            (),
            missing_handler_outcome=(
                runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
            ),
        )


def test_dispatching_runtime_probe_runner_rejects_untyped_handler_returns() -> None:
    """Dispatching runners keep the same strict typed return boundary."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]

    def handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> object:
        return {
            "plan_id": runner_request.plan_id,
            "request_id": runner_request.request_id,
        }

    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=runner_request.request.family_label,
                form_label=runner_request.request.form_label,
                handler=handler,
            ),
        )
    )

    with pytest.raises(ValueError, match="typed runtime probe execution attempts"):
        dispatching_runner(runner_request)


def test_dispatching_runtime_probe_runner_propagates_handler_exceptions() -> None:
    """Handler exceptions propagate unless an existing adapter wraps dispatch."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        raise RuntimeError("handler failed")

    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=runner_request.request.family_label,
                form_label=runner_request.request.form_label,
                handler=handler,
            ),
        )
    )

    with pytest.raises(RuntimeError, match="handler failed"):
        dispatching_runner(runner_request)

    adapted_runner = (
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(
            dispatching_runner
        )
    )
    normalized_attempt = adapted_runner(runner_request)

    assert calls == [runner_request, runner_request]
    assert (
        normalized_attempt.outcome
        is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    )
    assert normalized_attempt.request is runner_request.request
    assert normalized_attempt.execution_input is runner_request.execution_input


def test_failure_normalizing_runner_preserves_success_and_normalizes_exception() -> (
    None
):
    """Opt-in adapter preserves successes and converts Exceptions to failures."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request, third_request))
    )
    first_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_request_id", first_request.request_id),),
    )
    third_attempt = _execution_attempt(
        runner_batch.runner_requests[2].execution_input,
        normalized_payload=(_field("observed_request_id", third_request.request_id),),
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        if runner_request is runner_batch.runner_requests[0]:
            return first_attempt
        if runner_request is runner_batch.runner_requests[1]:
            raise RuntimeError("pid=12345 traceback frame local")
        return third_attempt

    adapted_runner = (
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(runner)
    )

    collection = collect_runtime_probe_execution_attempts_from_runner_requests(
        runner_batch,
        adapted_runner,
    )

    assert isinstance(
        adapted_runner,
        runtime_probe_execution.RuntimeProbeFailureNormalizingRunner,
    )
    assert tuple(calls) == runner_batch.runner_requests
    assert collection.attempts[0] is first_attempt
    assert collection.attempts[2] is third_attempt

    normalized_attempt = collection.attempts[1]
    assert normalized_attempt.plan_id == runner_batch.plan_id
    assert normalized_attempt.request_id == runner_batch.runner_requests[1].request_id
    assert normalized_attempt.request is runner_batch.runner_requests[1].request
    assert (
        normalized_attempt.execution_input
        is runner_batch.runner_requests[1].execution_input
    )
    assert (
        normalized_attempt.outcome
        is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    )
    assert normalized_attempt.normalized_payload == ()
    assert normalized_attempt.durable_artifact_reference is None
    assert normalized_attempt.failure_summary == (
        "runtime probe runner raised RuntimeError; normalized as crashed"
    )
    assert normalized_attempt.failure_detail_fields == (
        _field("failure_normalization_source", "runner_exception"),
        _field("normalized_outcome", "crashed"),
        _field("exception_type", "builtins.RuntimeError"),
    )
    assert "pid=12345" not in normalized_attempt.failure_summary
    assert all(
        "pid=12345" not in detail.value
        for detail in normalized_attempt.failure_detail_fields
    )

    normalized_result = collection.result_batch.results[1]
    assert isinstance(
        normalized_result,
        runtime_probe_results.RuntimeProbeNonProofResult,
    )
    assert normalized_result.request_id == normalized_attempt.request_id
    assert normalized_result.request is normalized_attempt.request
    assert normalized_result.replay_artifact is (
        runner_batch.runner_requests[1].replay_artifact
    )
    assert normalized_result.is_admissible_runtime_backed_proof is False


@pytest.mark.parametrize(
    "outcome",
    (
        runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        runtime_probe_results.RuntimeProbeResultOutcome.MISSING_ENVIRONMENT,
        runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
    ),
)
def test_failure_normalizing_runtime_probe_runner_supports_non_proof_outcomes(
    outcome: runtime_probe_results.RuntimeProbeResultOutcome,
) -> None:
    """Failure normalization is limited to explicit non-proof outcomes."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        raise LookupError("local path /private/tmp/runtime-probe")

    adapted_runner = runtime_probe_execution.RuntimeProbeFailureNormalizingRunner(
        runner=runner,
        outcome=outcome,
    )

    attempt = adapted_runner(runner_request)

    assert attempt.outcome is outcome
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.failure_summary == (
        f"runtime probe runner raised LookupError; normalized as {outcome.value}"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_normalization_source", "runner_exception"),
        _field("normalized_outcome", outcome.value),
        _field("exception_type", "builtins.LookupError"),
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None


def test_failure_normalizing_runtime_probe_runner_rejects_observed_outcome() -> None:
    """Failure normalization cannot be configured to produce proof outcomes."""

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        return _execution_attempt(runner_request.execution_input)

    with pytest.raises(ValueError, match="non-proof outcome"):
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(
            runner,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
        )


def test_failure_normalizing_runtime_probe_runner_rejects_untyped_returns() -> None:
    """Malformed runner returns remain strict errors instead of normalized failures."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> object:
        return {
            "plan_id": runner_request.plan_id,
            "request_id": runner_request.request_id,
        }

    adapted_runner = (
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(runner)
    )

    with pytest.raises(ValueError, match="typed runtime probe execution attempts"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            adapted_runner,
        )


def test_failure_normalizing_runtime_probe_runner_does_not_catch_base_exception() -> (
    None
):
    """Only Exception subclasses are normalized; BaseException subclasses propagate."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        raise SystemExit("runner requested shutdown")

    adapted_runner = (
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(runner)
    )

    with pytest.raises(SystemExit, match="runner requested shutdown"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            adapted_runner,
        )


def test_runtime_probe_runner_attempt_collection_rejects_order_and_result_drift() -> (
    None
):
    """The collection envelope enforces runner-request-gated assembly."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request))
    )
    attempts = tuple(
        _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(
                _field("observed_request_id", runner_request.request_id),
            ),
        )
        for runner_request in runner_batch.runner_requests
    )
    result_batch = _assemble_runner_request_result_batch(runner_batch, attempts)
    reversed_attempts = tuple(reversed(attempts))
    reversed_attempt_result_batch = _assemble_runner_request_result_batch(
        runner_batch,
        reversed_attempts,
    )
    reversed_result_batch = runtime_probe_results.RuntimeProbeResultBatch(
        plan_id=runner_batch.plan_id,
        results=tuple(reversed(result_batch.results)),
    )

    with pytest.raises(ValueError, match="runner request order"):
        runtime_probe_execution.RuntimeProbeRunnerAttemptCollection(
            runner_request_batch=runner_batch,
            attempts=reversed_attempts,
            result_batch=reversed_attempt_result_batch,
        )

    with pytest.raises(
        ValueError,
        match="result_batch must be in runner request order",
    ):
        runtime_probe_execution.RuntimeProbeRunnerAttemptCollection(
            runner_request_batch=runner_batch,
            attempts=attempts,
            result_batch=reversed_result_batch,
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
    diagnostic = _diagnostic_for_plan(plan)
    preparation = _prepare_runner_requests(diagnostic)
    input_item = _materialized_batch(plan).inputs[0]
    runner_batch = _runner_request_batch(_materialized_batch(plan))
    runner_request = runner_batch.runner_requests[0]
    attempt = _execution_attempt(
        input_item,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    collection_attempt = _execution_attempt(
        runner_request.execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    collection = runtime_probe_execution.RuntimeProbeRunnerAttemptCollection(
        runner_request_batch=runner_batch,
        attempts=(collection_attempt,),
        result_batch=_assemble_runner_request_result_batch(
            runner_batch,
            (collection_attempt,),
        ),
    )

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        return _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )

    handler_entry = runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
        family_label=runner_request.request.family_label,
        form_label=runner_request.request.form_label,
        handler=runner,
    )
    dispatching_runner = runtime_probe_execution.RuntimeProbeDispatchingRunner(
        handler_entries=(handler_entry,),
    )
    normalizing_runner = runtime_probe_execution.RuntimeProbeFailureNormalizingRunner(
        runner=runner,
    )
    local_python_context = (
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            _local_python_runner_request()
        )
    )
    local_python_invocation = _local_python_subprocess_invocation()
    local_python_completion = _local_python_process_completion(local_python_invocation)

    with pytest.raises(FrozenInstanceError):
        input_item.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        runner_request.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        runner_batch.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        attempt.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        collection.runner_request_batch = runner_batch
    with pytest.raises(FrozenInstanceError):
        preparation.request_plan = (
            runtime_probe_requests.build_runtime_probe_request_plan(())
        )
    with pytest.raises(FrozenInstanceError):
        normalizing_runner.outcome = (
            runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT
        )
    with pytest.raises(FrozenInstanceError):
        handler_entry.form_label = "dynamic_import:mutated/1"
    with pytest.raises(FrozenInstanceError):
        dispatching_runner.missing_handler_outcome = (
            runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT
        )
    with pytest.raises(FrozenInstanceError):
        local_python_context.working_directory = "/tmp/context-ir"
    with pytest.raises(FrozenInstanceError):
        local_python_invocation.working_directory = "/tmp/context-ir"
    with pytest.raises(FrozenInstanceError):
        local_python_completion.stdout_text = "mutated"

    assert (
        "RuntimeProbeDiagnosticRunnerRequestPreparation"
        in runtime_probe_execution.__all__
    )
    assert "RuntimeProbeDispatchingRunner" in runtime_probe_execution.__all__
    assert "RuntimeProbeExecutionAttempt" in runtime_probe_execution.__all__
    assert "RuntimeProbeExecutionInput" in runtime_probe_execution.__all__
    assert "RuntimeProbeExecutionInputBatch" in runtime_probe_execution.__all__
    assert "RuntimeProbeFailureNormalizingRunner" in runtime_probe_execution.__all__
    assert (
        "RuntimeProbeLocalPythonEnvironmentContext" in runtime_probe_execution.__all__
    )
    assert "RuntimeProbeLocalPythonProcessCompletion" in (
        runtime_probe_execution.__all__
    )
    assert (
        "RuntimeProbeLocalPythonSubprocessInvocation" in runtime_probe_execution.__all__
    )
    assert "RuntimeProbeRunnerHandlerEntry" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerHandlerKey" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerAttemptCollection" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerCallable" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerRequest" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerRequestBatch" in runtime_probe_execution.__all__
    assert "assemble_runtime_probe_result_batch_from_execution_attempts" in (
        runtime_probe_execution.__all__
    )
    assert "assemble_runtime_probe_result_batch_from_runner_request_attempts" in (
        runtime_probe_execution.__all__
    )
    assert "collect_runtime_probe_execution_attempts_from_runner_requests" in (
        runtime_probe_execution.__all__
    )
    assert "derive_runtime_probe_local_python_environment_context" in (
        runtime_probe_execution.__all__
    )
    assert "execute_runtime_probe_local_python_subprocess_invocation" in (
        runtime_probe_execution.__all__
    )
    assert "make_dispatching_runtime_probe_runner" in runtime_probe_execution.__all__
    assert "make_failure_normalizing_runtime_probe_runner" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_execution_input_batch" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_process_completion_attempt" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_process_completion" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_subprocess_exception_attempt" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_subprocess_invocation" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_runner_request_batch" in (
        runtime_probe_execution.__all__
    )
    assert "prepare_runtime_probe_runner_requests_for_diagnostic" in (
        runtime_probe_execution.__all__
    )
    assert "RuntimeProbeDiagnosticRunnerRequestPreparation" not in context_ir.__all__
    assert "RuntimeProbeDispatchingRunner" not in context_ir.__all__
    assert "RuntimeProbeExecutionAttempt" not in context_ir.__all__
    assert "RuntimeProbeExecutionInput" not in context_ir.__all__
    assert "RuntimeProbeExecutionInputBatch" not in context_ir.__all__
    assert "RuntimeProbeFailureNormalizingRunner" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonEnvironmentContext" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonProcessCompletion" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonSubprocessInvocation" not in context_ir.__all__
    assert "RuntimeProbeRunnerHandlerEntry" not in context_ir.__all__
    assert "RuntimeProbeRunnerHandlerKey" not in context_ir.__all__
    assert "RuntimeProbeRunnerAttemptCollection" not in context_ir.__all__
    assert "RuntimeProbeRunnerCallable" not in context_ir.__all__
    assert "RuntimeProbeRunnerRequest" not in context_ir.__all__
    assert "RuntimeProbeRunnerRequestBatch" not in context_ir.__all__
    assert "assemble_runtime_probe_result_batch_from_execution_attempts" not in (
        context_ir.__all__
    )
    assert "assemble_runtime_probe_result_batch_from_runner_request_attempts" not in (
        context_ir.__all__
    )
    assert (
        "collect_runtime_probe_execution_attempts_from_runner_requests"
        not in context_ir.__all__
    )
    assert "derive_runtime_probe_local_python_environment_context" not in (
        context_ir.__all__
    )
    assert (
        "execute_runtime_probe_local_python_subprocess_invocation"
        not in context_ir.__all__
    )
    assert "make_dispatching_runtime_probe_runner" not in context_ir.__all__
    assert "make_failure_normalizing_runtime_probe_runner" not in context_ir.__all__
    assert "materialize_runtime_probe_execution_input_batch" not in context_ir.__all__
    assert (
        "materialize_runtime_probe_local_python_process_completion_attempt"
        not in context_ir.__all__
    )
    assert (
        "materialize_runtime_probe_local_python_subprocess_invocation"
        not in context_ir.__all__
    )
    assert (
        "materialize_runtime_probe_local_python_subprocess_exception_attempt"
        not in context_ir.__all__
    )
    assert "materialize_runtime_probe_runner_request_batch" not in context_ir.__all__
    assert (
        "prepare_runtime_probe_runner_requests_for_diagnostic" not in context_ir.__all__
    )
    assert not hasattr(context_ir, "RuntimeProbeDiagnosticRunnerRequestPreparation")
    assert not hasattr(context_ir, "RuntimeProbeDispatchingRunner")
    assert not hasattr(context_ir, "RuntimeProbeExecutionAttempt")
    assert not hasattr(context_ir, "RuntimeProbeExecutionInput")
    assert not hasattr(context_ir, "RuntimeProbeExecutionInputBatch")
    assert not hasattr(context_ir, "RuntimeProbeFailureNormalizingRunner")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonEnvironmentContext")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonProcessCompletion")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonSubprocessInvocation")
    assert not hasattr(context_ir, "RuntimeProbeRunnerHandlerEntry")
    assert not hasattr(context_ir, "RuntimeProbeRunnerHandlerKey")
    assert not hasattr(context_ir, "RuntimeProbeRunnerAttemptCollection")
    assert not hasattr(context_ir, "RuntimeProbeRunnerCallable")
    assert not hasattr(context_ir, "RuntimeProbeRunnerRequest")
    assert not hasattr(context_ir, "RuntimeProbeRunnerRequestBatch")
    assert not hasattr(
        context_ir,
        "assemble_runtime_probe_result_batch_from_execution_attempts",
    )
    assert not hasattr(
        context_ir,
        "assemble_runtime_probe_result_batch_from_runner_request_attempts",
    )
    assert not hasattr(
        context_ir,
        "collect_runtime_probe_execution_attempts_from_runner_requests",
    )
    assert not hasattr(
        context_ir,
        "derive_runtime_probe_local_python_environment_context",
    )
    assert not hasattr(
        context_ir,
        "execute_runtime_probe_local_python_subprocess_invocation",
    )
    assert not hasattr(
        context_ir,
        "make_dispatching_runtime_probe_runner",
    )
    assert not hasattr(
        context_ir,
        "make_failure_normalizing_runtime_probe_runner",
    )
    assert not hasattr(
        context_ir,
        "prepare_runtime_probe_runner_requests_for_diagnostic",
    )
    assert not hasattr(context_ir, "materialize_runtime_probe_execution_input_batch")
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_process_completion_attempt",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_process_completion",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_subprocess_exception_attempt",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_subprocess_invocation",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_runner_request_batch",
    )

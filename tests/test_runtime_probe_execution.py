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


def test_runtime_probe_execution_input_contract_is_frozen_and_module_local() -> None:
    """Execution-input records stay frozen and absent from package-root exports."""
    request = _request()
    plan = _plan(request)
    input_item = _materialized_batch(plan).inputs[0]

    with pytest.raises(FrozenInstanceError):
        input_item.plan_id = "runtime_probe_request_plan:mutated"

    assert "RuntimeProbeExecutionInput" in runtime_probe_execution.__all__
    assert "RuntimeProbeExecutionInputBatch" in runtime_probe_execution.__all__
    assert "materialize_runtime_probe_execution_input_batch" in (
        runtime_probe_execution.__all__
    )
    assert "RuntimeProbeExecutionInput" not in context_ir.__all__
    assert "RuntimeProbeExecutionInputBatch" not in context_ir.__all__
    assert "materialize_runtime_probe_execution_input_batch" not in context_ir.__all__
    assert not hasattr(context_ir, "RuntimeProbeExecutionInput")
    assert not hasattr(context_ir, "RuntimeProbeExecutionInputBatch")
    assert not hasattr(context_ir, "materialize_runtime_probe_execution_input_batch")

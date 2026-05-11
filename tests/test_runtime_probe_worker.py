"""Tests for the fail-closed local Python runtime probe worker ingress."""

from __future__ import annotations

import contextlib
import importlib
import json
import os
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import FrozenInstanceError, replace
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

import context_ir
import context_ir.runtime_probe_requests as runtime_probe_requests
import context_ir.runtime_probe_results as runtime_probe_results
import context_ir.runtime_probe_worker as runtime_probe_worker
from context_ir.runtime_probe_execution import (
    RuntimeProbeLocalPythonSubprocessInvocation,
    RuntimeProbeLocalPythonWorkerRequestPayload,
    materialize_runtime_probe_execution_input_batch,
    materialize_runtime_probe_local_python_process_completion,
    materialize_runtime_probe_local_python_stdout_protocol_attempt,
    materialize_runtime_probe_local_python_stdout_protocol_result,
    materialize_runtime_probe_local_python_subprocess_invocation,
    materialize_runtime_probe_local_python_worker_request_payload,
    materialize_runtime_probe_runner_request_batch,
    serialize_runtime_probe_local_python_worker_request_payload,
)
from context_ir.semantic_types import (
    RepositorySnapshotBasis,
    SemanticSubjectKind,
    SourceSite,
    SourceSpan,
    UnresolvedReasonCode,
)

DynamicImportWorkerRequest = (
    runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportWorkerRequest
)
DynamicImportWorkerObservation = (
    runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportWorkerObservation
)
DynamicImportReplayTarget = (
    runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportReplayTarget
)
WorkerSuccessResponse = (
    runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse
)
_DYNAMIC_IMPORT_TARGET_OBSERVER_HELPER = (
    "materialize_runtime_probe_dynamic_import_worker_observation_from_target"
)
_DYNAMIC_IMPORT_REPLAY_TARGET_RESOLVER_HELPER = (
    "resolve_runtime_probe_dynamic_import_replay_target_callable"
)
_DYNAMIC_IMPORT_SOURCE_MODULE_IMPORT_HELPER = (
    "import_runtime_probe_dynamic_import_replay_target_source_module"
)
_DYNAMIC_IMPORT_CONCRETE_OBSERVER_HELPER = (
    "observe_runtime_probe_dynamic_import_worker_request"
)
_IMPORTLIB_IMPORT_MODULE_FORM_LABEL = "dynamic_import:importlib.import_module/1"
_LOADER_IMPORT_MODULE_FORM_LABEL = "dynamic_import:loader.import_module/1"
_IMPORTED_IMPORT_MODULE_FORM_LABEL = "dynamic_import:import_module/1"


def _boundary_text_for_form_label(form_label: str) -> str:
    """Return the one-argument source boundary represented by a form label."""
    if form_label == _LOADER_IMPORT_MODULE_FORM_LABEL:
        return "loader.import_module(name)"
    if form_label == _IMPORTED_IMPORT_MODULE_FORM_LABEL:
        return "import_module(name)"
    return "importlib.import_module(name)"


def _field(key: str, value: str) -> runtime_probe_results.RuntimeProbeReplayField:
    """Return one replay metadata field for worker ingress tests."""
    return runtime_probe_results.RuntimeProbeReplayField(key=key, value=value)


def _request(
    *,
    source_file_path: str = "main.py",
    replay_target_seed: str = "main.run",
    replay_selector_seed: str | None = None,
    form_label: str = _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one deterministic planned runtime probe request."""
    boundary_text = _boundary_text_for_form_label(form_label)
    resolved_replay_selector_seed = (
        f"call:{replay_target_seed}:{form_label}@{source_file_path}:3:4:3:28"
        if replay_selector_seed is None
        else replay_selector_seed
    )
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:{source_file_path}:3:4",
        source_site=SourceSite(
            site_id=f"site:{source_file_path}:3:4",
            file_path=source_file_path,
            span=SourceSpan(
                start_line=3,
                start_column=4,
                end_line=3,
                end_column=28,
            ),
            snippet=boundary_text,
        ),
        reason_code=UnresolvedReasonCode.DYNAMIC_IMPORT,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label=form_label,
        replay_target_seed=replay_target_seed,
        replay_selector_seed=resolved_replay_selector_seed,
    )


def _valid_worker_invocation(
    *,
    source_file_path: str = "main.py",
    replay_target_seed: str = "main.run",
    replay_selector_seed: str | None = None,
    form_label: str = _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
    python_executable: str = "/workspace/context-ir/.venv/bin/python",
    working_directory: str = "/workspace/context-ir",
    python_path_entries: tuple[str, ...] = ("/workspace/context-ir/src",),
) -> RuntimeProbeLocalPythonSubprocessInvocation:
    """Return one strict worker invocation produced by the parent contract."""
    request = _request(
        source_file_path=source_file_path,
        replay_target_seed=replay_target_seed,
        replay_selector_seed=replay_selector_seed,
        form_label=form_label,
    )
    return _valid_worker_invocation_for_request(
        request,
        python_executable=python_executable,
        working_directory=working_directory,
        python_path_entries=python_path_entries,
    )


def _valid_worker_invocation_for_request(
    request: runtime_probe_requests.RuntimeProbeRequest,
    *,
    python_executable: str = "/workspace/context-ir/.venv/bin/python",
    working_directory: str = "/workspace/context-ir",
    python_path_entries: tuple[str, ...] = ("/workspace/context-ir/src",),
) -> RuntimeProbeLocalPythonSubprocessInvocation:
    """Return one strict worker invocation for a planned request."""
    request_plan = runtime_probe_requests.build_runtime_probe_request_plan((request,))
    input_batch = materialize_runtime_probe_execution_input_batch(
        request_plan,
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        probe_contract_revision="runtime-probe-contract:test.1",
        runtime_assumptions=(
            _field("python_version", "3.11"),
            _field("dependency_mode", "offline-fixture"),
        ),
    )
    runner_batch = materialize_runtime_probe_runner_request_batch(
        input_batch,
        runner_contract_revision="runtime-probe-runner:test.1",
        timeout_seconds=30,
        runner_environment=(
            _field("repository_root", working_directory),
            _field("working_directory", working_directory),
            *(
                _field("python_path_entry", python_path_entry)
                for python_path_entry in python_path_entries
            ),
        ),
        runner_assumptions=(
            _field("network", "disabled"),
            _field("filesystem_mode", "read_only_fixture"),
        ),
    )
    invocation = materialize_runtime_probe_local_python_subprocess_invocation(
        runner_batch.runner_requests[0],
        python_executable=python_executable,
        module_name="context_ir.runtime_probe_worker",
        invocation_contract_revision=("runtime-probe-local-python-subprocess:test.1"),
    )
    return invocation


def _valid_worker_payload(
    *,
    source_file_path: str = "main.py",
    replay_target_seed: str = "main.run",
    replay_selector_seed: str | None = None,
    form_label: str = _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
    python_executable: str = "/workspace/context-ir/.venv/bin/python",
    working_directory: str = "/workspace/context-ir",
    python_path_entries: tuple[str, ...] = ("/workspace/context-ir/src",),
) -> RuntimeProbeLocalPythonWorkerRequestPayload:
    """Return the strict worker payload produced by the parent contract."""
    invocation = _valid_worker_invocation(
        source_file_path=source_file_path,
        replay_target_seed=replay_target_seed,
        replay_selector_seed=replay_selector_seed,
        form_label=form_label,
        python_executable=python_executable,
        working_directory=working_directory,
        python_path_entries=python_path_entries,
    )
    return materialize_runtime_probe_local_python_worker_request_payload(invocation)


def _valid_dynamic_import_worker_request(
    *,
    source_file_path: str = "main.py",
    replay_target_seed: str = "main.run",
    replay_selector_seed: str | None = None,
    form_label: str = _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
    working_directory: str = "/workspace/context-ir",
    python_path_entries: tuple[str, ...] = ("/workspace/context-ir/src",),
) -> DynamicImportWorkerRequest:
    """Return one worker-local dynamic-import request contract."""
    return runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
        _valid_worker_payload(
            source_file_path=source_file_path,
            replay_target_seed=replay_target_seed,
            replay_selector_seed=replay_selector_seed,
            form_label=form_label,
            working_directory=working_directory,
            python_path_entries=python_path_entries,
        )
    )


def _valid_dynamic_import_replay_target(
    *,
    source_file_path: str = "main.py",
    replay_target_seed: str = "main.run",
    replay_selector_seed: str | None = None,
    form_label: str = _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
    working_directory: str = "/workspace/context-ir",
    python_path_entries: tuple[str, ...] = ("/workspace/context-ir/src",),
) -> DynamicImportReplayTarget:
    """Return one worker-local non-executing replay target contract."""
    request = _valid_dynamic_import_worker_request(
        source_file_path=source_file_path,
        replay_target_seed=replay_target_seed,
        replay_selector_seed=replay_selector_seed,
        form_label=form_label,
        working_directory=working_directory,
        python_path_entries=python_path_entries,
    )
    return runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target(
        request
    )


def _valid_dynamic_import_worker_observation(
    *,
    request: DynamicImportWorkerRequest | None = None,
    imported_module: str = "plugins.weather",
) -> DynamicImportWorkerObservation:
    """Return one worker-local dynamic-import observation contract."""
    worker_module = runtime_probe_worker
    validated_request = (
        _valid_dynamic_import_worker_request() if request is None else request
    )
    return worker_module.materialize_runtime_probe_dynamic_import_worker_observation(
        validated_request,
        imported_module=imported_module,
    )


def _dynamic_import_worker_observation_from_target(
    observation_source: DynamicImportWorkerRequest | DynamicImportReplayTarget,
    target: runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportTargetCallable,
) -> DynamicImportWorkerObservation:
    """Return one harness observation from an injected target callable."""
    materialize_from_target = getattr(
        runtime_probe_worker,
        _DYNAMIC_IMPORT_TARGET_OBSERVER_HELPER,
    )
    return materialize_from_target(observation_source, target)


def _dynamic_import_replay_target_callable(
    replay_target: DynamicImportReplayTarget,
    source_module: ModuleType,
) -> runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportTargetCallable:
    """Resolve one injected replay target callable for worker tests."""
    resolve_target = getattr(
        runtime_probe_worker,
        _DYNAMIC_IMPORT_REPLAY_TARGET_RESOLVER_HELPER,
    )
    return resolve_target(replay_target, source_module)


def _dynamic_import_replay_target_source_module(
    replay_target: DynamicImportReplayTarget,
) -> ModuleType:
    """Import one validated replay target source module for worker tests."""
    import_source_module = getattr(
        runtime_probe_worker,
        _DYNAMIC_IMPORT_SOURCE_MODULE_IMPORT_HELPER,
    )
    return import_source_module(replay_target)


def _observe_dynamic_import_worker_request(
    request: DynamicImportWorkerRequest,
) -> DynamicImportWorkerObservation:
    """Observe one concrete dynamic-import worker request for worker tests."""
    observe_request = getattr(
        runtime_probe_worker,
        _DYNAMIC_IMPORT_CONCRETE_OBSERVER_HELPER,
    )
    return observe_request(request)


def _dynamic_import_worker_request_with_source(
    tmp_path: Path,
    *,
    module_name: str,
    source_text: str,
    replay_target_name: str = "run",
    form_label: str = _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
) -> DynamicImportWorkerRequest:
    """Return a worker request backed by a real temp source module."""
    working_directory = tmp_path / f"{module_name}_workspace"
    python_path = tmp_path / f"{module_name}_python_path"
    working_directory.mkdir()
    python_path.mkdir()
    module_path = python_path / f"{module_name}.py"
    module_path.write_text(source_text, encoding="utf-8")
    return _valid_dynamic_import_worker_request(
        source_file_path=f"{module_name}.py",
        replay_target_seed=f"{module_name}.{replay_target_name}",
        form_label=form_label,
        working_directory=str(working_directory),
        python_path_entries=(str(python_path),),
    )


def _dynamic_import_worker_success_response(
    observation: DynamicImportWorkerObservation,
) -> WorkerSuccessResponse:
    """Return the worker stdout success response for one observation."""
    worker_module = runtime_probe_worker
    materialize_success_response = (
        worker_module.materialize_runtime_probe_dynamic_import_worker_success_response
    )
    return materialize_success_response(observation)


def _serialize_worker_success_response(
    response: WorkerSuccessResponse,
) -> str:
    """Serialize one worker stdout success response."""
    worker_module = runtime_probe_worker
    return worker_module.serialize_runtime_probe_local_python_worker_success_response(
        response
    )


def _valid_worker_stdin_text() -> str:
    """Return strict worker stdin JSON produced by the accepted parent contract."""
    payload = _valid_worker_payload()
    return serialize_runtime_probe_local_python_worker_request_payload(payload)


def _run_worker(stdin_text: str) -> tuple[int, str, str]:
    """Run the worker entrypoint with an explicit empty handler table."""
    return _run_worker_with_handlers(stdin_text, ())


def _run_worker_with_default_handlers(stdin_text: str) -> tuple[int, str, str]:
    """Run the worker entrypoint with omitted handler entries."""
    stdout = StringIO()
    stderr = StringIO()
    exit_code = runtime_probe_worker.main(
        stdin=StringIO(stdin_text),
        stdout=stdout,
        stderr=stderr,
    )
    return (exit_code, stdout.getvalue(), stderr.getvalue())


def _run_worker_with_handlers(
    stdin_text: str,
    handler_entries: Iterable[
        runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry
    ],
) -> tuple[int, str, str]:
    """Run the importable worker entrypoint with an injected handler table."""
    stdout = StringIO()
    stderr = StringIO()
    exit_code = runtime_probe_worker.main(
        stdin=StringIO(stdin_text),
        stdout=stdout,
        stderr=stderr,
        handler_entries=handler_entries,
    )
    return (exit_code, stdout.getvalue(), stderr.getvalue())


def _assert_sanitized_worker_stderr(stderr_text: str, raw_stdin: str) -> None:
    """Assert worker stderr contains no caller-controlled or environment detail."""
    assert raw_stdin not in stderr_text
    assert "Traceback" not in stderr_text
    assert "secret-token" not in stderr_text
    assert "PYTHONPATH" not in stderr_text
    assert "/private/tmp" not in stderr_text
    assert "/workspace/context-ir" not in stderr_text
    assert "RuntimeError" not in stderr_text
    assert "ValueError" not in stderr_text
    assert "handler failed" not in stderr_text
    assert "valid JSON" not in stderr_text
    assert "unknown keys" not in stderr_text
    assert "typed" not in stderr_text


def _assert_no_success_stdout_protocol(stdout_text: str) -> None:
    """Assert the worker did not emit the observed-result stdout protocol."""
    assert stdout_text == ""
    assert "runtime_probe_stdout_protocol_revision" not in stdout_text
    assert "normalized_payload" not in stdout_text
    assert "durable_artifact_reference" not in stdout_text
    assert "observed" not in stdout_text


def _replay_fields_by_key(
    fields: tuple[runtime_probe_results.RuntimeProbeReplayField, ...],
) -> dict[str, str]:
    """Return replay fields keyed by metadata key for contract assertions."""
    return {field.key: field.value for field in fields}


def _worker_payload_with_replay_field(
    key: str,
    value: str,
) -> RuntimeProbeLocalPythonWorkerRequestPayload:
    """Return a valid worker payload with one replay field tampered in place."""
    payload = _valid_worker_payload()
    object.__setattr__(
        payload,
        "request_replay_payload_fields",
        tuple(
            _field(field.key, value) if field.key == key else field
            for field in payload.request_replay_payload_fields
        ),
    )
    return payload


def test_registered_worker_handler_emits_success_stdout_protocol() -> None:
    """A matching injected handler can emit the parent stdout success protocol."""
    stdin_text = _valid_worker_stdin_text()
    handler_payloads: list[RuntimeProbeLocalPythonWorkerRequestPayload] = []

    def handler(
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse:
        handler_payloads.append(payload)
        return runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse(
            normalized_payload=(
                _field("first_observed_module", "plugins.weather"),
                _field("second_observed_module", "plugins.forecast"),
            ),
            durable_artifact_reference="runtime-artifact:local-python:abc123",
        )

    entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        handler=handler,
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )

    assert len(handler_payloads) == 1
    assert exit_code == 0
    assert stderr_text == ""
    assert stdout_text == (
        '{"runtime_probe_stdout_protocol_revision":'
        '"runtime_probe_local_python_stdout_protocol:v1",'
        '"normalized_payload":['
        '{"key":"first_observed_module","value":"plugins.weather"},'
        '{"key":"second_observed_module","value":"plugins.forecast"}],'
        '"durable_artifact_reference":"runtime-artifact:local-python:abc123"}'
    )
    assert not stdout_text.endswith("\n")


def test_worker_success_stdout_is_parent_parser_compatible() -> None:
    """Worker success stdout parses into the existing parent observed attempt."""
    stdin_text = _valid_worker_stdin_text()

    def handler(
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse:
        del payload
        return runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse(
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )

    entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        handler=handler,
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )
    completion = materialize_runtime_probe_local_python_process_completion(
        _valid_worker_invocation(),
        returncode=exit_code,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        completion_contract_revision=(
            "runtime-probe-local-python-process-completion:test.1"
        ),
    )

    protocol_result = materialize_runtime_probe_local_python_stdout_protocol_result(
        completion
    )
    attempt = materialize_runtime_probe_local_python_stdout_protocol_attempt(
        protocol_result
    )

    assert protocol_result.stdout_protocol_revision == (
        "runtime_probe_local_python_stdout_protocol:v1"
    )
    assert protocol_result.normalized_payload == (
        _field("observed_module", "plugins.weather"),
    )
    assert protocol_result.durable_artifact_reference is None
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("observed_module", "plugins.weather"),)
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None


def test_worker_success_stdout_allows_durable_only_success() -> None:
    """Durable-only worker success emits an empty normalized payload array."""
    stdin_text = _valid_worker_stdin_text()

    def handler(
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse:
        del payload
        return runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse(
            normalized_payload=(),
            durable_artifact_reference="runtime-artifact:local-python:durable-only",
        )

    entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        handler=handler,
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )

    assert exit_code == 0
    assert stderr_text == ""
    assert stdout_text == (
        '{"runtime_probe_stdout_protocol_revision":'
        '"runtime_probe_local_python_stdout_protocol:v1",'
        '"normalized_payload":[],'
        '"durable_artifact_reference":'
        '"runtime-artifact:local-python:durable-only"}'
    )


def test_worker_success_response_contract_is_frozen_and_proof_bearing() -> None:
    """Worker success responses are immutable typed proof payload contracts."""
    response = runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )

    assert response.normalized_payload == (
        _field("observed_module", "plugins.weather"),
    )
    assert response.durable_artifact_reference is None
    with pytest.raises(FrozenInstanceError):
        response.durable_artifact_reference = "runtime-artifact:local-python:mutated"
    with pytest.raises(ValueError, match="normalized_payload or durable"):
        runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse(
            normalized_payload=()
        )
    with pytest.raises(ValueError, match="durable_artifact_reference"):
        runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse(
            normalized_payload=(),
            durable_artifact_reference=" runtime-artifact:local-python:abc123",
        )


def test_malformed_worker_success_metadata_fails_closed() -> None:
    """Tampered typed success metadata is rejected without stdout or raw details."""
    stdin_text = _valid_worker_stdin_text()

    def handler(
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse:
        del payload
        response = runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse(
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )
        object.__setattr__(
            response,
            "durable_artifact_reference",
            " runtime-artifact:local-python:secret-token:/private/tmp",
        )
        return response

    entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        handler=handler,
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )

    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert (
        stderr_text
        == "runtime_probe_worker: rejected invalid worker handler response\n"
    )
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_dynamic_import_worker_request_materializes_replay_contract() -> None:
    """The worker derives a non-executing import-module request from payload."""
    payload = _valid_worker_payload()
    request = (
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )
    )
    replay_fields = _replay_fields_by_key(payload.request_replay_payload_fields)

    assert request.plan_id == payload.plan_id
    assert request.request_id == payload.request_id
    assert request.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert request.subject_id == replay_fields["subject_id"]
    assert request.source_site_id == replay_fields["source_site_id"]
    assert request.source_file_path == replay_fields["source_file_path"]
    assert request.source_start_line == int(replay_fields["source_start_line"])
    assert request.source_start_column == int(replay_fields["source_start_column"])
    assert request.source_end_line == int(replay_fields["source_end_line"])
    assert request.source_end_column == int(replay_fields["source_end_column"])
    assert request.reason_code is UnresolvedReasonCode.DYNAMIC_IMPORT
    assert request.boundary_text == "importlib.import_module(name)"
    assert (
        request.family_label is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert request.form_label == "dynamic_import:importlib.import_module/1"
    assert request.replay_target_seed == payload.replay_target_seed
    assert request.replay_selector_seed == payload.replay_selector_seed
    assert request.argv == payload.argv
    assert request.working_directory == payload.working_directory
    assert request.python_path_entries == payload.python_path_entries
    assert request.timeout_seconds == payload.timeout_seconds
    assert request.invocation_identity == payload.invocation_identity
    assert (
        request.request_replay_payload_fields is payload.request_replay_payload_fields
    )


@pytest.mark.parametrize(
    ("form_label", "expected_boundary_text"),
    (
        (_IMPORTLIB_IMPORT_MODULE_FORM_LABEL, "importlib.import_module(name)"),
        (_LOADER_IMPORT_MODULE_FORM_LABEL, "loader.import_module(name)"),
        (_IMPORTED_IMPORT_MODULE_FORM_LABEL, "import_module(name)"),
    ),
)
def test_dynamic_import_worker_request_accepts_exact_import_module_forms(
    form_label: str,
    expected_boundary_text: str,
) -> None:
    """Only the exact import-module subprocess forms materialize."""
    payload = _valid_worker_payload(form_label=form_label)

    request = (
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )
    )

    assert request.form_label == form_label
    assert request.boundary_text == expected_boundary_text
    assert (
        _replay_fields_by_key(request.request_replay_payload_fields)["form_label"]
        == form_label
    )


def test_dynamic_import_worker_request_contract_is_frozen() -> None:
    """Worker-local dynamic-import requests are immutable replay contracts."""
    request = (
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            _valid_worker_payload()
        )
    )

    with pytest.raises(FrozenInstanceError):
        request.boundary_text = "importlib.import_module(other)"


def test_dynamic_import_worker_request_constructor_rejects_blank_boundary() -> None:
    """Direct dataclass construction reruns worker-request metadata validation."""
    request = (
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            _valid_worker_payload()
        )
    )

    with pytest.raises(ValueError, match="boundary_text"):
        replace(request, boundary_text=" ")


@pytest.mark.parametrize(
    ("family_label", "form_label", "error_match"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            "reflective_builtin:getattr/2",
            "family_label",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            "dynamic_import:load_module/1",
            "form_label",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            "dynamic_import:__import__/1",
            "form_label",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            "dynamic_import:builtins.__import__/1",
            "form_label",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            "dynamic_import:loader.__import__/1",
            "form_label",
        ),
    ),
)
def test_dynamic_import_worker_request_validates_exact_family_form(
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
    error_match: str,
) -> None:
    """Adjacent dynamic-import and non-dynamic forms stay fail-closed."""
    payload = _valid_worker_payload()
    object.__setattr__(payload, "family_label", family_label)
    object.__setattr__(payload, "form_label", form_label)

    with pytest.raises(ValueError, match=error_match):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )


@pytest.mark.parametrize(
    ("replay_key", "replay_value", "error_match"),
    (
        ("reason_code", "reflective_builtin", "reason_code"),
        ("boundary_text", "importlib.import_module(name)\n", "boundary_text"),
    ),
)
def test_dynamic_import_worker_request_validates_reason_and_boundary(
    replay_key: str,
    replay_value: str,
    error_match: str,
) -> None:
    """Reason and boundary replay metadata are checked before execution exists."""
    payload = _worker_payload_with_replay_field(replay_key, replay_value)

    with pytest.raises(ValueError, match=error_match):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )


def test_dynamic_import_worker_request_rejects_blank_payload_metadata() -> None:
    """Blank top-level metadata is rejected while materializing the request."""
    payload = _valid_worker_payload()
    object.__setattr__(payload, "replay_target_seed", " ")

    with pytest.raises(ValueError, match="replay_target_seed"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )


@pytest.mark.parametrize("replay_key", ("subject_id", "boundary_text"))
def test_dynamic_import_worker_request_rejects_missing_replay_fields(
    replay_key: str,
) -> None:
    """Required request replay fields must remain present exactly once."""
    payload = _valid_worker_payload()
    object.__setattr__(
        payload,
        "request_replay_payload_fields",
        tuple(
            field
            for field in payload.request_replay_payload_fields
            if field.key != replay_key
        ),
    )

    with pytest.raises(ValueError, match=f"exactly one {replay_key}"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )


def test_dynamic_import_worker_request_rejects_duplicate_replay_fields() -> None:
    """Duplicate required replay fields are rejected as drift, not normalized."""
    payload = _valid_worker_payload()
    object.__setattr__(
        payload,
        "request_replay_payload_fields",
        (
            *payload.request_replay_payload_fields,
            _field("request_id", payload.request_id),
        ),
    )

    with pytest.raises(ValueError, match="exactly one request_id"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )


def test_dynamic_import_worker_request_rejects_top_level_replay_drift() -> None:
    """Top-level identity must match its duplicated replay-field identity."""
    payload = _valid_worker_payload()
    object.__setattr__(payload, "request_id", "runtime_probe:wrong")

    with pytest.raises(ValueError, match="request_id must match request replay"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )


@pytest.mark.parametrize(
    ("replay_key", "replay_value"),
    (
        ("source_start_line", "0"),
        ("source_start_column", "not-an-int"),
        ("source_end_column", "1"),
    ),
)
def test_dynamic_import_worker_request_rejects_malformed_source_span(
    replay_key: str,
    replay_value: str,
) -> None:
    """Malformed source span values fail before any import behavior exists."""
    payload = _worker_payload_with_replay_field(replay_key, replay_value)

    with pytest.raises(ValueError, match="source"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )


@pytest.mark.parametrize(
    "invocation_identity",
    (
        "runtime_probe_local_python_subprocess_invocation:not-a-digest",
        "runtime_probe_local_python_subprocess_invocation:" + ("0" * 64),
    ),
)
def test_dynamic_import_worker_request_rejects_malformed_replay_identity(
    invocation_identity: str,
) -> None:
    """Invocation identity must match the copied replay-sensitive payload fields."""
    payload = _valid_worker_payload()
    object.__setattr__(
        payload,
        "invocation_identity",
        invocation_identity,
    )

    with pytest.raises(ValueError, match="invocation_identity"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )


def test_dynamic_import_worker_request_preserves_argv_paths_and_invocation() -> None:
    """Argv, Python path order, and invocation identity survive materialization."""
    payload = _valid_worker_payload(
        python_path_entries=(
            "/workspace/context-ir/tests/fixtures",
            "/workspace/context-ir/src",
        )
    )
    request = (
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
            payload
        )
    )

    assert request.argv == payload.argv
    assert request.python_path_entries == (
        "/workspace/context-ir/tests/fixtures",
        "/workspace/context-ir/src",
    )
    assert request.invocation_identity == payload.invocation_identity


@pytest.mark.parametrize(
    (
        "source_file_path",
        "replay_target_seed",
        "source_module_name",
        "replay_target_attribute_path",
    ),
    (
        ("main.py", "main.run", "main", ("run",)),
        (
            "pkg/runtime.py",
            "pkg.runtime.resolve_plugin",
            "pkg.runtime",
            ("resolve_plugin",),
        ),
        (
            "pkg/__init__.py",
            "pkg.bootstrap.resolve",
            "pkg",
            ("bootstrap", "resolve"),
        ),
    ),
)
def test_dynamic_import_replay_target_derives_module_and_attribute_path(
    source_file_path: str,
    replay_target_seed: str,
    source_module_name: str,
    replay_target_attribute_path: tuple[str, ...],
) -> None:
    """Replay targets derive source modules and target attributes without imports."""
    request = _valid_dynamic_import_worker_request(
        source_file_path=source_file_path,
        replay_target_seed=replay_target_seed,
    )

    replay_target = (
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target(
            request
        )
    )

    assert replay_target.request is request
    assert replay_target.plan_id == request.plan_id
    assert replay_target.request_id == request.request_id
    assert replay_target.source_file_path == source_file_path
    assert replay_target.source_module_name == source_module_name
    assert replay_target.replay_target_seed == replay_target_seed
    assert replay_target.replay_target_attribute_path == replay_target_attribute_path
    assert replay_target.replay_selector_seed == request.replay_selector_seed
    assert replay_target.invocation_identity == request.invocation_identity
    assert replay_target.request_replay_payload_fields is (
        request.request_replay_payload_fields
    )


def test_dynamic_import_replay_target_contract_is_frozen() -> None:
    """Worker-local replay targets are immutable non-executing contracts."""
    replay_target = _valid_dynamic_import_replay_target()

    with pytest.raises(FrozenInstanceError):
        replay_target.source_module_name = "other"


def test_dynamic_import_replay_target_revalidates_request() -> None:
    """Replay target materialization reruns worker request validation."""
    request = _valid_dynamic_import_worker_request()
    object.__setattr__(request, "source_start_line", 0)

    with pytest.raises(ValueError, match="source span"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target(
            request
        )


def test_dynamic_import_replay_target_constructor_rejects_drift() -> None:
    """Direct dataclass construction reruns derived target validation."""
    replay_target = _valid_dynamic_import_replay_target()

    with pytest.raises(ValueError, match="source_module_name"):
        replace(replay_target, source_module_name="main.other")
    with pytest.raises(ValueError, match="replay_target_attribute_path"):
        replace(replay_target, replay_target_attribute_path=("other",))


@pytest.mark.parametrize(
    ("source_file_path", "replay_target_seed"),
    (
        ("/abs/main.py", "main.run"),
        ("../main.py", "main.run"),
        ("pkg/../runtime.py", "pkg.runtime.run"),
        ("pkg//runtime.py", "pkg.runtime.run"),
        ("pkg/runtime.txt", "pkg.runtime.run"),
        ("pkg/3runtime.py", "pkg.3runtime.run"),
        ("__init__.py", "__init__.run"),
    ),
)
def test_dynamic_import_replay_target_rejects_malformed_source_paths(
    source_file_path: str,
    replay_target_seed: str,
) -> None:
    """Replay targets require strict repository-relative Python source paths."""
    request = _valid_dynamic_import_worker_request(
        source_file_path=source_file_path,
        replay_target_seed=replay_target_seed,
    )

    with pytest.raises(ValueError, match="source"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target(
            request
        )


def test_dynamic_import_replay_target_rejects_source_fallback_seed() -> None:
    """source: fallback seeds remain unsupported by the local replay contract."""
    request = _valid_dynamic_import_worker_request(
        replay_target_seed="source:main.py:3"
    )

    with pytest.raises(ValueError, match="unsupported"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target(
            request
        )


def test_dynamic_import_replay_target_rejects_source_module_drift() -> None:
    """Replay target seeds must be rooted at the derived source module."""
    request = _valid_dynamic_import_worker_request(
        source_file_path="pkg/runtime.py",
        replay_target_seed="pkg.other.run",
    )

    with pytest.raises(ValueError, match="source_module_name"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target(
            request
        )


@pytest.mark.parametrize(
    "replay_target_seed",
    (
        "pkg.runtime",
        "pkg.runtime.",
        "pkg.runtime..run",
        "pkg.runtime.3run",
        "pkg.runtime.run-name",
    ),
)
def test_dynamic_import_replay_target_rejects_malformed_target_segments(
    replay_target_seed: str,
) -> None:
    """Replay target module and attribute segments must be strict identifiers."""
    request = _valid_dynamic_import_worker_request(
        source_file_path="pkg/runtime.py",
        replay_target_seed=replay_target_seed,
    )

    with pytest.raises(ValueError, match="replay_target"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target(
            request
        )


def test_dynamic_import_replay_target_rejects_request_drift() -> None:
    """Replay target validation catches a carried request mutated after creation."""
    request = _valid_dynamic_import_worker_request()
    replay_target = (
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target(
            request
        )
    )
    object.__setattr__(request, "replay_selector_seed", "call:drifted")

    with pytest.raises(ValueError, match="replay_selector_seed"):
        replace(replay_target)


def test_dynamic_import_replay_target_source_import_uses_request_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Source import uses request cwd/path and captures import-time streams."""
    working_directory = tmp_path / "workspace"
    first_python_path = tmp_path / "first-path"
    second_python_path = tmp_path / "second-path"
    working_directory.mkdir()
    first_python_path.mkdir()
    second_python_path.mkdir()
    module_name = "runtime_probe_source_import_env_case"
    replay_target = _valid_dynamic_import_replay_target(
        source_file_path=f"{module_name}.py",
        replay_target_seed=f"{module_name}.run",
        working_directory=str(working_directory),
        python_path_entries=(str(first_python_path), str(second_python_path)),
    )
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    import_calls: list[tuple[str, str | None, str, tuple[str, ...]]] = []
    outer_stdout = StringIO()
    outer_stderr = StringIO()

    def controlled_import_module(
        name: str,
        package: str | None = None,
    ) -> ModuleType:
        print("source stdout runtime_probe_stdout_protocol_revision")
        print("source stderr secret-token /private/tmp", file=sys.stderr)
        import_calls.append(
            (
                name,
                package,
                os.getcwd(),
                tuple(sys.path[:3]),
            )
        )
        imported_module = ModuleType(name)
        imported_module.run = lambda: None
        return imported_module

    monkeypatch.setattr(importlib, "import_module", controlled_import_module)

    with (
        contextlib.redirect_stdout(outer_stdout),
        contextlib.redirect_stderr(outer_stderr),
    ):
        imported_module = _dynamic_import_replay_target_source_module(replay_target)

    assert imported_module.__name__ == module_name
    assert import_calls == [
        (
            module_name,
            None,
            str(working_directory),
            (str(working_directory), str(first_python_path), str(second_python_path)),
        )
    ]
    assert outer_stdout.getvalue() == ""
    assert outer_stderr.getvalue() == ""
    assert sys.path == original_sys_path
    assert os.getcwd() == original_working_directory


def test_dynamic_import_replay_target_source_import_prefers_ordered_python_path(
    tmp_path: Path,
) -> None:
    """Real source imports resolve through the request's ordered Python path."""
    working_directory = tmp_path / "workspace"
    first_python_path = tmp_path / "first-path"
    second_python_path = tmp_path / "second-path"
    working_directory.mkdir()
    first_python_path.mkdir()
    second_python_path.mkdir()
    module_name = "runtime_probe_source_import_order_case"
    first_module_path = first_python_path / f"{module_name}.py"
    second_module_path = second_python_path / f"{module_name}.py"
    first_module_path.write_text(
        'ORIGIN = "first"\n\ndef run():\n    return None\n',
        encoding="utf-8",
    )
    second_module_path.write_text(
        'ORIGIN = "second"\n\ndef run():\n    return None\n',
        encoding="utf-8",
    )
    replay_target = _valid_dynamic_import_replay_target(
        source_file_path=f"{module_name}.py",
        replay_target_seed=f"{module_name}.run",
        working_directory=str(working_directory),
        python_path_entries=(str(first_python_path), str(second_python_path)),
    )
    sys.modules.pop(module_name, None)

    try:
        imported_module = _dynamic_import_replay_target_source_module(replay_target)
    finally:
        sys.modules.pop(module_name, None)

    assert imported_module.__name__ == module_name
    assert imported_module.ORIGIN == "first"


def test_dynamic_import_replay_target_source_import_rejects_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replay-target drift is rejected before mutating import state."""
    replay_target = _valid_dynamic_import_replay_target()
    object.__setattr__(replay_target, "request_id", "runtime_probe:wrong")
    import_calls: list[str] = []
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()

    def controlled_import_module(
        name: str,
        package: str | None = None,
    ) -> ModuleType:
        del package
        import_calls.append(name)
        return ModuleType(name)

    monkeypatch.setattr(importlib, "import_module", controlled_import_module)

    with pytest.raises(ValueError, match="request_id"):
        _dynamic_import_replay_target_source_module(replay_target)

    assert import_calls == []
    assert sys.path == original_sys_path
    assert os.getcwd() == original_working_directory


def test_dynamic_import_replay_target_source_import_rejects_import_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Import failures use deterministic errors without leaking raw streams."""
    working_directory = tmp_path / "workspace"
    python_path = tmp_path / "python-path"
    working_directory.mkdir()
    python_path.mkdir()
    module_name = "runtime_probe_source_import_failure_case"
    replay_target = _valid_dynamic_import_replay_target(
        source_file_path=f"{module_name}.py",
        replay_target_seed=f"{module_name}.run",
        working_directory=str(working_directory),
        python_path_entries=(str(python_path),),
    )
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    outer_stdout = StringIO()
    outer_stderr = StringIO()

    def controlled_import_module(
        name: str,
        package: str | None = None,
    ) -> ModuleType:
        del name, package
        print("source stdout runtime_probe_stdout_protocol_revision")
        print("source stderr secret-token /private/tmp", file=sys.stderr)
        raise RuntimeError("source import failed with secret-token /private/tmp")

    monkeypatch.setattr(importlib, "import_module", controlled_import_module)

    with (
        contextlib.redirect_stdout(outer_stdout),
        contextlib.redirect_stderr(outer_stderr),
        pytest.raises(ValueError, match="source module import failed") as error_info,
    ):
        _dynamic_import_replay_target_source_module(replay_target)

    assert isinstance(error_info.value.__cause__, RuntimeError)
    assert "secret-token" not in str(error_info.value)
    assert "/private/tmp" not in str(error_info.value)
    assert outer_stdout.getvalue() == ""
    assert outer_stderr.getvalue() == ""
    assert sys.path == original_sys_path
    assert os.getcwd() == original_working_directory


@pytest.mark.parametrize(
    ("returned_module", "error_match"),
    (
        (cast(ModuleType, object()), "source module"),
        (ModuleType("runtime_probe_source_import_drifted"), "source_module_name"),
    ),
)
def test_dynamic_import_replay_target_source_import_rejects_malformed_results(
    returned_module: ModuleType,
    error_match: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Imported source modules must be typed and match the replay target name."""
    working_directory = tmp_path / "workspace"
    python_path = tmp_path / "python-path"
    working_directory.mkdir()
    python_path.mkdir()
    module_name = "runtime_probe_source_import_validation_case"
    replay_target = _valid_dynamic_import_replay_target(
        source_file_path=f"{module_name}.py",
        replay_target_seed=f"{module_name}.run",
        working_directory=str(working_directory),
        python_path_entries=(str(python_path),),
    )
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()

    def controlled_import_module(
        name: str,
        package: str | None = None,
    ) -> ModuleType:
        del name, package
        return returned_module

    monkeypatch.setattr(importlib, "import_module", controlled_import_module)

    with pytest.raises(ValueError, match=error_match):
        _dynamic_import_replay_target_source_module(replay_target)

    assert sys.path == original_sys_path
    assert os.getcwd() == original_working_directory


def test_dynamic_import_replay_target_resolver_returns_injected_callable() -> None:
    """The resolver walks an injected module attribute path without execution."""
    replay_target = _valid_dynamic_import_replay_target(
        source_file_path="pkg/runtime.py",
        replay_target_seed="pkg.runtime.bootstrap.resolve",
    )
    source_module = ModuleType("pkg.runtime")
    nested_target_container = ModuleType("pkg.runtime.bootstrap")
    target_calls: list[str] = []

    def target() -> object:
        target_calls.append("called")
        return importlib.import_module("plugins.weather")

    nested_target_container.resolve = target
    source_module.bootstrap = nested_target_container

    resolved_target = _dynamic_import_replay_target_callable(
        replay_target,
        source_module,
    )

    assert resolved_target is target
    assert target_calls == []
    assert "plugins.weather" not in sys.modules


def test_dynamic_import_replay_target_resolver_rejects_nonmodule_source() -> None:
    """Replay target resolution requires an injected source module object."""
    replay_target = _valid_dynamic_import_replay_target()
    source_module = cast(ModuleType, object())

    with pytest.raises(ValueError, match="source module"):
        _dynamic_import_replay_target_callable(
            replay_target,
            source_module,
        )


def test_dynamic_import_replay_target_resolver_rejects_source_module_drift() -> None:
    """Injected source modules must match the replay target module identity."""
    replay_target = _valid_dynamic_import_replay_target()
    source_module = ModuleType("other")
    source_module.run = lambda: None

    with pytest.raises(ValueError, match="source_module_name"):
        _dynamic_import_replay_target_callable(
            replay_target,
            source_module,
        )


def test_dynamic_import_replay_target_resolver_rejects_request_drift() -> None:
    """Resolution revalidates the carried request before attribute lookup."""
    replay_target = _valid_dynamic_import_replay_target()
    source_module = ModuleType("main")
    target_calls: list[str] = []

    def target() -> None:
        target_calls.append("called")

    source_module.run = target
    object.__setattr__(replay_target.request, "replay_selector_seed", "call:drifted")

    with pytest.raises(ValueError, match="replay_selector_seed"):
        _dynamic_import_replay_target_callable(
            replay_target,
            source_module,
        )

    assert target_calls == []


def test_dynamic_import_replay_target_resolver_rejects_replay_target_drift() -> None:
    """Resolution rejects replay target copies that drift from their request."""
    replay_target = _valid_dynamic_import_replay_target()
    source_module = ModuleType("main")
    source_module.run = lambda: None
    object.__setattr__(replay_target, "request_id", "runtime_probe:wrong")

    with pytest.raises(ValueError, match="request_id"):
        _dynamic_import_replay_target_callable(
            replay_target,
            source_module,
        )


def test_dynamic_import_replay_target_resolver_rejects_missing_attribute() -> None:
    """Missing replay target attributes fail without importing or executing code."""
    replay_target = _valid_dynamic_import_replay_target(
        source_file_path="pkg/runtime.py",
        replay_target_seed="pkg.runtime.bootstrap.resolve",
    )
    source_module = ModuleType("pkg.runtime")
    source_module.bootstrap = ModuleType("pkg.runtime.bootstrap")

    with pytest.raises(ValueError, match="attribute_path"):
        _dynamic_import_replay_target_callable(
            replay_target,
            source_module,
        )


def test_dynamic_import_replay_target_resolver_rejects_noncallable_target() -> None:
    """The final resolved attribute must be a callable harness target."""
    replay_target = _valid_dynamic_import_replay_target()
    source_module = ModuleType("main")
    source_module.run = object()

    with pytest.raises(ValueError, match="target"):
        _dynamic_import_replay_target_callable(
            replay_target,
            source_module,
        )


def test_dynamic_import_worker_observation_materializes_replay_identity() -> None:
    """The worker derives observation metadata from a validated request."""
    request = _valid_dynamic_import_worker_request()
    observation = _valid_dynamic_import_worker_observation(request=request)

    assert observation.request is request
    assert observation.plan_id == request.plan_id
    assert observation.request_id == request.request_id
    assert observation.replay_target_seed == request.replay_target_seed
    assert observation.replay_selector_seed == request.replay_selector_seed
    assert (
        observation.invocation_contract_revision == request.invocation_contract_revision
    )
    assert observation.invocation_identity == request.invocation_identity
    assert observation.request_replay_payload_fields is (
        request.request_replay_payload_fields
    )
    assert observation.imported_module == "plugins.weather"


def test_dynamic_import_worker_observation_success_response_is_deterministic() -> None:
    """Observation proof metadata emits one deterministic imported-module field."""
    observation = _valid_dynamic_import_worker_observation()

    response = _dynamic_import_worker_success_response(observation)
    stdout_text = _serialize_worker_success_response(response)

    assert response.normalized_payload == (
        _field("imported_module", "plugins.weather"),
    )
    assert response.durable_artifact_reference is None
    assert stdout_text == (
        '{"runtime_probe_stdout_protocol_revision":'
        '"runtime_probe_local_python_stdout_protocol:v1",'
        '"normalized_payload":['
        '{"key":"imported_module","value":"plugins.weather"}]}'
    )


def test_dynamic_import_worker_observation_contract_is_frozen() -> None:
    """Dynamic-import observation metadata is immutable before response emission."""
    observation = _valid_dynamic_import_worker_observation()

    with pytest.raises(FrozenInstanceError):
        observation.imported_module = "plugins.forecast"


def test_dynamic_import_worker_observation_constructor_rejects_identity_drift() -> None:
    """Direct observation construction reruns request identity validation."""
    observation = _valid_dynamic_import_worker_observation()

    with pytest.raises(ValueError, match="request_id"):
        replace(observation, request_id="runtime_probe:wrong")
    with pytest.raises(ValueError, match="imported_module"):
        replace(observation, imported_module=" plugins.weather")


@pytest.mark.parametrize(
    "imported_module",
    (
        "",
        " ",
        " plugins.weather",
        "plugins.weather ",
        "plugins\nweather",
        ".plugins.weather",
        "..plugins",
        "plugins.",
        "plugins..weather",
        "plugins-weather",
        "plugins.3weather",
        "plugins.weather!",
    ),
)
def test_dynamic_import_worker_observation_rejects_invalid_imported_module(
    imported_module: str,
) -> None:
    """Observed module names must be strict absolute dotted identifiers."""
    request = _valid_dynamic_import_worker_request()

    with pytest.raises(ValueError, match="imported_module"):
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_observation(
            request,
            imported_module=imported_module,
        )


def test_dynamic_import_worker_observation_rejects_request_drift() -> None:
    """Success response materialization rechecks the carried request identity."""
    request = _valid_dynamic_import_worker_request()
    observation = _valid_dynamic_import_worker_observation(request=request)
    object.__setattr__(request, "replay_selector_seed", "call:drifted")

    with pytest.raises(ValueError, match="replay_selector_seed"):
        _dynamic_import_worker_success_response(observation)


def test_dynamic_import_worker_target_harness_observes_request_import() -> None:
    """The target harness captures one import-module call from a worker request."""
    request = _valid_dynamic_import_worker_request()
    original_import_module = importlib.import_module
    outer_stdout = StringIO()
    outer_stderr = StringIO()

    def target() -> object:
        print("target stdout secret-token")
        print("target stderr /private/tmp", file=sys.stderr)
        imported_module = importlib.import_module("plugins.weather")
        assert imported_module.__name__ == "plugins.weather"
        return imported_module

    with (
        contextlib.redirect_stdout(outer_stdout),
        contextlib.redirect_stderr(outer_stderr),
    ):
        observation = _dynamic_import_worker_observation_from_target(request, target)

    assert observation.request is request
    assert observation.imported_module == "plugins.weather"
    assert outer_stdout.getvalue() == ""
    assert outer_stderr.getvalue() == ""
    assert importlib.import_module is original_import_module


def test_dynamic_import_worker_target_harness_accepts_replay_target() -> None:
    """Replay-target observation does not import or resolve the source module."""
    request = _valid_dynamic_import_worker_request(
        source_file_path="runtime_probe_unique_source.py",
        replay_target_seed="runtime_probe_unique_source.run",
    )
    replay_target = (
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target(
            request
        )
    )
    observed_module_name = "plugins.runtime_probe_unique_observed"
    assert replay_target.source_module_name not in sys.modules
    assert observed_module_name not in sys.modules

    def target() -> None:
        importlib.import_module(observed_module_name)

    observation = _dynamic_import_worker_observation_from_target(replay_target, target)

    assert observation.request is request
    assert observation.imported_module == observed_module_name
    assert replay_target.source_module_name not in sys.modules
    assert observed_module_name not in sys.modules


def test_dynamic_import_worker_target_harness_is_worker_stdout_safe() -> None:
    """Target stdout and stderr cannot contaminate the worker stdout protocol."""

    def observer(request: DynamicImportWorkerRequest) -> DynamicImportWorkerObservation:
        def target() -> None:
            print("target stdout runtime_probe_stdout_protocol_revision")
            print("target stderr secret-token /private/tmp", file=sys.stderr)
            importlib.import_module("plugins.protocol_safe")

        return _dynamic_import_worker_observation_from_target(request, target)

    entry = (
        runtime_probe_worker.build_runtime_probe_dynamic_import_worker_handler_entry(
            observer
        )
    )
    worker_stdout = StringIO()
    worker_stderr = StringIO()

    with (
        contextlib.redirect_stdout(worker_stdout),
        contextlib.redirect_stderr(worker_stderr),
    ):
        exit_code = runtime_probe_worker.main(
            stdin=StringIO(_valid_worker_stdin_text()),
            handler_entries=(entry,),
        )
    stdout_text = worker_stdout.getvalue()
    stderr_text = worker_stderr.getvalue()

    assert exit_code == 0
    assert stderr_text == ""
    assert stdout_text == (
        '{"runtime_probe_stdout_protocol_revision":'
        '"runtime_probe_local_python_stdout_protocol:v1",'
        '"normalized_payload":['
        '{"key":"imported_module","value":"plugins.protocol_safe"}]}'
    )
    assert "target stdout" not in stdout_text
    assert "target stderr" not in stderr_text


@pytest.mark.parametrize(
    ("target", "error_match"),
    (
        (lambda: None, "exactly one"),
        (
            lambda: (
                importlib.import_module("plugins.first"),
                importlib.import_module("plugins.second"),
            ),
            "exactly one",
        ),
        (lambda: importlib.import_module("plugins-weather"), "module name"),
        (lambda: importlib.import_module(".weather"), "relative"),
        (
            lambda: importlib.import_module(
                "plugins.weather",
                package="plugins",
            ),
            "package",
        ),
    ),
)
def test_dynamic_import_worker_target_harness_rejects_bad_import_shapes(
    target: runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportTargetCallable,
    error_match: str,
) -> None:
    """The harness accepts exactly one absolute import-module call."""
    request = _valid_dynamic_import_worker_request()
    original_import_module = importlib.import_module

    with pytest.raises(ValueError, match=error_match):
        _dynamic_import_worker_observation_from_target(request, target)

    assert importlib.import_module is original_import_module


def test_dynamic_import_worker_target_harness_rejects_caught_errors() -> None:
    """Rejected import shapes remain rejected even if the target catches them."""
    request = _valid_dynamic_import_worker_request()

    def target() -> None:
        with contextlib.suppress(ValueError):
            importlib.import_module(".weather")

    with pytest.raises(ValueError, match="relative"):
        _dynamic_import_worker_observation_from_target(request, target)


def test_dynamic_import_worker_target_harness_rejects_noncallable_target() -> None:
    """Non-callable target injections are rejected before wrapper installation."""
    request = _valid_dynamic_import_worker_request()
    original_import_module = importlib.import_module
    target = cast(
        runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportTargetCallable,
        object(),
    )

    with pytest.raises(ValueError, match="target"):
        _dynamic_import_worker_observation_from_target(request, target)

    assert importlib.import_module is original_import_module


def test_dynamic_import_worker_target_harness_rejects_replay_target_drift() -> None:
    """Replay-target drift is rejected before the injected target is invoked."""
    replay_target = _valid_dynamic_import_replay_target()
    object.__setattr__(replay_target, "request_id", "runtime_probe:wrong")
    target_calls: list[str] = []

    def target() -> None:
        target_calls.append("called")
        importlib.import_module("plugins.weather")

    with pytest.raises(ValueError, match="request_id"):
        _dynamic_import_worker_observation_from_target(replay_target, target)

    assert target_calls == []


def test_dynamic_import_worker_target_harness_restores_wrapper_on_failure() -> None:
    """The import-module wrapper is restored when target execution raises."""
    request = _valid_dynamic_import_worker_request()
    original_import_module = importlib.import_module

    def target() -> None:
        importlib.import_module("plugins.weather")
        raise RuntimeError("target failed with secret-token")

    with pytest.raises(RuntimeError, match="target failed"):
        _dynamic_import_worker_observation_from_target(request, target)

    assert importlib.import_module is original_import_module


def test_dynamic_import_worker_concrete_observer_observes_source_target(
    tmp_path: Path,
) -> None:
    """The concrete observer imports, resolves, executes, and observes one request."""
    module_name = "runtime_probe_concrete_observer_success_case"
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        source_text=(
            "import importlib\n"
            "import sys\n\n"
            'print("source stdout runtime_probe_stdout_protocol_revision")\n'
            'print("source stderr secret-token /private/tmp", file=sys.stderr)\n\n'
            "def run():\n"
            '    print("target stdout runtime_probe_stdout_protocol_revision")\n'
            '    print("target stderr secret-token /private/tmp", file=sys.stderr)\n'
            '    return importlib.import_module("plugins.composed")\n'
        ),
    )
    original_import_module = importlib.import_module
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    outer_stdout = StringIO()
    outer_stderr = StringIO()
    sys.modules.pop(module_name, None)
    sys.modules.pop("plugins.composed", None)

    try:
        with (
            contextlib.redirect_stdout(outer_stdout),
            contextlib.redirect_stderr(outer_stderr),
        ):
            observation = _observe_dynamic_import_worker_request(request)
    finally:
        sys.modules.pop(module_name, None)
        sys.modules.pop("plugins.composed", None)

    assert observation.request is request
    assert observation.imported_module == "plugins.composed"
    assert outer_stdout.getvalue() == ""
    assert outer_stderr.getvalue() == ""
    assert sys.path == original_sys_path
    assert os.getcwd() == original_working_directory
    assert importlib.import_module is original_import_module


def test_dynamic_import_worker_concrete_observer_is_handler_injectable(
    tmp_path: Path,
) -> None:
    """The concrete observer can be injected through the existing handler factory."""
    module_name = "runtime_probe_concrete_observer_handler_case"
    source_text = (
        "import importlib\n\n"
        "def run():\n"
        '    return importlib.import_module("plugins.handler_observed")\n'
    )
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        source_text=source_text,
    )
    payload = _valid_worker_payload(
        source_file_path=request.source_file_path,
        replay_target_seed=request.replay_target_seed,
        working_directory=request.working_directory,
        python_path_entries=request.python_path_entries,
    )
    observer = getattr(runtime_probe_worker, _DYNAMIC_IMPORT_CONCRETE_OBSERVER_HELPER)
    entry = (
        runtime_probe_worker.build_runtime_probe_dynamic_import_worker_handler_entry(
            observer
        )
    )
    sys.modules.pop(module_name, None)

    try:
        exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
            serialize_runtime_probe_local_python_worker_request_payload(payload),
            (entry,),
        )
    finally:
        sys.modules.pop(module_name, None)

    assert exit_code == 0
    assert stderr_text == ""
    assert stdout_text == (
        '{"runtime_probe_stdout_protocol_revision":'
        '"runtime_probe_local_python_stdout_protocol:v1",'
        '"normalized_payload":['
        '{"key":"imported_module","value":"plugins.handler_observed"}]}'
    )


def test_dynamic_import_worker_default_handler_dispatches_concrete_observer(
    tmp_path: Path,
) -> None:
    """Omitted handler entries use the concrete dynamic-import observer."""
    module_name = "runtime_probe_default_observer_success_case"
    source_text = (
        "import importlib\n"
        "import sys\n\n"
        'print("source stdout runtime_probe_stdout_protocol_revision")\n'
        'print("source stderr secret-token /private/tmp", file=sys.stderr)\n\n'
        "def run():\n"
        '    print("target stdout runtime_probe_stdout_protocol_revision")\n'
        '    print("target stderr secret-token /private/tmp", file=sys.stderr)\n'
        '    return importlib.import_module("plugins.default_observed")\n'
    )
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        source_text=source_text,
    )
    payload = _valid_worker_payload(
        source_file_path=request.source_file_path,
        replay_target_seed=request.replay_target_seed,
        working_directory=request.working_directory,
        python_path_entries=request.python_path_entries,
    )
    sys.modules.pop(module_name, None)

    try:
        exit_code, stdout_text, stderr_text = _run_worker_with_default_handlers(
            serialize_runtime_probe_local_python_worker_request_payload(payload)
        )
    finally:
        sys.modules.pop(module_name, None)

    assert exit_code == 0
    assert stderr_text == ""
    assert stdout_text == (
        '{"runtime_probe_stdout_protocol_revision":'
        '"runtime_probe_local_python_stdout_protocol:v1",'
        '"normalized_payload":['
        '{"key":"imported_module","value":"plugins.default_observed"}]}'
    )
    assert "source stdout" not in stdout_text
    assert "target stdout" not in stdout_text


def test_dynamic_import_worker_default_subprocess_observes_loader_import_module(
    tmp_path: Path,
) -> None:
    """The real worker module observes loader.import_module through defaults."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    module_name = "runtime_probe_loader_default_worker_case"
    (tmp_path / f"{module_name}.py").write_text(
        (
            "import importlib as loader\n\n"
            "def run():\n"
            '    return loader.import_module("plugins.loader_worker_subprocess")\n'
        ),
        encoding="utf-8",
    )
    payload = _valid_worker_payload(
        source_file_path=f"{module_name}.py",
        replay_target_seed=f"{module_name}.run",
        form_label=_LOADER_IMPORT_MODULE_FORM_LABEL,
        python_executable=sys.executable,
        working_directory=str(tmp_path),
        python_path_entries=(project_source_path,),
    )

    completed = subprocess.run(
        (sys.executable, "-m", "context_ir.runtime_probe_worker"),
        input=serialize_runtime_probe_local_python_worker_request_payload(payload),
        text=True,
        capture_output=True,
        cwd=str(tmp_path),
        env={**os.environ, "PYTHONPATH": project_source_path},
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    protocol_payload = json.loads(completed.stdout)
    assert protocol_payload == {
        "runtime_probe_stdout_protocol_revision": (
            "runtime_probe_local_python_stdout_protocol:v1"
        ),
        "normalized_payload": [
            {
                "key": "imported_module",
                "value": "plugins.loader_worker_subprocess",
            },
        ],
    }


def test_dynamic_import_worker_concrete_observer_observes_imported_import_module(
    tmp_path: Path,
) -> None:
    """The concrete observer captures a source-global imported import_module."""
    module_name = "runtime_probe_imported_name_concrete_observer_case"
    observed_module_name = "plugins.imported_name_concrete"
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        form_label=_IMPORTED_IMPORT_MODULE_FORM_LABEL,
        source_text=(
            "from importlib import import_module\n"
            "import sys\n\n"
            "def run():\n"
            '    print("target stdout runtime_probe_stdout_protocol_revision")\n'
            '    print("target stderr secret-token /private/tmp", file=sys.stderr)\n'
            f'    return import_module("{observed_module_name}")\n'
        ),
    )
    original_import_module = importlib.import_module
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    outer_stdout = StringIO()
    outer_stderr = StringIO()
    sys.modules.pop(module_name, None)
    sys.modules.pop(observed_module_name, None)

    try:
        with (
            contextlib.redirect_stdout(outer_stdout),
            contextlib.redirect_stderr(outer_stderr),
        ):
            observation = _observe_dynamic_import_worker_request(request)
        source_module = sys.modules[module_name]
        assert source_module.__dict__["import_module"] is original_import_module
        assert observed_module_name not in sys.modules
    finally:
        sys.modules.pop(module_name, None)
        sys.modules.pop(observed_module_name, None)

    assert observation.request is request
    assert observation.imported_module == observed_module_name
    assert outer_stdout.getvalue() == ""
    assert outer_stderr.getvalue() == ""
    assert sys.path == original_sys_path
    assert os.getcwd() == original_working_directory
    assert importlib.import_module is original_import_module


@pytest.mark.parametrize(
    ("source_text", "error_match"),
    (
        (
            (
                "import importlib\n\n"
                "def run():\n"
                '    return importlib.import_module("plugins.not_reached")\n'
            ),
            "import_module global is missing",
        ),
        (
            (
                "import_module = object()\n\n"
                "def run():\n"
                '    raise AssertionError("target should not execute")\n'
            ),
            "import_module global must be importlib.import_module",
        ),
    ),
)
def test_dynamic_import_worker_concrete_observer_rejects_imported_global_drift(
    source_text: str,
    error_match: str,
    tmp_path: Path,
) -> None:
    """Imported-name forms fail closed unless the module global is exact."""
    module_name = "runtime_probe_imported_name_global_validation_case"
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        form_label=_IMPORTED_IMPORT_MODULE_FORM_LABEL,
        source_text=source_text,
    )
    original_import_module = importlib.import_module
    sys.modules.pop(module_name, None)
    sys.modules.pop("plugins.not_reached", None)

    try:
        with pytest.raises(ValueError, match=error_match):
            _observe_dynamic_import_worker_request(request)
    finally:
        sys.modules.pop(module_name, None)
        sys.modules.pop("plugins.not_reached", None)

    assert importlib.import_module is original_import_module
    assert "plugins.not_reached" not in sys.modules


def test_dynamic_import_worker_concrete_observer_restores_imported_global_on_drift(
    tmp_path: Path,
) -> None:
    """Imported-name global tampering fails closed after restoring the source."""
    module_name = "runtime_probe_imported_name_restore_validation_case"
    observed_module_name = "plugins.imported_name_restore"
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        form_label=_IMPORTED_IMPORT_MODULE_FORM_LABEL,
        source_text=(
            "from importlib import import_module\n\n"
            "def run():\n"
            "    global import_module\n"
            f'    imported_module = import_module("{observed_module_name}")\n'
            "    import_module = object()\n"
            "    return imported_module\n"
        ),
    )
    original_import_module = importlib.import_module
    sys.modules.pop(module_name, None)
    sys.modules.pop(observed_module_name, None)

    try:
        with pytest.raises(ValueError, match="import_module global changed"):
            _observe_dynamic_import_worker_request(request)
        source_module = sys.modules[module_name]
        assert source_module.__dict__["import_module"] is original_import_module
        assert observed_module_name not in sys.modules
    finally:
        sys.modules.pop(module_name, None)
        sys.modules.pop(observed_module_name, None)

    assert importlib.import_module is original_import_module


def test_dynamic_import_worker_default_subprocess_observes_imported_import_module(
    tmp_path: Path,
) -> None:
    """The real worker module observes imported import_module through defaults."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    module_name = "runtime_probe_imported_name_default_worker_case"
    (tmp_path / f"{module_name}.py").write_text(
        (
            "from importlib import import_module\n\n"
            "def run():\n"
            '    return import_module("plugins.imported_name_worker_subprocess")\n'
        ),
        encoding="utf-8",
    )
    payload = _valid_worker_payload(
        source_file_path=f"{module_name}.py",
        replay_target_seed=f"{module_name}.run",
        form_label=_IMPORTED_IMPORT_MODULE_FORM_LABEL,
        python_executable=sys.executable,
        working_directory=str(tmp_path),
        python_path_entries=(project_source_path,),
    )

    completed = subprocess.run(
        (sys.executable, "-m", "context_ir.runtime_probe_worker"),
        input=serialize_runtime_probe_local_python_worker_request_payload(payload),
        text=True,
        capture_output=True,
        cwd=str(tmp_path),
        env={**os.environ, "PYTHONPATH": project_source_path},
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    protocol_payload = json.loads(completed.stdout)
    assert protocol_payload == {
        "runtime_probe_stdout_protocol_revision": (
            "runtime_probe_local_python_stdout_protocol:v1"
        ),
        "normalized_payload": [
            {
                "key": "imported_module",
                "value": "plugins.imported_name_worker_subprocess",
            },
        ],
    }


def test_dynamic_import_worker_default_handler_observer_failure_fails_closed(
    tmp_path: Path,
) -> None:
    """Default concrete observer failures stay sanitized at the main boundary."""
    module_name = "runtime_probe_default_observer_failure_case"
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        source_text=(
            "def run():\n"
            '    raise RuntimeError("target failed with secret-token /private/tmp")\n'
        ),
    )
    payload = _valid_worker_payload(
        source_file_path=request.source_file_path,
        replay_target_seed=request.replay_target_seed,
        working_directory=request.working_directory,
        python_path_entries=request.python_path_entries,
    )
    stdin_text = serialize_runtime_probe_local_python_worker_request_payload(payload)
    sys.modules.pop(module_name, None)

    try:
        exit_code, stdout_text, stderr_text = _run_worker_with_default_handlers(
            stdin_text
        )
    finally:
        sys.modules.pop(module_name, None)

    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert stderr_text == "runtime_probe_worker: rejected worker handler failure\n"
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


@pytest.mark.parametrize(
    ("family_label", "form_label", "reason_code", "boundary_text"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            "dynamic_import:other_form/1",
            UnresolvedReasonCode.DYNAMIC_IMPORT,
            "importlib.import_module(name)",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            "reflective_builtin:getattr/2",
            UnresolvedReasonCode.REFLECTIVE_BUILTIN,
            "getattr(obj, name)",
        ),
    ),
)
def test_dynamic_import_worker_default_handler_rejects_unsupported_family_form(
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
    reason_code: UnresolvedReasonCode,
    boundary_text: str,
) -> None:
    """The omitted-handler default table is limited to one dynamic-import form."""
    request = replace(
        _request(),
        family_label=family_label,
        form_label=form_label,
        reason_code=reason_code,
        boundary_text=boundary_text,
        replay_selector_seed=f"call:main.run:{form_label}@main.py:3:4:3:28",
    )
    invocation = _valid_worker_invocation_for_request(request)
    payload = materialize_runtime_probe_local_python_worker_request_payload(invocation)
    stdin_text = serialize_runtime_probe_local_python_worker_request_payload(payload)

    exit_code, stdout_text, stderr_text = _run_worker_with_default_handlers(stdin_text)

    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert (
        stderr_text
        == "runtime_probe_worker: rejected worker request without executing probe\n"
    )
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_dynamic_import_worker_concrete_observer_revalidates_request_before_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Drifted requests fail before the concrete observer mutates import state."""
    request = _valid_dynamic_import_worker_request()
    object.__setattr__(request, "replay_selector_seed", "call:drifted")
    import_calls: list[str] = []
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()

    def controlled_import_module(
        name: str,
        package: str | None = None,
    ) -> ModuleType:
        del package
        import_calls.append(name)
        return ModuleType(name)

    monkeypatch.setattr(importlib, "import_module", controlled_import_module)

    with pytest.raises(ValueError, match="replay_selector_seed"):
        _observe_dynamic_import_worker_request(request)

    assert import_calls == []
    assert sys.path == original_sys_path
    assert os.getcwd() == original_working_directory


def test_dynamic_import_worker_concrete_observer_rejects_source_import_failure(
    tmp_path: Path,
) -> None:
    """Source import failures stay deterministic and stream-shielded."""
    module_name = "runtime_probe_concrete_observer_source_failure_case"
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        source_text=(
            "import sys\n"
            'print("source stdout runtime_probe_stdout_protocol_revision")\n'
            'print("source stderr secret-token /private/tmp", file=sys.stderr)\n'
            'raise RuntimeError("source failed with secret-token /private/tmp")\n'
        ),
    )
    outer_stdout = StringIO()
    outer_stderr = StringIO()
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    sys.modules.pop(module_name, None)

    try:
        with (
            contextlib.redirect_stdout(outer_stdout),
            contextlib.redirect_stderr(outer_stderr),
            pytest.raises(
                ValueError,
                match="source module import failed",
            ) as error_info,
        ):
            _observe_dynamic_import_worker_request(request)
    finally:
        sys.modules.pop(module_name, None)

    assert "secret-token" not in str(error_info.value)
    assert "/private/tmp" not in str(error_info.value)
    assert outer_stdout.getvalue() == ""
    assert outer_stderr.getvalue() == ""
    assert sys.path == original_sys_path
    assert os.getcwd() == original_working_directory


@pytest.mark.parametrize(
    ("source_text", "error_match"),
    (
        ("VALUE = 1\n", "attribute_path"),
        ("run = object()\n", "target"),
    ),
)
def test_dynamic_import_worker_concrete_observer_rejects_bad_target_resolution(
    source_text: str,
    error_match: str,
    tmp_path: Path,
) -> None:
    """Missing and non-callable concrete replay targets fail closed."""
    module_name = "runtime_probe_concrete_observer_target_resolution_case"
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        source_text=source_text,
    )
    sys.modules.pop(module_name, None)

    try:
        with pytest.raises(ValueError, match=error_match):
            _observe_dynamic_import_worker_request(request)
    finally:
        sys.modules.pop(module_name, None)


@pytest.mark.parametrize(
    ("target_body", "error_match"),
    (
        ("    return None\n", "exactly one"),
        ('    return importlib.import_module("plugins-weather")\n', "module name"),
        ('    return importlib.import_module(".weather")\n', "relative"),
        (
            (
                '    return importlib.import_module("plugins.weather", '
                'package="plugins")\n'
            ),
            "package",
        ),
    ),
)
def test_dynamic_import_worker_concrete_observer_rejects_bad_import_shapes(
    target_body: str,
    error_match: str,
    tmp_path: Path,
) -> None:
    """The concrete observer preserves import-shape rejection semantics."""
    module_name = "runtime_probe_concrete_observer_bad_import_shape_case"
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        source_text="import importlib\n\ndef run():\n" + target_body,
    )
    original_import_module = importlib.import_module
    sys.modules.pop(module_name, None)

    try:
        with pytest.raises(ValueError, match=error_match):
            _observe_dynamic_import_worker_request(request)
    finally:
        sys.modules.pop(module_name, None)

    assert importlib.import_module is original_import_module


@pytest.mark.parametrize(
    "failure_statement",
    (
        'raise RuntimeError("target failed with secret-token /private/tmp")',
        'raise ValueError("target failed with secret-token /private/tmp")',
    ),
)
def test_dynamic_import_worker_concrete_observer_rejects_target_execution_failure(
    failure_statement: str,
    tmp_path: Path,
) -> None:
    """Target exceptions are wrapped as deterministic worker-local failures."""
    module_name = "runtime_probe_concrete_observer_target_failure_case"
    request = _dynamic_import_worker_request_with_source(
        tmp_path,
        module_name=module_name,
        source_text=(
            "import sys\n\n"
            "def run():\n"
            '    print("target stdout runtime_probe_stdout_protocol_revision")\n'
            '    print("target stderr secret-token /private/tmp", file=sys.stderr)\n'
            f"    {failure_statement}\n"
        ),
    )
    original_import_module = importlib.import_module
    outer_stdout = StringIO()
    outer_stderr = StringIO()
    sys.modules.pop(module_name, None)

    try:
        with (
            contextlib.redirect_stdout(outer_stdout),
            contextlib.redirect_stderr(outer_stderr),
            pytest.raises(
                ValueError,
                match="target execution failed",
            ) as error_info,
        ):
            _observe_dynamic_import_worker_request(request)
    finally:
        sys.modules.pop(module_name, None)

    assert "secret-token" not in str(error_info.value)
    assert "/private/tmp" not in str(error_info.value)
    assert outer_stdout.getvalue() == ""
    assert outer_stderr.getvalue() == ""
    assert importlib.import_module is original_import_module


def test_dynamic_import_worker_handler_factory_metadata() -> None:
    """The factory returns the exact dynamic-import family/form handler entry."""

    def observer(request: DynamicImportWorkerRequest) -> DynamicImportWorkerObservation:
        return _valid_dynamic_import_worker_observation(request=request)

    entry = (
        runtime_probe_worker.build_runtime_probe_dynamic_import_worker_handler_entry(
            observer
        )
    )

    assert (
        entry.family_label is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert entry.form_label == "dynamic_import:importlib.import_module/1"
    assert isinstance(
        entry.handler,
        runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter,
    )
    with pytest.raises(FrozenInstanceError):
        entry.handler.observer = observer


def test_dynamic_import_worker_handler_factory_rejects_noncallable_observer() -> None:
    """The injected observer contract is enforced before handler registration."""
    observer = cast(
        runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportWorkerObserver,
        object(),
    )

    with pytest.raises(ValueError, match="observer"):
        runtime_probe_worker.build_runtime_probe_dynamic_import_worker_handler_entry(
            observer
        )


def test_dynamic_import_worker_adapter_materializes_observed_success() -> None:
    """The adapter validates the payload before invoking the observer."""
    observed_requests: list[DynamicImportWorkerRequest] = []

    def observer(request: DynamicImportWorkerRequest) -> DynamicImportWorkerObservation:
        assert isinstance(request, DynamicImportWorkerRequest)
        assert (
            request.family_label
            is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
        )
        assert request.form_label == "dynamic_import:importlib.import_module/1"
        observed_requests.append(request)
        return _valid_dynamic_import_worker_observation(
            request=request,
            imported_module="plugins.forecast",
        )

    adapter = (
        runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter(
            observer=observer
        )
    )

    response = adapter(_valid_worker_payload())

    assert len(observed_requests) == 1
    assert (
        response
        == runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse(
            normalized_payload=(_field("imported_module", "plugins.forecast"),)
        )
    )


def test_dynamic_import_worker_adapter_rejects_payload_before_observer() -> None:
    """Invalid worker payload metadata never reaches the injected observer."""
    observer_calls: list[DynamicImportWorkerRequest] = []

    def observer(request: DynamicImportWorkerRequest) -> DynamicImportWorkerObservation:
        observer_calls.append(request)
        return _valid_dynamic_import_worker_observation(request=request)

    adapter = (
        runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter(
            observer=observer
        )
    )
    payload = _worker_payload_with_replay_field("reason_code", "reflective_builtin")

    with pytest.raises(ValueError, match="reason_code"):
        adapter(payload)

    assert observer_calls == []


def test_dynamic_import_worker_factory_dispatches_success_through_main() -> None:
    """Worker main can consume the injected dynamic-import handler factory."""

    def observer(request: DynamicImportWorkerRequest) -> DynamicImportWorkerObservation:
        return _valid_dynamic_import_worker_observation(
            request=request,
            imported_module="plugins.dispatch",
        )

    entry = (
        runtime_probe_worker.build_runtime_probe_dynamic_import_worker_handler_entry(
            observer
        )
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        _valid_worker_stdin_text(),
        (entry,),
    )

    assert exit_code == 0
    assert stderr_text == ""
    assert stdout_text == (
        '{"runtime_probe_stdout_protocol_revision":'
        '"runtime_probe_local_python_stdout_protocol:v1",'
        '"normalized_payload":['
        '{"key":"imported_module","value":"plugins.dispatch"}]}'
    )


def test_dynamic_import_worker_observer_exception_fails_closed() -> None:
    """Observer exceptions are sanitized through the worker dispatch boundary."""
    stdin_text = _valid_worker_stdin_text()

    def observer(request: DynamicImportWorkerRequest) -> DynamicImportWorkerObservation:
        del request
        raise RuntimeError("handler failed with secret-token /private/tmp Traceback")

    entry = (
        runtime_probe_worker.build_runtime_probe_dynamic_import_worker_handler_entry(
            observer
        )
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )

    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert stderr_text == "runtime_probe_worker: rejected worker handler failure\n"
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_dynamic_import_worker_drifted_observation_fails_closed() -> None:
    """Returned observations are revalidated against the adapted request."""
    stdin_text = _valid_worker_stdin_text()

    def observer(request: DynamicImportWorkerRequest) -> DynamicImportWorkerObservation:
        observation = _valid_dynamic_import_worker_observation(request=request)
        object.__setattr__(observation, "request_id", "runtime_probe:wrong")
        return observation

    adapter = (
        runtime_probe_worker.RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter(
            observer=observer
        )
    )
    with pytest.raises(ValueError, match="request_id"):
        adapter(_valid_worker_payload())

    entry = (
        runtime_probe_worker.build_runtime_probe_dynamic_import_worker_handler_entry(
            observer
        )
    )
    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )

    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert stderr_text == "runtime_probe_worker: rejected worker handler failure\n"
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_valid_worker_request_parses_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid worker stdin is parsed once, then rejected without proof output."""
    stdin_text = _valid_worker_stdin_text()
    parse_calls: list[str] = []
    original_parse = (
        runtime_probe_worker.parse_runtime_probe_local_python_worker_request_payload
    )

    def spy_parse(
        payload_json: str,
    ) -> RuntimeProbeLocalPythonWorkerRequestPayload:
        parse_calls.append(payload_json)
        return original_parse(payload_json)

    monkeypatch.setattr(
        runtime_probe_worker,
        "parse_runtime_probe_local_python_worker_request_payload",
        spy_parse,
    )

    exit_code, stdout_text, stderr_text = _run_worker(stdin_text)

    assert parse_calls == [stdin_text]
    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert (
        stderr_text
        == "runtime_probe_worker: rejected worker request without executing probe\n"
    )
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_registered_worker_handler_dispatches_by_payload_family_and_form() -> None:
    """Injected handlers are routed only by parsed payload family/form metadata."""
    stdin_text = _valid_worker_stdin_text()
    handler_payloads: list[RuntimeProbeLocalPythonWorkerRequestPayload] = []

    def handler(
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> runtime_probe_worker.RuntimeProbeLocalPythonWorkerResponse:
        handler_payloads.append(payload)
        return runtime_probe_worker.RuntimeProbeLocalPythonWorkerResponse()

    entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        handler=handler,
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )

    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert (
        stderr_text
        == "runtime_probe_worker: rejected worker request without executing probe\n"
    )
    assert len(handler_payloads) == 1
    assert (
        handler_payloads[0].family_label
        is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert handler_payloads[0].form_label == (
        "dynamic_import:importlib.import_module/1"
    )
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_missing_worker_handler_fails_closed_without_calling_other_forms() -> None:
    """Non-matching registered handlers are ignored and no proof is emitted."""
    stdin_text = _valid_worker_stdin_text()
    calls: list[RuntimeProbeLocalPythonWorkerRequestPayload] = []

    def handler(
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> runtime_probe_worker.RuntimeProbeLocalPythonWorkerResponse:
        calls.append(payload)
        return runtime_probe_worker.RuntimeProbeLocalPythonWorkerResponse()

    entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:other_form/1",
        handler=handler,
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )

    assert calls == []
    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert (
        stderr_text
        == "runtime_probe_worker: rejected worker request without executing probe\n"
    )
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_duplicate_worker_handler_fails_closed_with_sanitized_stderr() -> None:
    """Duplicate family/form handler entries are rejected before dispatch."""
    stdin_text = _valid_worker_stdin_text()
    calls: list[RuntimeProbeLocalPythonWorkerRequestPayload] = []

    def handler(
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> runtime_probe_worker.RuntimeProbeLocalPythonWorkerResponse:
        calls.append(payload)
        return runtime_probe_worker.RuntimeProbeLocalPythonWorkerResponse()

    first_entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        handler=handler,
    )
    duplicate_entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        handler=handler,
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (first_entry, duplicate_entry),
    )

    assert calls == []
    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert stderr_text == "runtime_probe_worker: rejected duplicate worker handler\n"
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_malformed_worker_handler_fails_closed_with_sanitized_stderr() -> None:
    """Malformed injected handler entries are rejected without raw details."""
    stdin_text = _valid_worker_stdin_text()
    handler_entries = cast(
        Iterable[runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry],
        (object(),),
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        handler_entries,
    )

    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert stderr_text == "runtime_probe_worker: rejected malformed worker handler\n"
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_worker_handler_exception_fails_closed_with_sanitized_stderr() -> None:
    """Handler exceptions are normalized without leaking exception details."""
    stdin_text = _valid_worker_stdin_text()
    calls: list[RuntimeProbeLocalPythonWorkerRequestPayload] = []

    def handler(
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> runtime_probe_worker.RuntimeProbeLocalPythonWorkerResponse:
        calls.append(payload)
        raise RuntimeError("handler failed with secret-token /private/tmp Traceback")

    entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        handler=handler,
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )

    assert len(calls) == 1
    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert stderr_text == "runtime_probe_worker: rejected worker handler failure\n"
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_invalid_worker_handler_response_fails_closed_with_sanitized_stderr() -> None:
    """Untyped handler responses are rejected without reflecting their data."""
    stdin_text = _valid_worker_stdin_text()

    def handler(payload: RuntimeProbeLocalPythonWorkerRequestPayload) -> object:
        del payload
        return {
            "stdout": "runtime_probe_stdout_protocol_revision",
            "token": "secret-token",
            "path": "/private/tmp/context-ir",
        }

    entry = runtime_probe_worker.RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        handler=handler,
    )

    exit_code, stdout_text, stderr_text = _run_worker_with_handlers(
        stdin_text,
        (entry,),
    )

    assert exit_code == 78
    _assert_no_success_stdout_protocol(stdout_text)
    assert (
        stderr_text
        == "runtime_probe_worker: rejected invalid worker handler response\n"
    )
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_worker_response_contract_is_frozen_and_non_proof() -> None:
    """Worker responses are immutable typed markers for non-proof rejection."""
    response = runtime_probe_worker.RuntimeProbeLocalPythonWorkerResponse()

    assert response.rejected_without_proof is True
    with pytest.raises(FrozenInstanceError):
        response.rejected_without_proof = False
    with pytest.raises(ValueError, match="non-proof"):
        runtime_probe_worker.RuntimeProbeLocalPythonWorkerResponse(
            rejected_without_proof=False
        )


def test_malformed_worker_request_fails_closed_with_sanitized_stderr() -> None:
    """Malformed stdin is rejected without reflecting raw input or parse errors."""
    stdin_text = (
        '{"bad":"/private/tmp/context-ir",'
        '"token":"secret-token",'
        '"env":"PYTHONPATH=/private/tmp/context-ir",'
        '"trace":"Traceback (most recent call last)"}'
    )

    exit_code, stdout_text, stderr_text = _run_worker(stdin_text)

    assert exit_code == 64
    _assert_no_success_stdout_protocol(stdout_text)
    assert stderr_text == "runtime_probe_worker: rejected malformed worker request\n"
    _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_worker_without_handlers_never_emits_success_protocol_shape() -> None:
    """Explicit empty handler ingress cannot produce observed proof stdout."""
    malformed_stdin = "not json with secret-token /private/tmp Traceback"

    for stdin_text in (_valid_worker_stdin_text(), malformed_stdin):
        exit_code, stdout_text, stderr_text = _run_worker(stdin_text)

        assert exit_code != 0
        _assert_no_success_stdout_protocol(stdout_text)
        assert "runtime_probe_stdout_protocol_revision" not in stderr_text
        assert "normalized_payload" not in stderr_text
        assert "durable_artifact_reference" not in stderr_text
        assert "observed" not in stderr_text
        _assert_sanitized_worker_stderr(stderr_text, stdin_text)


def test_worker_entrypoint_is_importable() -> None:
    """The subprocess target module exposes module-local worker entrypoints."""
    module = __import__(
        "context_ir.runtime_probe_worker",
        fromlist=["main"],
    )

    assert isinstance(module, ModuleType)
    assert module is runtime_probe_worker
    assert callable(runtime_probe_worker.main)
    assert callable(
        runtime_probe_worker.build_runtime_probe_dynamic_import_worker_handler_entry
    )
    assert hasattr(
        runtime_probe_worker,
        "RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter",
    )
    assert hasattr(
        runtime_probe_worker,
        "RuntimeProbeLocalPythonDynamicImportWorkerObserver",
    )
    assert hasattr(
        runtime_probe_worker,
        "RuntimeProbeLocalPythonDynamicImportReplayTarget",
    )
    assert callable(
        runtime_probe_worker.materialize_runtime_probe_dynamic_import_replay_target
    )
    resolve_target = getattr(
        runtime_probe_worker,
        _DYNAMIC_IMPORT_REPLAY_TARGET_RESOLVER_HELPER,
    )
    assert callable(resolve_target)
    observe_from_target = getattr(
        runtime_probe_worker,
        _DYNAMIC_IMPORT_TARGET_OBSERVER_HELPER,
    )
    assert callable(observe_from_target)
    import_source_module = getattr(
        runtime_probe_worker,
        _DYNAMIC_IMPORT_SOURCE_MODULE_IMPORT_HELPER,
    )
    assert callable(import_source_module)
    observe_request = getattr(
        runtime_probe_worker,
        _DYNAMIC_IMPORT_CONCRETE_OBSERVER_HELPER,
    )
    assert callable(observe_request)


def test_package_root_exports_remain_unchanged() -> None:
    """Worker ingress stays module-local and absent from the package root API."""
    assert "runtime_probe_worker" not in context_ir.__all__
    assert "main" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonDynamicImportWorkerRequest" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonDynamicImportWorkerObservation" not in (
        context_ir.__all__
    )
    assert "RuntimeProbeLocalPythonDynamicImportReplayTarget" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonWorkerSuccessResponse" not in context_ir.__all__
    assert (
        "RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter"
        not in context_ir.__all__
    )
    assert (
        "RuntimeProbeLocalPythonDynamicImportWorkerObserver" not in context_ir.__all__
    )
    assert "materialize_runtime_probe_dynamic_import_worker_request" not in (
        context_ir.__all__
    )
    assert "materialize_runtime_probe_dynamic_import_worker_observation" not in (
        context_ir.__all__
    )
    assert "materialize_runtime_probe_dynamic_import_replay_target" not in (
        context_ir.__all__
    )
    assert _DYNAMIC_IMPORT_REPLAY_TARGET_RESOLVER_HELPER not in context_ir.__all__
    assert _DYNAMIC_IMPORT_SOURCE_MODULE_IMPORT_HELPER not in context_ir.__all__
    assert _DYNAMIC_IMPORT_CONCRETE_OBSERVER_HELPER not in context_ir.__all__
    assert "materialize_runtime_probe_dynamic_import_worker_success_response" not in (
        context_ir.__all__
    )
    assert "build_runtime_probe_dynamic_import_worker_handler_entry" not in (
        context_ir.__all__
    )
    assert _DYNAMIC_IMPORT_TARGET_OBSERVER_HELPER not in context_ir.__all__
    assert "RuntimeProbeLocalPythonDynamicImportTargetCallable" not in (
        context_ir.__all__
    )
    assert "serialize_runtime_probe_local_python_worker_success_response" not in (
        context_ir.__all__
    )
    assert not hasattr(context_ir, "main")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonDynamicImportWorkerRequest")
    assert not hasattr(
        context_ir,
        "RuntimeProbeLocalPythonDynamicImportWorkerObservation",
    )
    assert not hasattr(
        context_ir,
        "RuntimeProbeLocalPythonDynamicImportReplayTarget",
    )
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonWorkerSuccessResponse")
    assert not hasattr(
        context_ir,
        "RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter",
    )
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonDynamicImportWorkerObserver")
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_dynamic_import_worker_request",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_dynamic_import_worker_observation",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_dynamic_import_replay_target",
    )
    assert not hasattr(
        context_ir,
        _DYNAMIC_IMPORT_REPLAY_TARGET_RESOLVER_HELPER,
    )
    assert not hasattr(
        context_ir,
        _DYNAMIC_IMPORT_SOURCE_MODULE_IMPORT_HELPER,
    )
    assert not hasattr(
        context_ir,
        _DYNAMIC_IMPORT_CONCRETE_OBSERVER_HELPER,
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_dynamic_import_worker_success_response",
    )
    assert not hasattr(
        context_ir,
        "build_runtime_probe_dynamic_import_worker_handler_entry",
    )
    assert not hasattr(
        context_ir,
        _DYNAMIC_IMPORT_TARGET_OBSERVER_HELPER,
    )
    assert not hasattr(
        context_ir,
        "RuntimeProbeLocalPythonDynamicImportTargetCallable",
    )
    assert not hasattr(
        context_ir,
        "serialize_runtime_probe_local_python_worker_success_response",
    )

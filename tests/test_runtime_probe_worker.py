"""Tests for the fail-closed local Python runtime probe worker ingress."""

from __future__ import annotations

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
WorkerSuccessResponse = (
    runtime_probe_worker.RuntimeProbeLocalPythonWorkerSuccessResponse
)


def _field(key: str, value: str) -> runtime_probe_results.RuntimeProbeReplayField:
    """Return one replay metadata field for worker ingress tests."""
    return runtime_probe_results.RuntimeProbeReplayField(key=key, value=value)


def _request() -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one deterministic planned runtime probe request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id="unsupported:call:main.py:3:4",
        source_site=SourceSite(
            site_id="site:main.py:3:4",
            file_path="main.py",
            span=SourceSpan(
                start_line=3,
                start_column=4,
                end_line=3,
                end_column=28,
            ),
            snippet="importlib.import_module(name)",
        ),
        reason_code=UnresolvedReasonCode.DYNAMIC_IMPORT,
        boundary_text="importlib.import_module(name)",
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label="dynamic_import:importlib.import_module/1",
        replay_target_seed="main.run",
        replay_selector_seed="call:main.run:dynamic_import@main.py:3:4:3:28",
    )


def _valid_worker_invocation(
    *,
    python_path_entries: tuple[str, ...] = ("/workspace/context-ir/src",),
) -> RuntimeProbeLocalPythonSubprocessInvocation:
    """Return one strict worker invocation produced by the parent contract."""
    request_plan = runtime_probe_requests.build_runtime_probe_request_plan(
        (_request(),)
    )
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
            _field("repository_root", "/workspace/context-ir"),
            _field("working_directory", "/workspace/context-ir"),
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
        python_executable="/workspace/context-ir/.venv/bin/python",
        module_name="context_ir.runtime_probe_worker",
        invocation_contract_revision=("runtime-probe-local-python-subprocess:test.1"),
    )
    return invocation


def _valid_worker_payload(
    *,
    python_path_entries: tuple[str, ...] = ("/workspace/context-ir/src",),
) -> RuntimeProbeLocalPythonWorkerRequestPayload:
    """Return the strict worker payload produced by the parent contract."""
    invocation = _valid_worker_invocation(python_path_entries=python_path_entries)
    return materialize_runtime_probe_local_python_worker_request_payload(invocation)


def _valid_dynamic_import_worker_request() -> DynamicImportWorkerRequest:
    """Return one worker-local dynamic-import request contract."""
    return runtime_probe_worker.materialize_runtime_probe_dynamic_import_worker_request(
        _valid_worker_payload()
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
    """Run the importable worker entrypoint without spawning a subprocess."""
    return _run_worker_with_handlers(stdin_text, ())


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
    ("field_name", "field_value", "error_match"),
    (
        (
            "family_label",
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            "family_label",
        ),
        ("form_label", "dynamic_import:other_form/1", "form_label"),
    ),
)
def test_dynamic_import_worker_request_validates_exact_family_form(
    field_name: str,
    field_value: object,
    error_match: str,
) -> None:
    """Only the first importlib.import_module dynamic-import form materializes."""
    payload = _valid_worker_payload()
    object.__setattr__(payload, field_name, field_value)

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


def test_dynamic_import_worker_observation_does_not_import_modules() -> None:
    """The observation contract adds no importlib import surface."""
    for source_path in (
        Path(runtime_probe_worker.__file__),
        Path(__file__),
    ):
        source_text = source_path.read_text(encoding="utf-8")

        assert not any(
            line.startswith(("import importlib", "from importlib"))
            for line in source_text.splitlines()
        )


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
    """Default valid and malformed ingress cannot produce observed proof stdout."""
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


def test_package_root_exports_remain_unchanged() -> None:
    """Worker ingress stays module-local and absent from the package root API."""
    assert "runtime_probe_worker" not in context_ir.__all__
    assert "main" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonDynamicImportWorkerRequest" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonDynamicImportWorkerObservation" not in (
        context_ir.__all__
    )
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
    assert "materialize_runtime_probe_dynamic_import_worker_success_response" not in (
        context_ir.__all__
    )
    assert "build_runtime_probe_dynamic_import_worker_handler_entry" not in (
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
        "materialize_runtime_probe_dynamic_import_worker_success_response",
    )
    assert not hasattr(
        context_ir,
        "build_runtime_probe_dynamic_import_worker_handler_entry",
    )
    assert not hasattr(
        context_ir,
        "serialize_runtime_probe_local_python_worker_success_response",
    )

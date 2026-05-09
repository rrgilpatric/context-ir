"""Tests for the fail-closed local Python runtime probe worker ingress."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import FrozenInstanceError
from io import StringIO
from types import ModuleType
from typing import cast

import pytest

import context_ir
import context_ir.runtime_probe_requests as runtime_probe_requests
import context_ir.runtime_probe_results as runtime_probe_results
import context_ir.runtime_probe_worker as runtime_probe_worker
from context_ir.runtime_probe_execution import (
    RuntimeProbeLocalPythonWorkerRequestPayload,
    materialize_runtime_probe_execution_input_batch,
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


def _valid_worker_stdin_text() -> str:
    """Return strict worker stdin JSON produced by the accepted parent contract."""
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
            _field("python_path_entry", "/workspace/context-ir/src"),
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
    payload = materialize_runtime_probe_local_python_worker_request_payload(invocation)
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


def test_worker_never_emits_success_protocol_shape() -> None:
    """Neither valid nor malformed ingress can produce observed proof stdout."""
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
    """The subprocess target module exists and exposes a callable main."""
    module = __import__(
        "context_ir.runtime_probe_worker",
        fromlist=["main"],
    )

    assert isinstance(module, ModuleType)
    assert module is runtime_probe_worker
    assert callable(runtime_probe_worker.main)


def test_package_root_exports_remain_unchanged() -> None:
    """Worker ingress stays module-local and absent from the package root API."""
    assert "runtime_probe_worker" not in context_ir.__all__
    assert "main" not in context_ir.__all__
    assert not hasattr(context_ir, "main")

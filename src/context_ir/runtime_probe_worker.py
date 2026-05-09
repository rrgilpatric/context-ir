"""Fail-closed local Python runtime probe worker ingress."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TextIO, TypeAlias

from context_ir.runtime_probe_execution import (
    RuntimeProbeLocalPythonWorkerRequestPayload,
    parse_runtime_probe_local_python_worker_request_payload,
)
from context_ir.runtime_probe_requests import RuntimeProbeFamily
from context_ir.runtime_probe_results import RuntimeProbeReplayField

RuntimeProbeLocalPythonWorkerHandlerKey: TypeAlias = tuple[RuntimeProbeFamily, str]
_MALFORMED_REQUEST_EXIT_CODE = 64
_REJECTED_REQUEST_EXIT_CODE = 78
_SUCCESS_EXIT_CODE = 0
_RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION = (
    "runtime_probe_local_python_stdout_protocol:v1"
)
_RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION_KEY = (
    "runtime_probe_stdout_protocol_revision"
)
_MALFORMED_REQUEST_MESSAGE = "runtime_probe_worker: rejected malformed worker request\n"
_REJECTED_REQUEST_MESSAGE = (
    "runtime_probe_worker: rejected worker request without executing probe\n"
)
_DUPLICATE_HANDLER_MESSAGE = "runtime_probe_worker: rejected duplicate worker handler\n"
_MALFORMED_HANDLER_MESSAGE = "runtime_probe_worker: rejected malformed worker handler\n"
_HANDLER_EXCEPTION_MESSAGE = "runtime_probe_worker: rejected worker handler failure\n"
_INVALID_RESPONSE_MESSAGE = (
    "runtime_probe_worker: rejected invalid worker handler response\n"
)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonWorkerResponse:
    """Typed non-proof worker response that cannot carry stdout payload data."""

    rejected_without_proof: bool = True

    def __post_init__(self) -> None:
        """Reject response values that could be confused with runtime proof."""
        _validate_runtime_probe_worker_response(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Typed worker response carrying the stdout success protocol payload."""

    normalized_payload: tuple[RuntimeProbeReplayField, ...]
    durable_artifact_reference: str | None = None

    def __post_init__(self) -> None:
        """Reject malformed success payload metadata before stdout emission."""
        _validate_runtime_probe_worker_success_response(self)


RuntimeProbeLocalPythonWorkerHandlerResponse: TypeAlias = (
    RuntimeProbeLocalPythonWorkerResponse | RuntimeProbeLocalPythonWorkerSuccessResponse
)
RuntimeProbeLocalPythonWorkerCallable: TypeAlias = Callable[
    [RuntimeProbeLocalPythonWorkerRequestPayload],
    RuntimeProbeLocalPythonWorkerHandlerResponse,
]


@dataclass(frozen=True)
class RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Typed dispatch-table entry for one worker family/form handler."""

    family_label: RuntimeProbeFamily
    form_label: str
    handler: RuntimeProbeLocalPythonWorkerCallable

    def __post_init__(self) -> None:
        """Reject incomplete or uncallable worker handler metadata."""
        _validate_runtime_probe_worker_handler_entry(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonDispatchingWorker:
    """Dispatch parsed worker payloads to registered family/form handlers."""

    handler_entries: tuple[RuntimeProbeLocalPythonWorkerHandlerEntry, ...]
    _handlers_by_key: Mapping[
        RuntimeProbeLocalPythonWorkerHandlerKey,
        RuntimeProbeLocalPythonWorkerCallable,
    ] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Reject ambiguous handler tables before any payload dispatch."""
        handlers_by_key = _index_runtime_probe_worker_handler_entries(
            self.handler_entries
        )
        object.__setattr__(
            self,
            "_handlers_by_key",
            MappingProxyType(handlers_by_key),
        )

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerHandlerResponse:
        """Route a parsed payload by family/form without emitting proof."""
        if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
            raise _RuntimeProbeWorkerDispatchError(_MALFORMED_REQUEST_MESSAGE)
        handler = self._handlers_by_key.get(_runtime_probe_worker_payload_key(payload))
        if handler is None:
            raise _RuntimeProbeWorkerDispatchError(_REJECTED_REQUEST_MESSAGE)
        try:
            response = handler(payload)
        except Exception as error:
            raise _RuntimeProbeWorkerDispatchError(
                _HANDLER_EXCEPTION_MESSAGE
            ) from error
        try:
            _validate_runtime_probe_worker_handler_response(response)
        except Exception as error:
            raise _RuntimeProbeWorkerDispatchError(_INVALID_RESPONSE_MESSAGE) from error
        return response


class _RuntimeProbeWorkerDuplicateHandlerError(Exception):
    """Internal marker for duplicate worker handler keys."""


class _RuntimeProbeWorkerDispatchError(Exception):
    """Internal dispatch failure carrying only sanitized stderr text."""

    def __init__(self, stderr_message: str) -> None:
        super().__init__(stderr_message)
        self.stderr_message = stderr_message


def main(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    *,
    handler_entries: Iterable[RuntimeProbeLocalPythonWorkerHandlerEntry] = (),
) -> int:
    """Read one worker request from stdin and route injected handlers fail-closed."""
    input_stream = sys.stdin if stdin is None else stdin
    output_stream = sys.stdout if stdout is None else stdout
    error_stream = sys.stderr if stderr is None else stderr

    stdin_text = input_stream.read()
    try:
        payload = parse_runtime_probe_local_python_worker_request_payload(stdin_text)
    except Exception:
        error_stream.write(_MALFORMED_REQUEST_MESSAGE)
        return _MALFORMED_REQUEST_EXIT_CODE

    try:
        response = _dispatch_runtime_probe_local_python_worker_payload(
            payload,
            handler_entries,
        )
    except _RuntimeProbeWorkerDuplicateHandlerError:
        error_stream.write(_DUPLICATE_HANDLER_MESSAGE)
        return _REJECTED_REQUEST_EXIT_CODE
    except _RuntimeProbeWorkerDispatchError as error:
        error_stream.write(error.stderr_message)
        return _REJECTED_REQUEST_EXIT_CODE
    except Exception:
        error_stream.write(_MALFORMED_HANDLER_MESSAGE)
        return _REJECTED_REQUEST_EXIT_CODE

    if isinstance(response, RuntimeProbeLocalPythonWorkerSuccessResponse):
        try:
            stdout_text = serialize_runtime_probe_local_python_worker_success_response(
                response
            )
        except Exception:
            error_stream.write(_INVALID_RESPONSE_MESSAGE)
            return _REJECTED_REQUEST_EXIT_CODE
        output_stream.write(stdout_text)
        return _SUCCESS_EXIT_CODE

    error_stream.write(_REJECTED_REQUEST_MESSAGE)
    return _REJECTED_REQUEST_EXIT_CODE


def _dispatch_runtime_probe_local_python_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    handler_entries: Iterable[RuntimeProbeLocalPythonWorkerHandlerEntry],
) -> RuntimeProbeLocalPythonWorkerHandlerResponse:
    """Dispatch one parsed worker payload through an injected handler table."""
    try:
        dispatching_worker = RuntimeProbeLocalPythonDispatchingWorker(
            handler_entries=tuple(handler_entries),
        )
    except _RuntimeProbeWorkerDuplicateHandlerError:
        raise
    except Exception as error:
        raise _RuntimeProbeWorkerDispatchError(_MALFORMED_HANDLER_MESSAGE) from error
    return dispatching_worker(payload)


def serialize_runtime_probe_local_python_worker_success_response(
    response: RuntimeProbeLocalPythonWorkerSuccessResponse,
) -> str:
    """Serialize a worker success response as the parent stdout protocol JSON."""
    _validate_runtime_probe_worker_success_response(response)
    protocol: dict[str, object] = {
        _RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION_KEY: (
            _RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION
        ),
        "normalized_payload": _runtime_probe_worker_replay_fields_json_array(
            response.normalized_payload
        ),
    }
    if response.durable_artifact_reference is not None:
        protocol["durable_artifact_reference"] = response.durable_artifact_reference
    return json.dumps(protocol, separators=(",", ":"))


def _index_runtime_probe_worker_handler_entries(
    handler_entries: tuple[RuntimeProbeLocalPythonWorkerHandlerEntry, ...],
) -> dict[
    RuntimeProbeLocalPythonWorkerHandlerKey,
    RuntimeProbeLocalPythonWorkerCallable,
]:
    """Return worker handlers keyed by family/form after duplicate checks."""
    if not isinstance(handler_entries, tuple):
        raise ValueError("runtime probe worker handler entries must be a tuple")
    handlers_by_key: dict[
        RuntimeProbeLocalPythonWorkerHandlerKey,
        RuntimeProbeLocalPythonWorkerCallable,
    ] = {}
    for handler_entry in handler_entries:
        _validate_runtime_probe_worker_handler_entry(handler_entry)
        handler_key = _runtime_probe_worker_handler_entry_key(handler_entry)
        if handler_key in handlers_by_key:
            raise _RuntimeProbeWorkerDuplicateHandlerError(
                "duplicate runtime probe worker handler key"
            )
        handlers_by_key[handler_key] = handler_entry.handler
    return handlers_by_key


def _runtime_probe_worker_handler_entry_key(
    handler_entry: RuntimeProbeLocalPythonWorkerHandlerEntry,
) -> RuntimeProbeLocalPythonWorkerHandlerKey:
    """Return the dispatch-table key carried by one worker handler entry."""
    return (handler_entry.family_label, handler_entry.form_label)


def _runtime_probe_worker_payload_key(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonWorkerHandlerKey:
    """Return the family/form dispatch key carried by a parsed payload."""
    return (payload.family_label, payload.form_label)


def _validate_runtime_probe_worker_handler_entry(
    handler_entry: RuntimeProbeLocalPythonWorkerHandlerEntry,
) -> None:
    """Reject malformed worker dispatch handler metadata."""
    if not isinstance(handler_entry, RuntimeProbeLocalPythonWorkerHandlerEntry):
        raise ValueError("runtime probe worker handler entries must be typed")
    if not isinstance(handler_entry.family_label, RuntimeProbeFamily):
        raise ValueError("runtime probe worker handler family_label must be typed")
    if not isinstance(handler_entry.form_label, str) or not (
        handler_entry.form_label.strip()
    ):
        raise ValueError("runtime probe worker handler form_label must be non-empty")
    if not callable(handler_entry.handler):
        raise ValueError("runtime probe worker handler must be callable")


def _validate_runtime_probe_worker_response(
    response: RuntimeProbeLocalPythonWorkerResponse,
) -> None:
    """Reject worker responses that could carry proof or success semantics."""
    if not isinstance(response, RuntimeProbeLocalPythonWorkerResponse):
        raise ValueError("runtime probe worker response must be typed")
    if response.rejected_without_proof is not True:
        raise ValueError("runtime probe worker response must be non-proof")


def _validate_runtime_probe_worker_success_response(
    response: RuntimeProbeLocalPythonWorkerSuccessResponse,
) -> None:
    """Reject success responses that do not match the stdout proof contract."""
    if not isinstance(response, RuntimeProbeLocalPythonWorkerSuccessResponse):
        raise ValueError("runtime probe worker success response must be typed")
    _validate_runtime_probe_worker_replay_fields(
        response.normalized_payload,
        field_name="normalized_payload",
    )
    _validate_runtime_probe_worker_durable_artifact_reference(
        response.durable_artifact_reference
    )
    if not response.normalized_payload and response.durable_artifact_reference is None:
        raise ValueError(
            "runtime probe worker success responses require normalized_payload "
            "or durable_artifact_reference"
        )


def _validate_runtime_probe_worker_handler_response(
    response: RuntimeProbeLocalPythonWorkerHandlerResponse,
) -> None:
    """Reject handler responses outside the typed worker response contracts."""
    if isinstance(response, RuntimeProbeLocalPythonWorkerSuccessResponse):
        _validate_runtime_probe_worker_success_response(response)
        return
    if isinstance(response, RuntimeProbeLocalPythonWorkerResponse):
        _validate_runtime_probe_worker_response(response)
        return
    raise ValueError("runtime probe worker handler response must be typed")


def _validate_runtime_probe_worker_replay_fields(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    field_name: str,
) -> None:
    """Reject replay fields whose shape or frozen values were tampered."""
    if not isinstance(fields, tuple):
        raise ValueError(f"runtime probe worker {field_name} must be a tuple")
    for replay_field in fields:
        if not isinstance(replay_field, RuntimeProbeReplayField):
            raise ValueError(
                f"runtime probe worker {field_name} must contain replay fields"
            )
        if not replay_field.key.strip() or not replay_field.value.strip():
            raise ValueError(
                f"runtime probe worker {field_name} must not contain blank fields"
            )


def _validate_runtime_probe_worker_durable_artifact_reference(
    durable_artifact_reference: str | None,
) -> None:
    """Reject durable artifact references the parent stdout parser rejects."""
    if durable_artifact_reference is None:
        return
    if (
        not isinstance(durable_artifact_reference, str)
        or not durable_artifact_reference.strip()
    ):
        raise ValueError(
            "runtime probe worker durable_artifact_reference must be non-empty"
        )
    if (
        durable_artifact_reference != durable_artifact_reference.strip()
        or _contains_control_character(durable_artifact_reference)
    ):
        raise ValueError("runtime probe worker durable_artifact_reference is malformed")


def _runtime_probe_worker_replay_fields_json_array(
    fields: tuple[RuntimeProbeReplayField, ...],
) -> list[dict[str, str]]:
    """Return replay fields as ordered strict JSON key/value objects."""
    _validate_runtime_probe_worker_replay_fields(
        fields,
        field_name="normalized_payload",
    )
    return [{"key": field.key, "value": field.value} for field in fields]


def _contains_control_character(value: str) -> bool:
    """Return whether a metadata value contains JSON-protocol control characters."""
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


if __name__ == "__main__":
    raise SystemExit(main())

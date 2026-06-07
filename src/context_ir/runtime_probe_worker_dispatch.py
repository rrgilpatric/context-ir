"""Private runtime probe worker dispatch contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TypeAlias

from context_ir import runtime_probe_worker_response_protocol as _response_protocol
from context_ir.runtime_probe_execution import (
    RuntimeProbeLocalPythonWorkerRequestPayload,
)
from context_ir.runtime_probe_requests import RuntimeProbeFamily

RuntimeProbeLocalPythonWorkerHandlerKey: TypeAlias = tuple[RuntimeProbeFamily, str]
RuntimeProbeLocalPythonWorkerCallable: TypeAlias = Callable[
    [RuntimeProbeLocalPythonWorkerRequestPayload],
    _response_protocol.RuntimeProbeLocalPythonWorkerHandlerResponse,
]

_MALFORMED_REQUEST_MESSAGE = "runtime_probe_worker: rejected malformed worker request\n"
_REJECTED_REQUEST_MESSAGE = (
    "runtime_probe_worker: rejected worker request without executing probe\n"
)
_HANDLER_EXCEPTION_MESSAGE = "runtime_probe_worker: rejected worker handler failure\n"
_INVALID_RESPONSE_MESSAGE = (
    "runtime_probe_worker: rejected invalid worker handler response\n"
)


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
    ) -> _response_protocol.RuntimeProbeLocalPythonWorkerHandlerResponse:
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
            _response_protocol._validate_runtime_probe_worker_handler_response(response)
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

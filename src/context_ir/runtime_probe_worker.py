"""Fail-closed local Python runtime probe worker ingress."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import TextIO, TypeAlias

from context_ir.runtime_probe_execution import (
    RuntimeProbeLocalPythonWorkerRequestPayload,
    parse_runtime_probe_local_python_worker_request_payload,
)
from context_ir.runtime_probe_requests import RuntimeProbeFamily
from context_ir.runtime_probe_results import RuntimeProbeReplayField
from context_ir.semantic_types import SemanticSubjectKind, UnresolvedReasonCode

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
_DYNAMIC_IMPORT_WORKER_FORM_LABEL = "dynamic_import:importlib.import_module/1"
_DYNAMIC_IMPORT_WORKER_INVOCATION_IDENTITY_PREFIX = (
    "runtime_probe_local_python_subprocess_invocation:"
)
_DYNAMIC_IMPORT_REQUIRED_REPLAY_FIELD_KEYS = (
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


@dataclass(frozen=True)
class RuntimeProbeLocalPythonDynamicImportWorkerRequest:
    """Worker-local request contract for importlib.import_module probes only."""

    plan_id: str
    request_id: str
    subject_kind: SemanticSubjectKind
    subject_id: str
    source_site_id: str
    source_file_path: str
    source_start_line: int
    source_start_column: int
    source_end_line: int
    source_end_column: int
    reason_code: UnresolvedReasonCode
    boundary_text: str
    family_label: RuntimeProbeFamily
    form_label: str
    replay_target_seed: str
    replay_selector_seed: str
    argv: tuple[str, ...]
    working_directory: str
    python_path_entries: tuple[str, ...]
    timeout_seconds: int
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject drifted or non-dynamic-import worker request metadata."""
        _validate_runtime_probe_dynamic_import_worker_request(self)


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


def materialize_runtime_probe_dynamic_import_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonDynamicImportWorkerRequest:
    """Derive a non-executing dynamic-import worker request from stdin payload."""
    _validate_runtime_probe_dynamic_import_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonDynamicImportWorkerRequest(
        plan_id=payload.plan_id,
        request_id=payload.request_id,
        subject_kind=_runtime_probe_worker_subject_kind_from_replay_field(
            replay_fields_by_key["subject_kind"]
        ),
        subject_id=replay_fields_by_key["subject_id"],
        source_site_id=replay_fields_by_key["source_site_id"],
        source_file_path=replay_fields_by_key["source_file_path"],
        source_start_line=_runtime_probe_worker_replay_span_value(
            replay_fields_by_key["source_start_line"],
            field_name="source_start_line",
        ),
        source_start_column=_runtime_probe_worker_replay_span_value(
            replay_fields_by_key["source_start_column"],
            field_name="source_start_column",
        ),
        source_end_line=_runtime_probe_worker_replay_span_value(
            replay_fields_by_key["source_end_line"],
            field_name="source_end_line",
        ),
        source_end_column=_runtime_probe_worker_replay_span_value(
            replay_fields_by_key["source_end_column"],
            field_name="source_end_column",
        ),
        reason_code=_runtime_probe_worker_reason_code_from_replay_field(
            replay_fields_by_key["reason_code"]
        ),
        boundary_text=replay_fields_by_key["boundary_text"],
        family_label=payload.family_label,
        form_label=payload.form_label,
        replay_target_seed=payload.replay_target_seed,
        replay_selector_seed=payload.replay_selector_seed,
        argv=payload.argv,
        working_directory=payload.working_directory,
        python_path_entries=payload.python_path_entries,
        timeout_seconds=payload.timeout_seconds,
        invocation_contract_revision=payload.invocation_contract_revision,
        invocation_identity=payload.invocation_identity,
        request_replay_payload_fields=payload.request_replay_payload_fields,
    )


def _validate_runtime_probe_dynamic_import_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local import-module request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError("runtime probe dynamic import worker payload must be typed")
    _validate_runtime_probe_dynamic_import_payload_family_form(
        family_label=payload.family_label,
        form_label=payload.form_label,
    )
    _validate_runtime_probe_worker_metadata_text(
        payload.plan_id,
        field_name="plan_id",
    )
    _validate_runtime_probe_worker_metadata_text(
        payload.request_id,
        field_name="request_id",
    )
    _validate_runtime_probe_worker_metadata_text(
        payload.replay_target_seed,
        field_name="replay_target_seed",
    )
    _validate_runtime_probe_worker_metadata_text(
        payload.replay_selector_seed,
        field_name="replay_selector_seed",
    )
    _validate_runtime_probe_worker_metadata_text(
        payload.invocation_contract_revision,
        field_name="invocation_contract_revision",
    )
    _validate_runtime_probe_worker_invocation_identity(payload.invocation_identity)
    _validate_runtime_probe_worker_argv(payload.argv)
    _validate_runtime_probe_worker_path_text(
        payload.working_directory,
        field_name="working_directory",
    )
    _validate_runtime_probe_worker_python_path_entries(payload.python_path_entries)
    _validate_runtime_probe_worker_timeout_seconds(payload.timeout_seconds)

    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    _validate_runtime_probe_dynamic_import_replay_metadata(
        replay_fields_by_key,
        plan_id=payload.plan_id,
        request_id=payload.request_id,
        family_label=payload.family_label,
        form_label=payload.form_label,
        replay_target_seed=payload.replay_target_seed,
        replay_selector_seed=payload.replay_selector_seed,
    )
    expected_identity = _runtime_probe_worker_invocation_identity_from_parts(
        plan_id=payload.plan_id,
        request_id=payload.request_id,
        invocation_contract_revision=payload.invocation_contract_revision,
        argv=payload.argv,
        working_directory=payload.working_directory,
        python_path_entries=payload.python_path_entries,
        timeout_seconds=payload.timeout_seconds,
        request_replay_payload_fields=payload.request_replay_payload_fields,
    )
    if payload.invocation_identity != expected_identity:
        raise ValueError(
            "runtime probe dynamic import worker invocation_identity must match "
            "payload replay identity"
        )


def _validate_runtime_probe_dynamic_import_worker_request(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> None:
    """Reject dynamic-import worker requests whose copied metadata drifted."""
    if not isinstance(request, RuntimeProbeLocalPythonDynamicImportWorkerRequest):
        raise ValueError("runtime probe dynamic import worker request must be typed")
    _validate_runtime_probe_dynamic_import_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe dynamic import worker subject_kind is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.DYNAMIC_IMPORT:
        raise ValueError(
            "runtime probe dynamic import worker reason_code is unsupported"
        )
    _validate_runtime_probe_worker_metadata_text(
        request.plan_id,
        field_name="plan_id",
    )
    _validate_runtime_probe_worker_metadata_text(
        request.request_id,
        field_name="request_id",
    )
    _validate_runtime_probe_worker_metadata_text(
        request.subject_id,
        field_name="subject_id",
    )
    _validate_runtime_probe_worker_metadata_text(
        request.source_site_id,
        field_name="source_site_id",
    )
    _validate_runtime_probe_worker_metadata_text(
        request.source_file_path,
        field_name="source_file_path",
    )
    _validate_runtime_probe_worker_metadata_text(
        request.boundary_text,
        field_name="boundary_text",
    )
    _validate_runtime_probe_worker_metadata_text(
        request.replay_target_seed,
        field_name="replay_target_seed",
    )
    _validate_runtime_probe_worker_metadata_text(
        request.replay_selector_seed,
        field_name="replay_selector_seed",
    )
    _validate_runtime_probe_worker_metadata_text(
        request.invocation_contract_revision,
        field_name="invocation_contract_revision",
    )
    _validate_runtime_probe_worker_source_span(
        start_line=request.source_start_line,
        start_column=request.source_start_column,
        end_line=request.source_end_line,
        end_column=request.source_end_column,
    )
    _validate_runtime_probe_worker_invocation_identity(request.invocation_identity)
    _validate_runtime_probe_worker_argv(request.argv)
    _validate_runtime_probe_worker_path_text(
        request.working_directory,
        field_name="working_directory",
    )
    _validate_runtime_probe_worker_python_path_entries(request.python_path_entries)
    _validate_runtime_probe_worker_timeout_seconds(request.timeout_seconds)

    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        request.request_replay_payload_fields
    )
    _validate_runtime_probe_dynamic_import_replay_metadata(
        replay_fields_by_key,
        plan_id=request.plan_id,
        request_id=request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="subject_kind",
        expected_value=request.subject_kind.value,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="subject_id",
        expected_value=request.subject_id,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="source_site_id",
        expected_value=request.source_site_id,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="source_file_path",
        expected_value=request.source_file_path,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="source_start_line",
        expected_value=str(request.source_start_line),
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="source_start_column",
        expected_value=str(request.source_start_column),
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="source_end_line",
        expected_value=str(request.source_end_line),
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="source_end_column",
        expected_value=str(request.source_end_column),
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="reason_code",
        expected_value=request.reason_code.value,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="boundary_text",
        expected_value=request.boundary_text,
    )
    expected_identity = _runtime_probe_worker_invocation_identity_from_parts(
        plan_id=request.plan_id,
        request_id=request.request_id,
        invocation_contract_revision=request.invocation_contract_revision,
        argv=request.argv,
        working_directory=request.working_directory,
        python_path_entries=request.python_path_entries,
        timeout_seconds=request.timeout_seconds,
        request_replay_payload_fields=request.request_replay_payload_fields,
    )
    if request.invocation_identity != expected_identity:
        raise ValueError(
            "runtime probe dynamic import worker invocation_identity must match "
            "request replay identity"
        )


def _validate_runtime_probe_dynamic_import_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject non-importlib dynamic-import worker request family/form labels."""
    if family_label is not RuntimeProbeFamily.DYNAMIC_IMPORT:
        raise ValueError(
            "runtime probe dynamic import worker family_label is unsupported"
        )
    if form_label != _DYNAMIC_IMPORT_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe dynamic import worker form_label is unsupported"
        )


def _validate_runtime_probe_dynamic_import_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from dynamic-import worker metadata."""
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="plan_id",
        expected_value=plan_id,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="request_id",
        expected_value=request_id,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="family_label",
        expected_value=family_label.value,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="form_label",
        expected_value=form_label,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="replay_target_seed",
        expected_value=replay_target_seed,
    )
    _validate_runtime_probe_worker_replay_field_match(
        replay_fields_by_key,
        field_key="replay_selector_seed",
        expected_value=replay_selector_seed,
    )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe dynamic import worker subject_kind is unsupported"
        )
    if replay_fields_by_key["reason_code"] != UnresolvedReasonCode.DYNAMIC_IMPORT.value:
        raise ValueError(
            "runtime probe dynamic import worker reason_code is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_reason_code_from_replay_field(
        replay_fields_by_key["reason_code"]
    )
    _validate_runtime_probe_worker_metadata_text(
        replay_fields_by_key["subject_id"],
        field_name="subject_id",
    )
    _validate_runtime_probe_worker_metadata_text(
        replay_fields_by_key["source_site_id"],
        field_name="source_site_id",
    )
    _validate_runtime_probe_worker_metadata_text(
        replay_fields_by_key["source_file_path"],
        field_name="source_file_path",
    )
    _validate_runtime_probe_worker_metadata_text(
        replay_fields_by_key["boundary_text"],
        field_name="boundary_text",
    )
    _validate_runtime_probe_worker_source_span(
        start_line=_runtime_probe_worker_replay_span_value(
            replay_fields_by_key["source_start_line"],
            field_name="source_start_line",
        ),
        start_column=_runtime_probe_worker_replay_span_value(
            replay_fields_by_key["source_start_column"],
            field_name="source_start_column",
        ),
        end_line=_runtime_probe_worker_replay_span_value(
            replay_fields_by_key["source_end_line"],
            field_name="source_end_line",
        ),
        end_column=_runtime_probe_worker_replay_span_value(
            replay_fields_by_key["source_end_column"],
            field_name="source_end_column",
        ),
    )


def _runtime_probe_worker_required_replay_fields_by_key(
    fields: tuple[RuntimeProbeReplayField, ...],
) -> dict[str, str]:
    """Return required replay fields after enforcing exact singleton keys."""
    _validate_runtime_probe_worker_replay_fields(
        fields,
        field_name="request_replay_payload_fields",
    )
    fields_by_key: dict[str, str] = {}
    for required_key in _DYNAMIC_IMPORT_REQUIRED_REPLAY_FIELD_KEYS:
        matching_fields = tuple(field for field in fields if field.key == required_key)
        if len(matching_fields) != 1:
            raise ValueError(
                "runtime probe dynamic import worker request_replay_payload_fields "
                f"must contain exactly one {required_key}"
            )
        fields_by_key[required_key] = matching_fields[0].value
    return fields_by_key


def _validate_runtime_probe_worker_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied top-level request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe dynamic import worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_subject_kind_from_replay_field(
    value: str,
) -> SemanticSubjectKind:
    """Parse and validate the subject kind copied into replay metadata."""
    try:
        subject_kind = SemanticSubjectKind(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe dynamic import worker subject_kind is unsupported"
        ) from error
    if subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe dynamic import worker subject_kind is unsupported"
        )
    return subject_kind


def _runtime_probe_worker_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the dynamic-import reason copied into replay metadata."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe dynamic import worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.DYNAMIC_IMPORT:
        raise ValueError(
            "runtime probe dynamic import worker reason_code is unsupported"
        )
    return reason_code


def _runtime_probe_worker_replay_span_value(value: str, *, field_name: str) -> int:
    """Parse a source-span replay value as a non-negative integer."""
    if not isinstance(value, str) or not value.isdecimal():
        raise ValueError(
            f"runtime probe dynamic import worker {field_name} is malformed"
        )
    return int(value)


def _validate_runtime_probe_worker_source_span(
    *,
    start_line: int,
    start_column: int,
    end_line: int,
    end_column: int,
) -> None:
    """Reject impossible source-span coordinates before future execution."""
    span_values = (start_line, start_column, end_line, end_column)
    if any(
        not isinstance(value, int) or isinstance(value, bool) for value in span_values
    ):
        raise ValueError("runtime probe dynamic import worker source span is malformed")
    if start_line < 1 or end_line < 1 or start_column < 0 or end_column < 0:
        raise ValueError("runtime probe dynamic import worker source span is malformed")
    if end_line < start_line:
        raise ValueError("runtime probe dynamic import worker source span is malformed")
    if end_line == start_line and end_column < start_column:
        raise ValueError("runtime probe dynamic import worker source span is malformed")


def _validate_runtime_probe_worker_metadata_text(
    value: str, *, field_name: str
) -> None:
    """Reject blank or control-character-bearing worker request metadata."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"runtime probe dynamic import worker {field_name} must be non-empty"
        )
    if value != value.strip() or _contains_control_character(value):
        raise ValueError(
            f"runtime probe dynamic import worker {field_name} is malformed"
        )


def _validate_runtime_probe_worker_path_text(value: str, *, field_name: str) -> None:
    """Reject blank worker path metadata while preserving the copied string."""
    _validate_runtime_probe_worker_metadata_text(value, field_name=field_name)
    if not _is_runtime_probe_worker_absolute_path_metadata(value):
        raise ValueError(
            f"runtime probe dynamic import worker {field_name} must be absolute"
        )


def _validate_runtime_probe_worker_argv(argv: tuple[str, ...]) -> None:
    """Reject malformed copied argv metadata without executing it."""
    if not isinstance(argv, tuple) or len(argv) < 3:
        raise ValueError("runtime probe dynamic import worker argv is malformed")
    for token in argv:
        _validate_runtime_probe_worker_metadata_text(token, field_name="argv")
    if not _is_runtime_probe_worker_absolute_path_metadata(argv[0]) or argv[1] != "-m":
        raise ValueError("runtime probe dynamic import worker argv is malformed")


def _validate_runtime_probe_worker_python_path_entries(
    python_path_entries: tuple[str, ...],
) -> None:
    """Reject unordered or malformed Python path metadata."""
    if not isinstance(python_path_entries, tuple) or not python_path_entries:
        raise ValueError(
            "runtime probe dynamic import worker python_path_entries must be a tuple"
        )
    for python_path_entry in python_path_entries:
        _validate_runtime_probe_worker_path_text(
            python_path_entry,
            field_name="python_path_entries",
        )


def _validate_runtime_probe_worker_timeout_seconds(timeout_seconds: int) -> None:
    """Reject non-positive or untyped timeout metadata."""
    if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool):
        raise ValueError(
            "runtime probe dynamic import worker timeout_seconds must be an int"
        )
    if timeout_seconds <= 0:
        raise ValueError(
            "runtime probe dynamic import worker timeout_seconds must be positive"
        )


def _validate_runtime_probe_worker_invocation_identity(
    invocation_identity: str,
) -> None:
    """Reject malformed local-Python invocation identity metadata."""
    _validate_runtime_probe_worker_metadata_text(
        invocation_identity,
        field_name="invocation_identity",
    )
    if not invocation_identity.startswith(
        _DYNAMIC_IMPORT_WORKER_INVOCATION_IDENTITY_PREFIX
    ):
        raise ValueError(
            "runtime probe dynamic import worker invocation_identity is malformed"
        )
    digest = invocation_identity.removeprefix(
        _DYNAMIC_IMPORT_WORKER_INVOCATION_IDENTITY_PREFIX
    )
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(
            "runtime probe dynamic import worker invocation_identity is malformed"
        )


def _runtime_probe_worker_invocation_identity_from_parts(
    *,
    plan_id: str,
    request_id: str,
    invocation_contract_revision: str,
    argv: tuple[str, ...],
    working_directory: str,
    python_path_entries: tuple[str, ...],
    timeout_seconds: int,
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...],
) -> str:
    """Return the stable local-Python invocation identity for copied metadata."""
    replay_payload_identity = tuple(
        (field.key, field.value) for field in request_replay_payload_fields
    )
    serialized_identity = json.dumps(
        (
            ("plan_id", plan_id),
            ("request_id", request_id),
            ("invocation_contract_revision", invocation_contract_revision),
            ("argv", argv),
            ("working_directory", working_directory),
            ("python_path_entries", python_path_entries),
            ("timeout_seconds", timeout_seconds),
            ("request_replay_payload_fields", replay_payload_identity),
        ),
        separators=(",", ":"),
    )
    digest = hashlib.sha256(serialized_identity.encode("utf-8")).hexdigest()
    return f"{_DYNAMIC_IMPORT_WORKER_INVOCATION_IDENTITY_PREFIX}{digest}"


def _is_runtime_probe_worker_absolute_path_metadata(value: str) -> bool:
    """Return whether copied worker path metadata is absolute."""
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()


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
        if not isinstance(replay_field.key, str) or not replay_field.key.strip():
            raise ValueError(
                f"runtime probe worker {field_name} must not contain blank fields"
            )
        if not isinstance(replay_field.value, str) or not replay_field.value.strip():
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

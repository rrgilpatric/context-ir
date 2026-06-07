"""Private runtime probe worker stdout response protocol contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TypeAlias

from context_ir import (
    runtime_probe_worker_exec_or_eval_contracts as _exec_or_eval_contracts,
)
from context_ir.runtime_probe_results import RuntimeProbeReplayField

_RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION = (
    "runtime_probe_local_python_stdout_protocol:v1"
)
_RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION_KEY = (
    "runtime_probe_stdout_protocol_revision"
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
    observed_replay_inputs: tuple[RuntimeProbeReplayField, ...] = ()

    def __post_init__(self) -> None:
        """Reject malformed success payload metadata before stdout emission."""
        _validate_runtime_probe_worker_success_response(self)


RuntimeProbeLocalPythonWorkerHandlerResponse: TypeAlias = (
    RuntimeProbeLocalPythonWorkerResponse | RuntimeProbeLocalPythonWorkerSuccessResponse
)


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
    if response.observed_replay_inputs:
        protocol["observed_replay_inputs"] = (
            _runtime_probe_worker_replay_fields_json_array(
                response.observed_replay_inputs
            )
        )
    return json.dumps(protocol, separators=(",", ":"))


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
    _validate_runtime_probe_worker_replay_fields(
        response.observed_replay_inputs,
        field_name="observed_replay_inputs",
    )
    _validate_runtime_probe_worker_observed_replay_inputs(
        response.observed_replay_inputs
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


def _validate_runtime_probe_worker_observed_replay_inputs(
    observed_replay_inputs: tuple[RuntimeProbeReplayField, ...],
) -> None:
    """Reject observed replay inputs outside exact exec/eval source proof."""
    if not observed_replay_inputs:
        return
    fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        observed_replay_inputs,
        field_name="observed_replay_inputs",
    )
    exec_source_shape = _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHAPE
    exec_source_sha256 = _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHA256
    eval_source_shape = _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHAPE
    eval_source_sha256 = _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHA256
    exact_exec_source_proof = {
        "source_shape": exec_source_shape,
        "source_sha256": exec_source_sha256,
    }
    exact_eval_source_proof = {
        "source_shape": eval_source_shape,
        "source_sha256": eval_source_sha256,
    }
    if fields_by_key not in (exact_exec_source_proof, exact_eval_source_proof):
        raise ValueError(
            "runtime probe worker observed_replay_inputs must carry exact exec/eval "
            "source proof"
        )


def _runtime_probe_worker_replay_fields_by_key(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    field_name: str,
) -> dict[str, str]:
    """Return replay fields keyed by exact singleton key."""
    _validate_runtime_probe_worker_replay_fields(fields, field_name=field_name)
    fields_by_key: dict[str, str] = {}
    for field_item in fields:
        if field_item.key in fields_by_key:
            raise ValueError(
                f"runtime probe worker {field_name} must not contain duplicate keys"
            )
        fields_by_key[field_item.key] = field_item.value
    return fields_by_key


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

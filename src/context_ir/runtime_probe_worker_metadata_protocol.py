"""Private runtime probe worker metadata and replay validation helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import PurePosixPath, PureWindowsPath

from context_ir import runtime_probe_worker_response_protocol as _response_protocol
from context_ir.runtime_probe_results import RuntimeProbeReplayField
from context_ir.semantic_types import SemanticSubjectKind

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


def _runtime_probe_worker_required_replay_fields_by_key(
    fields: tuple[RuntimeProbeReplayField, ...],
) -> dict[str, str]:
    """Return required replay fields after enforcing exact singleton keys."""
    _response_protocol._validate_runtime_probe_worker_replay_fields(
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
    if value != value.strip() or _response_protocol._contains_control_character(value):
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

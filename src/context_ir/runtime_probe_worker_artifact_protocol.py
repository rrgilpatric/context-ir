"""Private durable artifact reference helpers for runtime probe workers."""

from __future__ import annotations

from context_ir import runtime_probe_worker_metadata_protocol as _metadata_protocol


def _runtime_probe_dir_listing_artifact_reference(request_id: str) -> str:
    """Return the deterministic durable reference for a captured dir listing."""
    _metadata_protocol._validate_runtime_probe_worker_metadata_text(
        request_id,
        field_name="request_id",
    )
    return f"artifact://runtime-probe/dir-listing/{request_id}.json"


def _runtime_probe_setattr_value_artifact_reference(request_id: str) -> str:
    """Return the deterministic durable reference for the assigned value argument."""
    _metadata_protocol._validate_runtime_probe_worker_metadata_text(
        request_id,
        field_name="request_id",
    )
    return f"artifact://runtime-probe/setattr-value/{request_id}.json"


def _runtime_probe_exec_source_artifact_reference(request_id: str) -> str:
    """Return the deterministic durable artifact reference for exec source proof."""
    _metadata_protocol._validate_runtime_probe_worker_metadata_text(
        request_id,
        field_name="request_id",
    )
    return f"artifact://runtime-probe/exec-source/{request_id}.json"


def _runtime_probe_eval_source_artifact_reference(request_id: str) -> str:
    """Return the deterministic durable artifact reference for eval source proof."""
    _metadata_protocol._validate_runtime_probe_worker_metadata_text(
        request_id,
        field_name="request_id",
    )
    return f"artifact://runtime-probe/eval-source/{request_id}.json"


def _runtime_probe_metaclass_selection_artifact_reference(request_id: str) -> str:
    """Return the deterministic durable artifact reference for metaclass proof."""
    _metadata_protocol._validate_runtime_probe_worker_metadata_text(
        request_id,
        field_name="request_id",
    )
    return f"artifact://runtime-probe/metaclass-selection/{request_id}.json"

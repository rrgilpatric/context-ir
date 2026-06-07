"""Private runtime probe worker replay-target path helpers."""

from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath

from context_ir import runtime_probe_worker_metadata_protocol as _metadata_protocol


def _runtime_probe_dynamic_import_source_module_name_from_path(
    source_file_path: str,
) -> str:
    """Return the strict dotted source module name for a repository Python file."""
    _metadata_protocol._validate_runtime_probe_worker_metadata_text(
        source_file_path,
        field_name="source_file_path",
    )
    if (
        PurePosixPath(source_file_path).is_absolute()
        or PureWindowsPath(source_file_path).is_absolute()
    ):
        raise ValueError(
            "runtime probe dynamic import replay target source_file_path "
            "must be repository-relative"
        )

    path_segments = tuple(source_file_path.split("/"))
    if any(segment in {"", ".", ".."} for segment in path_segments):
        raise ValueError(
            "runtime probe dynamic import replay target source_file_path is malformed"
        )

    file_name = path_segments[-1]
    if not file_name.endswith(".py"):
        raise ValueError(
            "runtime probe dynamic import replay target source_file_path "
            "must be a Python source file"
        )
    if file_name == "__init__.py":
        module_segments = path_segments[:-1]
    else:
        module_segments = (*path_segments[:-1], file_name.removesuffix(".py"))
    if not module_segments:
        raise ValueError(
            "runtime probe dynamic import replay target source module is malformed"
        )
    _validate_runtime_probe_dynamic_import_dotted_identifier_segments(
        module_segments,
        field_name="source module",
    )
    return ".".join(module_segments)


def _runtime_probe_dynamic_import_replay_target_attribute_path(
    *,
    source_module_name: str,
    replay_target_seed: str,
) -> tuple[str, ...]:
    """Return the attribute path for a replay target rooted at the source module."""
    source_module_segments = tuple(source_module_name.split("."))
    _validate_runtime_probe_dynamic_import_dotted_identifier_segments(
        source_module_segments,
        field_name="source_module_name",
    )
    _metadata_protocol._validate_runtime_probe_worker_metadata_text(
        replay_target_seed,
        field_name="replay_target_seed",
    )
    if replay_target_seed.startswith("source:"):
        raise ValueError(
            "runtime probe dynamic import replay target replay_target_seed "
            "is unsupported"
        )

    replay_target_segments = tuple(replay_target_seed.split("."))
    _validate_runtime_probe_dynamic_import_dotted_identifier_segments(
        replay_target_segments,
        field_name="replay_target_seed",
    )
    if replay_target_segments[: len(source_module_segments)] != source_module_segments:
        raise ValueError(
            "runtime probe dynamic import replay target replay_target_seed "
            "must be rooted at source_module_name"
        )
    replay_target_attribute_path = replay_target_segments[len(source_module_segments) :]
    if not replay_target_attribute_path:
        raise ValueError(
            "runtime probe dynamic import replay target "
            "replay_target_attribute_path must be non-empty"
        )
    _validate_runtime_probe_dynamic_import_dotted_identifier_segments(
        replay_target_attribute_path,
        field_name="replay_target_attribute_path",
    )
    return replay_target_attribute_path


def _validate_runtime_probe_dynamic_import_dotted_identifier_segments(
    segments: tuple[str, ...],
    *,
    field_name: str,
) -> None:
    """Reject blank or non-identifier module and attribute path segments."""
    if not segments:
        raise ValueError(
            f"runtime probe dynamic import replay target {field_name} must be non-empty"
        )
    if any(not segment or not segment.isidentifier() for segment in segments):
        raise ValueError(
            "runtime probe dynamic import replay target "
            f"{field_name} contains malformed module or attribute segments"
        )

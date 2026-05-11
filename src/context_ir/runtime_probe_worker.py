"""Fail-closed local Python runtime probe worker ingress."""

from __future__ import annotations

import builtins
import contextlib
import hashlib
import importlib
import io
import json
import os
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath, PureWindowsPath
from types import MappingProxyType, ModuleType
from typing import TextIO, TypeAlias, cast

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
_DYNAMIC_IMPORT_WORKER_LOADER_FORM_LABEL = "dynamic_import:loader.import_module/1"
_DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL = "dynamic_import:import_module/1"
_DYNAMIC_IMPORT_WORKER_LOAD_MODULE_FORM_LABEL = "dynamic_import:load_module/1"
_DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL = "dynamic_import:__import__/1"
_DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL = (
    "dynamic_import:builtins.__import__/1"
)
_DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL = (
    "dynamic_import:loader.__import__/1"
)
_DYNAMIC_IMPORT_WORKER_FORM_LABELS = (
    _DYNAMIC_IMPORT_WORKER_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_LOADER_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_LOAD_MODULE_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL,
)
_DYNAMIC_IMPORT_WORKER_IMPORT_MODULE_GLOBAL_NAME = "import_module"
_DYNAMIC_IMPORT_WORKER_LOAD_MODULE_GLOBAL_NAME = "load_module"
_DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAME = "builtins"
_DYNAMIC_IMPORT_WORKER_LOADER_GLOBAL_NAME = "loader"
_DYNAMIC_IMPORT_WORKER_SOURCE_GLOBAL_NAMES_BY_FORM_LABEL = MappingProxyType(
    {
        _DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL: (
            _DYNAMIC_IMPORT_WORKER_IMPORT_MODULE_GLOBAL_NAME
        ),
        _DYNAMIC_IMPORT_WORKER_LOAD_MODULE_FORM_LABEL: (
            _DYNAMIC_IMPORT_WORKER_LOAD_MODULE_GLOBAL_NAME
        ),
    }
)
_DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAMES_BY_FORM_LABEL = MappingProxyType(
    {
        _DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL: (
            _DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAME
        ),
        _DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL: (
            _DYNAMIC_IMPORT_WORKER_LOADER_GLOBAL_NAME
        ),
    }
)
_DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL = object()
_DYNAMIC_IMPORT_WORKER_MISSING_MODULE = object()
_DYNAMIC_IMPORT_WORKER_INVOCATION_IDENTITY_PREFIX = (
    "runtime_probe_local_python_subprocess_invocation:"
)
_DYNAMIC_IMPORT_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe dynamic import worker target execution failed"
)
_DYNAMIC_IMPORT_WORKER_IMPORT_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe dynamic import worker package imports are unsupported",
        "runtime probe dynamic import worker relative imports are unsupported",
        "runtime probe dynamic import worker module name is malformed",
    )
)
_REFLECTIVE_BUILTIN_HASATTR_WORKER_FORM_LABEL = "reflective_builtin:hasattr/2"
_REFLECTIVE_BUILTIN_HASATTR_WORKER_BOUNDARY_TEXT = "hasattr(obj, name)"
_REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME = "hasattr"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_FORM_LABEL = "reflective_builtin:getattr/2"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_BOUNDARY_TEXT = "getattr(obj, name)"
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_FORM_LABEL = "reflective_builtin:getattr/3"
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_BOUNDARY_TEXT = "getattr(obj, name, default)"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME = "getattr"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_VALUE = "returned_value"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_RAISED_ATTRIBUTE_ERROR = "raised_attribute_error"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_DEFAULT_VALUE = "returned_default_value"
_REFLECTIVE_BUILTIN_VARS_WORKER_FORM_LABEL = "reflective_builtin:vars/1"
_REFLECTIVE_BUILTIN_VARS_WORKER_BOUNDARY_TEXT = "vars(obj)"
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_FORM_LABEL = "reflective_builtin:vars/0"
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_BOUNDARY_TEXT = "vars()"
_REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME = "vars"
_REFLECTIVE_BUILTIN_VARS_WORKER_RETURNED_NAMESPACE = "returned_namespace"
_REFLECTIVE_BUILTIN_VARS_WORKER_RAISED_TYPE_ERROR = "raised_type_error"
_REFLECTIVE_BUILTIN_WORKER_FORM_LABELS = (
    _REFLECTIVE_BUILTIN_HASATTR_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_GETATTR_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_VARS_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_FORM_LABEL,
)
_REFLECTIVE_BUILTIN_HASATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe reflective builtin hasattr worker target execution failed"
)
_REFLECTIVE_BUILTIN_HASATTR_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe reflective builtin hasattr worker form must be exactly "
        "hasattr(obj, name)",
        "runtime probe reflective builtin hasattr worker attribute name must be a "
        "string",
    )
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe reflective builtin getattr worker target execution failed"
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe reflective builtin getattr worker form must be exactly "
        "getattr(obj, name)",
        "runtime probe reflective builtin getattr worker attribute name must be a "
        "string",
    )
)
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe reflective builtin getattr default worker target execution failed"
)
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe reflective builtin getattr default worker form must be "
        "exactly getattr(obj, name, default)",
        "runtime probe reflective builtin getattr default worker attribute name "
        "must be a string",
    )
)
_REFLECTIVE_BUILTIN_VARS_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe reflective builtin vars worker target execution failed"
)
_REFLECTIVE_BUILTIN_VARS_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    ("runtime probe reflective builtin vars worker form must be exactly vars(obj)",)
)
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe reflective builtin vars zero worker target execution failed"
)
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    ("runtime probe reflective builtin vars zero worker form must be exactly vars()",)
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
    """Worker-local request contract for import-module probes only."""

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
class RuntimeProbeLocalPythonDynamicImportWorkerObservation:
    """Worker-local dynamic-import observation metadata before stdout emission."""

    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    imported_module: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed module observations."""
        _validate_runtime_probe_dynamic_import_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonDynamicImportReplayTarget:
    """Worker-local non-executing replay target plan for dynamic imports."""

    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest
    plan_id: str
    request_id: str
    source_file_path: str
    source_module_name: str
    replay_target_seed: str
    replay_target_attribute_path: tuple[str, ...]
    replay_selector_seed: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject replay targets whose copied request identity has drifted."""
        _validate_runtime_probe_dynamic_import_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest:
    """Worker-local request contract for exact ``hasattr(obj, name)`` probes."""

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
        """Reject drifted or non-hasattr reflective worker request metadata."""
        _validate_runtime_probe_reflective_hasattr_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation:
    """Worker-local observation metadata for exact ``hasattr`` probes."""

    request: RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    attribute_present: bool

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed hasattr observations."""
        _validate_runtime_probe_reflective_hasattr_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveHasattrReplayTarget:
    """Worker-local non-executing replay target plan for exact ``hasattr``."""

    request: RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest
    plan_id: str
    request_id: str
    source_file_path: str
    source_module_name: str
    replay_target_seed: str
    replay_target_attribute_path: tuple[str, ...]
    replay_selector_seed: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject replay targets whose copied request identity has drifted."""
        _validate_runtime_probe_reflective_hasattr_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest:
    """Worker-local request contract for exact ``getattr(obj, name)`` probes."""

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
        """Reject drifted or non-getattr reflective worker request metadata."""
        _validate_runtime_probe_reflective_getattr_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation:
    """Worker-local observation metadata for exact ``getattr`` probes."""

    request: RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    lookup_outcome: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed getattr observations."""
        _validate_runtime_probe_reflective_getattr_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveGetattrReplayTarget:
    """Worker-local non-executing replay target plan for exact ``getattr``."""

    request: RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest
    plan_id: str
    request_id: str
    source_file_path: str
    source_module_name: str
    replay_target_seed: str
    replay_target_attribute_path: tuple[str, ...]
    replay_selector_seed: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject replay targets whose copied request identity has drifted."""
        _validate_runtime_probe_reflective_getattr_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest:
    """Worker-local request contract for exact ``getattr(obj, name, default)``."""

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
        """Reject drifted or non-getattr-default reflective request metadata."""
        _validate_runtime_probe_reflective_getattr_default_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation:
    """Worker-local observation metadata for exact ``getattr`` default probes."""

    request: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    lookup_outcome: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed getattr/3 observations."""
        _validate_runtime_probe_reflective_getattr_default_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveGetattrDefaultReplayTarget:
    """Worker-local non-executing replay target plan for exact ``getattr/3``."""

    request: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest
    plan_id: str
    request_id: str
    source_file_path: str
    source_module_name: str
    replay_target_seed: str
    replay_target_attribute_path: tuple[str, ...]
    replay_selector_seed: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject replay targets whose copied request identity has drifted."""
        _validate_runtime_probe_reflective_getattr_default_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveVarsWorkerRequest:
    """Worker-local request contract for exact ``vars(obj)`` probes."""

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
        """Reject drifted or non-vars reflective worker request metadata."""
        _validate_runtime_probe_reflective_vars_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveVarsWorkerObservation:
    """Worker-local observation metadata for exact ``vars`` probes."""

    request: RuntimeProbeLocalPythonReflectiveVarsWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    lookup_outcome: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed vars observations."""
        _validate_runtime_probe_reflective_vars_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveVarsReplayTarget:
    """Worker-local non-executing replay target plan for exact ``vars/1``."""

    request: RuntimeProbeLocalPythonReflectiveVarsWorkerRequest
    plan_id: str
    request_id: str
    source_file_path: str
    source_module_name: str
    replay_target_seed: str
    replay_target_attribute_path: tuple[str, ...]
    replay_selector_seed: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject replay targets whose copied request identity has drifted."""
        _validate_runtime_probe_reflective_vars_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest:
    """Worker-local request contract for exact ``vars()`` probes."""

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
        """Reject drifted or non-vars/0 reflective worker request metadata."""
        _validate_runtime_probe_reflective_vars_zero_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation:
    """Worker-local observation metadata for exact ``vars()`` probes."""

    request: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    lookup_outcome: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed vars/0 observations."""
        _validate_runtime_probe_reflective_vars_zero_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveVarsZeroReplayTarget:
    """Worker-local non-executing replay target plan for exact ``vars/0``."""

    request: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest
    plan_id: str
    request_id: str
    source_file_path: str
    source_module_name: str
    replay_target_seed: str
    replay_target_attribute_path: tuple[str, ...]
    replay_selector_seed: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject replay targets whose copied request identity has drifted."""
        _validate_runtime_probe_reflective_vars_zero_replay_target(self)


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
RuntimeProbeLocalPythonDynamicImportWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonDynamicImportWorkerRequest],
    RuntimeProbeLocalPythonDynamicImportWorkerObservation,
]
RuntimeProbeLocalPythonReflectiveHasattrWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest],
    RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation,
]
RuntimeProbeLocalPythonReflectiveGetattrWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest],
    RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation,
]
RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest],
    RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation,
]
RuntimeProbeLocalPythonReflectiveVarsWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonReflectiveVarsWorkerRequest],
    RuntimeProbeLocalPythonReflectiveVarsWorkerObservation,
]
RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest],
    RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation,
]
RuntimeProbeLocalPythonDynamicImportTargetCallable: TypeAlias = Callable[[], object]
RuntimeProbeLocalPythonReflectiveHasattrTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonReflectiveGetattrTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonReflectiveGetattrDefaultTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonReflectiveVarsTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonReflectiveVarsZeroTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonDynamicImportObservationSource: TypeAlias = (
    RuntimeProbeLocalPythonDynamicImportWorkerRequest
    | RuntimeProbeLocalPythonDynamicImportReplayTarget
)
RuntimeProbeLocalPythonWorkerCallable: TypeAlias = Callable[
    [RuntimeProbeLocalPythonWorkerRequestPayload],
    RuntimeProbeLocalPythonWorkerHandlerResponse,
]


@dataclass
class _RuntimeProbeDynamicImportCapture:
    """Mutable capture state for one controlled import-module execution."""

    captured_modules: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)
    captured_sys_modules: dict[str, ModuleType | object] = field(default_factory=dict)

    def import_module(self, name: str, package: str | None = None) -> ModuleType:
        """Capture one import-module request without importing the real module."""
        if package is not None:
            self.captured_rejections.append("package")
            raise ValueError(
                "runtime probe dynamic import worker package imports are unsupported"
            )
        if name.startswith("."):
            self.captured_rejections.append("relative")
            raise ValueError(
                "runtime probe dynamic import worker relative imports are unsupported"
            )
        try:
            _validate_runtime_probe_dynamic_import_imported_module(name)
        except ValueError as error:
            self.captured_rejections.append("malformed")
            raise ValueError(
                "runtime probe dynamic import worker module name is malformed"
            ) from error
        self.captured_modules.append(name)
        return ModuleType(name)

    def builtin_import(self, *args: object, **kwargs: object) -> ModuleType:
        """Capture one bare __import__(name) request without importing."""
        if kwargs:
            if "package" in kwargs:
                self.captured_rejections.append("package")
                raise ValueError(
                    "runtime probe dynamic import worker package imports are "
                    "unsupported"
                )
            elif "level" in kwargs:
                self.captured_rejections.append("relative")
                raise ValueError(
                    "runtime probe dynamic import worker relative imports are "
                    "unsupported"
                )
            elif {"globals", "locals", "fromlist"} & set(kwargs):
                self.captured_rejections.append("import_context")
                raise ValueError(
                    "runtime probe dynamic import worker __import__ globals locals "
                    "and fromlist arguments are unsupported"
                )
            else:
                self.captured_rejections.append("keyword")
                raise ValueError(
                    "runtime probe dynamic import worker __import__ keyword "
                    "arguments are unsupported"
                )
        if len(args) != 1:
            if len(args) > 1:
                self.captured_rejections.append("import_context")
                raise ValueError(
                    "runtime probe dynamic import worker __import__ globals locals "
                    "and fromlist arguments are unsupported"
                )
            else:
                self.captured_rejections.append("arity")
                raise ValueError(
                    "runtime probe dynamic import worker __import__ form must be "
                    "exactly __import__(name)"
                )
        name = args[0]
        if not isinstance(name, str):
            self.captured_rejections.append("malformed")
            raise ValueError(
                "runtime probe dynamic import worker module name is malformed"
            )
        if name.startswith("."):
            self.captured_rejections.append("relative")
            raise ValueError(
                "runtime probe dynamic import worker relative imports are unsupported"
            )
        try:
            _validate_runtime_probe_dynamic_import_imported_module(name)
        except ValueError as error:
            self.captured_rejections.append("malformed")
            raise ValueError(
                "runtime probe dynamic import worker module name is malformed"
            ) from error
        self.captured_modules.append(name)
        controlled_module = ModuleType(name)
        self._insert_controlled_sys_module(name, controlled_module)
        return controlled_module

    def restore_sys_modules(self) -> ValueError | None:
        """Restore sys.modules entries controlled by captured __import__ calls."""
        for module_name, original_module in reversed(
            tuple(self.captured_sys_modules.items())
        ):
            try:
                if original_module is _DYNAMIC_IMPORT_WORKER_MISSING_MODULE:
                    sys.modules.pop(module_name, None)
                else:
                    sys.modules[module_name] = cast(ModuleType, original_module)
            except Exception:
                return ValueError(
                    "runtime probe dynamic import worker sys.modules entry could "
                    "not be restored"
                )
        return None

    def _insert_controlled_sys_module(
        self,
        name: str,
        controlled_module: ModuleType,
    ) -> None:
        """Insert one temporary sys.modules entry and remember prior state."""
        if name not in self.captured_sys_modules:
            self.captured_sys_modules[name] = sys.modules.get(
                name,
                _DYNAMIC_IMPORT_WORKER_MISSING_MODULE,
            )
        sys.modules[name] = controlled_module


@dataclass
class _RuntimeProbeReflectiveHasattrCapture:
    """Mutable capture state for one controlled ``hasattr`` execution."""

    original_hasattr: Callable[[object, str], bool]
    captured_attribute_presence: list[bool] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def hasattr(self, *args: object, **kwargs: object) -> bool:
        """Capture one exact two-argument ``hasattr`` call."""
        if kwargs or len(args) != 2:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe reflective builtin hasattr worker form must be "
                "exactly hasattr(obj, name)"
            )
        obj, name = args
        if not isinstance(name, str):
            self.captured_rejections.append("name")
            raise ValueError(
                "runtime probe reflective builtin hasattr worker attribute name "
                "must be a string"
            )
        attribute_present = self.original_hasattr(obj, name)
        self.captured_attribute_presence.append(attribute_present)
        return attribute_present


@dataclass
class _RuntimeProbeReflectiveGetattrCapture:
    """Mutable capture state for one controlled ``getattr`` execution."""

    original_getattr: Callable[[object, str], object]
    captured_lookup_outcomes: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def getattr(self, *args: object, **kwargs: object) -> object:
        """Capture one exact two-argument ``getattr`` call."""
        if kwargs or len(args) != 2:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe reflective builtin getattr worker form must be "
                "exactly getattr(obj, name)"
            )
        obj, name = args
        if not isinstance(name, str):
            self.captured_rejections.append("name")
            raise ValueError(
                "runtime probe reflective builtin getattr worker attribute name "
                "must be a string"
            )
        try:
            result = self.original_getattr(obj, name)
        except AttributeError:
            self.captured_lookup_outcomes.append(
                _REFLECTIVE_BUILTIN_GETATTR_WORKER_RAISED_ATTRIBUTE_ERROR
            )
            raise
        self.captured_lookup_outcomes.append(
            _REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_VALUE
        )
        return result


@dataclass
class _RuntimeProbeReflectiveGetattrDefaultCapture:
    """Mutable capture state for one controlled ``getattr`` default execution."""

    original_getattr: Callable[..., object]
    captured_lookup_outcomes: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def getattr(self, *args: object, **kwargs: object) -> object:
        """Capture one exact three-argument ``getattr`` call."""
        if kwargs or len(args) != 3:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe reflective builtin getattr default worker form must "
                "be exactly getattr(obj, name, default)"
            )
        obj, name, default = args
        if not isinstance(name, str):
            self.captured_rejections.append("name")
            raise ValueError(
                "runtime probe reflective builtin getattr default worker attribute "
                "name must be a string"
            )
        try:
            result = self.original_getattr(obj, name)
        except AttributeError:
            self.captured_lookup_outcomes.append(
                _REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_DEFAULT_VALUE
            )
            return default
        self.captured_lookup_outcomes.append(
            _REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_VALUE
        )
        return result


@dataclass
class _RuntimeProbeReflectiveVarsCapture:
    """Mutable capture state for one controlled ``vars`` execution."""

    original_vars: Callable[[object], object]
    captured_lookup_outcomes: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def vars(self, *args: object, **kwargs: object) -> object:
        """Capture one exact one-argument ``vars`` call."""
        if kwargs or len(args) != 1:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe reflective builtin vars worker form must be exactly "
                "vars(obj)"
            )
        (obj,) = args
        try:
            namespace = self.original_vars(obj)
        except TypeError:
            self.captured_lookup_outcomes.append(
                _REFLECTIVE_BUILTIN_VARS_WORKER_RAISED_TYPE_ERROR
            )
            raise
        self.captured_lookup_outcomes.append(
            _REFLECTIVE_BUILTIN_VARS_WORKER_RETURNED_NAMESPACE
        )
        return namespace


@dataclass
class _RuntimeProbeReflectiveVarsZeroCapture:
    """Mutable capture state for one controlled zero-argument ``vars`` execution."""

    captured_lookup_outcomes: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def vars(self, *args: object, **kwargs: object) -> object:
        """Capture one exact zero-argument ``vars`` call."""
        if kwargs or args:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe reflective builtin vars zero worker form must be "
                "exactly vars()"
            )
        caller_namespace = dict(sys._getframe(1).f_locals)
        self.captured_lookup_outcomes.append(
            _REFLECTIVE_BUILTIN_VARS_WORKER_RETURNED_NAMESPACE
        )
        return caller_namespace


@dataclass(frozen=True)
class RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected dynamic-import observer."""

    observer: RuntimeProbeLocalPythonDynamicImportWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_dynamic_import_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_dynamic_import_worker_request(payload)
        observation = self.observer(request)
        _validate_runtime_probe_dynamic_import_worker_observation_for_request(
            observation,
            request,
        )
        return materialize_runtime_probe_dynamic_import_worker_success_response(
            observation
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveHasattrWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-hasattr observer."""

    observer: RuntimeProbeLocalPythonReflectiveHasattrWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_reflective_hasattr_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_reflective_hasattr_worker_request(payload)
        observation = self.observer(request)
        _validate_runtime_probe_reflective_hasattr_worker_observation_for_request(
            observation,
            request,
        )
        return materialize_runtime_probe_reflective_hasattr_worker_success_response(
            observation
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveGetattrWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-getattr observer."""

    observer: RuntimeProbeLocalPythonReflectiveGetattrWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_reflective_getattr_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_reflective_getattr_worker_request(payload)
        observation = self.observer(request)
        _validate_runtime_probe_reflective_getattr_worker_observation_for_request(
            observation,
            request,
        )
        return materialize_runtime_probe_reflective_getattr_worker_success_response(
            observation
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-getattr/3 observer."""

    observer: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_reflective_getattr_default_worker_observer(
            self.observer
        )

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_reflective_getattr_default_worker_request(
            payload
        )
        observation = self.observer(request)
        _validate_runtime_probe_reflective_getattr_default_worker_observation_for_request(
            observation,
            request,
        )
        materialize_success_response = (
            materialize_runtime_probe_reflective_getattr_default_worker_success_response
        )
        return materialize_success_response(observation)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveVarsWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-vars observer."""

    observer: RuntimeProbeLocalPythonReflectiveVarsWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_reflective_vars_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_reflective_vars_worker_request(payload)
        observation = self.observer(request)
        _validate_runtime_probe_reflective_vars_worker_observation_for_request(
            observation,
            request,
        )
        return materialize_runtime_probe_reflective_vars_worker_success_response(
            observation
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveVarsZeroWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-vars/0 observer."""

    observer: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_reflective_vars_zero_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_reflective_vars_zero_worker_request(payload)
        observation = self.observer(request)
        _validate_runtime_probe_reflective_vars_zero_worker_observation_for_request(
            observation,
            request,
        )
        return materialize_runtime_probe_reflective_vars_zero_worker_success_response(
            observation
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


class _RuntimeProbeWorkerDefaultHandlerEntries:
    """Marker for omitted worker handler entries."""


_DEFAULT_RUNTIME_PROBE_WORKER_HANDLER_ENTRIES = (
    _RuntimeProbeWorkerDefaultHandlerEntries()
)


def main(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    *,
    handler_entries: (
        Iterable[RuntimeProbeLocalPythonWorkerHandlerEntry]
        | _RuntimeProbeWorkerDefaultHandlerEntries
    ) = _DEFAULT_RUNTIME_PROBE_WORKER_HANDLER_ENTRIES,
) -> int:
    """Read one worker request from stdin and route handlers fail-closed."""
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
    handler_entries: (
        Iterable[RuntimeProbeLocalPythonWorkerHandlerEntry]
        | _RuntimeProbeWorkerDefaultHandlerEntries
    ),
) -> RuntimeProbeLocalPythonWorkerHandlerResponse:
    """Dispatch one parsed worker payload through resolved worker handlers."""
    try:
        dispatching_worker = RuntimeProbeLocalPythonDispatchingWorker(
            handler_entries=tuple(
                _runtime_probe_local_python_worker_handler_entries(handler_entries)
            ),
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


def materialize_runtime_probe_dynamic_import_worker_observation(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
    *,
    imported_module: str,
) -> RuntimeProbeLocalPythonDynamicImportWorkerObservation:
    """Build non-executing dynamic-import observation metadata from a request."""
    _validate_runtime_probe_dynamic_import_worker_request(request)
    return RuntimeProbeLocalPythonDynamicImportWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        imported_module=imported_module,
    )


def materialize_runtime_probe_dynamic_import_replay_target(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> RuntimeProbeLocalPythonDynamicImportReplayTarget:
    """Derive a non-executing local Python replay target from a request."""
    _validate_runtime_probe_dynamic_import_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonDynamicImportReplayTarget(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        source_file_path=request.source_file_path,
        source_module_name=source_module_name,
        replay_target_seed=request.replay_target_seed,
        replay_target_attribute_path=replay_target_attribute_path,
        replay_selector_seed=request.replay_selector_seed,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
    )


def materialize_runtime_probe_dynamic_import_worker_success_response(
    observation: RuntimeProbeLocalPythonDynamicImportWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one module observation."""
    _validate_runtime_probe_dynamic_import_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="imported_module",
                value=observation.imported_module,
            ),
        ),
    )


def materialize_runtime_probe_reflective_hasattr_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest:
    """Derive an exact-hasattr worker request from stdin payload."""
    _validate_runtime_probe_reflective_hasattr_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest(
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
        reason_code=_runtime_probe_worker_reflective_hasattr_reason_code_from_replay_field(
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


def materialize_runtime_probe_reflective_hasattr_worker_observation(
    request: RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest,
    *,
    attribute_present: bool,
) -> RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation:
    """Build non-executing exact-hasattr observation metadata from a request."""
    _validate_runtime_probe_reflective_hasattr_worker_request(request)
    return RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        attribute_present=attribute_present,
    )


def materialize_runtime_probe_reflective_hasattr_replay_target(
    request: RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveHasattrReplayTarget:
    """Derive a non-executing local Python replay target from a request."""
    _validate_runtime_probe_reflective_hasattr_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonReflectiveHasattrReplayTarget(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        source_file_path=request.source_file_path,
        source_module_name=source_module_name,
        replay_target_seed=request.replay_target_seed,
        replay_target_attribute_path=replay_target_attribute_path,
        replay_selector_seed=request.replay_selector_seed,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
    )


def materialize_runtime_probe_reflective_hasattr_worker_success_response(
    observation: RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one hasattr observation."""
    _validate_runtime_probe_reflective_hasattr_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="attribute_present",
                value=("true" if observation.attribute_present else "false"),
            ),
        ),
    )


def materialize_runtime_probe_reflective_getattr_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest:
    """Derive an exact-getattr worker request from stdin payload."""
    _validate_runtime_probe_reflective_getattr_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest(
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
        reason_code=_runtime_probe_worker_reflective_getattr_reason_code_from_replay_field(
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


def materialize_runtime_probe_reflective_getattr_worker_observation(
    request: RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest,
    *,
    lookup_outcome: str,
) -> RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation:
    """Build non-executing exact-getattr observation metadata from a request."""
    _validate_runtime_probe_reflective_getattr_worker_request(request)
    return RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        lookup_outcome=lookup_outcome,
    )


def materialize_runtime_probe_reflective_getattr_replay_target(
    request: RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveGetattrReplayTarget:
    """Derive a non-executing local Python replay target from a request."""
    _validate_runtime_probe_reflective_getattr_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonReflectiveGetattrReplayTarget(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        source_file_path=request.source_file_path,
        source_module_name=source_module_name,
        replay_target_seed=request.replay_target_seed,
        replay_target_attribute_path=replay_target_attribute_path,
        replay_selector_seed=request.replay_selector_seed,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
    )


def materialize_runtime_probe_reflective_getattr_worker_success_response(
    observation: RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one getattr observation."""
    _validate_runtime_probe_reflective_getattr_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="lookup_outcome",
                value=observation.lookup_outcome,
            ),
        ),
    )


def materialize_runtime_probe_reflective_getattr_default_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest:
    """Derive an exact-getattr/3 worker request from stdin payload."""
    _validate_runtime_probe_reflective_getattr_default_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest(
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
        reason_code=(
            _runtime_probe_worker_reflective_getattr_default_reason_code_from_replay_field(
                replay_fields_by_key["reason_code"]
            )
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


def materialize_runtime_probe_reflective_getattr_default_worker_observation(
    request: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest,
    *,
    lookup_outcome: str,
) -> RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation:
    """Build non-executing exact-getattr/3 observation metadata from a request."""
    _validate_runtime_probe_reflective_getattr_default_worker_request(request)
    return RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        lookup_outcome=lookup_outcome,
    )


def materialize_runtime_probe_reflective_getattr_default_replay_target(
    request: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveGetattrDefaultReplayTarget:
    """Derive a non-executing local Python replay target from a request."""
    _validate_runtime_probe_reflective_getattr_default_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonReflectiveGetattrDefaultReplayTarget(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        source_file_path=request.source_file_path,
        source_module_name=source_module_name,
        replay_target_seed=request.replay_target_seed,
        replay_target_attribute_path=replay_target_attribute_path,
        replay_selector_seed=request.replay_selector_seed,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
    )


def materialize_runtime_probe_reflective_getattr_default_worker_success_response(
    observation: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one getattr/3 observation."""
    _validate_runtime_probe_reflective_getattr_default_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="lookup_outcome",
                value=observation.lookup_outcome,
            ),
        ),
    )


def materialize_runtime_probe_reflective_vars_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonReflectiveVarsWorkerRequest:
    """Derive an exact-vars worker request from stdin payload."""
    _validate_runtime_probe_reflective_vars_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonReflectiveVarsWorkerRequest(
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
        reason_code=_runtime_probe_worker_reflective_vars_reason_code_from_replay_field(
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


def materialize_runtime_probe_reflective_vars_worker_observation(
    request: RuntimeProbeLocalPythonReflectiveVarsWorkerRequest,
    *,
    lookup_outcome: str,
) -> RuntimeProbeLocalPythonReflectiveVarsWorkerObservation:
    """Build non-executing exact-vars observation metadata from a request."""
    _validate_runtime_probe_reflective_vars_worker_request(request)
    return RuntimeProbeLocalPythonReflectiveVarsWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        lookup_outcome=lookup_outcome,
    )


def materialize_runtime_probe_reflective_vars_replay_target(
    request: RuntimeProbeLocalPythonReflectiveVarsWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveVarsReplayTarget:
    """Derive a non-executing local Python replay target from a request."""
    _validate_runtime_probe_reflective_vars_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonReflectiveVarsReplayTarget(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        source_file_path=request.source_file_path,
        source_module_name=source_module_name,
        replay_target_seed=request.replay_target_seed,
        replay_target_attribute_path=replay_target_attribute_path,
        replay_selector_seed=request.replay_selector_seed,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
    )


def materialize_runtime_probe_reflective_vars_worker_success_response(
    observation: RuntimeProbeLocalPythonReflectiveVarsWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one vars observation."""
    _validate_runtime_probe_reflective_vars_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="lookup_outcome",
                value=observation.lookup_outcome,
            ),
        ),
    )


def materialize_runtime_probe_reflective_vars_zero_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest:
    """Derive an exact-vars/0 worker request from stdin payload."""
    _validate_runtime_probe_reflective_vars_zero_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest(
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
        reason_code=(
            _runtime_probe_worker_reflective_vars_zero_reason_code_from_replay_field(
                replay_fields_by_key["reason_code"]
            )
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


def materialize_runtime_probe_reflective_vars_zero_worker_observation(
    request: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest,
    *,
    lookup_outcome: str,
) -> RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation:
    """Build non-executing exact-vars/0 observation metadata from a request."""
    _validate_runtime_probe_reflective_vars_zero_worker_request(request)
    return RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        lookup_outcome=lookup_outcome,
    )


def materialize_runtime_probe_reflective_vars_zero_replay_target(
    request: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveVarsZeroReplayTarget:
    """Derive a non-executing local Python replay target from a vars/0 request."""
    _validate_runtime_probe_reflective_vars_zero_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonReflectiveVarsZeroReplayTarget(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        source_file_path=request.source_file_path,
        source_module_name=source_module_name,
        replay_target_seed=request.replay_target_seed,
        replay_target_attribute_path=replay_target_attribute_path,
        replay_selector_seed=request.replay_selector_seed,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
    )


def materialize_runtime_probe_reflective_vars_zero_worker_success_response(
    observation: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one vars/0 observation."""
    _validate_runtime_probe_reflective_vars_zero_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="lookup_outcome",
                value=observation.lookup_outcome,
            ),
        ),
    )


def materialize_runtime_probe_dynamic_import_worker_observation_from_target(
    observation_source: RuntimeProbeLocalPythonDynamicImportObservationSource,
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
) -> RuntimeProbeLocalPythonDynamicImportWorkerObservation:
    """Observe one injected zero-argument target under import-module interception."""
    request = _runtime_probe_dynamic_import_observation_source_request(
        observation_source
    )
    _validate_runtime_probe_dynamic_import_target_callable(target)
    if request.form_label in (
        _DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL,
        _DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL,
        _DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL,
    ):
        imported_module = _runtime_probe_dynamic_import_captured_builtin_import_name(
            target
        )
    else:
        imported_module = _runtime_probe_dynamic_import_captured_import_module_name(
            target
        )
    return materialize_runtime_probe_dynamic_import_worker_observation(
        request,
        imported_module=imported_module,
    )


def observe_runtime_probe_dynamic_import_worker_request(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> RuntimeProbeLocalPythonDynamicImportWorkerObservation:
    """Observe one concrete dynamic-import worker request in local Python."""
    _validate_runtime_probe_dynamic_import_worker_request(request)
    replay_target = materialize_runtime_probe_dynamic_import_replay_target(request)
    source_module = import_runtime_probe_dynamic_import_replay_target_source_module(
        replay_target
    )
    target = resolve_runtime_probe_dynamic_import_replay_target_callable(
        replay_target,
        source_module,
    )
    deterministic_target = _runtime_probe_dynamic_import_target_execution_guard(target)
    if request.form_label in _DYNAMIC_IMPORT_WORKER_SOURCE_GLOBAL_NAMES_BY_FORM_LABEL:
        return _materialize_runtime_probe_dynamic_import_worker_observation_from_global(
            replay_target=replay_target,
            source_module=source_module,
            target=deterministic_target,
            global_name=_runtime_probe_dynamic_import_source_global_name_for_form(
                request.form_label
            ),
        )
    if request.form_label == _DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL:
        return _materialize_runtime_probe_dynamic_import_builtin_observation(
            replay_target=replay_target,
            source_module=source_module,
            target=deterministic_target,
        )
    if request.form_label in _DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAMES_BY_FORM_LABEL:
        return _materialize_runtime_probe_dynamic_import_builtins_observation(
            replay_target=replay_target,
            source_module=source_module,
            target=deterministic_target,
            global_name=_runtime_probe_dynamic_import_source_builtins_global_name_for_form(
                request.form_label
            ),
        )
    return materialize_runtime_probe_dynamic_import_worker_observation_from_target(
        replay_target,
        deterministic_target,
    )


def materialize_runtime_probe_reflective_hasattr_worker_observation_from_target(
    replay_target: RuntimeProbeLocalPythonReflectiveHasattrReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveHasattrTargetCallable,
) -> RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation:
    """Observe one zero-argument target under exact ``hasattr`` interception."""
    _validate_runtime_probe_reflective_hasattr_replay_target(replay_target)
    _validate_runtime_probe_reflective_hasattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_hasattr_target_callable(target)
    attribute_present = _runtime_probe_reflective_hasattr_captured_attribute_present(
        source_module,
        target,
    )
    return materialize_runtime_probe_reflective_hasattr_worker_observation(
        replay_target.request,
        attribute_present=attribute_present,
    )


def observe_runtime_probe_reflective_hasattr_worker_request(
    request: RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation:
    """Observe one concrete exact-hasattr worker request in local Python."""
    _validate_runtime_probe_reflective_hasattr_worker_request(request)
    replay_target = materialize_runtime_probe_reflective_hasattr_replay_target(request)
    source_module = import_runtime_probe_reflective_hasattr_replay_target_source_module(
        replay_target
    )
    target = resolve_runtime_probe_reflective_hasattr_replay_target_callable(
        replay_target,
        source_module,
    )
    return materialize_runtime_probe_reflective_hasattr_worker_observation_from_target(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_reflective_getattr_worker_observation_from_target(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveGetattrTargetCallable,
) -> RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation:
    """Observe one zero-argument target under exact ``getattr`` interception."""
    _validate_runtime_probe_reflective_getattr_replay_target(replay_target)
    _validate_runtime_probe_reflective_getattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_getattr_target_callable(target)
    lookup_outcome = _runtime_probe_reflective_getattr_captured_lookup_outcome(
        source_module,
        target,
    )
    return materialize_runtime_probe_reflective_getattr_worker_observation(
        replay_target.request,
        lookup_outcome=lookup_outcome,
    )


def observe_runtime_probe_reflective_getattr_worker_request(
    request: RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation:
    """Observe one concrete exact-getattr worker request in local Python."""
    _validate_runtime_probe_reflective_getattr_worker_request(request)
    replay_target = materialize_runtime_probe_reflective_getattr_replay_target(request)
    source_module = import_runtime_probe_reflective_getattr_replay_target_source_module(
        replay_target
    )
    target = resolve_runtime_probe_reflective_getattr_replay_target_callable(
        replay_target,
        source_module,
    )
    return materialize_runtime_probe_reflective_getattr_worker_observation_from_target(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_reflective_getattr_default_worker_observation_from_target(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrDefaultReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveGetattrDefaultTargetCallable,
) -> RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation:
    """Observe one zero-argument target under exact ``getattr/3`` interception."""
    _validate_runtime_probe_reflective_getattr_default_replay_target(replay_target)
    _validate_runtime_probe_reflective_getattr_default_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_getattr_default_target_callable(target)
    lookup_outcome = _runtime_probe_reflective_getattr_default_captured_lookup_outcome(
        source_module,
        target,
    )
    return materialize_runtime_probe_reflective_getattr_default_worker_observation(
        replay_target.request,
        lookup_outcome=lookup_outcome,
    )


def observe_runtime_probe_reflective_getattr_default_worker_request(
    request: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation:
    """Observe one concrete exact-getattr/3 worker request in local Python."""
    _validate_runtime_probe_reflective_getattr_default_worker_request(request)
    replay_target = materialize_runtime_probe_reflective_getattr_default_replay_target(
        request
    )
    source_module = (
        import_runtime_probe_reflective_getattr_default_replay_target_source_module(
            replay_target
        )
    )
    target = resolve_runtime_probe_reflective_getattr_default_replay_target_callable(
        replay_target,
        source_module,
    )
    return (
        materialize_runtime_probe_reflective_getattr_default_worker_observation_from_target
    )(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_reflective_vars_worker_observation_from_target(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveVarsTargetCallable,
) -> RuntimeProbeLocalPythonReflectiveVarsWorkerObservation:
    """Observe one zero-argument target under exact ``vars`` interception."""
    _validate_runtime_probe_reflective_vars_replay_target(replay_target)
    _validate_runtime_probe_reflective_vars_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_vars_target_callable(target)
    lookup_outcome = _runtime_probe_reflective_vars_captured_lookup_outcome(
        source_module,
        target,
    )
    return materialize_runtime_probe_reflective_vars_worker_observation(
        replay_target.request,
        lookup_outcome=lookup_outcome,
    )


def observe_runtime_probe_reflective_vars_worker_request(
    request: RuntimeProbeLocalPythonReflectiveVarsWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveVarsWorkerObservation:
    """Observe one concrete exact-vars worker request in local Python."""
    _validate_runtime_probe_reflective_vars_worker_request(request)
    replay_target = materialize_runtime_probe_reflective_vars_replay_target(request)
    source_module = import_runtime_probe_reflective_vars_replay_target_source_module(
        replay_target
    )
    target = resolve_runtime_probe_reflective_vars_replay_target_callable(
        replay_target,
        source_module,
    )
    return materialize_runtime_probe_reflective_vars_worker_observation_from_target(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_reflective_vars_zero_worker_observation_from_target(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsZeroReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveVarsZeroTargetCallable,
) -> RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation:
    """Observe one zero-argument target under exact ``vars()`` interception."""
    _validate_runtime_probe_reflective_vars_zero_replay_target(replay_target)
    _validate_runtime_probe_reflective_vars_zero_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_vars_zero_target_callable(target)
    lookup_outcome = _runtime_probe_reflective_vars_zero_captured_lookup_outcome(
        source_module,
        target,
    )
    return materialize_runtime_probe_reflective_vars_zero_worker_observation(
        replay_target.request,
        lookup_outcome=lookup_outcome,
    )


def observe_runtime_probe_reflective_vars_zero_worker_request(
    request: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation:
    """Observe one concrete exact-vars/0 worker request in local Python."""
    _validate_runtime_probe_reflective_vars_zero_worker_request(request)
    replay_target = materialize_runtime_probe_reflective_vars_zero_replay_target(
        request
    )
    source_module = (
        import_runtime_probe_reflective_vars_zero_replay_target_source_module(
            replay_target
        )
    )
    target = resolve_runtime_probe_reflective_vars_zero_replay_target_callable(
        replay_target,
        source_module,
    )
    materialize_observation = (
        materialize_runtime_probe_reflective_vars_zero_worker_observation_from_target
    )
    return materialize_observation(
        replay_target,
        source_module,
        target,
    )


def import_runtime_probe_dynamic_import_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonDynamicImportReplayTarget,
) -> ModuleType:
    """Import a replay target source module under request-local import state."""
    _validate_runtime_probe_dynamic_import_replay_target(replay_target)
    request = replay_target.request
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    try:
        os.chdir(request.working_directory)
        sys.path[:] = [
            request.working_directory,
            *request.python_path_entries,
            *original_sys_path,
        ]
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            imported_module = importlib.import_module(replay_target.source_module_name)
    except Exception as error:
        raise ValueError(
            "runtime probe dynamic import source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_dynamic_import_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_reflective_hasattr_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveHasattrReplayTarget,
) -> ModuleType:
    """Import a replay target source module under request-local import state."""
    _validate_runtime_probe_reflective_hasattr_replay_target(replay_target)
    request = replay_target.request
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    try:
        os.chdir(request.working_directory)
        sys.path[:] = [
            request.working_directory,
            *request.python_path_entries,
            *original_sys_path,
        ]
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            imported_module = importlib.import_module(replay_target.source_module_name)
    except Exception as error:
        raise ValueError(
            "runtime probe reflective builtin hasattr source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_reflective_hasattr_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_reflective_getattr_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrReplayTarget,
) -> ModuleType:
    """Import a replay target source module under request-local import state."""
    _validate_runtime_probe_reflective_getattr_replay_target(replay_target)
    request = replay_target.request
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    try:
        os.chdir(request.working_directory)
        sys.path[:] = [
            request.working_directory,
            *request.python_path_entries,
            *original_sys_path,
        ]
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            imported_module = importlib.import_module(replay_target.source_module_name)
    except Exception as error:
        raise ValueError(
            "runtime probe reflective builtin getattr source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_reflective_getattr_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_reflective_getattr_default_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrDefaultReplayTarget,
) -> ModuleType:
    """Import a replay target source module under request-local import state."""
    _validate_runtime_probe_reflective_getattr_default_replay_target(replay_target)
    request = replay_target.request
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    try:
        os.chdir(request.working_directory)
        sys.path[:] = [
            request.working_directory,
            *request.python_path_entries,
            *original_sys_path,
        ]
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            imported_module = importlib.import_module(replay_target.source_module_name)
    except Exception as error:
        raise ValueError(
            "runtime probe reflective builtin getattr default source module import "
            "failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_reflective_getattr_default_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_reflective_vars_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsReplayTarget,
) -> ModuleType:
    """Import a replay target source module under request-local import state."""
    _validate_runtime_probe_reflective_vars_replay_target(replay_target)
    request = replay_target.request
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    try:
        os.chdir(request.working_directory)
        sys.path[:] = [
            request.working_directory,
            *request.python_path_entries,
            *original_sys_path,
        ]
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            imported_module = importlib.import_module(replay_target.source_module_name)
    except Exception as error:
        raise ValueError(
            "runtime probe reflective builtin vars source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_reflective_vars_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_reflective_vars_zero_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsZeroReplayTarget,
) -> ModuleType:
    """Import a vars/0 replay target source module under request-local state."""
    _validate_runtime_probe_reflective_vars_zero_replay_target(replay_target)
    request = replay_target.request
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    try:
        os.chdir(request.working_directory)
        sys.path[:] = [
            request.working_directory,
            *request.python_path_entries,
            *original_sys_path,
        ]
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            imported_module = importlib.import_module(replay_target.source_module_name)
    except Exception as error:
        raise ValueError(
            "runtime probe reflective builtin vars zero source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_reflective_vars_zero_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def resolve_runtime_probe_dynamic_import_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonDynamicImportReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonDynamicImportTargetCallable:
    """Resolve an injected source module replay target without executing it."""
    _validate_runtime_probe_dynamic_import_replay_target(replay_target)
    _validate_runtime_probe_dynamic_import_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe dynamic import replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_dynamic_import_target_callable(resolved_target)
    return cast(RuntimeProbeLocalPythonDynamicImportTargetCallable, resolved_target)


def resolve_runtime_probe_reflective_hasattr_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonReflectiveHasattrReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonReflectiveHasattrTargetCallable:
    """Resolve an injected source module replay target without executing it."""
    _validate_runtime_probe_reflective_hasattr_replay_target(replay_target)
    _validate_runtime_probe_reflective_hasattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe reflective builtin hasattr replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_reflective_hasattr_target_callable(resolved_target)
    return cast(RuntimeProbeLocalPythonReflectiveHasattrTargetCallable, resolved_target)


def resolve_runtime_probe_reflective_getattr_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonReflectiveGetattrTargetCallable:
    """Resolve an injected source module replay target without executing it."""
    _validate_runtime_probe_reflective_getattr_replay_target(replay_target)
    _validate_runtime_probe_reflective_getattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe reflective builtin getattr replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_reflective_getattr_target_callable(resolved_target)
    return cast(RuntimeProbeLocalPythonReflectiveGetattrTargetCallable, resolved_target)


def resolve_runtime_probe_reflective_getattr_default_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrDefaultReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonReflectiveGetattrDefaultTargetCallable:
    """Resolve an injected source module replay target without executing it."""
    _validate_runtime_probe_reflective_getattr_default_replay_target(replay_target)
    _validate_runtime_probe_reflective_getattr_default_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe reflective builtin getattr default replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_reflective_getattr_default_target_callable(resolved_target)
    return cast(
        RuntimeProbeLocalPythonReflectiveGetattrDefaultTargetCallable,
        resolved_target,
    )


def resolve_runtime_probe_reflective_vars_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonReflectiveVarsTargetCallable:
    """Resolve an injected source module replay target without executing it."""
    _validate_runtime_probe_reflective_vars_replay_target(replay_target)
    _validate_runtime_probe_reflective_vars_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe reflective builtin vars replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_reflective_vars_target_callable(resolved_target)
    return cast(RuntimeProbeLocalPythonReflectiveVarsTargetCallable, resolved_target)


def resolve_runtime_probe_reflective_vars_zero_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsZeroReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonReflectiveVarsZeroTargetCallable:
    """Resolve an injected source module vars/0 replay target without executing it."""
    _validate_runtime_probe_reflective_vars_zero_replay_target(replay_target)
    _validate_runtime_probe_reflective_vars_zero_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe reflective builtin vars zero replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_reflective_vars_zero_target_callable(resolved_target)
    return cast(
        RuntimeProbeLocalPythonReflectiveVarsZeroTargetCallable,
        resolved_target,
    )


def build_runtime_probe_dynamic_import_worker_handler_entry(
    observer: RuntimeProbeLocalPythonDynamicImportWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for the import-module worker form."""
    return _build_runtime_probe_dynamic_import_worker_handler_entry(
        observer=observer,
        form_label=_DYNAMIC_IMPORT_WORKER_FORM_LABEL,
    )


def _build_runtime_probe_dynamic_import_worker_handler_entry(
    *,
    observer: RuntimeProbeLocalPythonDynamicImportWorkerObserver,
    form_label: str,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for one exact dynamic-import form."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label=form_label,
        handler=RuntimeProbeLocalPythonDynamicImportWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_reflective_hasattr_worker_handler_entry(
    observer: RuntimeProbeLocalPythonReflectiveHasattrWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``hasattr(obj, name)``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_REFLECTIVE_BUILTIN_HASATTR_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonReflectiveHasattrWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_reflective_getattr_worker_handler_entry(
    observer: RuntimeProbeLocalPythonReflectiveGetattrWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``getattr(obj, name)``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_REFLECTIVE_BUILTIN_GETATTR_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonReflectiveGetattrWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_reflective_getattr_default_worker_handler_entry(
    observer: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``getattr(obj, name, default)``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_reflective_vars_worker_handler_entry(
    observer: RuntimeProbeLocalPythonReflectiveVarsWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``vars(obj)``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_REFLECTIVE_BUILTIN_VARS_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonReflectiveVarsWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_reflective_vars_zero_worker_handler_entry(
    observer: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``vars()``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonReflectiveVarsZeroWorkerHandlerAdapter(
            observer=observer
        ),
    )


def _runtime_probe_local_python_worker_handler_entries(
    handler_entries: (
        Iterable[RuntimeProbeLocalPythonWorkerHandlerEntry]
        | _RuntimeProbeWorkerDefaultHandlerEntries
    ),
) -> Iterable[RuntimeProbeLocalPythonWorkerHandlerEntry]:
    """Return explicit handler entries or the module-local default table."""
    if isinstance(handler_entries, _RuntimeProbeWorkerDefaultHandlerEntries):
        return _default_runtime_probe_local_python_worker_handler_entries()
    return handler_entries


def _default_runtime_probe_local_python_worker_handler_entries() -> tuple[
    RuntimeProbeLocalPythonWorkerHandlerEntry,
    ...,
]:
    """Return the default concrete local-Python worker handler entries."""
    dynamic_import_entries = tuple(
        _build_runtime_probe_dynamic_import_worker_handler_entry(
            observer=observe_runtime_probe_dynamic_import_worker_request,
            form_label=form_label,
        )
        for form_label in _DYNAMIC_IMPORT_WORKER_FORM_LABELS
    )
    reflective_hasattr_entries = (
        build_runtime_probe_reflective_hasattr_worker_handler_entry(
            observe_runtime_probe_reflective_hasattr_worker_request
        ),
    )
    reflective_getattr_entries = (
        build_runtime_probe_reflective_getattr_worker_handler_entry(
            observe_runtime_probe_reflective_getattr_worker_request
        ),
    )
    reflective_getattr_default_entries = (
        build_runtime_probe_reflective_getattr_default_worker_handler_entry(
            observe_runtime_probe_reflective_getattr_default_worker_request
        ),
    )
    reflective_vars_entries = (
        build_runtime_probe_reflective_vars_worker_handler_entry(
            observe_runtime_probe_reflective_vars_worker_request
        ),
    )
    reflective_vars_zero_entries = (
        build_runtime_probe_reflective_vars_zero_worker_handler_entry(
            observe_runtime_probe_reflective_vars_zero_worker_request
        ),
    )
    return (
        *dynamic_import_entries,
        *reflective_hasattr_entries,
        *reflective_getattr_entries,
        *reflective_getattr_default_entries,
        *reflective_vars_entries,
        *reflective_vars_zero_entries,
    )


def _validate_runtime_probe_reflective_hasattr_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local hasattr request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker payload must be typed"
        )
    _validate_runtime_probe_reflective_hasattr_payload_family_form(
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
    _validate_runtime_probe_reflective_hasattr_replay_metadata(
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
            "runtime probe reflective builtin hasattr worker invocation_identity "
            "must match payload replay identity"
        )


def _validate_runtime_probe_reflective_hasattr_worker_request(
    request: RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest,
) -> None:
    """Reject exact-hasattr worker requests whose copied metadata drifted."""
    if not isinstance(
        request,
        RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest,
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker request must be typed"
        )
    _validate_runtime_probe_reflective_hasattr_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker subject_kind is "
            "unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker reason_code is unsupported"
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
    _validate_runtime_probe_reflective_hasattr_worker_request_boundary_text(
        request.boundary_text
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
    _validate_runtime_probe_reflective_hasattr_replay_metadata(
        replay_fields_by_key,
        plan_id=request.plan_id,
        request_id=request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="subject_kind",
        expected_value=request.subject_kind.value,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="subject_id",
        expected_value=request.subject_id,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="source_site_id",
        expected_value=request.source_site_id,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="source_file_path",
        expected_value=request.source_file_path,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="source_start_line",
        expected_value=str(request.source_start_line),
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="source_start_column",
        expected_value=str(request.source_start_column),
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="source_end_line",
        expected_value=str(request.source_end_line),
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="source_end_column",
        expected_value=str(request.source_end_column),
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="reason_code",
        expected_value=request.reason_code.value,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
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
            "runtime probe reflective builtin hasattr worker invocation_identity "
            "must match request replay identity"
        )


def _validate_runtime_probe_reflective_hasattr_worker_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject exact-hasattr requests that do not carry the approved boundary."""
    if boundary_text != _REFLECTIVE_BUILTIN_HASATTR_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker boundary_text must be "
            f"{_REFLECTIVE_BUILTIN_HASATTR_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_reflective_hasattr_worker_observer(
    observer: RuntimeProbeLocalPythonReflectiveHasattrWorkerObserver,
) -> None:
    """Reject non-callable exact-hasattr observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker observer must be callable"
        )


def _validate_runtime_probe_reflective_hasattr_target_callable(
    target: object,
) -> None:
    """Reject non-callable target injections before hasattr interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker target must be callable"
        )


def _validate_runtime_probe_reflective_hasattr_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveHasattrReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe reflective builtin hasattr replay target source module "
            "must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe reflective builtin hasattr replay target source module "
            "must match source_module_name"
        )


def _runtime_probe_reflective_hasattr_captured_attribute_present(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveHasattrTargetCallable,
) -> bool:
    """Run a target while capturing one exact bare ``hasattr(obj, name)`` call."""
    _validate_runtime_probe_reflective_hasattr_source_global_absent(source_module)
    original_hasattr: Callable[[object, str], bool] = builtins.hasattr
    capture = _RuntimeProbeReflectiveHasattrCapture(original_hasattr=original_hasattr)
    controlled_hasattr: Callable[..., bool] = capture.hasattr
    target_failure: BaseException | None = None

    try:
        builtins.hasattr = controlled_hasattr
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            target()
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_reflective_hasattr_builtin(
        expected_hasattr=controlled_hasattr,
        original_hasattr=original_hasattr,
    )
    source_restore_failure = _restore_runtime_probe_reflective_hasattr_source_global(
        source_module
    )

    if builtin_restore_failure is not None:
        if target_failure is not None:
            raise builtin_restore_failure from target_failure
        raise builtin_restore_failure
    if source_restore_failure is not None:
        if target_failure is not None:
            raise source_restore_failure from target_failure
        raise source_restore_failure
    if target_failure is not None:
        _raise_runtime_probe_reflective_hasattr_target_failure(target_failure)

    return _runtime_probe_reflective_hasattr_capture_attribute_present(capture)


def _runtime_probe_reflective_hasattr_capture_attribute_present(
    capture: _RuntimeProbeReflectiveHasattrCapture,
) -> bool:
    """Return the single captured attribute-present result after validation."""
    _validate_runtime_probe_reflective_hasattr_intercepted_calls(
        captured_attribute_presence=capture.captured_attribute_presence,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_attribute_presence[0]


def _validate_runtime_probe_reflective_hasattr_intercepted_calls(
    *,
    captured_attribute_presence: list[bool],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted hasattr behavior outside the exact two-argument form."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker form must be exactly "
            "hasattr(obj, name)"
        )
    if "name" in captured_rejections:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker attribute name must be "
            "a string"
        )
    if len(captured_attribute_presence) != 1:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker target must capture "
            "exactly one hasattr call"
        )


def _raise_runtime_probe_reflective_hasattr_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _REFLECTIVE_BUILTIN_HASATTR_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _REFLECTIVE_BUILTIN_HASATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_reflective_hasattr_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``hasattr`` global resolution."""
    if (
        source_module.__dict__.get(
            _REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker target module "
            "hasattr global must be absent"
        )


def _restore_runtime_probe_reflective_hasattr_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``hasattr`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe reflective builtin hasattr worker target module hasattr "
            "global could not be restored"
        )
    if (
        module_globals.get(
            _REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe reflective builtin hasattr worker target module hasattr "
            "global could not be restored"
        )
    return ValueError(
        "runtime probe reflective builtin hasattr worker target module hasattr "
        "global changed during execution"
    )


def _restore_runtime_probe_reflective_hasattr_builtin(
    *,
    expected_hasattr: object,
    original_hasattr: Callable[[object, str], bool],
) -> ValueError | None:
    """Restore builtins.hasattr and report target-time hook drift."""
    current_hasattr = getattr(
        builtins,
        _REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_hasattr is not expected_hasattr:
        restore_failure = ValueError(
            "runtime probe reflective builtin hasattr worker builtins.hasattr "
            "changed during execution"
        )
    try:
        builtins.hasattr = original_hasattr
    except Exception:
        return ValueError(
            "runtime probe reflective builtin hasattr worker builtins.hasattr "
            "could not be restored"
        )
    if (
        getattr(
            builtins,
            _REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_hasattr
    ):
        return ValueError(
            "runtime probe reflective builtin hasattr worker builtins.hasattr "
            "could not be restored"
        )
    return restore_failure


def _validate_runtime_probe_reflective_hasattr_worker_observation_for_request(
    observation: RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation,
    request: RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted request."""
    _validate_runtime_probe_reflective_hasattr_worker_request(request)
    _validate_runtime_probe_reflective_hasattr_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker observation request "
            "must match adapted request"
        )


def _validate_runtime_probe_reflective_hasattr_worker_observation(
    observation: RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation,
) -> None:
    """Reject exact-hasattr observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonReflectiveHasattrWorkerObservation,
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker observation must be typed"
        )
    _validate_runtime_probe_reflective_hasattr_worker_request(observation.request)
    if not isinstance(observation.attribute_present, bool):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker attribute_present "
            "must be a bool"
        )
    _validate_runtime_probe_reflective_hasattr_observation_field_match(
        field_name="plan_id",
        value=observation.plan_id,
        expected_value=observation.request.plan_id,
    )
    _validate_runtime_probe_reflective_hasattr_observation_field_match(
        field_name="request_id",
        value=observation.request_id,
        expected_value=observation.request.request_id,
    )
    _validate_runtime_probe_reflective_hasattr_observation_field_match(
        field_name="replay_target_seed",
        value=observation.replay_target_seed,
        expected_value=observation.request.replay_target_seed,
    )
    _validate_runtime_probe_reflective_hasattr_observation_field_match(
        field_name="replay_selector_seed",
        value=observation.replay_selector_seed,
        expected_value=observation.request.replay_selector_seed,
    )
    _validate_runtime_probe_reflective_hasattr_observation_field_match(
        field_name="invocation_contract_revision",
        value=observation.invocation_contract_revision,
        expected_value=observation.request.invocation_contract_revision,
    )
    _validate_runtime_probe_reflective_hasattr_observation_field_match(
        field_name="invocation_identity",
        value=observation.invocation_identity,
        expected_value=observation.request.invocation_identity,
    )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_reflective_hasattr_replay_target(
    replay_target: RuntimeProbeLocalPythonReflectiveHasattrReplayTarget,
) -> None:
    """Reject non-executing replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonReflectiveHasattrReplayTarget,
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr replay target must be typed"
        )
    request = replay_target.request
    _validate_runtime_probe_reflective_hasattr_worker_request(request)
    _validate_runtime_probe_reflective_hasattr_replay_target_field_match(
        field_name="plan_id",
        value=replay_target.plan_id,
        expected_value=request.plan_id,
    )
    _validate_runtime_probe_reflective_hasattr_replay_target_field_match(
        field_name="request_id",
        value=replay_target.request_id,
        expected_value=request.request_id,
    )
    _validate_runtime_probe_reflective_hasattr_replay_target_field_match(
        field_name="source_file_path",
        value=replay_target.source_file_path,
        expected_value=request.source_file_path,
    )
    _validate_runtime_probe_reflective_hasattr_replay_target_field_match(
        field_name="replay_target_seed",
        value=replay_target.replay_target_seed,
        expected_value=request.replay_target_seed,
    )
    _validate_runtime_probe_reflective_hasattr_replay_target_field_match(
        field_name="replay_selector_seed",
        value=replay_target.replay_selector_seed,
        expected_value=request.replay_selector_seed,
    )
    _validate_runtime_probe_reflective_hasattr_replay_target_field_match(
        field_name="invocation_identity",
        value=replay_target.invocation_identity,
        expected_value=request.invocation_identity,
    )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe reflective builtin hasattr replay target "
            "source_module_name must match request source_file_path"
        )
    expected_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=expected_source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    if replay_target.replay_target_attribute_path != expected_attribute_path:
        raise ValueError(
            "runtime probe reflective builtin hasattr replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_reflective_hasattr_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin hasattr replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_hasattr_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_hasattr_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported reflective-builtin worker family/form labels."""
    if family_label is not RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker family_label is "
            "unsupported"
        )
    if form_label != _REFLECTIVE_BUILTIN_HASATTR_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker form_label is unsupported"
        )


def _validate_runtime_probe_reflective_hasattr_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-hasattr worker metadata."""
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="plan_id",
        expected_value=plan_id,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="request_id",
        expected_value=request_id,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="family_label",
        expected_value=family_label.value,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="form_label",
        expected_value=form_label,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="replay_target_seed",
        expected_value=replay_target_seed,
    )
    _validate_runtime_probe_reflective_hasattr_replay_field_match(
        replay_fields_by_key,
        field_key="replay_selector_seed",
        expected_value=replay_selector_seed,
    )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker subject_kind is "
            "unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN.value
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker reason_code is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_reflective_hasattr_reason_code_from_replay_field(
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
    _validate_runtime_probe_reflective_hasattr_worker_request_boundary_text(
        replay_fields_by_key["boundary_text"]
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


def _validate_runtime_probe_reflective_hasattr_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-hasattr request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_reflective_hasattr_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the reflective-builtin reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin hasattr worker reason_code is unsupported"
        )
    return reason_code


def _validate_runtime_probe_reflective_getattr_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local getattr request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe reflective builtin getattr worker payload must be typed"
        )
    _validate_runtime_probe_reflective_getattr_payload_family_form(
        family_label=payload.family_label,
        form_label=payload.form_label,
    )
    _validate_runtime_probe_worker_metadata_text(payload.plan_id, field_name="plan_id")
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
    _validate_runtime_probe_reflective_getattr_replay_metadata(
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
            "runtime probe reflective builtin getattr worker invocation_identity "
            "must match payload replay identity"
        )


def _validate_runtime_probe_reflective_getattr_worker_request(
    request: RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest,
) -> None:
    """Reject exact-getattr worker requests whose copied metadata drifted."""
    if not isinstance(
        request,
        RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker request must be typed"
        )
    _validate_runtime_probe_reflective_getattr_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe reflective builtin getattr worker subject_kind is "
            "unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin getattr worker reason_code is unsupported"
        )
    _validate_runtime_probe_worker_metadata_text(request.plan_id, field_name="plan_id")
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
    _validate_runtime_probe_reflective_getattr_worker_request_boundary_text(
        request.boundary_text
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
    _validate_runtime_probe_reflective_getattr_replay_metadata(
        replay_fields_by_key,
        plan_id=request.plan_id,
        request_id=request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
    )
    for field_key, expected_value in (
        ("subject_kind", request.subject_kind.value),
        ("subject_id", request.subject_id),
        ("source_site_id", request.source_site_id),
        ("source_file_path", request.source_file_path),
        ("source_start_line", str(request.source_start_line)),
        ("source_start_column", str(request.source_start_column)),
        ("source_end_line", str(request.source_end_line)),
        ("source_end_column", str(request.source_end_column)),
        ("reason_code", request.reason_code.value),
        ("boundary_text", request.boundary_text),
    ):
        _validate_runtime_probe_reflective_getattr_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
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
            "runtime probe reflective builtin getattr worker invocation_identity "
            "must match request replay identity"
        )


def _validate_runtime_probe_reflective_getattr_worker_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject exact-getattr requests that do not carry the approved boundary."""
    if boundary_text != _REFLECTIVE_BUILTIN_GETATTR_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe reflective builtin getattr worker boundary_text must be "
            f"{_REFLECTIVE_BUILTIN_GETATTR_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_reflective_getattr_worker_observer(
    observer: RuntimeProbeLocalPythonReflectiveGetattrWorkerObserver,
) -> None:
    """Reject non-callable exact-getattr observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe reflective builtin getattr worker observer must be callable"
        )


def _validate_runtime_probe_reflective_getattr_target_callable(
    target: object,
) -> None:
    """Reject non-callable target injections before getattr interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe reflective builtin getattr worker target must be callable"
        )


def _validate_runtime_probe_reflective_getattr_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe reflective builtin getattr replay target source module "
            "must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe reflective builtin getattr replay target source module "
            "must match source_module_name"
        )


def _runtime_probe_reflective_getattr_captured_lookup_outcome(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveGetattrTargetCallable,
) -> str:
    """Run a target while capturing one exact bare ``getattr(obj, name)`` call."""
    _validate_runtime_probe_reflective_getattr_source_global_absent(source_module)
    original_getattr: Callable[[object, str], object] = builtins.getattr
    capture = _RuntimeProbeReflectiveGetattrCapture(original_getattr=original_getattr)
    controlled_getattr: Callable[..., object] = capture.getattr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME] = (
            controlled_getattr
        )
        try:
            sys.stdout = shielded_stdout
            sys.stderr = shielded_stderr
            target()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_reflective_getattr_builtin(
        expected_getattr=controlled_getattr,
        original_getattr=original_getattr,
    )
    source_restore_failure = _restore_runtime_probe_reflective_getattr_source_global(
        source_module
    )

    if builtin_restore_failure is not None:
        if target_failure is not None:
            raise builtin_restore_failure from target_failure
        raise builtin_restore_failure
    if source_restore_failure is not None:
        if target_failure is not None:
            raise source_restore_failure from target_failure
        raise source_restore_failure
    if target_failure is not None:
        _raise_runtime_probe_reflective_getattr_target_failure(target_failure)

    return _runtime_probe_reflective_getattr_capture_lookup_outcome(capture)


def _runtime_probe_reflective_getattr_capture_lookup_outcome(
    capture: _RuntimeProbeReflectiveGetattrCapture,
) -> str:
    """Return the single captured lookup outcome after validation."""
    _validate_runtime_probe_reflective_getattr_intercepted_calls(
        captured_lookup_outcomes=capture.captured_lookup_outcomes,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_lookup_outcomes[0]


def _validate_runtime_probe_reflective_getattr_intercepted_calls(
    *,
    captured_lookup_outcomes: list[str],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted getattr behavior outside the exact two-argument form."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe reflective builtin getattr worker form must be exactly "
            "getattr(obj, name)"
        )
    if "name" in captured_rejections:
        raise ValueError(
            "runtime probe reflective builtin getattr worker attribute name must be "
            "a string"
        )
    if len(captured_lookup_outcomes) != 1:
        raise ValueError(
            "runtime probe reflective builtin getattr worker target must capture "
            "exactly one getattr call"
        )


def _raise_runtime_probe_reflective_getattr_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _REFLECTIVE_BUILTIN_GETATTR_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _REFLECTIVE_BUILTIN_GETATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_reflective_getattr_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``getattr`` global resolution."""
    if (
        source_module.__dict__.get(
            _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker target module "
            "getattr global must be absent"
        )


def _restore_runtime_probe_reflective_getattr_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``getattr`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe reflective builtin getattr worker target module getattr "
            "global could not be restored"
        )
    if (
        module_globals.get(
            _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe reflective builtin getattr worker target module getattr "
            "global could not be restored"
        )
    return ValueError(
        "runtime probe reflective builtin getattr worker target module getattr "
        "global changed during execution"
    )


def _restore_runtime_probe_reflective_getattr_builtin(
    *,
    expected_getattr: object,
    original_getattr: Callable[[object, str], object],
) -> ValueError | None:
    """Restore builtins.getattr and report target-time hook drift."""
    current_getattr = builtins.__dict__.get(
        _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_getattr is not expected_getattr:
        restore_failure = ValueError(
            "runtime probe reflective builtin getattr worker builtins.getattr "
            "changed during execution"
        )
    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME] = (
            original_getattr
        )
    except Exception:
        return ValueError(
            "runtime probe reflective builtin getattr worker builtins.getattr "
            "could not be restored"
        )
    if (
        builtins.__dict__.get(
            _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_getattr
    ):
        return ValueError(
            "runtime probe reflective builtin getattr worker builtins.getattr "
            "could not be restored"
        )
    return restore_failure


def _runtime_probe_reflective_getattr_default_captured_lookup_outcome(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveGetattrDefaultTargetCallable,
) -> str:
    """Run a target while capturing one exact ``getattr(obj, name, default)``."""
    _validate_runtime_probe_reflective_getattr_default_source_global_absent(
        source_module
    )
    original_getattr: Callable[..., object] = builtins.getattr
    capture = _RuntimeProbeReflectiveGetattrDefaultCapture(
        original_getattr=original_getattr
    )
    controlled_getattr: Callable[..., object] = capture.getattr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME] = (
            controlled_getattr
        )
        try:
            sys.stdout = shielded_stdout
            sys.stderr = shielded_stderr
            target()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_reflective_getattr_default_builtin(
        expected_getattr=controlled_getattr,
        original_getattr=original_getattr,
    )
    source_restore_failure = (
        _restore_runtime_probe_reflective_getattr_default_source_global(source_module)
    )

    if builtin_restore_failure is not None:
        if target_failure is not None:
            raise builtin_restore_failure from target_failure
        raise builtin_restore_failure
    if source_restore_failure is not None:
        if target_failure is not None:
            raise source_restore_failure from target_failure
        raise source_restore_failure
    if target_failure is not None:
        _raise_runtime_probe_reflective_getattr_default_target_failure(target_failure)

    return _runtime_probe_reflective_getattr_default_capture_lookup_outcome(capture)


def _runtime_probe_reflective_getattr_default_capture_lookup_outcome(
    capture: _RuntimeProbeReflectiveGetattrDefaultCapture,
) -> str:
    """Return the single captured lookup outcome after validation."""
    _validate_runtime_probe_reflective_getattr_default_intercepted_calls(
        captured_lookup_outcomes=capture.captured_lookup_outcomes,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_lookup_outcomes[0]


def _validate_runtime_probe_reflective_getattr_default_intercepted_calls(
    *,
    captured_lookup_outcomes: list[str],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted getattr behavior outside the exact three-argument form."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker form must be "
            "exactly getattr(obj, name, default)"
        )
    if "name" in captured_rejections:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker attribute name "
            "must be a string"
        )
    if len(captured_lookup_outcomes) != 1:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker target must "
            "capture exactly one getattr call"
        )


def _raise_runtime_probe_reflective_getattr_default_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error)
        in _REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_reflective_getattr_default_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``getattr`` global resolution."""
    if (
        source_module.__dict__.get(
            _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker target module "
            "getattr global must be absent"
        )


def _restore_runtime_probe_reflective_getattr_default_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``getattr`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe reflective builtin getattr default worker target module "
            "getattr global could not be restored"
        )
    if (
        module_globals.get(
            _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe reflective builtin getattr default worker target module "
            "getattr global could not be restored"
        )
    return ValueError(
        "runtime probe reflective builtin getattr default worker target module "
        "getattr global changed during execution"
    )


def _restore_runtime_probe_reflective_getattr_default_builtin(
    *,
    expected_getattr: object,
    original_getattr: Callable[..., object],
) -> ValueError | None:
    """Restore builtins.getattr and report target-time hook drift."""
    current_getattr = builtins.__dict__.get(
        _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_getattr is not expected_getattr:
        restore_failure = ValueError(
            "runtime probe reflective builtin getattr default worker builtins.getattr "
            "changed during execution"
        )
    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME] = (
            original_getattr
        )
    except Exception:
        return ValueError(
            "runtime probe reflective builtin getattr default worker builtins.getattr "
            "could not be restored"
        )
    if (
        builtins.__dict__.get(
            _REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_getattr
    ):
        return ValueError(
            "runtime probe reflective builtin getattr default worker builtins.getattr "
            "could not be restored"
        )
    return restore_failure


def _runtime_probe_reflective_vars_captured_lookup_outcome(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveVarsTargetCallable,
) -> str:
    """Run a target while capturing one exact ``vars(obj)`` call."""
    _validate_runtime_probe_reflective_vars_source_global_absent(source_module)
    original_vars: Callable[[object], object] = builtins.vars
    capture = _RuntimeProbeReflectiveVarsCapture(original_vars=original_vars)
    controlled_vars: Callable[..., object] = capture.vars
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME] = controlled_vars
        try:
            sys.stdout = shielded_stdout
            sys.stderr = shielded_stderr
            target()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_reflective_vars_builtin(
        expected_vars=controlled_vars,
        original_vars=original_vars,
    )
    source_restore_failure = _restore_runtime_probe_reflective_vars_source_global(
        source_module
    )

    if builtin_restore_failure is not None:
        if target_failure is not None:
            raise builtin_restore_failure from target_failure
        raise builtin_restore_failure
    if source_restore_failure is not None:
        if target_failure is not None:
            raise source_restore_failure from target_failure
        raise source_restore_failure
    if target_failure is not None:
        _raise_runtime_probe_reflective_vars_target_failure(target_failure)

    return _runtime_probe_reflective_vars_capture_lookup_outcome(capture)


def _runtime_probe_reflective_vars_capture_lookup_outcome(
    capture: _RuntimeProbeReflectiveVarsCapture,
) -> str:
    """Return the single captured vars lookup outcome after validation."""
    _validate_runtime_probe_reflective_vars_intercepted_calls(
        captured_lookup_outcomes=capture.captured_lookup_outcomes,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_lookup_outcomes[0]


def _validate_runtime_probe_reflective_vars_intercepted_calls(
    *,
    captured_lookup_outcomes: list[str],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted vars behavior outside the exact one-argument form."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe reflective builtin vars worker form must be exactly "
            "vars(obj)"
        )
    if len(captured_lookup_outcomes) != 1:
        raise ValueError(
            "runtime probe reflective builtin vars worker target must capture "
            "exactly one vars call"
        )


def _raise_runtime_probe_reflective_vars_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _REFLECTIVE_BUILTIN_VARS_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _REFLECTIVE_BUILTIN_VARS_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_reflective_vars_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``vars`` global resolution."""
    if (
        source_module.__dict__.get(
            _REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe reflective builtin vars worker target module vars global "
            "must be absent"
        )


def _restore_runtime_probe_reflective_vars_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``vars`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe reflective builtin vars worker target module vars global "
            "could not be restored"
        )
    if (
        module_globals.get(
            _REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe reflective builtin vars worker target module vars global "
            "could not be restored"
        )
    return ValueError(
        "runtime probe reflective builtin vars worker target module vars global "
        "changed during execution"
    )


def _restore_runtime_probe_reflective_vars_builtin(
    *,
    expected_vars: object,
    original_vars: Callable[[object], object],
) -> ValueError | None:
    """Restore builtins.vars and report target-time hook drift."""
    current_vars = builtins.__dict__.get(
        _REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_vars is not expected_vars:
        restore_failure = ValueError(
            "runtime probe reflective builtin vars worker builtins.vars changed "
            "during execution"
        )
    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME] = original_vars
    except Exception:
        return ValueError(
            "runtime probe reflective builtin vars worker builtins.vars could not "
            "be restored"
        )
    if (
        builtins.__dict__.get(
            _REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_vars
    ):
        return ValueError(
            "runtime probe reflective builtin vars worker builtins.vars could not "
            "be restored"
        )
    return restore_failure


def _runtime_probe_reflective_vars_zero_captured_lookup_outcome(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveVarsZeroTargetCallable,
) -> str:
    """Run a target while capturing one exact ``vars()`` call."""
    _validate_runtime_probe_reflective_vars_source_global_absent(source_module)
    original_vars: Callable[..., object] = builtins.vars
    capture = _RuntimeProbeReflectiveVarsZeroCapture()
    controlled_vars: Callable[..., object] = capture.vars
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME] = controlled_vars
        try:
            sys.stdout = shielded_stdout
            sys.stderr = shielded_stderr
            target()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_reflective_vars_zero_builtin(
        expected_vars=controlled_vars,
        original_vars=original_vars,
    )
    source_restore_failure = _restore_runtime_probe_reflective_vars_source_global(
        source_module
    )

    if builtin_restore_failure is not None:
        if target_failure is not None:
            raise builtin_restore_failure from target_failure
        raise builtin_restore_failure
    if source_restore_failure is not None:
        if target_failure is not None:
            raise source_restore_failure from target_failure
        raise source_restore_failure
    if target_failure is not None:
        _raise_runtime_probe_reflective_vars_zero_target_failure(target_failure)

    return _runtime_probe_reflective_vars_zero_capture_lookup_outcome(capture)


def _runtime_probe_reflective_vars_zero_capture_lookup_outcome(
    capture: _RuntimeProbeReflectiveVarsZeroCapture,
) -> str:
    """Return the single captured vars/0 lookup outcome after validation."""
    _validate_runtime_probe_reflective_vars_zero_intercepted_calls(
        captured_lookup_outcomes=capture.captured_lookup_outcomes,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_lookup_outcomes[0]


def _validate_runtime_probe_reflective_vars_zero_intercepted_calls(
    *,
    captured_lookup_outcomes: list[str],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted vars behavior outside the exact zero-argument form."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker form must be exactly "
            "vars()"
        )
    if len(captured_lookup_outcomes) != 1:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker target must capture "
            "exactly one vars call"
        )


def _raise_runtime_probe_reflective_vars_zero_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _restore_runtime_probe_reflective_vars_zero_builtin(
    *,
    expected_vars: object,
    original_vars: Callable[..., object],
) -> ValueError | None:
    """Restore builtins.vars and report target-time hook drift."""
    current_vars = builtins.__dict__.get(
        _REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_vars is not expected_vars:
        restore_failure = ValueError(
            "runtime probe reflective builtin vars zero worker builtins.vars changed "
            "during execution"
        )
    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME] = original_vars
    except Exception:
        return ValueError(
            "runtime probe reflective builtin vars zero worker builtins.vars could "
            "not be restored"
        )
    if (
        builtins.__dict__.get(
            _REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_vars
    ):
        return ValueError(
            "runtime probe reflective builtin vars zero worker builtins.vars could "
            "not be restored"
        )
    return restore_failure


def _validate_runtime_probe_reflective_getattr_worker_observation_for_request(
    observation: RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation,
    request: RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted request."""
    _validate_runtime_probe_reflective_getattr_worker_request(request)
    _validate_runtime_probe_reflective_getattr_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe reflective builtin getattr worker observation request "
            "must match adapted request"
        )


def _validate_runtime_probe_reflective_getattr_worker_observation(
    observation: RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation,
) -> None:
    """Reject exact-getattr observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonReflectiveGetattrWorkerObservation,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker observation must be typed"
        )
    _validate_runtime_probe_reflective_getattr_worker_request(observation.request)
    if observation.lookup_outcome not in (
        _REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_VALUE,
        _REFLECTIVE_BUILTIN_GETATTR_WORKER_RAISED_ATTRIBUTE_ERROR,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker lookup_outcome "
            "is unsupported"
        )
    for field_name, value, expected_value in (
        ("plan_id", observation.plan_id, observation.request.plan_id),
        ("request_id", observation.request_id, observation.request.request_id),
        (
            "replay_target_seed",
            observation.replay_target_seed,
            observation.request.replay_target_seed,
        ),
        (
            "replay_selector_seed",
            observation.replay_selector_seed,
            observation.request.replay_selector_seed,
        ),
        (
            "invocation_contract_revision",
            observation.invocation_contract_revision,
            observation.request.invocation_contract_revision,
        ),
        (
            "invocation_identity",
            observation.invocation_identity,
            observation.request.invocation_identity,
        ),
    ):
        _validate_runtime_probe_reflective_getattr_observation_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_reflective_getattr_replay_target(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrReplayTarget,
) -> None:
    """Reject non-executing replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonReflectiveGetattrReplayTarget,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr replay target must be typed"
        )
    request = replay_target.request
    _validate_runtime_probe_reflective_getattr_worker_request(request)
    for field_name, value, expected_value in (
        ("plan_id", replay_target.plan_id, request.plan_id),
        ("request_id", replay_target.request_id, request.request_id),
        ("source_file_path", replay_target.source_file_path, request.source_file_path),
        (
            "replay_target_seed",
            replay_target.replay_target_seed,
            request.replay_target_seed,
        ),
        (
            "replay_selector_seed",
            replay_target.replay_selector_seed,
            request.replay_selector_seed,
        ),
        (
            "invocation_identity",
            replay_target.invocation_identity,
            request.invocation_identity,
        ),
    ):
        _validate_runtime_probe_reflective_getattr_replay_target_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe reflective builtin getattr replay target "
            "source_module_name must match request source_file_path"
        )
    expected_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=expected_source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    if replay_target.replay_target_attribute_path != expected_attribute_path:
        raise ValueError(
            "runtime probe reflective builtin getattr replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_reflective_getattr_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin getattr replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_getattr_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin getattr worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_getattr_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported reflective-builtin worker family/form labels."""
    if family_label is not RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin getattr worker family_label is "
            "unsupported"
        )
    if form_label != _REFLECTIVE_BUILTIN_GETATTR_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe reflective builtin getattr worker form_label is unsupported"
        )


def _validate_runtime_probe_reflective_getattr_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-getattr worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_reflective_getattr_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker subject_kind is "
            "unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN.value
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker reason_code is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_reflective_getattr_reason_code_from_replay_field(
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
    _validate_runtime_probe_reflective_getattr_worker_request_boundary_text(
        replay_fields_by_key["boundary_text"]
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


def _validate_runtime_probe_reflective_getattr_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-getattr request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe reflective builtin getattr worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_reflective_getattr_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the reflective-builtin reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe reflective builtin getattr worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin getattr worker reason_code is unsupported"
        )
    return reason_code


def _validate_runtime_probe_reflective_getattr_default_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local getattr/3 request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker payload must be "
            "typed"
        )
    _validate_runtime_probe_reflective_getattr_default_payload_family_form(
        family_label=payload.family_label,
        form_label=payload.form_label,
    )
    _validate_runtime_probe_worker_metadata_text(payload.plan_id, field_name="plan_id")
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
    _validate_runtime_probe_reflective_getattr_default_replay_metadata(
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
            "runtime probe reflective builtin getattr default worker "
            "invocation_identity must match payload replay identity"
        )


def _validate_runtime_probe_reflective_getattr_default_worker_request(
    request: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest,
) -> None:
    """Reject exact-getattr/3 worker requests whose copied metadata drifted."""
    if not isinstance(
        request,
        RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker request must be "
            "typed"
        )
    _validate_runtime_probe_reflective_getattr_default_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker subject_kind "
            "is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker reason_code "
            "is unsupported"
        )
    _validate_runtime_probe_worker_metadata_text(request.plan_id, field_name="plan_id")
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
    _validate_runtime_probe_reflective_getattr_default_worker_request_boundary_text(
        request.boundary_text
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
    _validate_runtime_probe_reflective_getattr_default_replay_metadata(
        replay_fields_by_key,
        plan_id=request.plan_id,
        request_id=request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
    )
    for field_key, expected_value in (
        ("subject_kind", request.subject_kind.value),
        ("subject_id", request.subject_id),
        ("source_site_id", request.source_site_id),
        ("source_file_path", request.source_file_path),
        ("source_start_line", str(request.source_start_line)),
        ("source_start_column", str(request.source_start_column)),
        ("source_end_line", str(request.source_end_line)),
        ("source_end_column", str(request.source_end_column)),
        ("reason_code", request.reason_code.value),
        ("boundary_text", request.boundary_text),
    ):
        _validate_runtime_probe_reflective_getattr_default_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
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
            "runtime probe reflective builtin getattr default worker "
            "invocation_identity must match request replay identity"
        )


def _validate_runtime_probe_reflective_getattr_default_worker_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject exact-getattr/3 requests that do not carry the approved boundary."""
    if boundary_text != _REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker boundary_text "
            "must be "
            f"{_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_reflective_getattr_default_worker_observer(
    observer: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObserver,
) -> None:
    """Reject non-callable exact-getattr/3 observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker observer must "
            "be callable"
        )


def _validate_runtime_probe_reflective_getattr_default_target_callable(
    target: object,
) -> None:
    """Reject non-callable target injections before getattr/3 interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker target must be "
            "callable"
        )


def _validate_runtime_probe_reflective_getattr_default_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrDefaultReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe reflective builtin getattr default replay target source "
            "module must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe reflective builtin getattr default replay target source "
            "module must match source_module_name"
        )


def _validate_runtime_probe_reflective_getattr_default_worker_observation_for_request(
    observation: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation,
    request: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted request."""
    _validate_runtime_probe_reflective_getattr_default_worker_request(request)
    _validate_runtime_probe_reflective_getattr_default_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker observation "
            "request must match adapted request"
        )


def _validate_runtime_probe_reflective_getattr_default_worker_observation(
    observation: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation,
) -> None:
    """Reject exact-getattr/3 observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerObservation,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker observation "
            "must be typed"
        )
    _validate_runtime_probe_reflective_getattr_default_worker_request(
        observation.request
    )
    if observation.lookup_outcome not in (
        _REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_VALUE,
        _REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_DEFAULT_VALUE,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker lookup_outcome "
            "is unsupported"
        )
    for field_name, value, expected_value in (
        ("plan_id", observation.plan_id, observation.request.plan_id),
        ("request_id", observation.request_id, observation.request.request_id),
        (
            "replay_target_seed",
            observation.replay_target_seed,
            observation.request.replay_target_seed,
        ),
        (
            "replay_selector_seed",
            observation.replay_selector_seed,
            observation.request.replay_selector_seed,
        ),
        (
            "invocation_contract_revision",
            observation.invocation_contract_revision,
            observation.request.invocation_contract_revision,
        ),
        (
            "invocation_identity",
            observation.invocation_identity,
            observation.request.invocation_identity,
        ),
    ):
        _validate_runtime_probe_reflective_getattr_default_observation_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_reflective_getattr_default_replay_target(
    replay_target: RuntimeProbeLocalPythonReflectiveGetattrDefaultReplayTarget,
) -> None:
    """Reject non-executing replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonReflectiveGetattrDefaultReplayTarget,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default replay target must be "
            "typed"
        )
    request = replay_target.request
    _validate_runtime_probe_reflective_getattr_default_worker_request(request)
    for field_name, value, expected_value in (
        ("plan_id", replay_target.plan_id, request.plan_id),
        ("request_id", replay_target.request_id, request.request_id),
        ("source_file_path", replay_target.source_file_path, request.source_file_path),
        (
            "replay_target_seed",
            replay_target.replay_target_seed,
            request.replay_target_seed,
        ),
        (
            "replay_selector_seed",
            replay_target.replay_selector_seed,
            request.replay_selector_seed,
        ),
        (
            "invocation_identity",
            replay_target.invocation_identity,
            request.invocation_identity,
        ),
    ):
        _validate_runtime_probe_reflective_getattr_default_replay_target_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe reflective builtin getattr default replay target "
            "source_module_name must match request source_file_path"
        )
    expected_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=expected_source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    if replay_target.replay_target_attribute_path != expected_attribute_path:
        raise ValueError(
            "runtime probe reflective builtin getattr default replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_reflective_getattr_default_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin getattr default replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_getattr_default_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_getattr_default_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported reflective-builtin getattr/3 family/form labels."""
    if family_label is not RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker family_label "
            "is unsupported"
        )
    if form_label != _REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker form_label "
            "is unsupported"
        )


def _validate_runtime_probe_reflective_getattr_default_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-getattr/3 worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_reflective_getattr_default_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker subject_kind "
            "is unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN.value
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker reason_code "
            "is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_reflective_getattr_default_reason_code_from_replay_field(
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
    _validate_runtime_probe_reflective_getattr_default_worker_request_boundary_text(
        replay_fields_by_key["boundary_text"]
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


def _validate_runtime_probe_reflective_getattr_default_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-getattr/3 request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_reflective_getattr_default_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the reflective-builtin reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker reason_code "
            "is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker reason_code "
            "is unsupported"
        )
    return reason_code


def _validate_runtime_probe_reflective_vars_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local vars request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe reflective builtin vars worker payload must be typed"
        )
    _validate_runtime_probe_reflective_vars_payload_family_form(
        family_label=payload.family_label,
        form_label=payload.form_label,
    )
    _validate_runtime_probe_worker_metadata_text(payload.plan_id, field_name="plan_id")
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
    _validate_runtime_probe_reflective_vars_replay_metadata(
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
            "runtime probe reflective builtin vars worker invocation_identity must "
            "match payload replay identity"
        )


def _validate_runtime_probe_reflective_vars_worker_request(
    request: RuntimeProbeLocalPythonReflectiveVarsWorkerRequest,
) -> None:
    """Reject exact-vars worker requests whose copied metadata drifted."""
    if not isinstance(request, RuntimeProbeLocalPythonReflectiveVarsWorkerRequest):
        raise ValueError(
            "runtime probe reflective builtin vars worker request must be typed"
        )
    _validate_runtime_probe_reflective_vars_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe reflective builtin vars worker subject_kind is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin vars worker reason_code is unsupported"
        )
    _validate_runtime_probe_worker_metadata_text(request.plan_id, field_name="plan_id")
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
    _validate_runtime_probe_reflective_vars_worker_request_boundary_text(
        request.boundary_text
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
    _validate_runtime_probe_reflective_vars_replay_metadata(
        replay_fields_by_key,
        plan_id=request.plan_id,
        request_id=request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
    )
    for field_key, expected_value in (
        ("subject_kind", request.subject_kind.value),
        ("subject_id", request.subject_id),
        ("source_site_id", request.source_site_id),
        ("source_file_path", request.source_file_path),
        ("source_start_line", str(request.source_start_line)),
        ("source_start_column", str(request.source_start_column)),
        ("source_end_line", str(request.source_end_line)),
        ("source_end_column", str(request.source_end_column)),
        ("reason_code", request.reason_code.value),
        ("boundary_text", request.boundary_text),
    ):
        _validate_runtime_probe_reflective_vars_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
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
            "runtime probe reflective builtin vars worker invocation_identity must "
            "match request replay identity"
        )


def _validate_runtime_probe_reflective_vars_worker_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject exact-vars requests that do not carry the approved boundary."""
    if boundary_text != _REFLECTIVE_BUILTIN_VARS_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe reflective builtin vars worker boundary_text must be "
            f"{_REFLECTIVE_BUILTIN_VARS_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_reflective_vars_worker_observer(
    observer: RuntimeProbeLocalPythonReflectiveVarsWorkerObserver,
) -> None:
    """Reject non-callable exact-vars observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe reflective builtin vars worker observer must be callable"
        )


def _validate_runtime_probe_reflective_vars_target_callable(target: object) -> None:
    """Reject non-callable target injections before vars interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe reflective builtin vars worker target must be callable"
        )


def _validate_runtime_probe_reflective_vars_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe reflective builtin vars replay target source module must "
            "be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe reflective builtin vars replay target source module must "
            "match source_module_name"
        )


def _validate_runtime_probe_reflective_vars_worker_observation_for_request(
    observation: RuntimeProbeLocalPythonReflectiveVarsWorkerObservation,
    request: RuntimeProbeLocalPythonReflectiveVarsWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted request."""
    _validate_runtime_probe_reflective_vars_worker_request(request)
    _validate_runtime_probe_reflective_vars_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe reflective builtin vars worker observation request must "
            "match adapted request"
        )


def _validate_runtime_probe_reflective_vars_worker_observation(
    observation: RuntimeProbeLocalPythonReflectiveVarsWorkerObservation,
) -> None:
    """Reject exact-vars observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonReflectiveVarsWorkerObservation,
    ):
        raise ValueError(
            "runtime probe reflective builtin vars worker observation must be typed"
        )
    _validate_runtime_probe_reflective_vars_worker_request(observation.request)
    if observation.lookup_outcome not in (
        _REFLECTIVE_BUILTIN_VARS_WORKER_RETURNED_NAMESPACE,
        _REFLECTIVE_BUILTIN_VARS_WORKER_RAISED_TYPE_ERROR,
    ):
        raise ValueError(
            "runtime probe reflective builtin vars worker lookup_outcome is unsupported"
        )
    for field_name, value, expected_value in (
        ("plan_id", observation.plan_id, observation.request.plan_id),
        ("request_id", observation.request_id, observation.request.request_id),
        (
            "replay_target_seed",
            observation.replay_target_seed,
            observation.request.replay_target_seed,
        ),
        (
            "replay_selector_seed",
            observation.replay_selector_seed,
            observation.request.replay_selector_seed,
        ),
        (
            "invocation_contract_revision",
            observation.invocation_contract_revision,
            observation.request.invocation_contract_revision,
        ),
        (
            "invocation_identity",
            observation.invocation_identity,
            observation.request.invocation_identity,
        ),
    ):
        _validate_runtime_probe_reflective_vars_observation_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin vars worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_reflective_vars_replay_target(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsReplayTarget,
) -> None:
    """Reject non-executing replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonReflectiveVarsReplayTarget,
    ):
        raise ValueError(
            "runtime probe reflective builtin vars replay target must be typed"
        )
    request = replay_target.request
    _validate_runtime_probe_reflective_vars_worker_request(request)
    for field_name, value, expected_value in (
        ("plan_id", replay_target.plan_id, request.plan_id),
        ("request_id", replay_target.request_id, request.request_id),
        ("source_file_path", replay_target.source_file_path, request.source_file_path),
        (
            "replay_target_seed",
            replay_target.replay_target_seed,
            request.replay_target_seed,
        ),
        (
            "replay_selector_seed",
            replay_target.replay_selector_seed,
            request.replay_selector_seed,
        ),
        (
            "invocation_identity",
            replay_target.invocation_identity,
            request.invocation_identity,
        ),
    ):
        _validate_runtime_probe_reflective_vars_replay_target_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin vars replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe reflective builtin vars replay target "
            "source_module_name must match request source_file_path"
        )
    expected_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=expected_source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    if replay_target.replay_target_attribute_path != expected_attribute_path:
        raise ValueError(
            "runtime probe reflective builtin vars replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_reflective_vars_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin vars replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_vars_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin vars worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_vars_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported reflective-builtin vars family/form labels."""
    if family_label is not RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin vars worker family_label is unsupported"
        )
    if form_label != _REFLECTIVE_BUILTIN_VARS_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe reflective builtin vars worker form_label is unsupported"
        )


def _validate_runtime_probe_reflective_vars_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-vars worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_reflective_vars_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe reflective builtin vars worker subject_kind is unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN.value
    ):
        raise ValueError(
            "runtime probe reflective builtin vars worker reason_code is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_reflective_vars_reason_code_from_replay_field(
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
    _validate_runtime_probe_reflective_vars_worker_request_boundary_text(
        replay_fields_by_key["boundary_text"]
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


def _validate_runtime_probe_reflective_vars_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-vars request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe reflective builtin vars worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_reflective_vars_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the reflective-builtin reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe reflective builtin vars worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin vars worker reason_code is unsupported"
        )
    return reason_code


def _validate_runtime_probe_reflective_vars_zero_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local vars/0 request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe reflective builtin vars zero worker payload must be typed"
        )
    _validate_runtime_probe_reflective_vars_zero_payload_family_form(
        family_label=payload.family_label,
        form_label=payload.form_label,
    )
    _validate_runtime_probe_worker_metadata_text(payload.plan_id, field_name="plan_id")
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
    _validate_runtime_probe_reflective_vars_zero_replay_metadata(
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
            "runtime probe reflective builtin vars zero worker invocation_identity "
            "must match payload replay identity"
        )


def _validate_runtime_probe_reflective_vars_zero_worker_request(
    request: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest,
) -> None:
    """Reject exact-vars/0 worker requests whose copied metadata drifted."""
    if not isinstance(request, RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest):
        raise ValueError(
            "runtime probe reflective builtin vars zero worker request must be typed"
        )
    _validate_runtime_probe_reflective_vars_zero_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker subject_kind "
            "is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker reason_code "
            "is unsupported"
        )
    _validate_runtime_probe_worker_metadata_text(request.plan_id, field_name="plan_id")
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
    _validate_runtime_probe_reflective_vars_zero_worker_request_boundary_text(
        request.boundary_text
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
    _validate_runtime_probe_reflective_vars_zero_replay_metadata(
        replay_fields_by_key,
        plan_id=request.plan_id,
        request_id=request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
    )
    for field_key, expected_value in (
        ("subject_kind", request.subject_kind.value),
        ("subject_id", request.subject_id),
        ("source_site_id", request.source_site_id),
        ("source_file_path", request.source_file_path),
        ("source_start_line", str(request.source_start_line)),
        ("source_start_column", str(request.source_start_column)),
        ("source_end_line", str(request.source_end_line)),
        ("source_end_column", str(request.source_end_column)),
        ("reason_code", request.reason_code.value),
        ("boundary_text", request.boundary_text),
    ):
        _validate_runtime_probe_reflective_vars_zero_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
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
            "runtime probe reflective builtin vars zero worker invocation_identity "
            "must match request replay identity"
        )


def _validate_runtime_probe_reflective_vars_zero_worker_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject exact-vars/0 requests that do not carry the approved boundary."""
    if boundary_text != _REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker boundary_text must be "
            f"{_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_reflective_vars_zero_worker_observer(
    observer: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObserver,
) -> None:
    """Reject non-callable exact-vars/0 observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe reflective builtin vars zero worker observer must "
            "be callable"
        )


def _validate_runtime_probe_reflective_vars_zero_target_callable(
    target: object,
) -> None:
    """Reject non-callable target injections before vars/0 interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe reflective builtin vars zero worker target must be callable"
        )


def _validate_runtime_probe_reflective_vars_zero_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsZeroReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the vars/0 replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe reflective builtin vars zero replay target source module "
            "must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe reflective builtin vars zero replay target source module "
            "must match source_module_name"
        )


def _validate_runtime_probe_reflective_vars_zero_worker_observation_for_request(
    observation: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation,
    request: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted vars/0 request."""
    _validate_runtime_probe_reflective_vars_zero_worker_request(request)
    _validate_runtime_probe_reflective_vars_zero_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker observation request "
            "must match adapted request"
        )


def _validate_runtime_probe_reflective_vars_zero_worker_observation(
    observation: RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation,
) -> None:
    """Reject exact-vars/0 observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonReflectiveVarsZeroWorkerObservation,
    ):
        raise ValueError(
            "runtime probe reflective builtin vars zero worker observation must "
            "be typed"
        )
    _validate_runtime_probe_reflective_vars_zero_worker_request(observation.request)
    if observation.lookup_outcome != _REFLECTIVE_BUILTIN_VARS_WORKER_RETURNED_NAMESPACE:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker lookup_outcome "
            "is unsupported"
        )
    for field_name, value, expected_value in (
        ("plan_id", observation.plan_id, observation.request.plan_id),
        ("request_id", observation.request_id, observation.request.request_id),
        (
            "replay_target_seed",
            observation.replay_target_seed,
            observation.request.replay_target_seed,
        ),
        (
            "replay_selector_seed",
            observation.replay_selector_seed,
            observation.request.replay_selector_seed,
        ),
        (
            "invocation_contract_revision",
            observation.invocation_contract_revision,
            observation.request.invocation_contract_revision,
        ),
        (
            "invocation_identity",
            observation.invocation_identity,
            observation.request.invocation_identity,
        ),
    ):
        _validate_runtime_probe_reflective_vars_zero_observation_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin vars zero worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_reflective_vars_zero_replay_target(
    replay_target: RuntimeProbeLocalPythonReflectiveVarsZeroReplayTarget,
) -> None:
    """Reject non-executing vars/0 replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonReflectiveVarsZeroReplayTarget,
    ):
        raise ValueError(
            "runtime probe reflective builtin vars zero replay target must be typed"
        )
    request = replay_target.request
    _validate_runtime_probe_reflective_vars_zero_worker_request(request)
    for field_name, value, expected_value in (
        ("plan_id", replay_target.plan_id, request.plan_id),
        ("request_id", replay_target.request_id, request.request_id),
        ("source_file_path", replay_target.source_file_path, request.source_file_path),
        (
            "replay_target_seed",
            replay_target.replay_target_seed,
            request.replay_target_seed,
        ),
        (
            "replay_selector_seed",
            replay_target.replay_selector_seed,
            request.replay_selector_seed,
        ),
        (
            "invocation_identity",
            replay_target.invocation_identity,
            request.invocation_identity,
        ),
    ):
        _validate_runtime_probe_reflective_vars_zero_replay_target_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin vars zero replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe reflective builtin vars zero replay target "
            "source_module_name must match request source_file_path"
        )
    expected_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=expected_source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    if replay_target.replay_target_attribute_path != expected_attribute_path:
        raise ValueError(
            "runtime probe reflective builtin vars zero replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_reflective_vars_zero_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied vars/0 replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin vars zero replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_vars_zero_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied vars/0 observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_vars_zero_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported reflective-builtin vars/0 family/form labels."""
    if family_label is not RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker family_label "
            "is unsupported"
        )
    if form_label != _REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker form_label "
            "is unsupported"
        )


def _validate_runtime_probe_reflective_vars_zero_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-vars/0 worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_reflective_vars_zero_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe reflective builtin vars zero worker subject_kind "
            "is unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN.value
    ):
        raise ValueError(
            "runtime probe reflective builtin vars zero worker reason_code "
            "is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_reflective_vars_zero_reason_code_from_replay_field(
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
    _validate_runtime_probe_reflective_vars_zero_worker_request_boundary_text(
        replay_fields_by_key["boundary_text"]
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


def _validate_runtime_probe_reflective_vars_zero_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-vars/0 request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_reflective_vars_zero_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the reflective-builtin reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker reason_code "
            "is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin vars zero worker reason_code "
            "is unsupported"
        )
    return reason_code


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
    _validate_runtime_probe_dynamic_import_worker_request_boundary_text(
        form_label=request.form_label,
        boundary_text=request.boundary_text,
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


def _validate_runtime_probe_dynamic_import_worker_request_boundary_text(
    *,
    form_label: str,
    boundary_text: str,
) -> None:
    """Reject supported __import__ requests that do not carry the exact shape."""
    expected_builtin_import_boundary_texts = {
        _DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL: "__import__(name)",
        _DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL: (
            "builtins.__import__(name)"
        ),
        _DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL: (
            "loader.__import__(name)"
        ),
    }
    expected_boundary_text = expected_builtin_import_boundary_texts.get(form_label)
    if expected_boundary_text is not None and boundary_text != expected_boundary_text:
        raise ValueError(
            "runtime probe dynamic import worker boundary_text must be "
            f"{expected_boundary_text}"
        )


def _validate_runtime_probe_dynamic_import_worker_observer(
    observer: RuntimeProbeLocalPythonDynamicImportWorkerObserver,
) -> None:
    """Reject non-callable dynamic-import observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe dynamic import worker observer must be callable"
        )


def _validate_runtime_probe_dynamic_import_target_callable(
    target: object,
) -> None:
    """Reject non-callable target injections before import interception."""
    if not callable(target):
        raise ValueError("runtime probe dynamic import worker target must be callable")


def _runtime_probe_dynamic_import_target_execution_guard(
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
) -> RuntimeProbeLocalPythonDynamicImportTargetCallable:
    """Wrap concrete target execution with deterministic worker-local failures."""

    def guarded_target() -> object:
        try:
            return target()
        except ValueError as error:
            if str(error) in _DYNAMIC_IMPORT_WORKER_IMPORT_SHAPE_ERROR_MESSAGES:
                raise
            raise ValueError(
                _DYNAMIC_IMPORT_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
            ) from error
        except Exception as error:
            raise ValueError(
                _DYNAMIC_IMPORT_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
            ) from error

    return guarded_target


def _validate_runtime_probe_dynamic_import_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonDynamicImportReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe dynamic import replay target source module must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe dynamic import replay target source module "
            "must match source_module_name"
        )


def _runtime_probe_dynamic_import_observation_source_request(
    observation_source: RuntimeProbeLocalPythonDynamicImportObservationSource,
) -> RuntimeProbeLocalPythonDynamicImportWorkerRequest:
    """Return the request carried by a validated request or replay target."""
    if isinstance(
        observation_source,
        RuntimeProbeLocalPythonDynamicImportWorkerRequest,
    ):
        _validate_runtime_probe_dynamic_import_worker_request(observation_source)
        return observation_source
    if isinstance(
        observation_source,
        RuntimeProbeLocalPythonDynamicImportReplayTarget,
    ):
        _validate_runtime_probe_dynamic_import_replay_target(observation_source)
        return observation_source.request
    raise ValueError(
        "runtime probe dynamic import worker observation source must be a "
        "request or replay target"
    )


def _runtime_probe_dynamic_import_captured_import_module_name(
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
) -> str:
    """Run a target while capturing one importlib.import_module module name."""
    capture = _RuntimeProbeDynamicImportCapture()
    original_import_module = importlib.import_module

    try:
        importlib.import_module = capture.import_module
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            target()
    finally:
        importlib.import_module = original_import_module

    return _runtime_probe_dynamic_import_capture_imported_module(capture)


def _materialize_runtime_probe_dynamic_import_builtin_observation(
    *,
    replay_target: RuntimeProbeLocalPythonDynamicImportReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
) -> RuntimeProbeLocalPythonDynamicImportWorkerObservation:
    """Observe a target by controlling the process builtins.__import__ hook."""
    _validate_runtime_probe_dynamic_import_replay_target(replay_target)
    _validate_runtime_probe_dynamic_import_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_dynamic_import_target_callable(target)
    _validate_runtime_probe_dynamic_import_source_builtin_import_global_absent(
        source_module
    )
    imported_module = _runtime_probe_dynamic_import_captured_builtin_import_name(target)
    return materialize_runtime_probe_dynamic_import_worker_observation(
        replay_target.request,
        imported_module=imported_module,
    )


def _materialize_runtime_probe_dynamic_import_builtins_observation(
    *,
    replay_target: RuntimeProbeLocalPythonDynamicImportReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
    global_name: str,
) -> RuntimeProbeLocalPythonDynamicImportWorkerObservation:
    """Observe a target through its exact source-global builtins module."""
    _validate_runtime_probe_dynamic_import_replay_target(replay_target)
    _validate_runtime_probe_dynamic_import_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_dynamic_import_target_callable(target)
    imported_module = _runtime_probe_dynamic_import_captured_builtins_import_name(
        source_module,
        target,
        global_name=global_name,
    )
    return materialize_runtime_probe_dynamic_import_worker_observation(
        replay_target.request,
        imported_module=imported_module,
    )


def _runtime_probe_dynamic_import_captured_builtin_import_name(
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
) -> str:
    """Run a target while capturing one exact bare __import__(name) call."""
    capture = _RuntimeProbeDynamicImportCapture()
    original_builtin_import: Callable[..., ModuleType] = builtins.__import__
    controlled_builtin_import: Callable[..., ModuleType] = capture.builtin_import
    target_failure: BaseException | None = None
    restore_failure: ValueError | None

    try:
        builtins.__import__ = controlled_builtin_import
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            target()
    except BaseException as error:
        target_failure = error
    restore_failure = _restore_runtime_probe_dynamic_import_builtin_import(
        expected_import=controlled_builtin_import,
        original_import=original_builtin_import,
    )
    sys_modules_restore_failure = capture.restore_sys_modules()

    if restore_failure is not None:
        if target_failure is not None:
            raise restore_failure from target_failure
        raise restore_failure
    if sys_modules_restore_failure is not None:
        if target_failure is not None:
            raise sys_modules_restore_failure from target_failure
        raise sys_modules_restore_failure
    if target_failure is not None:
        raise target_failure

    return _runtime_probe_dynamic_import_capture_imported_module(capture)


def _runtime_probe_dynamic_import_captured_builtins_import_name(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
    *,
    global_name: str,
) -> str:
    """Run a target while requiring an exact source-global builtins binding."""
    original_global = _runtime_probe_dynamic_import_source_builtins_global(
        source_module,
        global_name=global_name,
    )
    target_failure: BaseException | None = None
    imported_module = ""

    try:
        imported_module = _runtime_probe_dynamic_import_captured_builtin_import_name(
            target
        )
    except BaseException as error:
        target_failure = error

    restore_failure = _restore_runtime_probe_dynamic_import_source_builtins_global(
        source_module=source_module,
        global_name=global_name,
        expected_global=original_global,
        original_global=original_global,
    )

    if restore_failure is not None:
        if target_failure is not None:
            raise restore_failure from target_failure
        raise restore_failure
    if target_failure is not None:
        raise target_failure

    return imported_module


def _validate_runtime_probe_dynamic_import_source_builtin_import_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare __import__ global resolution."""
    if (
        source_module.__dict__.get(
            "__import__",
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe dynamic import worker target module __import__ "
            "global must be absent"
        )


def _runtime_probe_dynamic_import_source_builtins_global(
    source_module: ModuleType,
    *,
    global_name: str,
) -> ModuleType:
    """Return the exact source-module builtins global after strict validation."""
    builtins_global = source_module.__dict__.get(
        global_name,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if builtins_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        raise ValueError(
            f"runtime probe dynamic import worker target module {global_name} global "
            "is missing"
        )
    if builtins_global is not builtins:
        raise ValueError(
            f"runtime probe dynamic import worker target module {global_name} global "
            "must be the builtins module"
        )
    return builtins_global


def _restore_runtime_probe_dynamic_import_source_builtins_global(
    *,
    source_module: ModuleType,
    global_name: str,
    expected_global: object,
    original_global: ModuleType,
) -> ValueError | None:
    """Restore the source builtins global and report unsafe target-time drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        global_name,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_global is not expected_global:
        restore_failure = ValueError(
            f"runtime probe dynamic import worker target module {global_name} global "
            "changed during execution"
        )
    try:
        module_globals[global_name] = original_global
    except Exception:
        return ValueError(
            f"runtime probe dynamic import worker target module {global_name} global "
            "could not be restored"
        )
    if (
        module_globals.get(global_name, _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL)
        is not original_global
    ):
        return ValueError(
            f"runtime probe dynamic import worker target module {global_name} global "
            "could not be restored"
        )
    return restore_failure


def _restore_runtime_probe_dynamic_import_builtin_import(
    *,
    expected_import: object,
    original_import: Callable[..., ModuleType],
) -> ValueError | None:
    """Restore builtins.__import__ and report target-time hook drift."""
    current_import = builtins.__import__
    restore_failure: ValueError | None = None
    if current_import is not expected_import:
        restore_failure = ValueError(
            "runtime probe dynamic import worker builtins.__import__ changed "
            "during execution"
        )
    try:
        builtins.__import__ = original_import
    except Exception:
        return ValueError(
            "runtime probe dynamic import worker builtins.__import__ could not "
            "be restored"
        )
    if builtins.__import__ is not original_import:
        return ValueError(
            "runtime probe dynamic import worker builtins.__import__ could not "
            "be restored"
        )
    return restore_failure


def _materialize_runtime_probe_dynamic_import_worker_observation_from_global(
    *,
    replay_target: RuntimeProbeLocalPythonDynamicImportReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
    global_name: str,
) -> RuntimeProbeLocalPythonDynamicImportWorkerObservation:
    """Observe a target by rebinding its exact import_module/load_module global."""
    _validate_runtime_probe_dynamic_import_replay_target(replay_target)
    _validate_runtime_probe_dynamic_import_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_dynamic_import_target_callable(target)
    imported_module = _runtime_probe_dynamic_import_captured_import_module_global_name(
        source_module,
        target,
        global_name=global_name,
    )
    return materialize_runtime_probe_dynamic_import_worker_observation(
        replay_target.request,
        imported_module=imported_module,
    )


def _runtime_probe_dynamic_import_captured_import_module_global_name(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
    *,
    global_name: str,
) -> str:
    """Run a target while capturing one exact import_module/load_module global."""
    original_import_module = _runtime_probe_dynamic_import_source_import_module_global(
        source_module,
        global_name=global_name,
    )
    capture = _RuntimeProbeDynamicImportCapture()
    controlled_import_module = capture.import_module
    module_globals = source_module.__dict__
    target_failure: BaseException | None = None
    restore_failure: ValueError | None

    try:
        module_globals[global_name] = controlled_import_module
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            target()
    except BaseException as error:
        target_failure = error
    restore_failure = _restore_runtime_probe_dynamic_import_source_import_module_global(
        source_module=source_module,
        global_name=global_name,
        expected_global=controlled_import_module,
        original_global=original_import_module,
    )

    if restore_failure is not None:
        if target_failure is not None:
            raise restore_failure from target_failure
        raise restore_failure
    if target_failure is not None:
        raise target_failure

    return _runtime_probe_dynamic_import_capture_imported_module(capture)


def _runtime_probe_dynamic_import_source_global_name_for_form(form_label: str) -> str:
    """Return the exact source-module global controlled for one supported form."""
    try:
        return _DYNAMIC_IMPORT_WORKER_SOURCE_GLOBAL_NAMES_BY_FORM_LABEL[form_label]
    except KeyError as error:
        raise ValueError(
            "runtime probe dynamic import worker source global form is unsupported"
        ) from error


def _runtime_probe_dynamic_import_source_builtins_global_name_for_form(
    form_label: str,
) -> str:
    """Return the exact source-module builtins global for one supported form."""
    try:
        return _DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAMES_BY_FORM_LABEL[form_label]
    except KeyError as error:
        raise ValueError(
            "runtime probe dynamic import worker source builtins global form is "
            "unsupported"
        ) from error


def _runtime_probe_dynamic_import_source_import_module_global(
    source_module: ModuleType,
    *,
    global_name: str,
) -> object:
    """Return the exact import_module/load_module global after strict validation."""
    import_module_global = source_module.__dict__.get(
        global_name,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if import_module_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        raise ValueError(
            f"runtime probe dynamic import worker target module {global_name} "
            "global is missing"
        )
    if import_module_global is not importlib.import_module:
        raise ValueError(
            f"runtime probe dynamic import worker target module {global_name} "
            "global must be importlib.import_module"
        )
    return import_module_global


def _restore_runtime_probe_dynamic_import_source_import_module_global(
    *,
    source_module: ModuleType,
    global_name: str,
    expected_global: object,
    original_global: object,
) -> ValueError | None:
    """Restore the exact import_module/load_module global and report unsafe drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        global_name,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_global is not expected_global:
        restore_failure = ValueError(
            f"runtime probe dynamic import worker target module {global_name} "
            "global changed during execution"
        )
    try:
        module_globals[global_name] = original_global
    except Exception:
        return ValueError(
            f"runtime probe dynamic import worker target module {global_name} "
            "global could not be restored"
        )
    if (
        module_globals.get(
            global_name,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_global
    ):
        return ValueError(
            f"runtime probe dynamic import worker target module {global_name} "
            "global could not be restored"
        )
    return restore_failure


def _runtime_probe_dynamic_import_capture_imported_module(
    capture: _RuntimeProbeDynamicImportCapture,
) -> str:
    """Return the single captured module name after shape validation."""
    _validate_runtime_probe_dynamic_import_intercepted_calls(
        captured_modules=capture.captured_modules,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_modules[0]


def _validate_runtime_probe_dynamic_import_intercepted_calls(
    *,
    captured_modules: list[str],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted import behavior outside the single absolute-call form."""
    if "package" in captured_rejections:
        raise ValueError(
            "runtime probe dynamic import worker package imports are unsupported"
        )
    if "relative" in captured_rejections:
        raise ValueError(
            "runtime probe dynamic import worker relative imports are unsupported"
        )
    if "malformed" in captured_rejections:
        raise ValueError("runtime probe dynamic import worker module name is malformed")
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe dynamic import worker __import__ form must be exactly "
            "__import__(name)"
        )
    if "import_context" in captured_rejections:
        raise ValueError(
            "runtime probe dynamic import worker __import__ globals locals and "
            "fromlist arguments are unsupported"
        )
    if "keyword" in captured_rejections:
        raise ValueError(
            "runtime probe dynamic import worker __import__ keyword arguments are "
            "unsupported"
        )
    if len(captured_modules) != 1:
        raise ValueError(
            "runtime probe dynamic import worker target must capture exactly one "
            "absolute import"
        )


def _validate_runtime_probe_dynamic_import_worker_observation_for_request(
    observation: RuntimeProbeLocalPythonDynamicImportWorkerObservation,
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted request."""
    _validate_runtime_probe_dynamic_import_worker_request(request)
    _validate_runtime_probe_dynamic_import_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe dynamic import worker observation request must match "
            "adapted request"
        )


def _validate_runtime_probe_dynamic_import_worker_observation(
    observation: RuntimeProbeLocalPythonDynamicImportWorkerObservation,
) -> None:
    """Reject dynamic-import observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonDynamicImportWorkerObservation,
    ):
        raise ValueError(
            "runtime probe dynamic import worker observation must be typed"
        )
    _validate_runtime_probe_dynamic_import_worker_request(observation.request)
    _validate_runtime_probe_dynamic_import_imported_module(observation.imported_module)
    _validate_runtime_probe_dynamic_import_observation_field_match(
        field_name="plan_id",
        value=observation.plan_id,
        expected_value=observation.request.plan_id,
    )
    _validate_runtime_probe_dynamic_import_observation_field_match(
        field_name="request_id",
        value=observation.request_id,
        expected_value=observation.request.request_id,
    )
    _validate_runtime_probe_dynamic_import_observation_field_match(
        field_name="replay_target_seed",
        value=observation.replay_target_seed,
        expected_value=observation.request.replay_target_seed,
    )
    _validate_runtime_probe_dynamic_import_observation_field_match(
        field_name="replay_selector_seed",
        value=observation.replay_selector_seed,
        expected_value=observation.request.replay_selector_seed,
    )
    _validate_runtime_probe_dynamic_import_observation_field_match(
        field_name="invocation_contract_revision",
        value=observation.invocation_contract_revision,
        expected_value=observation.request.invocation_contract_revision,
    )
    _validate_runtime_probe_dynamic_import_observation_field_match(
        field_name="invocation_identity",
        value=observation.invocation_identity,
        expected_value=observation.request.invocation_identity,
    )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe dynamic import worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_dynamic_import_replay_target(
    replay_target: RuntimeProbeLocalPythonDynamicImportReplayTarget,
) -> None:
    """Reject non-executing replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonDynamicImportReplayTarget,
    ):
        raise ValueError("runtime probe dynamic import replay target must be typed")
    request = replay_target.request
    _validate_runtime_probe_dynamic_import_worker_request(request)
    _validate_runtime_probe_dynamic_import_replay_target_field_match(
        field_name="plan_id",
        value=replay_target.plan_id,
        expected_value=request.plan_id,
    )
    _validate_runtime_probe_dynamic_import_replay_target_field_match(
        field_name="request_id",
        value=replay_target.request_id,
        expected_value=request.request_id,
    )
    _validate_runtime_probe_dynamic_import_replay_target_field_match(
        field_name="source_file_path",
        value=replay_target.source_file_path,
        expected_value=request.source_file_path,
    )
    _validate_runtime_probe_dynamic_import_replay_target_field_match(
        field_name="replay_target_seed",
        value=replay_target.replay_target_seed,
        expected_value=request.replay_target_seed,
    )
    _validate_runtime_probe_dynamic_import_replay_target_field_match(
        field_name="replay_selector_seed",
        value=replay_target.replay_selector_seed,
        expected_value=request.replay_selector_seed,
    )
    _validate_runtime_probe_dynamic_import_replay_target_field_match(
        field_name="invocation_identity",
        value=replay_target.invocation_identity,
        expected_value=request.invocation_identity,
    )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe dynamic import replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe dynamic import replay target "
            "source_module_name must match request source_file_path"
        )
    expected_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=expected_source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    if replay_target.replay_target_attribute_path != expected_attribute_path:
        raise ValueError(
            "runtime probe dynamic import replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_dynamic_import_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe dynamic import replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_dynamic_import_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe dynamic import worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_dynamic_import_imported_module(
    imported_module: str,
) -> None:
    """Reject malformed observed dynamic-import module names."""
    if not isinstance(imported_module, str) or not imported_module.strip():
        raise ValueError(
            "runtime probe dynamic import worker imported_module must be non-empty"
        )
    if imported_module != imported_module.strip() or _contains_control_character(
        imported_module
    ):
        raise ValueError(
            "runtime probe dynamic import worker imported_module is malformed"
        )
    if imported_module.startswith("."):
        raise ValueError(
            "runtime probe dynamic import worker imported_module must be absolute"
        )
    module_segments = imported_module.split(".")
    if any(not module_segment for module_segment in module_segments):
        raise ValueError(
            "runtime probe dynamic import worker imported_module "
            "must not contain empty segments"
        )
    if any(not module_segment.isidentifier() for module_segment in module_segments):
        raise ValueError(
            "runtime probe dynamic import worker imported_module "
            "must be a dotted identifier"
        )


def _runtime_probe_dynamic_import_source_module_name_from_path(
    source_file_path: str,
) -> str:
    """Return the strict dotted source module name for a repository Python file."""
    _validate_runtime_probe_worker_metadata_text(
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
    _validate_runtime_probe_worker_metadata_text(
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


def _validate_runtime_probe_dynamic_import_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported dynamic-import worker request family/form labels."""
    if family_label is not RuntimeProbeFamily.DYNAMIC_IMPORT:
        raise ValueError(
            "runtime probe dynamic import worker family_label is unsupported"
        )
    if form_label not in _DYNAMIC_IMPORT_WORKER_FORM_LABELS:
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

"""Fail-closed local Python runtime probe worker ingress."""

from __future__ import annotations

import ast
import builtins
import contextlib
import hashlib
import importlib
import inspect
import io
import os
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from types import ModuleType
from typing import NoReturn, TextIO, TypeAlias, cast

from context_ir import runtime_probe_worker_dispatch as _worker_dispatch
from context_ir import (
    runtime_probe_worker_dynamic_import_contracts as _dynamic_import_contracts,
)
from context_ir import (
    runtime_probe_worker_exec_or_eval_contracts as _exec_or_eval_contracts,
)
from context_ir import (
    runtime_probe_worker_metaclass_contracts as _metaclass_contracts,
)
from context_ir import runtime_probe_worker_metadata_protocol as _metadata_protocol
from context_ir import (
    runtime_probe_worker_reflective_builtin_contracts as _rbc,
)
from context_ir import (
    runtime_probe_worker_replay_target_protocol as _replay_target,
)
from context_ir import (
    runtime_probe_worker_response_protocol as _response_protocol,
)
from context_ir import (
    runtime_probe_worker_runtime_mutation_contracts as _rmc,
)
from context_ir.runtime_probe_execution import (
    _EXACT_REPLAY_DELATTR_LITERAL_CONTRACT,
    _EXACT_REPLAY_DELATTR_NAME_CONTRACT,
    _EXACT_REPLAY_DIR_INT_DIRECTORY_CONTRACT,
    _EXACT_REPLAY_GETATTR_ATTRIBUTE_ERROR_CONTRACT,
    _EXACT_REPLAY_GETATTR_DEFAULT_MISSING_CONTRACT,
    _EXACT_REPLAY_GETATTR_DEFAULT_VALUE_CONTRACT,
    _EXACT_REPLAY_GETATTR_LITERAL_CONTRACT,
    _EXACT_REPLAY_GETATTR_NAME_CONTRACT,
    _EXACT_REPLAY_HASATTR_FALSE_CONTRACT,
    _EXACT_REPLAY_HASATTR_LITERAL_CONTRACT,
    _EXACT_REPLAY_HASATTR_NAME_CONTRACT,
    _EXACT_REPLAY_SETATTR_LITERAL_CONTRACT,
    _EXACT_REPLAY_SETATTR_NAME_CONTRACT,
    _EXACT_REPLAY_VARS_RETURNED_NAMESPACE_CONTRACT,
    _EXACT_REPLAY_VARS_TYPE_ERROR_CONTRACT,
    RuntimeProbeLocalPythonWorkerRequestPayload,
    _runtime_probe_exact_replay_contract_candidates_for_replay_fields,
    _runtime_probe_exact_replay_contract_for_replay_fields,
    _runtime_probe_exact_replay_payload_field_keys,
    _runtime_probe_exact_replay_payload_fields_by_key,
    _RuntimeProbeExactReplayContract,
    parse_runtime_probe_local_python_worker_request_payload,
)
from context_ir.runtime_probe_requests import RuntimeProbeFamily
from context_ir.runtime_probe_results import RuntimeProbeReplayField
from context_ir.semantic_types import SemanticSubjectKind, UnresolvedReasonCode

_MALFORMED_REQUEST_EXIT_CODE = 64
_REJECTED_REQUEST_EXIT_CODE = 78
_SUCCESS_EXIT_CODE = 0
_RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION = (
    _response_protocol._RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION
)
_RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION_KEY = (
    _response_protocol._RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION_KEY
)
_MALFORMED_REQUEST_MESSAGE = _worker_dispatch._MALFORMED_REQUEST_MESSAGE
_REJECTED_REQUEST_MESSAGE = _worker_dispatch._REJECTED_REQUEST_MESSAGE
_DUPLICATE_HANDLER_MESSAGE = "runtime_probe_worker: rejected duplicate worker handler\n"
_MALFORMED_HANDLER_MESSAGE = "runtime_probe_worker: rejected malformed worker handler\n"
_HANDLER_EXCEPTION_MESSAGE = _worker_dispatch._HANDLER_EXCEPTION_MESSAGE
_INVALID_RESPONSE_MESSAGE = _worker_dispatch._INVALID_RESPONSE_MESSAGE
_DYNAMIC_IMPORT_WORKER_FORM_LABEL = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_FORM_LABEL
)
_DYNAMIC_IMPORT_WORKER_LOADER_FORM_LABEL = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_LOADER_FORM_LABEL
)
_DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL
)
_DYNAMIC_IMPORT_WORKER_LOAD_MODULE_FORM_LABEL = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_LOAD_MODULE_FORM_LABEL
)
_DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL
)
_DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL
)
_DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL
)
_DYNAMIC_IMPORT_WORKER_FORM_LABELS = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_FORM_LABELS
)
_DYNAMIC_IMPORT_WORKER_IMPORT_MODULE_GLOBAL_NAME = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_IMPORT_MODULE_GLOBAL_NAME
)
_DYNAMIC_IMPORT_WORKER_LOAD_MODULE_GLOBAL_NAME = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_LOAD_MODULE_GLOBAL_NAME
)
_DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAME = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAME
)
_DYNAMIC_IMPORT_WORKER_LOADER_GLOBAL_NAME = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_LOADER_GLOBAL_NAME
)
_DynamicImportWorkerRenderCardContract = (
    _dynamic_import_contracts._DynamicImportWorkerRenderCardContract
)
_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH
)
_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET
)
_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE
)
_DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS
)
_DYNAMIC_IMPORT_WORKER_SOURCE_GLOBAL_NAMES_BY_FORM_LABEL = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_SOURCE_GLOBAL_NAMES_BY_FORM_LABEL
)
_DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAMES_BY_FORM_LABEL = (
    _dynamic_import_contracts._DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAMES_BY_FORM_LABEL
)
_DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL = object()
_DYNAMIC_IMPORT_WORKER_MISSING_MODULE = object()
_DYNAMIC_IMPORT_WORKER_INVOCATION_IDENTITY_PREFIX = (
    _metadata_protocol._DYNAMIC_IMPORT_WORKER_INVOCATION_IDENTITY_PREFIX
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
_runtime_probe_dynamic_import_source_module_name_from_path = (
    _replay_target._runtime_probe_dynamic_import_source_module_name_from_path
)
_runtime_probe_dynamic_import_replay_target_attribute_path = (
    _replay_target._runtime_probe_dynamic_import_replay_target_attribute_path
)
_validate_runtime_probe_dynamic_import_dotted_identifier_segments = (
    _replay_target._validate_runtime_probe_dynamic_import_dotted_identifier_segments
)
_REFLECTIVE_BUILTIN_HASATTR_WORKER_FORM_LABEL = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_WORKER_FORM_LABEL
)
_REFLECTIVE_BUILTIN_HASATTR_WORKER_BOUNDARY_TEXT = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_WORKER_BOUNDARY_TEXT
)
_REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT
)
_REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME
)
_REFLECTIVE_BUILTIN_HASATTR_OBJECT_TYPE_REPLAY_KEY = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_OBJECT_TYPE_REPLAY_KEY
)
_REFLECTIVE_BUILTIN_HASATTR_ATTRIBUTE_NAME_REPLAY_KEY = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_ATTRIBUTE_NAME_REPLAY_KEY
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SUBJECT_ID = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SUBJECT_ID
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_FILE_PATH = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_FILE_PATH
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_START_LINE = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_START_LINE
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_START_COLUMN = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_START_COLUMN
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_END_LINE = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_END_LINE
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_END_COLUMN = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_END_COLUMN
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_REPLAY_TARGET_SEED = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_REPLAY_TARGET_SEED
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_REPLAY_SELECTOR_SEED = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_REPLAY_SELECTOR_SEED
)
_REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_SOURCE_END_COLUMN = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_SOURCE_END_COLUMN
)
_REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_REPLAY_TARGET_SEED = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_REPLAY_TARGET_SEED
)
_REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_REPLAY_SELECTOR_SEED = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_REPLAY_SELECTOR_SEED
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_OBJECT_TYPE = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_OBJECT_TYPE
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_ATTRIBUTE_NAME = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_ATTRIBUTE_NAME
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_FORM_LABEL = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_WORKER_FORM_LABEL
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_BOUNDARY_TEXT = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_WORKER_BOUNDARY_TEXT
)
_REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT
)
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_FORM_LABEL = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_FORM_LABEL
)
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_BOUNDARY_TEXT = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_BOUNDARY_TEXT
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_VALUE = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_VALUE
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_RAISED_ATTRIBUTE_ERROR = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_WORKER_RAISED_ATTRIBUTE_ERROR
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_DEFAULT_VALUE = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_DEFAULT_VALUE
)
_REFLECTIVE_BUILTIN_GETATTR_OBJECT_TYPE_REPLAY_KEY = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_OBJECT_TYPE_REPLAY_KEY
)
_REFLECTIVE_BUILTIN_GETATTR_ATTRIBUTE_NAME_REPLAY_KEY = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_ATTRIBUTE_NAME_REPLAY_KEY
)
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SUBJECT_ID = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SUBJECT_ID
)
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_FILE_PATH = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_FILE_PATH
)
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_START_LINE = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_START_LINE
)
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_START_COLUMN = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_START_COLUMN
)
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_END_LINE = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_END_LINE
)
_REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_SOURCE_END_COLUMN = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_SOURCE_END_COLUMN
)
_REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_REPLAY_TARGET_SEED = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_REPLAY_TARGET_SEED
)
_REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_REPLAY_SELECTOR_SEED = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_REPLAY_SELECTOR_SEED
)
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_OBJECT_TYPE = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_OBJECT_TYPE
)
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_ATTRIBUTE_NAME = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_ATTRIBUTE_NAME
)
_REFLECTIVE_BUILTIN_VARS_WORKER_FORM_LABEL = (
    _rbc._REFLECTIVE_BUILTIN_VARS_WORKER_FORM_LABEL
)
_REFLECTIVE_BUILTIN_VARS_WORKER_BOUNDARY_TEXT = (
    _rbc._REFLECTIVE_BUILTIN_VARS_WORKER_BOUNDARY_TEXT
)
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_FORM_LABEL = (
    _rbc._REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_FORM_LABEL
)
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_BOUNDARY_TEXT = (
    _rbc._REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_BOUNDARY_TEXT
)
_REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME = (
    _rbc._REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME
)
_REFLECTIVE_BUILTIN_VARS_WORKER_RETURNED_NAMESPACE = (
    _rbc._REFLECTIVE_BUILTIN_VARS_WORKER_RETURNED_NAMESPACE
)
_REFLECTIVE_BUILTIN_VARS_WORKER_RAISED_TYPE_ERROR = (
    _rbc._REFLECTIVE_BUILTIN_VARS_WORKER_RAISED_TYPE_ERROR
)
_REFLECTIVE_BUILTIN_VARS_OBJECT_TYPE_REPLAY_KEY = (
    _rbc._REFLECTIVE_BUILTIN_VARS_OBJECT_TYPE_REPLAY_KEY
)
_REFLECTIVE_BUILTIN_VARS_TYPE_ERROR_OBJECT_TYPE = (
    _rbc._REFLECTIVE_BUILTIN_VARS_TYPE_ERROR_OBJECT_TYPE
)
_REFLECTIVE_BUILTIN_VARS_RETURNED_NAMESPACE_OBJECT_TYPE = (
    _rbc._REFLECTIVE_BUILTIN_VARS_RETURNED_NAMESPACE_OBJECT_TYPE
)
_REFLECTIVE_BUILTIN_VARS_PROBE_RECORD_CLASS_NAME = (
    _rbc._REFLECTIVE_BUILTIN_VARS_PROBE_RECORD_CLASS_NAME
)
_REFLECTIVE_BUILTIN_VARS_PROBE_RECORD_LABEL = (
    _rbc._REFLECTIVE_BUILTIN_VARS_PROBE_RECORD_LABEL
)
_REFLECTIVE_BUILTIN_DIR_WORKER_FORM_LABEL = (
    _rbc._REFLECTIVE_BUILTIN_DIR_WORKER_FORM_LABEL
)
_REFLECTIVE_BUILTIN_DIR_WORKER_BOUNDARY_TEXT = (
    _rbc._REFLECTIVE_BUILTIN_DIR_WORKER_BOUNDARY_TEXT
)
_REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_FORM_LABEL = (
    _rbc._REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_FORM_LABEL
)
_REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_BOUNDARY_TEXT = (
    _rbc._REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_BOUNDARY_TEXT
)
_REFLECTIVE_BUILTIN_DIR_WORKER_BOUNDARY_TEXT_BY_FORM_LABEL = (
    _rbc._REFLECTIVE_BUILTIN_DIR_WORKER_BOUNDARY_TEXT_BY_FORM_LABEL
)
_REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME = (
    _rbc._REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME
)
_REFLECTIVE_BUILTIN_DIR_OBJECT_TYPE_REPLAY_KEY = (
    _rbc._REFLECTIVE_BUILTIN_DIR_OBJECT_TYPE_REPLAY_KEY
)
_REFLECTIVE_BUILTIN_DIR_INT_DIRECTORY_OBJECT_TYPE = (
    _rbc._REFLECTIVE_BUILTIN_DIR_INT_DIRECTORY_OBJECT_TYPE
)
_REFLECTIVE_BUILTIN_WORKER_FORM_LABELS = _rbc._REFLECTIVE_BUILTIN_WORKER_FORM_LABELS
_REFLECTIVE_BUILTIN_HASATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_REFLECTIVE_BUILTIN_HASATTR_WORKER_SHAPE_ERROR_MESSAGES = (
    _rbc._REFLECTIVE_BUILTIN_HASATTR_WORKER_SHAPE_ERROR_MESSAGES
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_REFLECTIVE_BUILTIN_GETATTR_WORKER_SHAPE_ERROR_MESSAGES = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_WORKER_SHAPE_ERROR_MESSAGES
)
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_SHAPE_ERROR_MESSAGES = (
    _rbc._REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_SHAPE_ERROR_MESSAGES
)
_REFLECTIVE_BUILTIN_VARS_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rbc._REFLECTIVE_BUILTIN_VARS_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_REFLECTIVE_BUILTIN_VARS_WORKER_SHAPE_ERROR_MESSAGES = (
    _rbc._REFLECTIVE_BUILTIN_VARS_WORKER_SHAPE_ERROR_MESSAGES
)
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rbc._REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_SHAPE_ERROR_MESSAGES = (
    _rbc._REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_SHAPE_ERROR_MESSAGES
)
_REFLECTIVE_BUILTIN_DIR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rbc._REFLECTIVE_BUILTIN_DIR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_REFLECTIVE_BUILTIN_DIR_WORKER_SHAPE_ERROR_MESSAGES = (
    _rbc._REFLECTIVE_BUILTIN_DIR_WORKER_SHAPE_ERROR_MESSAGES
)
_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_FORM_LABEL = (
    _rmc._RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_FORM_LABEL
)
_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_BOUNDARY_TEXT = (
    _rmc._RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_BOUNDARY_TEXT
)
_RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME = (
    _rmc._RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME
)
_RUNTIME_MUTATION_GLOBALS_WORKER_RETURNED_NAMESPACE = (
    _rmc._RUNTIME_MUTATION_GLOBALS_WORKER_RETURNED_NAMESPACE
)
_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rmc._RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_SHAPE_ERROR_MESSAGES = (
    _rmc._RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_SHAPE_ERROR_MESSAGES
)
_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_FORM_LABEL = (
    _rmc._RUNTIME_MUTATION_LOCALS_ZERO_WORKER_FORM_LABEL
)
_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_BOUNDARY_TEXT = (
    _rmc._RUNTIME_MUTATION_LOCALS_ZERO_WORKER_BOUNDARY_TEXT
)
_RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME = (
    _rmc._RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME
)
_RUNTIME_MUTATION_LOCALS_WORKER_RETURNED_NAMESPACE = (
    _rmc._RUNTIME_MUTATION_LOCALS_WORKER_RETURNED_NAMESPACE
)
_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rmc._RUNTIME_MUTATION_LOCALS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_SHAPE_ERROR_MESSAGES = (
    _rmc._RUNTIME_MUTATION_LOCALS_ZERO_WORKER_SHAPE_ERROR_MESSAGES
)
_RUNTIME_MUTATION_SETATTR_WORKER_FORM_LABEL = (
    _rmc._RUNTIME_MUTATION_SETATTR_WORKER_FORM_LABEL
)
_RUNTIME_MUTATION_SETATTR_WORKER_BOUNDARY_TEXT = (
    _rmc._RUNTIME_MUTATION_SETATTR_WORKER_BOUNDARY_TEXT
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT
)
_RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME = (
    _rmc._RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME
)
_RUNTIME_MUTATION_SETATTR_WORKER_RETURNED_NONE = (
    _rmc._RUNTIME_MUTATION_SETATTR_WORKER_RETURNED_NONE
)
_RUNTIME_MUTATION_SETATTR_OBJECT_TYPE_REPLAY_KEY = (
    _rmc._RUNTIME_MUTATION_SETATTR_OBJECT_TYPE_REPLAY_KEY
)
_RUNTIME_MUTATION_SETATTR_ATTRIBUTE_NAME_REPLAY_KEY = (
    _rmc._RUNTIME_MUTATION_SETATTR_ATTRIBUTE_NAME_REPLAY_KEY
)
_RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_TYPE_REPLAY_KEY = (
    _rmc._RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_TYPE_REPLAY_KEY
)
_RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_LITERAL_REPLAY_KEY = (
    _rmc._RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_LITERAL_REPLAY_KEY
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SUBJECT_ID = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SUBJECT_ID
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_FILE_PATH = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_FILE_PATH
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_START_LINE = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_START_LINE
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_START_COLUMN = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_START_COLUMN
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_END_LINE = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_END_LINE
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_END_COLUMN = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_END_COLUMN
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_REPLAY_TARGET_SEED = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_REPLAY_TARGET_SEED
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_REPLAY_SELECTOR_SEED = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_REPLAY_SELECTOR_SEED
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_OBJECT_TYPE = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_OBJECT_TYPE
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_ATTRIBUTE_NAME = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_ATTRIBUTE_NAME
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_ASSIGNED_VALUE_TYPE = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_ASSIGNED_VALUE_TYPE
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_ASSIGNED_VALUE_LITERAL = (
    _rmc._RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_ASSIGNED_VALUE_LITERAL
)
_RUNTIME_MUTATION_SETATTR_NAME_FLAG_CLASS_NAME = (
    _rmc._RUNTIME_MUTATION_SETATTR_NAME_FLAG_CLASS_NAME
)
_RUNTIME_MUTATION_SETATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rmc._RUNTIME_MUTATION_SETATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_RUNTIME_MUTATION_SETATTR_WORKER_MUTATION_FAILED_MESSAGE = (
    _rmc._RUNTIME_MUTATION_SETATTR_WORKER_MUTATION_FAILED_MESSAGE
)
_RUNTIME_MUTATION_SETATTR_WORKER_SHAPE_ERROR_MESSAGES = (
    _rmc._RUNTIME_MUTATION_SETATTR_WORKER_SHAPE_ERROR_MESSAGES
)
_RUNTIME_MUTATION_DELATTR_WORKER_FORM_LABEL = (
    _rmc._RUNTIME_MUTATION_DELATTR_WORKER_FORM_LABEL
)
_RUNTIME_MUTATION_DELATTR_WORKER_BOUNDARY_TEXT = (
    _rmc._RUNTIME_MUTATION_DELATTR_WORKER_BOUNDARY_TEXT
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT
)
_RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME = (
    _rmc._RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME
)
_RUNTIME_MUTATION_DELATTR_WORKER_DELETED_ATTRIBUTE = (
    _rmc._RUNTIME_MUTATION_DELATTR_WORKER_DELETED_ATTRIBUTE
)
_RUNTIME_MUTATION_DELATTR_OBJECT_TYPE_REPLAY_KEY = (
    _rmc._RUNTIME_MUTATION_DELATTR_OBJECT_TYPE_REPLAY_KEY
)
_RUNTIME_MUTATION_DELATTR_ATTRIBUTE_NAME_REPLAY_KEY = (
    _rmc._RUNTIME_MUTATION_DELATTR_ATTRIBUTE_NAME_REPLAY_KEY
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SUBJECT_ID = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SUBJECT_ID
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_FILE_PATH = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_FILE_PATH
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_START_LINE = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_START_LINE
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_START_COLUMN = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_START_COLUMN
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_END_LINE = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_END_LINE
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_END_COLUMN = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_END_COLUMN
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_REPLAY_TARGET_SEED = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_REPLAY_TARGET_SEED
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_REPLAY_SELECTOR_SEED = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_REPLAY_SELECTOR_SEED
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_OBJECT_TYPE = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_OBJECT_TYPE
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_ATTRIBUTE_NAME = (
    _rmc._RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_ATTRIBUTE_NAME
)
_RUNTIME_MUTATION_DELATTR_PROBE_TARGET_CLASS_NAME = (
    _rmc._RUNTIME_MUTATION_DELATTR_PROBE_TARGET_CLASS_NAME
)
_RUNTIME_MUTATION_DELATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _rmc._RUNTIME_MUTATION_DELATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_RUNTIME_MUTATION_DELATTR_WORKER_DELETION_FAILED_MESSAGE = (
    _rmc._RUNTIME_MUTATION_DELATTR_WORKER_DELETION_FAILED_MESSAGE
)
_RUNTIME_MUTATION_DELATTR_WORKER_SHAPE_ERROR_MESSAGES = (
    _rmc._RUNTIME_MUTATION_DELATTR_WORKER_SHAPE_ERROR_MESSAGES
)
_EXEC_OR_EVAL_EXEC_WORKER_FORM_LABEL = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_FORM_LABEL
)
_EXEC_OR_EVAL_EXEC_WORKER_BOUNDARY_TEXT = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_BOUNDARY_TEXT
)
_EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME
)
_EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHAPE = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHAPE
)
_EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHA256 = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHA256
)
_EXEC_OR_EVAL_EXEC_WORKER_EXECUTION_OUTCOME = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_EXECUTION_OUTCOME
)
_EXEC_OR_EVAL_EXEC_WORKER_STATEMENT_KIND = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_STATEMENT_KIND
)
_EXEC_OR_EVAL_EXEC_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_EXEC_OR_EVAL_EXEC_WORKER_SHAPE_ERROR_MESSAGES = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EXEC_WORKER_SHAPE_ERROR_MESSAGES
)
_EXEC_OR_EVAL_EVAL_WORKER_FORM_LABEL = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_FORM_LABEL
)
_EXEC_OR_EVAL_EVAL_WORKER_BOUNDARY_TEXT = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_BOUNDARY_TEXT
)
_EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME
)
_EXEC_OR_EVAL_EVAL_WORKER_SOURCE_TEXT = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_SOURCE_TEXT
)
_EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHAPE = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHAPE
)
_EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHA256 = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHA256
)
_EXEC_OR_EVAL_EVAL_WORKER_EVALUATION_OUTCOME = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_EVALUATION_OUTCOME
)
_EXEC_OR_EVAL_EVAL_WORKER_RESULT_TYPE = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_RESULT_TYPE
)
_EXEC_OR_EVAL_EVAL_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
)
_EXEC_OR_EVAL_EVAL_WORKER_SHAPE_ERROR_MESSAGES = (
    _exec_or_eval_contracts._EXEC_OR_EVAL_EVAL_WORKER_SHAPE_ERROR_MESSAGES
)
_METACLASS_BEHAVIOR_KEYWORD_WORKER_FORM_LABEL = (
    _metaclass_contracts._METACLASS_BEHAVIOR_KEYWORD_WORKER_FORM_LABEL
)
_METACLASS_BEHAVIOR_KEYWORD_WORKER_BOUNDARY_TEXT = (
    _metaclass_contracts._METACLASS_BEHAVIOR_KEYWORD_WORKER_BOUNDARY_TEXT
)
_METACLASS_BEHAVIOR_KEYWORD_WORKER_BUILD_CLASS_GLOBAL_NAME = (
    _metaclass_contracts._METACLASS_BEHAVIOR_KEYWORD_WORKER_BUILD_CLASS_GLOBAL_NAME
)
_METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_CLASS_NAME = (
    _metaclass_contracts._METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_CLASS_NAME
)
_METACLASS_BEHAVIOR_KEYWORD_WORKER_SELECTED_METACLASS_NAME = (
    _metaclass_contracts._METACLASS_BEHAVIOR_KEYWORD_WORKER_SELECTED_METACLASS_NAME
)
_METACLASS_BEHAVIOR_KEYWORD_WORKER_CLASS_CREATION_OUTCOME = (
    _metaclass_contracts._METACLASS_BEHAVIOR_KEYWORD_WORKER_CLASS_CREATION_OUTCOME
)
_METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_IMPORT_FAILED_MESSAGE = (
    _metaclass_contracts._METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_IMPORT_FAILED_MESSAGE
)
_METACLASS_BEHAVIOR_KEYWORD_WORKER_SHAPE_ERROR_MESSAGES = (
    _metaclass_contracts._METACLASS_BEHAVIOR_KEYWORD_WORKER_SHAPE_ERROR_MESSAGES
)
_DYNAMIC_IMPORT_REQUIRED_REPLAY_FIELD_KEYS = (
    _metadata_protocol._DYNAMIC_IMPORT_REQUIRED_REPLAY_FIELD_KEYS
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
class RuntimeProbeLocalPythonReflectiveDirWorkerRequest:
    """Worker-local request contract for selected exact ``dir`` probes."""

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
        """Reject drifted or non-dir reflective worker request metadata."""
        _validate_runtime_probe_reflective_dir_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveDirWorkerObservation:
    """Worker-local observation metadata for selected exact ``dir`` probes."""

    request: RuntimeProbeLocalPythonReflectiveDirWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    listing_entry_count: int
    durable_artifact_reference: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed dir observations."""
        _validate_runtime_probe_reflective_dir_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonReflectiveDirReplayTarget:
    """Worker-local non-executing replay target plan for exact ``dir`` probes."""

    request: RuntimeProbeLocalPythonReflectiveDirWorkerRequest
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
        _validate_runtime_probe_reflective_dir_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest:
    """Worker-local request contract for exact ``globals()`` probes."""

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
        """Reject drifted or non-globals/0 runtime-mutation metadata."""
        _validate_runtime_probe_runtime_mutation_globals_zero_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation:
    """Worker-local observation metadata for exact ``globals()`` probes."""

    request: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    lookup_outcome: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed globals/0 observations."""
        _validate_runtime_probe_runtime_mutation_globals_zero_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroReplayTarget:
    """Worker-local non-executing replay target plan for exact ``globals/0``."""

    request: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest
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
        _validate_runtime_probe_runtime_mutation_globals_zero_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest:
    """Worker-local request contract for exact ``locals()`` probes."""

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
        """Reject drifted or non-locals/0 runtime-mutation metadata."""
        _validate_runtime_probe_runtime_mutation_locals_zero_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation:
    """Worker-local observation metadata for exact ``locals()`` probes."""

    request: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    lookup_outcome: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed locals/0 observations."""
        _validate_runtime_probe_runtime_mutation_locals_zero_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationLocalsZeroReplayTarget:
    """Worker-local non-executing replay target plan for exact ``locals/0``."""

    request: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest
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
        _validate_runtime_probe_runtime_mutation_locals_zero_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest:
    """Worker-local request contract for exact ``setattr(obj, name, value)``."""

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
        """Reject drifted or non-setattr runtime-mutation metadata."""
        _validate_runtime_probe_runtime_mutation_setattr_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation:
    """Worker-local observation metadata for exact ``setattr`` probes."""

    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    mutation_outcome: str
    durable_artifact_reference: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed setattr observations."""
        _validate_runtime_probe_runtime_mutation_setattr_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationSetattrReplayTarget:
    """Worker-local non-executing replay target plan for exact ``setattr/3``."""

    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest
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
        _validate_runtime_probe_runtime_mutation_setattr_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest:
    """Worker-local request contract for exact ``delattr(obj, name)`` probes."""

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
        """Reject drifted or non-delattr runtime-mutation metadata."""
        _validate_runtime_probe_runtime_mutation_delattr_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation:
    """Worker-local observation metadata for exact ``delattr`` probes."""

    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    mutation_outcome: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed delattr observations."""
        _validate_runtime_probe_runtime_mutation_delattr_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationDelattrReplayTarget:
    """Worker-local non-executing replay target plan for exact ``delattr/2``."""

    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest
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
        _validate_runtime_probe_runtime_mutation_delattr_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonExecWorkerRequest:
    """Worker-local request contract for exact ``exec(source)`` probes."""

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
        """Reject drifted or non-exec worker request metadata."""
        _validate_runtime_probe_exec_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonExecWorkerObservation:
    """Worker-local observation metadata for exact ``exec(source)`` probes."""

    request: RuntimeProbeLocalPythonExecWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    source_shape: str
    source_sha256: str
    execution_outcome: str
    statement_kind: str
    durable_artifact_reference: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed exec observations."""
        _validate_runtime_probe_exec_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonExecReplayTarget:
    """Worker-local non-executing replay target plan for exact ``exec``."""

    request: RuntimeProbeLocalPythonExecWorkerRequest
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
        _validate_runtime_probe_exec_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonEvalWorkerRequest:
    """Worker-local request contract for exact ``eval(source)`` probes."""

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
        """Reject drifted or non-eval worker request metadata."""
        _validate_runtime_probe_eval_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonEvalWorkerObservation:
    """Worker-local observation metadata for exact ``eval(source)`` probes."""

    request: RuntimeProbeLocalPythonEvalWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    source_shape: str
    source_sha256: str
    evaluation_outcome: str
    result_type: str
    durable_artifact_reference: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed eval observations."""
        _validate_runtime_probe_eval_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonEvalReplayTarget:
    """Worker-local non-executing replay target plan for exact ``eval``."""

    request: RuntimeProbeLocalPythonEvalWorkerRequest
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
        _validate_runtime_probe_eval_replay_target(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest:
    """Worker-local request contract for exact metaclass keyword probes."""

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
        """Reject drifted or non-metaclass-keyword worker request metadata."""
        _validate_runtime_probe_metaclass_keyword_worker_request(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation:
    """Worker-local observation metadata for exact metaclass keyword probes."""

    request: RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest
    plan_id: str
    request_id: str
    replay_target_seed: str
    replay_selector_seed: str
    invocation_contract_revision: str
    invocation_identity: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    class_creation_outcome: str
    created_class_qualified_name: str
    selected_metaclass_qualified_name: str
    durable_artifact_reference: str

    def __post_init__(self) -> None:
        """Reject drifted request identity or malformed metaclass observations."""
        _validate_runtime_probe_metaclass_keyword_worker_observation(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonMetaclassKeywordReplayTarget:
    """Worker-local non-executing replay target plan for metaclass import."""

    request: RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest
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
        _validate_runtime_probe_metaclass_keyword_replay_target(self)


RuntimeProbeLocalPythonWorkerResponse = (
    _response_protocol.RuntimeProbeLocalPythonWorkerResponse
)
RuntimeProbeLocalPythonWorkerSuccessResponse = (
    _response_protocol.RuntimeProbeLocalPythonWorkerSuccessResponse
)
RuntimeProbeLocalPythonWorkerHandlerResponse: TypeAlias = (
    _response_protocol.RuntimeProbeLocalPythonWorkerHandlerResponse
)
RuntimeProbeLocalPythonWorkerHandlerKey: TypeAlias = (
    _worker_dispatch.RuntimeProbeLocalPythonWorkerHandlerKey
)
RuntimeProbeLocalPythonWorkerCallable: TypeAlias = (
    _worker_dispatch.RuntimeProbeLocalPythonWorkerCallable
)
RuntimeProbeLocalPythonWorkerHandlerEntry = (
    _worker_dispatch.RuntimeProbeLocalPythonWorkerHandlerEntry
)
RuntimeProbeLocalPythonDispatchingWorker = (
    _worker_dispatch.RuntimeProbeLocalPythonDispatchingWorker
)
_RuntimeProbeWorkerDuplicateHandlerError = (
    _worker_dispatch._RuntimeProbeWorkerDuplicateHandlerError
)
_RuntimeProbeWorkerDispatchError = _worker_dispatch._RuntimeProbeWorkerDispatchError
_index_runtime_probe_worker_handler_entries = (
    _worker_dispatch._index_runtime_probe_worker_handler_entries
)
_runtime_probe_worker_handler_entry_key = (
    _worker_dispatch._runtime_probe_worker_handler_entry_key
)
_runtime_probe_worker_payload_key = _worker_dispatch._runtime_probe_worker_payload_key
_validate_runtime_probe_worker_handler_entry = (
    _worker_dispatch._validate_runtime_probe_worker_handler_entry
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
RuntimeProbeLocalPythonReflectiveDirWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonReflectiveDirWorkerRequest],
    RuntimeProbeLocalPythonReflectiveDirWorkerObservation,
]
RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest],
    RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation,
]
RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest],
    RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation,
]
RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest],
    RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation,
]
RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest],
    RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation,
]
RuntimeProbeLocalPythonExecWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonExecWorkerRequest],
    RuntimeProbeLocalPythonExecWorkerObservation,
]
RuntimeProbeLocalPythonEvalWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonEvalWorkerRequest],
    RuntimeProbeLocalPythonEvalWorkerObservation,
]
RuntimeProbeLocalPythonMetaclassKeywordWorkerObserver: TypeAlias = Callable[
    [RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest],
    RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation,
]
RuntimeProbeLocalPythonDynamicImportTargetCallable: TypeAlias = Callable[[], object]
RuntimeProbeLocalPythonReflectiveHasattrTargetCallable: TypeAlias = Callable[
    ...,
    object,
]
RuntimeProbeLocalPythonReflectiveGetattrTargetCallable: TypeAlias = Callable[
    ...,
    object,
]
RuntimeProbeLocalPythonReflectiveGetattrDefaultTargetCallable: TypeAlias = Callable[
    ...,
    object,
]
RuntimeProbeLocalPythonReflectiveVarsTargetCallable: TypeAlias = Callable[
    ...,
    object,
]
RuntimeProbeLocalPythonReflectiveVarsZeroTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonReflectiveDirTargetCallable: TypeAlias = Callable[..., object]
RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonRuntimeMutationLocalsZeroTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonRuntimeMutationSetattrTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonRuntimeMutationDelattrTargetCallable: TypeAlias = Callable[
    [],
    object,
]
RuntimeProbeLocalPythonExecTargetCallable: TypeAlias = Callable[[], object]
RuntimeProbeLocalPythonEvalTargetCallable: TypeAlias = Callable[[], object]
RuntimeProbeLocalPythonDynamicImportObservationSource: TypeAlias = (
    RuntimeProbeLocalPythonDynamicImportWorkerRequest
    | RuntimeProbeLocalPythonDynamicImportReplayTarget
)


@dataclass
class _RuntimeProbeDynamicImportCapture:
    """Mutable capture state for one controlled import-module execution."""

    captured_modules: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)
    captured_sys_modules: dict[str, ModuleType | object] = field(default_factory=dict)
    support_root_literal_render_card_fixture: bool = False
    support_root_name_render_card_fixture: bool = False
    support_root_alias_render_card_fixture: bool = False
    support_builtin_render_card_fixture: bool = False
    support_builtins_attr_render_card_fixture: bool = False
    support_builtins_alias_render_card_fixture: bool = False
    support_imported_name_render_card_fixture: bool = False
    support_imported_alias_render_card_fixture: bool = False
    support_imported_literal_render_card_fixture: bool = False

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
        if self.support_root_literal_render_card_fixture:
            stubbed_module = (
                _runtime_probe_dynamic_import_root_literal_render_card_module_stub(name)
            )
            if stubbed_module is not None:
                return stubbed_module
        if self.support_root_name_render_card_fixture:
            stubbed_module = (
                _runtime_probe_dynamic_import_root_name_render_card_module_stub(name)
            )
            if stubbed_module is not None:
                return stubbed_module
        if self.support_root_alias_render_card_fixture:
            stubbed_module = (
                _runtime_probe_dynamic_import_root_alias_render_card_module_stub(name)
            )
            if stubbed_module is not None:
                return stubbed_module
        if self.support_imported_name_render_card_fixture:
            stubbed_module = (
                _runtime_probe_dynamic_import_imported_name_render_card_module_stub(
                    name
                )
            )
            if stubbed_module is not None:
                return stubbed_module
        if self.support_imported_alias_render_card_fixture:
            stubbed_module = (
                _runtime_probe_dynamic_import_imported_alias_render_card_module_stub(
                    name
                )
            )
            if stubbed_module is not None:
                return stubbed_module
        if self.support_imported_literal_render_card_fixture:
            stubbed_module = (
                _runtime_probe_dynamic_import_imported_literal_render_card_module_stub(
                    name
                )
            )
            if stubbed_module is not None:
                return stubbed_module
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
        controlled_module = (
            _runtime_probe_dynamic_import_builtin_render_card_module_stub(name)
            if self.support_builtin_render_card_fixture
            else None
        )
        if controlled_module is None and self.support_builtins_attr_render_card_fixture:
            controlled_module = (
                _runtime_probe_dynamic_import_builtins_attr_render_card_module_stub(
                    name
                )
            )
        if (
            controlled_module is None
            and self.support_builtins_alias_render_card_fixture
        ):
            controlled_module = (
                _runtime_probe_dynamic_import_builtins_alias_render_card_module_stub(
                    name
                )
            )
        if controlled_module is None:
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
    captured_object_types: list[str] = field(default_factory=list)
    captured_attribute_names: list[str] = field(default_factory=list)
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
        self.captured_object_types.append(_runtime_probe_worker_object_type_name(obj))
        self.captured_attribute_names.append(name)
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
    captured_object_types: list[str] = field(default_factory=list)
    captured_attribute_names: list[str] = field(default_factory=list)
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
        self.captured_object_types.append(_runtime_probe_worker_object_type_name(obj))
        self.captured_attribute_names.append(name)
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


def _runtime_probe_worker_object_type_name(value: object) -> str:
    """Return the stable module-qualified type name for a captured object."""
    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"


@dataclass
class _RuntimeProbeReflectiveVarsCapture:
    """Mutable capture state for one controlled ``vars`` execution."""

    original_vars: Callable[[object], object]
    captured_lookup_outcomes: list[str] = field(default_factory=list)
    captured_object_types: list[str] = field(default_factory=list)
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
        self.captured_object_types.append(_runtime_probe_worker_object_type_name(obj))
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


@dataclass
class _RuntimeProbeReflectiveDirCapture:
    """Mutable capture state for one controlled ``dir`` execution."""

    expected_form_label: str
    original_dir: Callable[..., list[str]]
    captured_listings: list[tuple[str, ...]] = field(default_factory=list)
    captured_object_types: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def dir(self, *args: object, **kwargs: object) -> list[str]:
        """Capture one exact selected ``dir`` call."""
        if self.expected_form_label == _REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_FORM_LABEL:
            return self._capture_zero_arg_dir(args=args, kwargs=kwargs)
        return self._capture_one_arg_dir(args=args, kwargs=kwargs)

    def _capture_one_arg_dir(
        self,
        *,
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> list[str]:
        """Capture one exact one-argument ``dir`` call."""
        if kwargs or len(args) != 1:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe reflective builtin dir worker form must be exactly "
                "dir(obj)"
            )
        (obj,) = args
        listing = self.original_dir(obj)
        self.captured_listings.append(tuple(listing))
        self.captured_object_types.append(_runtime_probe_worker_object_type_name(obj))
        return listing

    def _capture_zero_arg_dir(
        self,
        *,
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> list[str]:
        """Capture one exact zero-argument ``dir`` call."""
        if kwargs or args:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe reflective builtin dir worker form must be exactly dir()"
            )
        listing = sorted(sys._getframe(2).f_locals)
        self.captured_listings.append(tuple(listing))
        return listing


@dataclass
class _RuntimeProbeRuntimeMutationGlobalsZeroCapture:
    """Mutable capture state for one controlled zero-argument ``globals`` execution."""

    captured_lookup_outcomes: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def globals(self, *args: object, **kwargs: object) -> object:
        """Capture one exact zero-argument ``globals`` call."""
        if kwargs or args:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe runtime mutation globals zero worker form must be "
                "exactly globals()"
            )
        caller_namespace = sys._getframe(1).f_globals
        self.captured_lookup_outcomes.append(
            _RUNTIME_MUTATION_GLOBALS_WORKER_RETURNED_NAMESPACE
        )
        return caller_namespace


@dataclass
class _RuntimeProbeRuntimeMutationLocalsZeroCapture:
    """Mutable capture state for one controlled zero-argument ``locals`` execution."""

    captured_lookup_outcomes: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def locals(self, *args: object, **kwargs: object) -> object:
        """Capture one exact zero-argument ``locals`` call."""
        if kwargs or args:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe runtime mutation locals zero worker form must be "
                "exactly locals()"
            )
        caller_namespace = dict(sys._getframe(1).f_locals)
        self.captured_lookup_outcomes.append(
            _RUNTIME_MUTATION_LOCALS_WORKER_RETURNED_NAMESPACE
        )
        return caller_namespace


@dataclass
class _RuntimeProbeRuntimeMutationSetattrCapture:
    """Mutable capture state for one controlled ``setattr`` execution."""

    original_setattr: Callable[[object, str, object], object]
    captured_mutation_outcomes: list[str] = field(default_factory=list)
    captured_objects: list[object] = field(default_factory=list)
    captured_object_types: list[str] = field(default_factory=list)
    captured_attribute_names: list[str] = field(default_factory=list)
    captured_assigned_value_types: list[str] = field(default_factory=list)
    captured_assigned_value_literals: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def setattr(self, *args: object, **kwargs: object) -> None:
        """Capture one exact three-argument ``setattr`` mutation."""
        if kwargs or len(args) != 3:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe runtime mutation setattr worker form must be exactly "
                "setattr(obj, name, value)"
            )
        obj, name, value = args
        if not isinstance(name, str):
            self.captured_rejections.append("name")
            raise ValueError(
                "runtime probe runtime mutation setattr worker attribute name must "
                "be a string"
            )
        self.captured_objects.append(obj)
        self.captured_object_types.append(_runtime_probe_worker_object_type_name(obj))
        self.captured_attribute_names.append(name)
        self.captured_assigned_value_types.append(
            _runtime_probe_worker_object_type_name(value)
        )
        if isinstance(value, str):
            self.captured_assigned_value_literals.append(value)
        else:
            self.captured_assigned_value_literals.append("")
        try:
            result = self.original_setattr(obj, name, value)
        except Exception as error:
            self.captured_rejections.append("mutation")
            raise ValueError(
                _RUNTIME_MUTATION_SETATTR_WORKER_MUTATION_FAILED_MESSAGE
            ) from error
        if result is not None:
            self.captured_rejections.append("mutation")
            raise ValueError(_RUNTIME_MUTATION_SETATTR_WORKER_MUTATION_FAILED_MESSAGE)
        self.captured_mutation_outcomes.append(
            _RUNTIME_MUTATION_SETATTR_WORKER_RETURNED_NONE
        )


@dataclass
class _RuntimeProbeRuntimeMutationDelattrCapture:
    """Mutable capture state for one controlled ``delattr`` execution."""

    original_delattr: Callable[[object, str], None]
    captured_mutation_outcomes: list[str] = field(default_factory=list)
    captured_object_types: list[str] = field(default_factory=list)
    captured_attribute_names: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def delattr(self, *args: object, **kwargs: object) -> None:
        """Capture one exact two-argument ``delattr`` deletion."""
        if kwargs or len(args) != 2:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe runtime mutation delattr worker form must be exactly "
                "delattr(obj, name)"
            )
        obj, name = args
        if not isinstance(name, str):
            self.captured_rejections.append("name")
            raise ValueError(
                "runtime probe runtime mutation delattr worker attribute name must "
                "be a string"
            )
        self.captured_object_types.append(_runtime_probe_worker_object_type_name(obj))
        self.captured_attribute_names.append(name)
        try:
            self.original_delattr(obj, name)
        except Exception as error:
            self.captured_rejections.append("deletion")
            raise ValueError(
                _RUNTIME_MUTATION_DELATTR_WORKER_DELETION_FAILED_MESSAGE
            ) from error
        self.captured_mutation_outcomes.append(
            _RUNTIME_MUTATION_DELATTR_WORKER_DELETED_ATTRIBUTE
        )


@dataclass
class _RuntimeProbeExecCapture:
    """Mutable capture state for one controlled ``exec(source)`` execution."""

    original_exec: Callable[..., object]
    captured_sources: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def exec(self, *args: object, **kwargs: object) -> object:
        """Capture one exact one-argument ``exec(source)`` call."""
        if kwargs or len(args) != 1:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe exec worker form must be exactly exec(source)"
            )
        (source,) = args
        if not isinstance(source, str):
            self.captured_rejections.append("source_type")
            raise ValueError("runtime probe exec worker source must be a string")
        try:
            _validate_runtime_probe_exec_observed_source(source)
        except ValueError as error:
            self.captured_rejections.append("source")
            raise error
        self.captured_sources.append(source)
        caller_frame = sys._getframe(1)
        return self.original_exec(source, caller_frame.f_globals, caller_frame.f_locals)


@dataclass
class _RuntimeProbeEvalCapture:
    """Mutable capture state for one controlled ``eval(source)`` execution."""

    original_eval: Callable[..., object]
    captured_sources: list[str] = field(default_factory=list)
    captured_rejections: list[str] = field(default_factory=list)

    def eval(self, *args: object, **kwargs: object) -> object:
        """Capture one exact one-argument ``eval(source)`` call."""
        if kwargs or len(args) != 1:
            self.captured_rejections.append("arity")
            raise ValueError(
                "runtime probe eval worker form must be exactly eval(source)"
            )
        (source,) = args
        if not isinstance(source, str):
            self.captured_rejections.append("source_type")
            raise ValueError("runtime probe eval worker source must be a string")
        try:
            _validate_runtime_probe_eval_observed_source(source)
        except ValueError as error:
            self.captured_rejections.append("source")
            raise error
        self.captured_sources.append(source)
        caller_frame = sys._getframe(1)
        result = self.original_eval(
            source,
            caller_frame.f_globals,
            caller_frame.f_locals,
        )
        if not isinstance(result, str):
            self.captured_rejections.append("result_type")
            raise ValueError("runtime probe eval worker result must be a string")
        return result


@dataclass(frozen=True)
class _RuntimeProbeMetaclassKeywordCaptureResult:
    """Captured top-level target class creation metadata."""

    created_class_qualified_name: str
    selected_metaclass_qualified_name: str


@dataclass
class _RuntimeProbeMetaclassKeywordBuildClassCapture:
    """Capture exact target class creation during source-module import."""

    original_build_class: Callable[..., object]
    target_class_name: str
    target_class_qualified_name: str
    selected_metaclass_qualified_name: str
    captured_classes: list[_RuntimeProbeMetaclassKeywordCaptureResult] = field(
        default_factory=list
    )

    def build_class(self, *args: object, **kwargs: object) -> object:
        """Wrap ``__build_class__`` and record only the planned target class."""
        created_class = self.original_build_class(*args, **kwargs)
        created_class_qualified_name = (
            _runtime_probe_metaclass_keyword_optional_qualified_name(created_class)
        )
        if created_class_qualified_name != self.target_class_qualified_name:
            return created_class

        if len(args) < 2 or args[1] != self.target_class_name:
            raise ValueError(
                "runtime probe metaclass behavior worker target class must be "
                "top-level Example"
            )
        if set(kwargs) != {"metaclass"}:
            raise ValueError(
                "runtime probe metaclass behavior worker target class must use "
                "exact metaclass keyword"
            )

        selected_metaclass = kwargs["metaclass"]
        selected_metaclass_qualified_name = (
            _runtime_probe_metaclass_keyword_qualified_name(
                selected_metaclass,
                field_name="selected_metaclass",
            )
        )
        if selected_metaclass_qualified_name != self.selected_metaclass_qualified_name:
            raise ValueError(
                "runtime probe metaclass behavior worker selected metaclass is "
                "unsupported"
            )

        actual_metaclass_qualified_name = (
            _runtime_probe_metaclass_keyword_qualified_name(
                type(created_class),
                field_name="selected_metaclass",
            )
        )
        if actual_metaclass_qualified_name != selected_metaclass_qualified_name:
            raise ValueError(
                "runtime probe metaclass behavior worker selected metaclass is "
                "unsupported"
            )

        self.captured_classes.append(
            _RuntimeProbeMetaclassKeywordCaptureResult(
                created_class_qualified_name=created_class_qualified_name,
                selected_metaclass_qualified_name=selected_metaclass_qualified_name,
            )
        )
        return created_class


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
class RuntimeProbeLocalPythonReflectiveDirWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-dir observer."""

    observer: RuntimeProbeLocalPythonReflectiveDirWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_reflective_dir_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_reflective_dir_worker_request(payload)
        observation = self.observer(request)
        _validate_runtime_probe_reflective_dir_worker_observation_for_request(
            observation,
            request,
        )
        return materialize_runtime_probe_reflective_dir_worker_success_response(
            observation
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-globals/0 observer."""

    observer: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_runtime_mutation_globals_zero_worker_observer(
            self.observer
        )

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = (
            materialize_runtime_probe_runtime_mutation_globals_zero_worker_request(
                payload
            )
        )
        observation = self.observer(request)
        _validate_runtime_probe_runtime_mutation_globals_zero_observation_for_request(
            observation,
            request,
        )
        return _materialize_runtime_mutation_globals_zero_worker_success_response(
            observation
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-locals/0 observer."""

    observer: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_runtime_mutation_locals_zero_worker_observer(
            self.observer
        )

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_runtime_mutation_locals_zero_worker_request(
            payload
        )
        observation = self.observer(request)
        _validate_runtime_probe_runtime_mutation_locals_zero_observation_for_request(
            observation,
            request,
        )
        return _materialize_runtime_mutation_locals_zero_worker_success_response(
            observation
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-setattr observer."""

    observer: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_runtime_mutation_setattr_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_runtime_mutation_setattr_worker_request(
            payload
        )
        observation = self.observer(request)
        _validate_runtime_probe_runtime_mutation_setattr_observation_for_request(
            observation,
            request,
        )
        return _materialize_runtime_mutation_setattr_worker_success_response(
            observation
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-delattr observer."""

    observer: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_runtime_mutation_delattr_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_runtime_mutation_delattr_worker_request(
            payload
        )
        observation = self.observer(request)
        _validate_runtime_probe_runtime_mutation_delattr_observation_for_request(
            observation,
            request,
        )
        return _materialize_runtime_mutation_delattr_worker_success_response(
            observation
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonExecWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-exec observer."""

    observer: RuntimeProbeLocalPythonExecWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_exec_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_exec_worker_request(payload)
        observation = self.observer(request)
        _validate_runtime_probe_exec_observation_for_request(observation, request)
        return materialize_runtime_probe_exec_worker_success_response(observation)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonEvalWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected exact-eval observer."""

    observer: RuntimeProbeLocalPythonEvalWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_eval_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_eval_worker_request(payload)
        observation = self.observer(request)
        _validate_runtime_probe_eval_observation_for_request(observation, request)
        return materialize_runtime_probe_eval_worker_success_response(observation)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonMetaclassKeywordWorkerHandlerAdapter:
    """Adapt parsed worker payloads to an injected metaclass-keyword observer."""

    observer: RuntimeProbeLocalPythonMetaclassKeywordWorkerObserver

    def __post_init__(self) -> None:
        """Reject malformed observer injection before worker dispatch."""
        _validate_runtime_probe_metaclass_keyword_worker_observer(self.observer)

    def __call__(
        self,
        payload: RuntimeProbeLocalPythonWorkerRequestPayload,
    ) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
        """Run the injected observer against a validated worker request."""
        request = materialize_runtime_probe_metaclass_keyword_worker_request(payload)
        observation = self.observer(request)
        _validate_runtime_probe_metaclass_keyword_observation_for_request(
            observation,
            request,
        )
        return materialize_runtime_probe_metaclass_keyword_worker_success_response(
            observation
        )


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


serialize_runtime_probe_local_python_worker_success_response = (
    _response_protocol.serialize_runtime_probe_local_python_worker_success_response
)


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


def materialize_runtime_probe_reflective_dir_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonReflectiveDirWorkerRequest:
    """Derive an exact-dir worker request from stdin payload."""
    _validate_runtime_probe_reflective_dir_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonReflectiveDirWorkerRequest(
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
        reason_code=_runtime_probe_worker_reflective_dir_reason_code_from_replay_field(
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


def materialize_runtime_probe_reflective_dir_worker_observation(
    request: RuntimeProbeLocalPythonReflectiveDirWorkerRequest,
    *,
    listing_entry_count: int,
) -> RuntimeProbeLocalPythonReflectiveDirWorkerObservation:
    """Build non-executing exact-dir observation metadata from a request."""
    _validate_runtime_probe_reflective_dir_worker_request(request)
    return RuntimeProbeLocalPythonReflectiveDirWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        listing_entry_count=listing_entry_count,
        durable_artifact_reference=(
            _runtime_probe_reflective_dir_listing_artifact_reference(request.request_id)
        ),
    )


def materialize_runtime_probe_reflective_dir_replay_target(
    request: RuntimeProbeLocalPythonReflectiveDirWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveDirReplayTarget:
    """Derive a non-executing local Python replay target from a dir request."""
    _validate_runtime_probe_reflective_dir_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonReflectiveDirReplayTarget(
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


def materialize_runtime_probe_reflective_dir_worker_success_response(
    observation: RuntimeProbeLocalPythonReflectiveDirWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one dir observation."""
    _validate_runtime_probe_reflective_dir_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="listing_entry_count",
                value=str(observation.listing_entry_count),
            ),
        ),
        durable_artifact_reference=observation.durable_artifact_reference,
    )


def materialize_runtime_probe_runtime_mutation_globals_zero_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest:
    """Derive an exact-globals/0 worker request from stdin payload."""
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest(
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
            _runtime_probe_worker_runtime_mutation_globals_zero_reason_code_from_replay_field(
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


def materialize_runtime_probe_runtime_mutation_globals_zero_worker_observation(
    request: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest,
    *,
    lookup_outcome: str,
) -> RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation:
    """Build non-executing exact-globals/0 observation metadata from a request."""
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_request(request)
    return RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation(
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


def materialize_runtime_probe_runtime_mutation_globals_zero_replay_target(
    request: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest,
) -> RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroReplayTarget:
    """Derive a non-executing local Python replay target from a globals/0 request."""
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroReplayTarget(
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


def materialize_runtime_probe_runtime_mutation_globals_zero_worker_success_response(
    observation: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one globals/0 observation."""
    return _materialize_runtime_mutation_globals_zero_worker_success_response(
        observation
    )


def _materialize_runtime_mutation_globals_zero_worker_success_response(
    observation: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for internal globals/0 callers."""
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_observation(
        observation
    )
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="lookup_outcome",
                value=observation.lookup_outcome,
            ),
        ),
    )


def materialize_runtime_probe_runtime_mutation_locals_zero_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest:
    """Derive an exact-locals/0 worker request from stdin payload."""
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest(
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
            _runtime_probe_worker_runtime_mutation_locals_zero_reason_code_from_replay_field(
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


def materialize_runtime_probe_runtime_mutation_locals_zero_worker_observation(
    request: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest,
    *,
    lookup_outcome: str,
) -> RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation:
    """Build non-executing exact-locals/0 observation metadata from a request."""
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_request(request)
    return RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation(
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


def materialize_runtime_probe_runtime_mutation_locals_zero_replay_target(
    request: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest,
) -> RuntimeProbeLocalPythonRuntimeMutationLocalsZeroReplayTarget:
    """Derive a non-executing local Python replay target from a locals/0 request."""
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonRuntimeMutationLocalsZeroReplayTarget(
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


def materialize_runtime_probe_runtime_mutation_locals_zero_worker_success_response(
    observation: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one locals/0 observation."""
    return _materialize_runtime_mutation_locals_zero_worker_success_response(
        observation
    )


def _materialize_runtime_mutation_locals_zero_worker_success_response(
    observation: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for internal locals/0 callers."""
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="lookup_outcome",
                value=observation.lookup_outcome,
            ),
        ),
    )


def materialize_runtime_probe_runtime_mutation_setattr_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest:
    """Derive an exact-setattr worker request from stdin payload."""
    _validate_runtime_probe_runtime_mutation_setattr_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest(
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
            _runtime_probe_worker_runtime_mutation_setattr_reason_code_from_replay_field(
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


def materialize_runtime_probe_runtime_mutation_setattr_worker_observation(
    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest,
    *,
    mutation_outcome: str,
) -> RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation:
    """Build non-executing exact-setattr observation metadata from a request."""
    _validate_runtime_probe_runtime_mutation_setattr_worker_request(request)
    return RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        mutation_outcome=mutation_outcome,
        durable_artifact_reference=(
            _runtime_probe_runtime_mutation_setattr_value_artifact_reference(
                request.request_id
            )
        ),
    )


def materialize_runtime_probe_runtime_mutation_setattr_replay_target(
    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest,
) -> RuntimeProbeLocalPythonRuntimeMutationSetattrReplayTarget:
    """Derive a non-executing local Python replay target from a setattr request."""
    _validate_runtime_probe_runtime_mutation_setattr_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonRuntimeMutationSetattrReplayTarget(
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


def materialize_runtime_probe_runtime_mutation_setattr_worker_success_response(
    observation: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one setattr observation."""
    return _materialize_runtime_mutation_setattr_worker_success_response(observation)


def _materialize_runtime_mutation_setattr_worker_success_response(
    observation: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for internal setattr callers."""
    _validate_runtime_probe_runtime_mutation_setattr_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="mutation_outcome",
                value=observation.mutation_outcome,
            ),
        ),
        durable_artifact_reference=observation.durable_artifact_reference,
    )


def materialize_runtime_probe_runtime_mutation_delattr_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest:
    """Derive an exact-delattr worker request from stdin payload."""
    _validate_runtime_probe_runtime_mutation_delattr_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest(
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
            _runtime_probe_worker_runtime_mutation_delattr_reason_code_from_replay_field(
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


def materialize_runtime_probe_runtime_mutation_delattr_worker_observation(
    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest,
    *,
    mutation_outcome: str,
) -> RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation:
    """Build non-executing exact-delattr observation metadata from a request."""
    _validate_runtime_probe_runtime_mutation_delattr_worker_request(request)
    return RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        mutation_outcome=mutation_outcome,
    )


def materialize_runtime_probe_runtime_mutation_delattr_replay_target(
    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest,
) -> RuntimeProbeLocalPythonRuntimeMutationDelattrReplayTarget:
    """Derive a non-executing local Python replay target from a delattr request."""
    _validate_runtime_probe_runtime_mutation_delattr_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonRuntimeMutationDelattrReplayTarget(
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


def materialize_runtime_probe_runtime_mutation_delattr_worker_success_response(
    observation: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one delattr observation."""
    return _materialize_runtime_mutation_delattr_worker_success_response(observation)


def _materialize_runtime_mutation_delattr_worker_success_response(
    observation: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for internal delattr callers."""
    _validate_runtime_probe_runtime_mutation_delattr_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="mutation_outcome",
                value=observation.mutation_outcome,
            ),
        ),
    )


def materialize_runtime_probe_exec_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonExecWorkerRequest:
    """Derive an exact-exec worker request from stdin payload."""
    _validate_runtime_probe_exec_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonExecWorkerRequest(
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
        reason_code=_runtime_probe_worker_exec_reason_code_from_replay_field(
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


def materialize_runtime_probe_exec_worker_observation(
    request: RuntimeProbeLocalPythonExecWorkerRequest,
) -> RuntimeProbeLocalPythonExecWorkerObservation:
    """Build exact-exec observation metadata from a validated request."""
    _validate_runtime_probe_exec_worker_request(request)
    return RuntimeProbeLocalPythonExecWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        source_shape=_EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHAPE,
        source_sha256=_EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHA256,
        execution_outcome=_EXEC_OR_EVAL_EXEC_WORKER_EXECUTION_OUTCOME,
        statement_kind=_EXEC_OR_EVAL_EXEC_WORKER_STATEMENT_KIND,
        durable_artifact_reference=_runtime_probe_exec_source_artifact_reference(
            request.request_id
        ),
    )


def materialize_runtime_probe_exec_replay_target(
    request: RuntimeProbeLocalPythonExecWorkerRequest,
) -> RuntimeProbeLocalPythonExecReplayTarget:
    """Derive a non-executing local Python replay target from an exec request."""
    _validate_runtime_probe_exec_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonExecReplayTarget(
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


def materialize_runtime_probe_exec_worker_success_response(
    observation: RuntimeProbeLocalPythonExecWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one exec observation."""
    _validate_runtime_probe_exec_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="execution_outcome",
                value=observation.execution_outcome,
            ),
            RuntimeProbeReplayField(
                key="statement_kind",
                value=observation.statement_kind,
            ),
        ),
        durable_artifact_reference=observation.durable_artifact_reference,
        observed_replay_inputs=(
            RuntimeProbeReplayField(
                key="source_shape",
                value=observation.source_shape,
            ),
            RuntimeProbeReplayField(
                key="source_sha256",
                value=observation.source_sha256,
            ),
        ),
    )


def materialize_runtime_probe_eval_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonEvalWorkerRequest:
    """Derive an exact-eval worker request from stdin payload."""
    _validate_runtime_probe_eval_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonEvalWorkerRequest(
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
        reason_code=_runtime_probe_worker_eval_reason_code_from_replay_field(
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


def materialize_runtime_probe_eval_worker_observation(
    request: RuntimeProbeLocalPythonEvalWorkerRequest,
) -> RuntimeProbeLocalPythonEvalWorkerObservation:
    """Build exact-eval observation metadata from a validated request."""
    _validate_runtime_probe_eval_worker_request(request)
    return RuntimeProbeLocalPythonEvalWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        source_shape=_EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHAPE,
        source_sha256=_EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHA256,
        evaluation_outcome=_EXEC_OR_EVAL_EVAL_WORKER_EVALUATION_OUTCOME,
        result_type=_EXEC_OR_EVAL_EVAL_WORKER_RESULT_TYPE,
        durable_artifact_reference=_runtime_probe_eval_source_artifact_reference(
            request.request_id
        ),
    )


def materialize_runtime_probe_eval_replay_target(
    request: RuntimeProbeLocalPythonEvalWorkerRequest,
) -> RuntimeProbeLocalPythonEvalReplayTarget:
    """Derive a non-executing local Python replay target from an eval request."""
    _validate_runtime_probe_eval_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonEvalReplayTarget(
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


def materialize_runtime_probe_eval_worker_success_response(
    observation: RuntimeProbeLocalPythonEvalWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one eval observation."""
    _validate_runtime_probe_eval_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="evaluation_outcome",
                value=observation.evaluation_outcome,
            ),
            RuntimeProbeReplayField(
                key="result_type",
                value=observation.result_type,
            ),
        ),
        durable_artifact_reference=observation.durable_artifact_reference,
        observed_replay_inputs=(
            RuntimeProbeReplayField(
                key="source_shape",
                value=observation.source_shape,
            ),
            RuntimeProbeReplayField(
                key="source_sha256",
                value=observation.source_sha256,
            ),
        ),
    )


def materialize_runtime_probe_metaclass_keyword_worker_request(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest:
    """Derive an exact metaclass-keyword worker request from stdin payload."""
    _validate_runtime_probe_metaclass_keyword_worker_payload(payload)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        payload.request_replay_payload_fields
    )
    return RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest(
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
        reason_code=_runtime_probe_worker_metaclass_reason_code_from_replay_field(
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


def materialize_runtime_probe_metaclass_keyword_worker_observation(
    request: RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest,
    *,
    created_class_qualified_name: str,
    selected_metaclass_qualified_name: str,
) -> RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation:
    """Build metaclass-keyword observation metadata from a validated request."""
    _validate_runtime_probe_metaclass_keyword_worker_request(request)
    return RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation(
        request=request,
        plan_id=request.plan_id,
        request_id=request.request_id,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        invocation_contract_revision=request.invocation_contract_revision,
        invocation_identity=request.invocation_identity,
        request_replay_payload_fields=request.request_replay_payload_fields,
        class_creation_outcome=(
            _METACLASS_BEHAVIOR_KEYWORD_WORKER_CLASS_CREATION_OUTCOME
        ),
        created_class_qualified_name=created_class_qualified_name,
        selected_metaclass_qualified_name=selected_metaclass_qualified_name,
        durable_artifact_reference=(
            _runtime_probe_metaclass_selection_artifact_reference(request.request_id)
        ),
    )


def materialize_runtime_probe_metaclass_keyword_replay_target(
    request: RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest,
) -> RuntimeProbeLocalPythonMetaclassKeywordReplayTarget:
    """Derive a non-executing source-module import target for metaclass probes."""
    _validate_runtime_probe_metaclass_keyword_worker_request(request)
    source_module_name = _runtime_probe_dynamic_import_source_module_name_from_path(
        request.source_file_path
    )
    replay_target_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    return RuntimeProbeLocalPythonMetaclassKeywordReplayTarget(
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


def materialize_runtime_probe_metaclass_keyword_worker_success_response(
    observation: RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation,
) -> RuntimeProbeLocalPythonWorkerSuccessResponse:
    """Materialize the stdout success response for one metaclass observation."""
    _validate_runtime_probe_metaclass_keyword_worker_observation(observation)
    return RuntimeProbeLocalPythonWorkerSuccessResponse(
        normalized_payload=(
            RuntimeProbeReplayField(
                key="class_creation_outcome",
                value=observation.class_creation_outcome,
            ),
            RuntimeProbeReplayField(
                key="created_class_qualified_name",
                value=observation.created_class_qualified_name,
            ),
            RuntimeProbeReplayField(
                key="selected_metaclass_qualified_name",
                value=observation.selected_metaclass_qualified_name,
            ),
        ),
        durable_artifact_reference=observation.durable_artifact_reference,
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
        supports_builtin_render_card_fixture = (
            _is_runtime_probe_dynamic_import_builtin_render_card_fixture_request(
                request
            )
        )
        imported_module = _runtime_probe_dynamic_import_captured_builtin_import_name(
            target,
            support_builtin_render_card_fixture=supports_builtin_render_card_fixture,
        )
        if supports_builtin_render_card_fixture:
            _validate_runtime_probe_dynamic_import_builtin_render_card_imported_module(
                imported_module
            )
    else:
        supports_root_literal_render_card_fixture = (
            _is_runtime_probe_dynamic_import_root_literal_render_card_fixture_request(
                request
            )
        )
        supports_root_name_render_card_fixture = (
            _is_runtime_probe_dynamic_import_root_name_render_card_fixture_request(
                request
            )
        )
        supports_root_alias_render_card_fixture = (
            _is_runtime_probe_dynamic_import_root_alias_render_card_fixture_request(
                request
            )
        )
        imported_module = _runtime_probe_dynamic_import_captured_import_module_name(
            target,
            support_root_literal_render_card_fixture=(
                supports_root_literal_render_card_fixture
            ),
            support_root_name_render_card_fixture=(
                supports_root_name_render_card_fixture
            ),
            support_root_alias_render_card_fixture=(
                supports_root_alias_render_card_fixture
            ),
        )
        if supports_root_literal_render_card_fixture:
            _validate_runtime_probe_dynamic_import_root_literal_render_card_imported_module(
                imported_module
            )
        if supports_root_name_render_card_fixture:
            _validate_runtime_probe_dynamic_import_root_name_render_card_imported_module(
                imported_module
            )
        if supports_root_alias_render_card_fixture:
            _validate_runtime_probe_dynamic_import_root_alias_render_card_imported_module(
                imported_module
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
        supports_imported_fixture = _supports_imported_literal_fixture(request)
        supports_imported_name_fixture = _supports_imported_name_fixture(request)
        supports_imported_alias_fixture = _supports_imported_alias_fixture(request)
        observation = (
            _materialize_runtime_probe_dynamic_import_worker_observation_from_global(
                replay_target=replay_target,
                source_module=source_module,
                target=deterministic_target,
                global_name=_runtime_probe_dynamic_import_source_global_name_for_form(
                    request.form_label
                ),
                support_imported_literal_render_card_fixture=(
                    supports_imported_fixture
                ),
                support_imported_name_render_card_fixture=(
                    supports_imported_name_fixture
                ),
                support_imported_alias_render_card_fixture=(
                    supports_imported_alias_fixture
                ),
            )
        )
        if supports_imported_fixture:
            _validate_runtime_probe_dynamic_import_imported_literal_render_card_imported_module(
                observation.imported_module
            )
        if supports_imported_name_fixture:
            _validate_runtime_probe_dynamic_import_imported_name_render_card_imported_module(
                observation.imported_module
            )
        if supports_imported_alias_fixture:
            _validate_runtime_probe_dynamic_import_imported_alias_render_card_imported_module(
                observation.imported_module
            )
        return observation
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
    """Observe a ``hasattr`` target with zero args or exact pilot replay inputs."""
    _validate_runtime_probe_reflective_hasattr_replay_target(replay_target)
    _validate_runtime_probe_reflective_hasattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_hasattr_target_callable(target)
    target_args = _runtime_probe_reflective_hasattr_target_args(replay_target.request)
    attribute_present = _runtime_probe_reflective_hasattr_captured_attribute_present(
        source_module,
        target,
        target_args=target_args,
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
    """Observe one target under exact ``getattr`` interception."""
    _validate_runtime_probe_reflective_getattr_replay_target(replay_target)
    _validate_runtime_probe_reflective_getattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_getattr_target_callable(target)
    exact_replay_inputs = _runtime_probe_reflective_getattr_exact_replay_inputs(
        replay_target.request
    )
    target_args = _runtime_probe_reflective_getattr_target_args(exact_replay_inputs)
    lookup_outcome = _runtime_probe_reflective_getattr_captured_lookup_outcome(
        source_module,
        target,
        target_args=target_args,
        exact_replay_inputs=exact_replay_inputs,
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
    """Observe one target under exact ``getattr/3`` interception."""
    _validate_runtime_probe_reflective_getattr_default_replay_target(replay_target)
    _validate_runtime_probe_reflective_getattr_default_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_getattr_default_target_callable(target)
    exact_replay_inputs = _runtime_probe_reflective_getattr_default_exact_replay_inputs(
        replay_target.request
    )
    target_args = _runtime_probe_reflective_getattr_default_target_args(
        exact_replay_inputs
    )
    lookup_outcome = _runtime_probe_reflective_getattr_default_captured_lookup_outcome(
        source_module,
        target,
        target_args=target_args,
        exact_replay_inputs=exact_replay_inputs,
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
    """Observe one target under exact ``vars`` interception."""
    _validate_runtime_probe_reflective_vars_replay_target(replay_target)
    _validate_runtime_probe_reflective_vars_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_vars_target_callable(target)
    exact_replay_inputs = _runtime_probe_reflective_vars_exact_replay_inputs(
        replay_target.request
    )
    target_args = _runtime_probe_reflective_vars_target_args(
        source_module,
        exact_replay_inputs,
    )
    lookup_outcome = _runtime_probe_reflective_vars_captured_lookup_outcome(
        source_module,
        target,
        target_args=target_args,
        exact_replay_inputs=exact_replay_inputs,
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


def materialize_runtime_probe_reflective_dir_worker_observation_from_target(
    replay_target: RuntimeProbeLocalPythonReflectiveDirReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveDirTargetCallable,
) -> RuntimeProbeLocalPythonReflectiveDirWorkerObservation:
    """Observe one zero-argument target under exact ``dir`` interception."""
    _validate_runtime_probe_reflective_dir_replay_target(replay_target)
    _validate_runtime_probe_reflective_dir_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_reflective_dir_target_callable(target)
    exact_replay_inputs = _runtime_probe_reflective_dir_exact_replay_inputs(
        replay_target.request
    )
    target_args = _runtime_probe_reflective_dir_target_args(exact_replay_inputs)
    listing_entry_count = _runtime_probe_reflective_dir_captured_listing_entry_count(
        source_module,
        target,
        form_label=replay_target.request.form_label,
        target_args=target_args,
        exact_replay_inputs=exact_replay_inputs,
    )
    return materialize_runtime_probe_reflective_dir_worker_observation(
        replay_target.request,
        listing_entry_count=listing_entry_count,
    )


def observe_runtime_probe_reflective_dir_worker_request(
    request: RuntimeProbeLocalPythonReflectiveDirWorkerRequest,
) -> RuntimeProbeLocalPythonReflectiveDirWorkerObservation:
    """Observe one concrete exact-dir worker request in local Python."""
    _validate_runtime_probe_reflective_dir_worker_request(request)
    replay_target = materialize_runtime_probe_reflective_dir_replay_target(request)
    source_module = import_runtime_probe_reflective_dir_replay_target_source_module(
        replay_target
    )
    target = resolve_runtime_probe_reflective_dir_replay_target_callable(
        replay_target,
        source_module,
    )
    return materialize_runtime_probe_reflective_dir_worker_observation_from_target(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_runtime_mutation_globals_zero_observation_from_target(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroTargetCallable,
) -> RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation:
    """Observe one zero-argument target under exact ``globals()`` interception."""
    _validate_runtime_probe_runtime_mutation_globals_zero_replay_target(replay_target)
    _validate_runtime_probe_runtime_mutation_globals_zero_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_runtime_mutation_globals_zero_target_callable(target)
    lookup_outcome = (
        _runtime_probe_runtime_mutation_globals_zero_captured_lookup_outcome(
            source_module,
            target,
        )
    )
    return materialize_runtime_probe_runtime_mutation_globals_zero_worker_observation(
        replay_target.request,
        lookup_outcome=lookup_outcome,
    )


def observe_runtime_probe_runtime_mutation_globals_zero_worker_request(
    request: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest,
) -> RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation:
    """Observe one concrete exact-globals/0 worker request in local Python."""
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_request(request)
    replay_target = (
        materialize_runtime_probe_runtime_mutation_globals_zero_replay_target(request)
    )
    source_module = (
        import_runtime_probe_runtime_mutation_globals_zero_replay_target_source_module(
            replay_target
        )
    )
    target = resolve_runtime_probe_runtime_mutation_globals_zero_replay_target_callable(
        replay_target,
        source_module,
    )
    materialize_observation = (
        materialize_runtime_probe_runtime_mutation_globals_zero_observation_from_target
    )
    return materialize_observation(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_runtime_mutation_locals_zero_observation_from_target(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroTargetCallable,
) -> RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation:
    """Observe one zero-argument target under exact ``locals()`` interception."""
    _validate_runtime_probe_runtime_mutation_locals_zero_replay_target(replay_target)
    _validate_runtime_probe_runtime_mutation_locals_zero_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_runtime_mutation_locals_zero_target_callable(target)
    lookup_outcome = (
        _runtime_probe_runtime_mutation_locals_zero_captured_lookup_outcome(
            source_module,
            target,
        )
    )
    return materialize_runtime_probe_runtime_mutation_locals_zero_worker_observation(
        replay_target.request,
        lookup_outcome=lookup_outcome,
    )


def observe_runtime_probe_runtime_mutation_locals_zero_worker_request(
    request: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest,
) -> RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation:
    """Observe one concrete exact-locals/0 worker request in local Python."""
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_request(request)
    replay_target = (
        materialize_runtime_probe_runtime_mutation_locals_zero_replay_target(request)
    )
    source_module = (
        import_runtime_probe_runtime_mutation_locals_zero_replay_target_source_module(
            replay_target
        )
    )
    target = resolve_runtime_probe_runtime_mutation_locals_zero_replay_target_callable(
        replay_target,
        source_module,
    )
    materialize_observation = (
        materialize_runtime_probe_runtime_mutation_locals_zero_observation_from_target
    )
    return materialize_observation(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_runtime_mutation_setattr_observation_from_target(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationSetattrReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonRuntimeMutationSetattrTargetCallable,
) -> RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation:
    """Observe a ``setattr`` target with zero args or exact pilot replay inputs."""
    _validate_runtime_probe_runtime_mutation_setattr_replay_target(replay_target)
    _validate_runtime_probe_runtime_mutation_setattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_runtime_mutation_setattr_target_callable(target)
    exact_replay_inputs = _runtime_probe_runtime_mutation_setattr_exact_replay_inputs(
        replay_target.request
    )
    target_args = _runtime_probe_runtime_mutation_setattr_target_args(
        source_module,
        replay_target.request,
        exact_replay_inputs,
    )
    mutation_outcome = _runtime_probe_runtime_mutation_setattr_captured_outcome(
        source_module,
        target,
        target_args=target_args,
        exact_replay_inputs=exact_replay_inputs,
    )
    return materialize_runtime_probe_runtime_mutation_setattr_worker_observation(
        replay_target.request,
        mutation_outcome=mutation_outcome,
    )


def observe_runtime_probe_runtime_mutation_setattr_worker_request(
    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest,
) -> RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation:
    """Observe one concrete exact-setattr worker request in local Python."""
    _validate_runtime_probe_runtime_mutation_setattr_worker_request(request)
    replay_target = materialize_runtime_probe_runtime_mutation_setattr_replay_target(
        request
    )
    source_module = (
        import_runtime_probe_runtime_mutation_setattr_replay_target_source_module(
            replay_target
        )
    )
    target = resolve_runtime_probe_runtime_mutation_setattr_replay_target_callable(
        replay_target,
        source_module,
    )
    materialize_observation = (
        materialize_runtime_probe_runtime_mutation_setattr_observation_from_target
    )
    return materialize_observation(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_runtime_mutation_delattr_observation_from_target(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationDelattrReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonRuntimeMutationDelattrTargetCallable,
) -> RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation:
    """Observe a ``delattr`` target with zero args or exact pilot replay inputs."""
    _validate_runtime_probe_runtime_mutation_delattr_replay_target(replay_target)
    _validate_runtime_probe_runtime_mutation_delattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_runtime_mutation_delattr_target_callable(target)
    exact_replay_inputs = _runtime_probe_runtime_mutation_delattr_exact_replay_inputs(
        replay_target.request
    )
    target_args = _runtime_probe_runtime_mutation_delattr_target_args(
        source_module,
        replay_target.request,
        exact_replay_inputs,
    )
    mutation_outcome = _runtime_probe_runtime_mutation_delattr_captured_outcome(
        source_module,
        target,
        target_args=target_args,
        exact_replay_inputs=exact_replay_inputs,
    )
    return materialize_runtime_probe_runtime_mutation_delattr_worker_observation(
        replay_target.request,
        mutation_outcome=mutation_outcome,
    )


def observe_runtime_probe_runtime_mutation_delattr_worker_request(
    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest,
) -> RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation:
    """Observe one concrete exact-delattr worker request in local Python."""
    _validate_runtime_probe_runtime_mutation_delattr_worker_request(request)
    replay_target = materialize_runtime_probe_runtime_mutation_delattr_replay_target(
        request
    )
    source_module = (
        import_runtime_probe_runtime_mutation_delattr_replay_target_source_module(
            replay_target
        )
    )
    target = resolve_runtime_probe_runtime_mutation_delattr_replay_target_callable(
        replay_target,
        source_module,
    )
    materialize_observation = (
        materialize_runtime_probe_runtime_mutation_delattr_observation_from_target
    )
    return materialize_observation(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_exec_observation_from_target(
    replay_target: RuntimeProbeLocalPythonExecReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonExecTargetCallable,
) -> RuntimeProbeLocalPythonExecWorkerObservation:
    """Observe one zero-argument target under exact ``exec(source)`` interception."""
    _validate_runtime_probe_exec_replay_target(replay_target)
    _validate_runtime_probe_exec_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_exec_target_callable(target)
    _runtime_probe_exec_captured_source(source_module, target)
    return materialize_runtime_probe_exec_worker_observation(replay_target.request)


def observe_runtime_probe_exec_worker_request(
    request: RuntimeProbeLocalPythonExecWorkerRequest,
) -> RuntimeProbeLocalPythonExecWorkerObservation:
    """Observe one concrete exact-exec worker request in local Python."""
    _validate_runtime_probe_exec_worker_request(request)
    replay_target = materialize_runtime_probe_exec_replay_target(request)
    source_module = import_runtime_probe_exec_replay_target_source_module(replay_target)
    target = resolve_runtime_probe_exec_replay_target_callable(
        replay_target,
        source_module,
    )
    return materialize_runtime_probe_exec_observation_from_target(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_eval_observation_from_target(
    replay_target: RuntimeProbeLocalPythonEvalReplayTarget,
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonEvalTargetCallable,
) -> RuntimeProbeLocalPythonEvalWorkerObservation:
    """Observe one zero-argument target under exact ``eval(source)`` interception."""
    _validate_runtime_probe_eval_replay_target(replay_target)
    _validate_runtime_probe_eval_replay_target_source_module(
        replay_target,
        source_module,
    )
    _validate_runtime_probe_eval_target_callable(target)
    _runtime_probe_eval_captured_source(source_module, target)
    return materialize_runtime_probe_eval_worker_observation(replay_target.request)


def observe_runtime_probe_eval_worker_request(
    request: RuntimeProbeLocalPythonEvalWorkerRequest,
) -> RuntimeProbeLocalPythonEvalWorkerObservation:
    """Observe one concrete exact-eval worker request in local Python."""
    _validate_runtime_probe_eval_worker_request(request)
    replay_target = materialize_runtime_probe_eval_replay_target(request)
    source_module = import_runtime_probe_eval_replay_target_source_module(replay_target)
    target = resolve_runtime_probe_eval_replay_target_callable(
        replay_target,
        source_module,
    )
    return materialize_runtime_probe_eval_observation_from_target(
        replay_target,
        source_module,
        target,
    )


def materialize_runtime_probe_metaclass_keyword_observation_from_import(
    replay_target: RuntimeProbeLocalPythonMetaclassKeywordReplayTarget,
) -> RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation:
    """Observe one target class by intercepting source-module class creation."""
    _validate_runtime_probe_metaclass_keyword_replay_target(replay_target)
    capture_result = _runtime_probe_metaclass_keyword_capture_source_module_import(
        replay_target
    )
    return materialize_runtime_probe_metaclass_keyword_worker_observation(
        replay_target.request,
        created_class_qualified_name=capture_result.created_class_qualified_name,
        selected_metaclass_qualified_name=(
            capture_result.selected_metaclass_qualified_name
        ),
    )


def observe_runtime_probe_metaclass_keyword_worker_request(
    request: RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest,
) -> RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation:
    """Observe one concrete exact metaclass-keyword worker request in local Python."""
    _validate_runtime_probe_metaclass_keyword_worker_request(request)
    replay_target = materialize_runtime_probe_metaclass_keyword_replay_target(request)
    return materialize_runtime_probe_metaclass_keyword_observation_from_import(
        replay_target
    )


def import_runtime_probe_exec_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonExecReplayTarget,
) -> ModuleType:
    """Import an exec replay target source module under request-local import state."""
    _validate_runtime_probe_exec_replay_target(replay_target)
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
        raise ValueError("runtime probe exec source module import failed") from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_exec_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_eval_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonEvalReplayTarget,
) -> ModuleType:
    """Import an eval replay target source module under request-local import state."""
    _validate_runtime_probe_eval_replay_target(replay_target)
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
        raise ValueError("runtime probe eval source module import failed") from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_eval_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


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


def import_runtime_probe_reflective_dir_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveDirReplayTarget,
) -> ModuleType:
    """Import a dir/1 replay target source module under request-local state."""
    _validate_runtime_probe_reflective_dir_replay_target(replay_target)
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
            "runtime probe reflective builtin dir source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_reflective_dir_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_runtime_mutation_globals_zero_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroReplayTarget,
) -> ModuleType:
    """Import a globals/0 replay target source module under request-local state."""
    _validate_runtime_probe_runtime_mutation_globals_zero_replay_target(replay_target)
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
            "runtime probe runtime mutation globals zero source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_runtime_mutation_globals_zero_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_runtime_mutation_locals_zero_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroReplayTarget,
) -> ModuleType:
    """Import a locals/0 replay target source module under request-local state."""
    _validate_runtime_probe_runtime_mutation_locals_zero_replay_target(replay_target)
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
            "runtime probe runtime mutation locals zero source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_runtime_mutation_locals_zero_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_runtime_mutation_setattr_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationSetattrReplayTarget,
) -> ModuleType:
    """Import a setattr replay target source module under request-local state."""
    _validate_runtime_probe_runtime_mutation_setattr_replay_target(replay_target)
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
            "runtime probe runtime mutation setattr source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_runtime_mutation_setattr_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return imported_module


def import_runtime_probe_runtime_mutation_delattr_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationDelattrReplayTarget,
) -> ModuleType:
    """Import a delattr replay target source module under request-local state."""
    _validate_runtime_probe_runtime_mutation_delattr_replay_target(replay_target)
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
            "runtime probe runtime mutation delattr source module import failed"
        ) from error
    finally:
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    _validate_runtime_probe_runtime_mutation_delattr_replay_target_source_module(
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


def resolve_runtime_probe_reflective_dir_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonReflectiveDirReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonReflectiveDirTargetCallable:
    """Resolve an injected source module dir/1 replay target without executing it."""
    _validate_runtime_probe_reflective_dir_replay_target(replay_target)
    _validate_runtime_probe_reflective_dir_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe reflective builtin dir replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_reflective_dir_target_callable(resolved_target)
    return cast(RuntimeProbeLocalPythonReflectiveDirTargetCallable, resolved_target)


def resolve_runtime_probe_runtime_mutation_globals_zero_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroTargetCallable:
    """Resolve a source module globals/0 replay target without executing it."""
    _validate_runtime_probe_runtime_mutation_globals_zero_replay_target(replay_target)
    _validate_runtime_probe_runtime_mutation_globals_zero_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe runtime mutation globals zero replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_runtime_mutation_globals_zero_target_callable(
        resolved_target
    )
    return cast(
        RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroTargetCallable,
        resolved_target,
    )


def resolve_runtime_probe_runtime_mutation_locals_zero_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonRuntimeMutationLocalsZeroTargetCallable:
    """Resolve a source module locals/0 replay target without executing it."""
    _validate_runtime_probe_runtime_mutation_locals_zero_replay_target(replay_target)
    _validate_runtime_probe_runtime_mutation_locals_zero_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe runtime mutation locals zero replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_runtime_mutation_locals_zero_target_callable(
        resolved_target
    )
    return cast(
        RuntimeProbeLocalPythonRuntimeMutationLocalsZeroTargetCallable,
        resolved_target,
    )


def resolve_runtime_probe_runtime_mutation_setattr_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationSetattrReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonRuntimeMutationSetattrTargetCallable:
    """Resolve a source module setattr replay target without executing it."""
    _validate_runtime_probe_runtime_mutation_setattr_replay_target(replay_target)
    _validate_runtime_probe_runtime_mutation_setattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe runtime mutation setattr replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_runtime_mutation_setattr_target_callable(resolved_target)
    return cast(
        RuntimeProbeLocalPythonRuntimeMutationSetattrTargetCallable,
        resolved_target,
    )


def resolve_runtime_probe_runtime_mutation_delattr_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationDelattrReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonRuntimeMutationDelattrTargetCallable:
    """Resolve a source module delattr replay target without executing it."""
    _validate_runtime_probe_runtime_mutation_delattr_replay_target(replay_target)
    _validate_runtime_probe_runtime_mutation_delattr_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe runtime mutation delattr replay target "
                "replay_target_attribute_path is missing"
            ) from error
    _validate_runtime_probe_runtime_mutation_delattr_target_callable(resolved_target)
    return cast(
        RuntimeProbeLocalPythonRuntimeMutationDelattrTargetCallable,
        resolved_target,
    )


def resolve_runtime_probe_exec_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonExecReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonExecTargetCallable:
    """Resolve a source module exec replay target without executing it."""
    _validate_runtime_probe_exec_replay_target(replay_target)
    _validate_runtime_probe_exec_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe exec replay target replay_target_attribute_path "
                "is missing"
            ) from error
    _validate_runtime_probe_exec_target_callable(resolved_target)
    return cast(RuntimeProbeLocalPythonExecTargetCallable, resolved_target)


def resolve_runtime_probe_eval_replay_target_callable(
    replay_target: RuntimeProbeLocalPythonEvalReplayTarget,
    source_module: ModuleType,
) -> RuntimeProbeLocalPythonEvalTargetCallable:
    """Resolve a source module eval replay target without executing it."""
    _validate_runtime_probe_eval_replay_target(replay_target)
    _validate_runtime_probe_eval_replay_target_source_module(
        replay_target,
        source_module,
    )
    resolved_target: object = source_module
    for attribute_name in replay_target.replay_target_attribute_path:
        try:
            resolved_target = getattr(resolved_target, attribute_name)
        except AttributeError as error:
            raise ValueError(
                "runtime probe eval replay target replay_target_attribute_path "
                "is missing"
            ) from error
    _validate_runtime_probe_eval_target_callable(resolved_target)
    return cast(RuntimeProbeLocalPythonEvalTargetCallable, resolved_target)


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


def build_runtime_probe_reflective_dir_worker_handler_entry(
    observer: RuntimeProbeLocalPythonReflectiveDirWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``dir(obj)``."""
    return _build_runtime_probe_reflective_dir_worker_handler_entry(
        observer=observer,
        form_label=_REFLECTIVE_BUILTIN_DIR_WORKER_FORM_LABEL,
    )


def _build_runtime_probe_reflective_dir_worker_handler_entry(
    *,
    observer: RuntimeProbeLocalPythonReflectiveDirWorkerObserver,
    form_label: str,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for one selected exact ``dir`` form."""
    _validate_runtime_probe_reflective_dir_form_label(form_label)
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=form_label,
        handler=RuntimeProbeLocalPythonReflectiveDirWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_runtime_mutation_globals_zero_worker_handler_entry(
    observer: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``globals()``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_runtime_mutation_locals_zero_worker_handler_entry(
    observer: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``locals()``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_runtime_mutation_setattr_worker_handler_entry(
    observer: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``setattr``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=_RUNTIME_MUTATION_SETATTR_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_runtime_mutation_delattr_worker_handler_entry(
    observer: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``delattr``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=_RUNTIME_MUTATION_DELATTR_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerHandlerAdapter(
            observer=observer
        ),
    )


def build_runtime_probe_exec_worker_handler_entry(
    observer: RuntimeProbeLocalPythonExecWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``exec(source)``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.EXEC_OR_EVAL,
        form_label=_EXEC_OR_EVAL_EXEC_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonExecWorkerHandlerAdapter(observer=observer),
    )


def build_runtime_probe_eval_worker_handler_entry(
    observer: RuntimeProbeLocalPythonEvalWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact ``eval(source)``."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.EXEC_OR_EVAL,
        form_label=_EXEC_OR_EVAL_EVAL_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonEvalWorkerHandlerAdapter(observer=observer),
    )


def build_runtime_probe_metaclass_keyword_worker_handler_entry(
    observer: RuntimeProbeLocalPythonMetaclassKeywordWorkerObserver,
) -> RuntimeProbeLocalPythonWorkerHandlerEntry:
    """Return an injected handler entry for exact metaclass keyword probes."""
    return RuntimeProbeLocalPythonWorkerHandlerEntry(
        family_label=RuntimeProbeFamily.METACLASS_BEHAVIOR,
        form_label=_METACLASS_BEHAVIOR_KEYWORD_WORKER_FORM_LABEL,
        handler=RuntimeProbeLocalPythonMetaclassKeywordWorkerHandlerAdapter(
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
    reflective_dir_entries = (
        *(
            _build_runtime_probe_reflective_dir_worker_handler_entry(
                observer=observe_runtime_probe_reflective_dir_worker_request,
                form_label=form_label,
            )
            for form_label in (
                _REFLECTIVE_BUILTIN_DIR_WORKER_FORM_LABEL,
                _REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_FORM_LABEL,
            )
        ),
    )
    runtime_mutation_globals_zero_entries = (
        build_runtime_probe_runtime_mutation_globals_zero_worker_handler_entry(
            observe_runtime_probe_runtime_mutation_globals_zero_worker_request
        ),
    )
    runtime_mutation_locals_zero_entries = (
        build_runtime_probe_runtime_mutation_locals_zero_worker_handler_entry(
            observe_runtime_probe_runtime_mutation_locals_zero_worker_request
        ),
    )
    runtime_mutation_setattr_entries = (
        build_runtime_probe_runtime_mutation_setattr_worker_handler_entry(
            observe_runtime_probe_runtime_mutation_setattr_worker_request
        ),
    )
    runtime_mutation_delattr_entries = (
        build_runtime_probe_runtime_mutation_delattr_worker_handler_entry(
            observe_runtime_probe_runtime_mutation_delattr_worker_request
        ),
    )
    exec_entries = (
        build_runtime_probe_exec_worker_handler_entry(
            observe_runtime_probe_exec_worker_request
        ),
    )
    eval_entries = (
        build_runtime_probe_eval_worker_handler_entry(
            observe_runtime_probe_eval_worker_request
        ),
    )
    metaclass_keyword_entries = (
        build_runtime_probe_metaclass_keyword_worker_handler_entry(
            observe_runtime_probe_metaclass_keyword_worker_request
        ),
    )
    return (
        *dynamic_import_entries,
        *reflective_hasattr_entries,
        *reflective_getattr_entries,
        *reflective_getattr_default_entries,
        *reflective_vars_entries,
        *reflective_vars_zero_entries,
        *reflective_dir_entries,
        *runtime_mutation_globals_zero_entries,
        *runtime_mutation_locals_zero_entries,
        *runtime_mutation_setattr_entries,
        *runtime_mutation_delattr_entries,
        *exec_entries,
        *eval_entries,
        *metaclass_keyword_entries,
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
    _validate_runtime_probe_reflective_hasattr_exact_replay_inputs_if_needed(
        payload.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
    _validate_runtime_probe_reflective_hasattr_exact_replay_inputs_if_needed(
        request.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject exact-hasattr requests outside approved boundary identities."""
    boundary_text = replay_fields_by_key["boundary_text"]
    if boundary_text == _REFLECTIVE_BUILTIN_HASATTR_WORKER_BOUNDARY_TEXT:
        return
    if (
        boundary_text
        == _REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT
        and _is_runtime_probe_reflective_hasattr_literal_bit_length_replay_input_pilot(
            replay_fields_by_key
        )
    ):
        return
    if (
        boundary_text
        == _REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker boundary_text must match "
            "the exact direct-literal bit_length replay identity"
        )
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


def _runtime_probe_reflective_hasattr_target_args(
    request: RuntimeProbeLocalPythonReflectiveHasattrWorkerRequest,
) -> tuple[object, ...]:
    """Return target arguments for the exact pilot, otherwise zero arguments."""
    _validate_runtime_probe_reflective_hasattr_worker_request(request)
    replay_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        request.request_replay_payload_fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_HASATTR_NAME_CONTRACT,
        _EXACT_REPLAY_HASATTR_FALSE_CONTRACT,
        _EXACT_REPLAY_HASATTR_LITERAL_CONTRACT,
    ):
        return ()

    _validate_runtime_probe_reflective_hasattr_exact_replay_inputs(
        replay_fields_by_key,
        contract=contract,
    )
    if contract is _EXACT_REPLAY_HASATTR_LITERAL_CONTRACT:
        return (1,)
    return (
        1,
        replay_fields_by_key[_REFLECTIVE_BUILTIN_HASATTR_ATTRIBUTE_NAME_REPLAY_KEY],
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
    *,
    target_args: tuple[object, ...],
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
            target(*target_args)
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
        replay_fields_by_key
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


def _validate_runtime_probe_reflective_hasattr_exact_replay_inputs_if_needed(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject drifted request replay inputs for the exact hasattr pilot."""
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_HASATTR_NAME_CONTRACT,
        _EXACT_REPLAY_HASATTR_FALSE_CONTRACT,
        _EXACT_REPLAY_HASATTR_LITERAL_CONTRACT,
    ):
        candidates = _runtime_probe_exact_replay_contract_candidates_for_replay_fields(
            replay_fields_by_key
        )
        if any(
            candidate
            in (
                _EXACT_REPLAY_HASATTR_NAME_CONTRACT,
                _EXACT_REPLAY_HASATTR_FALSE_CONTRACT,
                _EXACT_REPLAY_HASATTR_LITERAL_CONTRACT,
            )
            for candidate in candidates
        ):
            raise ValueError(
                "runtime probe reflective builtin hasattr worker exact replay "
                "inputs must match one accepted exact replay contract"
            )
        return
    _validate_runtime_probe_reflective_hasattr_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )


def _is_runtime_probe_reflective_hasattr_exact_replay_input_pilot(
    replay_fields_by_key: Mapping[str, str],
) -> bool:
    """Return whether replay identity targets an exact accepted hasattr pilot."""
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    return contract in (
        _EXACT_REPLAY_HASATTR_NAME_CONTRACT,
        _EXACT_REPLAY_HASATTR_FALSE_CONTRACT,
        _EXACT_REPLAY_HASATTR_LITERAL_CONTRACT,
    )


def _is_runtime_probe_reflective_hasattr_name_variable_replay_input_pilot(
    replay_fields_by_key: Mapping[str, str],
) -> bool:
    """Return whether replay identity targets ``hasattr(obj, name)``."""
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    return contract in (
        _EXACT_REPLAY_HASATTR_NAME_CONTRACT,
        _EXACT_REPLAY_HASATTR_FALSE_CONTRACT,
    )


def _is_runtime_probe_reflective_hasattr_literal_bit_length_replay_input_pilot(
    replay_fields_by_key: Mapping[str, str],
) -> bool:
    """Return whether replay identity targets ``hasattr(obj, "bit_length")``."""
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    return contract is _EXACT_REPLAY_HASATTR_LITERAL_CONTRACT


def _runtime_probe_worker_exact_replay_input_keys(
    contract: _RuntimeProbeExactReplayContract,
) -> frozenset[str]:
    """Return full request replay-input keys for one exact worker contract."""
    return frozenset(
        (
            *_DYNAMIC_IMPORT_REQUIRED_REPLAY_FIELD_KEYS,
            *_runtime_probe_exact_replay_payload_field_keys(contract),
        )
    )


def _runtime_probe_worker_exact_replay_payload_matches_contract(
    fields_by_key: Mapping[str, str],
    contract: _RuntimeProbeExactReplayContract,
) -> bool:
    """Return whether exact payload fields match the accepted contract values."""
    expected_fields = _runtime_probe_exact_replay_payload_fields_by_key(contract)
    return all(
        fields_by_key.get(field_key) == expected_value
        for field_key, expected_value in expected_fields.items()
    )


def _validate_runtime_probe_reflective_hasattr_exact_replay_inputs(
    fields_by_key: Mapping[str, str],
    *,
    contract: _RuntimeProbeExactReplayContract = (_EXACT_REPLAY_HASATTR_NAME_CONTRACT),
) -> None:
    """Require the exact pilot to carry only the accepted replay input pair."""
    if set(fields_by_key) != _runtime_probe_worker_exact_replay_input_keys(contract):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker exact replay inputs "
            "must contain only object_type and attribute_name"
        )
    if not _runtime_probe_worker_exact_replay_payload_matches_contract(
        fields_by_key,
        contract,
    ):
        raise ValueError(
            "runtime probe reflective builtin hasattr worker exact replay inputs "
            "must match one accepted object_type and attribute_name contract"
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
    _validate_runtime_probe_reflective_getattr_exact_replay_inputs_if_needed(
        payload.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
    _validate_runtime_probe_reflective_getattr_exact_replay_inputs_if_needed(
        request.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject exact-getattr requests outside approved boundary identities."""
    boundary_text = replay_fields_by_key["boundary_text"]
    if boundary_text == _REFLECTIVE_BUILTIN_GETATTR_WORKER_BOUNDARY_TEXT:
        return
    if (
        boundary_text
        == _REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT
        and _is_runtime_probe_reflective_getattr_literal_bit_length_replay_input_pilot(
            replay_fields_by_key
        )
    ):
        return
    if (
        boundary_text
        == _REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker boundary_text must match "
            "the exact direct-literal bit_length replay identity"
        )
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


def _runtime_probe_reflective_getattr_exact_replay_inputs(
    request: RuntimeProbeLocalPythonReflectiveGetattrWorkerRequest,
) -> Mapping[str, str] | None:
    """Return exact replay inputs for accepted getattr pilots, if present."""
    _validate_runtime_probe_reflective_getattr_worker_request(request)
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        request.request_replay_payload_fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_GETATTR_ATTRIBUTE_ERROR_CONTRACT,
        _EXACT_REPLAY_GETATTR_NAME_CONTRACT,
        _EXACT_REPLAY_GETATTR_LITERAL_CONTRACT,
    ):
        return None
    _validate_runtime_probe_reflective_getattr_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )
    return exact_fields_by_key


def _runtime_probe_reflective_getattr_target_args(
    exact_replay_inputs: Mapping[str, str] | None,
) -> tuple[object, ...]:
    """Return target arguments for exact getattr pilots, otherwise none."""
    if exact_replay_inputs is None:
        return ()
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_replay_inputs
    )
    if contract in (
        _EXACT_REPLAY_GETATTR_NAME_CONTRACT,
        _EXACT_REPLAY_GETATTR_ATTRIBUTE_ERROR_CONTRACT,
    ):
        return (
            1,
            exact_replay_inputs[_REFLECTIVE_BUILTIN_GETATTR_ATTRIBUTE_NAME_REPLAY_KEY],
        )
    if contract is not _EXACT_REPLAY_GETATTR_LITERAL_CONTRACT:
        raise ValueError(
            "runtime probe reflective builtin getattr worker exact replay inputs "
            "are unsupported"
        )
    return (1,)


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
    *,
    target_args: tuple[object, ...],
    exact_replay_inputs: Mapping[str, str] | None,
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
            target(*target_args)
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
    if (
        target_failure is not None
        and not _is_runtime_probe_reflective_getattr_expected_attribute_error(
            target_failure,
            capture,
            exact_replay_inputs=exact_replay_inputs,
        )
    ):
        _raise_runtime_probe_reflective_getattr_target_failure(target_failure)

    return _runtime_probe_reflective_getattr_capture_lookup_outcome(
        capture,
        exact_replay_inputs=exact_replay_inputs,
    )


def _is_runtime_probe_reflective_getattr_expected_attribute_error(
    error: BaseException,
    capture: _RuntimeProbeReflectiveGetattrCapture,
    *,
    exact_replay_inputs: Mapping[str, str] | None,
) -> bool:
    """Return whether an AttributeError is the approved exact replay outcome."""
    if not isinstance(error, AttributeError):
        return False
    if exact_replay_inputs is None:
        return False
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_replay_inputs
    )
    return contract is _EXACT_REPLAY_GETATTR_ATTRIBUTE_ERROR_CONTRACT and tuple(
        capture.captured_lookup_outcomes
    ) == (_REFLECTIVE_BUILTIN_GETATTR_WORKER_RAISED_ATTRIBUTE_ERROR,)


def _runtime_probe_reflective_getattr_capture_lookup_outcome(
    capture: _RuntimeProbeReflectiveGetattrCapture,
    *,
    exact_replay_inputs: Mapping[str, str] | None,
) -> str:
    """Return the single captured lookup outcome after validation."""
    _validate_runtime_probe_reflective_getattr_intercepted_calls(
        captured_lookup_outcomes=capture.captured_lookup_outcomes,
        captured_object_types=tuple(capture.captured_object_types),
        captured_attribute_names=tuple(capture.captured_attribute_names),
        captured_rejections=tuple(capture.captured_rejections),
        exact_replay_inputs=exact_replay_inputs,
    )
    return capture.captured_lookup_outcomes[0]


def _validate_runtime_probe_reflective_getattr_intercepted_calls(
    *,
    captured_lookup_outcomes: list[str],
    captured_object_types: tuple[str, ...],
    captured_attribute_names: tuple[str, ...],
    captured_rejections: tuple[str, ...],
    exact_replay_inputs: Mapping[str, str] | None,
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
    if len(captured_object_types) != 1 or len(captured_attribute_names) != 1:
        raise ValueError(
            "runtime probe reflective builtin getattr worker target must capture "
            "exactly one getattr call"
        )
    if exact_replay_inputs is None:
        return
    if (
        captured_object_types[0]
        != exact_replay_inputs[_REFLECTIVE_BUILTIN_GETATTR_OBJECT_TYPE_REPLAY_KEY]
        or captured_attribute_names[0]
        != exact_replay_inputs[_REFLECTIVE_BUILTIN_GETATTR_ATTRIBUTE_NAME_REPLAY_KEY]
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker exact replay inputs "
            "must match captured object_type and attribute_name"
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
    *,
    target_args: tuple[object, ...],
    exact_replay_inputs: Mapping[str, str] | None,
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
            target(*target_args)
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

    return _runtime_probe_reflective_getattr_default_capture_lookup_outcome(
        capture,
        exact_replay_inputs=exact_replay_inputs,
    )


def _runtime_probe_reflective_getattr_default_capture_lookup_outcome(
    capture: _RuntimeProbeReflectiveGetattrDefaultCapture,
    *,
    exact_replay_inputs: Mapping[str, str] | None,
) -> str:
    """Return the single captured lookup outcome after validation."""
    _validate_runtime_probe_reflective_getattr_default_intercepted_calls(
        captured_lookup_outcomes=capture.captured_lookup_outcomes,
        captured_object_types=tuple(capture.captured_object_types),
        captured_attribute_names=tuple(capture.captured_attribute_names),
        captured_rejections=tuple(capture.captured_rejections),
        exact_replay_inputs=exact_replay_inputs,
    )
    return capture.captured_lookup_outcomes[0]


def _validate_runtime_probe_reflective_getattr_default_intercepted_calls(
    *,
    captured_lookup_outcomes: list[str],
    captured_object_types: tuple[str, ...],
    captured_attribute_names: tuple[str, ...],
    captured_rejections: tuple[str, ...],
    exact_replay_inputs: Mapping[str, str] | None,
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
    if len(captured_object_types) != 1 or len(captured_attribute_names) != 1:
        raise ValueError(
            "runtime probe reflective builtin getattr default worker target must "
            "capture exactly one getattr call"
        )
    if exact_replay_inputs is None:
        return
    if (
        captured_object_types[0]
        != exact_replay_inputs[_REFLECTIVE_BUILTIN_GETATTR_OBJECT_TYPE_REPLAY_KEY]
        or captured_attribute_names[0]
        != exact_replay_inputs[_REFLECTIVE_BUILTIN_GETATTR_ATTRIBUTE_NAME_REPLAY_KEY]
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker exact replay "
            "inputs must match captured object_type and attribute_name"
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
    *,
    target_args: tuple[object, ...],
    exact_replay_inputs: Mapping[str, str] | None,
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
            target(*target_args)
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
    if (
        target_failure is not None
        and not _is_runtime_probe_reflective_vars_expected_type_error(
            target_failure,
            capture,
            exact_replay_inputs=exact_replay_inputs,
        )
    ):
        _raise_runtime_probe_reflective_vars_target_failure(target_failure)

    return _runtime_probe_reflective_vars_capture_lookup_outcome(
        capture,
        exact_replay_inputs=exact_replay_inputs,
    )


def _runtime_probe_reflective_vars_exact_replay_inputs(
    request: RuntimeProbeLocalPythonReflectiveVarsWorkerRequest,
) -> Mapping[str, str] | None:
    """Return exact replay inputs for accepted vars pilots, if present."""
    _validate_runtime_probe_reflective_vars_worker_request(request)
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        request.request_replay_payload_fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_VARS_TYPE_ERROR_CONTRACT,
        _EXACT_REPLAY_VARS_RETURNED_NAMESPACE_CONTRACT,
    ):
        return None
    _validate_runtime_probe_reflective_vars_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )
    return exact_fields_by_key


def _runtime_probe_reflective_vars_target_args(
    source_module: ModuleType,
    exact_replay_inputs: Mapping[str, str] | None,
) -> tuple[object, ...]:
    """Return target arguments for exact vars pilots, otherwise none."""
    if exact_replay_inputs is None:
        return ()
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_replay_inputs
    )
    if contract is _EXACT_REPLAY_VARS_TYPE_ERROR_CONTRACT:
        _validate_runtime_probe_reflective_vars_exact_replay_inputs(
            exact_replay_inputs,
            contract=contract,
        )
        return (1,)
    if contract is _EXACT_REPLAY_VARS_RETURNED_NAMESPACE_CONTRACT:
        _validate_runtime_probe_reflective_vars_exact_replay_inputs(
            exact_replay_inputs,
            contract=contract,
        )
        return (_runtime_probe_reflective_vars_exact_probe_record(source_module),)
    raise ValueError(
        "runtime probe reflective builtin vars worker exact replay inputs are "
        "unsupported"
    )


def _runtime_probe_reflective_vars_exact_probe_record(
    source_module: ModuleType,
) -> object:
    """Instantiate the accepted vars returned-namespace replay object."""
    if source_module.__name__ != "main":
        raise ValueError(
            "runtime probe reflective builtin vars worker exact replay source "
            "module is unsupported"
        )
    probe_record_class = source_module.__dict__.get(
        _REFLECTIVE_BUILTIN_VARS_PROBE_RECORD_CLASS_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if not isinstance(probe_record_class, type):
        raise ValueError(
            "runtime probe reflective builtin vars worker exact replay target "
            "class is unsupported"
        )
    try:
        probe_record = probe_record_class(_REFLECTIVE_BUILTIN_VARS_PROBE_RECORD_LABEL)
    except Exception as error:
        raise ValueError(
            "runtime probe reflective builtin vars worker exact replay target "
            "construction failed"
        ) from error
    if (
        _runtime_probe_worker_object_type_name(probe_record)
        != _REFLECTIVE_BUILTIN_VARS_RETURNED_NAMESPACE_OBJECT_TYPE
    ):
        raise ValueError(
            "runtime probe reflective builtin vars worker exact replay target "
            "object type is unsupported"
        )
    return probe_record


def _is_runtime_probe_reflective_vars_expected_type_error(
    error: BaseException,
    capture: _RuntimeProbeReflectiveVarsCapture,
    *,
    exact_replay_inputs: Mapping[str, str] | None,
) -> bool:
    """Return whether a TypeError is the approved exact replay outcome."""
    if not isinstance(error, TypeError):
        return False
    if exact_replay_inputs is None:
        return False
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_replay_inputs
    )
    return contract is _EXACT_REPLAY_VARS_TYPE_ERROR_CONTRACT and tuple(
        capture.captured_lookup_outcomes
    ) == (_REFLECTIVE_BUILTIN_VARS_WORKER_RAISED_TYPE_ERROR,)


def _runtime_probe_reflective_vars_capture_lookup_outcome(
    capture: _RuntimeProbeReflectiveVarsCapture,
    *,
    exact_replay_inputs: Mapping[str, str] | None,
) -> str:
    """Return the single captured vars lookup outcome after validation."""
    _validate_runtime_probe_reflective_vars_intercepted_calls(
        captured_lookup_outcomes=capture.captured_lookup_outcomes,
        captured_object_types=tuple(capture.captured_object_types),
        captured_rejections=tuple(capture.captured_rejections),
        exact_replay_inputs=exact_replay_inputs,
    )
    return capture.captured_lookup_outcomes[0]


def _validate_runtime_probe_reflective_vars_intercepted_calls(
    *,
    captured_lookup_outcomes: list[str],
    captured_object_types: tuple[str, ...],
    captured_rejections: tuple[str, ...],
    exact_replay_inputs: Mapping[str, str] | None,
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
    if exact_replay_inputs is None:
        return
    if len(captured_object_types) != 1:
        raise ValueError(
            "runtime probe reflective builtin vars worker target must capture "
            "exactly one vars call"
        )
    if (
        captured_object_types[0]
        != exact_replay_inputs[_REFLECTIVE_BUILTIN_VARS_OBJECT_TYPE_REPLAY_KEY]
    ):
        raise ValueError(
            "runtime probe reflective builtin vars worker exact replay inputs "
            "must match captured object_type"
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


def _runtime_probe_reflective_dir_captured_listing_entry_count(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonReflectiveDirTargetCallable,
    *,
    form_label: str,
    target_args: tuple[object, ...],
    exact_replay_inputs: Mapping[str, str] | None,
) -> int:
    """Run a target while capturing one exact selected ``dir`` call."""
    _validate_runtime_probe_reflective_dir_source_global_absent(source_module)
    _validate_runtime_probe_reflective_dir_form_label(form_label)
    original_dir: Callable[..., list[str]] = builtins.dir
    capture = _RuntimeProbeReflectiveDirCapture(
        expected_form_label=form_label,
        original_dir=original_dir,
    )
    controlled_dir: Callable[..., object] = capture.dir
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME] = controlled_dir
        try:
            sys.stdout = shielded_stdout
            sys.stderr = shielded_stderr
            target(*target_args)
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_reflective_dir_builtin(
        expected_dir=controlled_dir,
        original_dir=original_dir,
    )
    source_restore_failure = _restore_runtime_probe_reflective_dir_source_global(
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
        _raise_runtime_probe_reflective_dir_target_failure(target_failure)

    return _runtime_probe_reflective_dir_capture_listing_entry_count(
        capture,
        exact_replay_inputs=exact_replay_inputs,
    )


def _runtime_probe_reflective_dir_capture_listing_entry_count(
    capture: _RuntimeProbeReflectiveDirCapture,
    *,
    exact_replay_inputs: Mapping[str, str] | None,
) -> int:
    """Return the single captured dir listing count after validation."""
    _validate_runtime_probe_reflective_dir_intercepted_calls(
        captured_listings=capture.captured_listings,
        captured_object_types=tuple(capture.captured_object_types),
        captured_rejections=tuple(capture.captured_rejections),
        exact_replay_inputs=exact_replay_inputs,
    )
    return len(capture.captured_listings[0])


def _validate_runtime_probe_reflective_dir_intercepted_calls(
    *,
    captured_listings: list[tuple[str, ...]],
    captured_object_types: tuple[str, ...],
    captured_rejections: tuple[str, ...],
    exact_replay_inputs: Mapping[str, str] | None,
) -> None:
    """Reject intercepted dir behavior outside the exact one-argument form."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe reflective builtin dir worker form must be exactly dir(obj)"
        )
    if len(captured_listings) != 1:
        raise ValueError(
            "runtime probe reflective builtin dir worker target must capture "
            "exactly one dir call"
        )
    if exact_replay_inputs is None:
        return
    if len(captured_object_types) != 1:
        raise ValueError(
            "runtime probe reflective builtin dir worker target must capture "
            "exactly one dir call"
        )
    if (
        captured_object_types[0]
        != exact_replay_inputs[_REFLECTIVE_BUILTIN_DIR_OBJECT_TYPE_REPLAY_KEY]
    ):
        raise ValueError(
            "runtime probe reflective builtin dir worker exact replay inputs "
            "must match captured object_type"
        )


def _raise_runtime_probe_reflective_dir_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _REFLECTIVE_BUILTIN_DIR_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _REFLECTIVE_BUILTIN_DIR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_reflective_dir_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``dir`` global resolution."""
    if (
        source_module.__dict__.get(
            _REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe reflective builtin dir worker target module dir global "
            "must be absent"
        )


def _restore_runtime_probe_reflective_dir_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``dir`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe reflective builtin dir worker target module dir global "
            "could not be restored"
        )
    if (
        module_globals.get(
            _REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe reflective builtin dir worker target module dir global "
            "could not be restored"
        )
    return ValueError(
        "runtime probe reflective builtin dir worker target module dir global "
        "changed during execution"
    )


def _restore_runtime_probe_reflective_dir_builtin(
    *,
    expected_dir: object,
    original_dir: Callable[..., list[str]],
) -> ValueError | None:
    """Restore builtins.dir and report target-time hook drift."""
    current_dir = builtins.__dict__.get(
        _REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_dir is not expected_dir:
        restore_failure = ValueError(
            "runtime probe reflective builtin dir worker builtins.dir changed "
            "during execution"
        )
    try:
        builtins.__dict__[_REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME] = original_dir
    except Exception:
        return ValueError(
            "runtime probe reflective builtin dir worker builtins.dir could not "
            "be restored"
        )
    if (
        builtins.__dict__.get(
            _REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_dir
    ):
        return ValueError(
            "runtime probe reflective builtin dir worker builtins.dir could not "
            "be restored"
        )
    return restore_failure


def _runtime_probe_runtime_mutation_globals_zero_captured_lookup_outcome(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroTargetCallable,
) -> str:
    """Run a target while capturing one exact ``globals()`` call."""
    _validate_runtime_probe_runtime_mutation_globals_zero_source_global_absent(
        source_module
    )
    original_globals: Callable[..., dict[str, object]] = builtins.globals
    capture = _RuntimeProbeRuntimeMutationGlobalsZeroCapture()
    controlled_globals: Callable[..., object] = capture.globals
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME] = (
            controlled_globals
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
    builtin_restore_failure = (
        _restore_runtime_probe_runtime_mutation_globals_zero_builtin(
            expected_globals=controlled_globals,
            original_globals=original_globals,
        )
    )
    source_restore_failure = (
        _restore_runtime_probe_runtime_mutation_globals_zero_source_global(
            source_module
        )
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
        _raise_runtime_probe_runtime_mutation_globals_zero_target_failure(
            target_failure
        )

    return _runtime_probe_runtime_mutation_globals_zero_capture_lookup_outcome(capture)


def _runtime_probe_runtime_mutation_globals_zero_capture_lookup_outcome(
    capture: _RuntimeProbeRuntimeMutationGlobalsZeroCapture,
) -> str:
    """Return the single captured globals/0 lookup outcome after validation."""
    _validate_runtime_probe_runtime_mutation_globals_zero_intercepted_calls(
        captured_lookup_outcomes=capture.captured_lookup_outcomes,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_lookup_outcomes[0]


def _validate_runtime_probe_runtime_mutation_globals_zero_intercepted_calls(
    *,
    captured_lookup_outcomes: list[str],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted globals behavior outside the exact zero-argument form."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker form must be "
            "exactly globals()"
        )
    if len(captured_lookup_outcomes) != 1:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker target must capture "
            "exactly one globals call"
        )


def _raise_runtime_probe_runtime_mutation_globals_zero_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_runtime_mutation_globals_zero_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``globals`` global resolution."""
    if (
        source_module.__dict__.get(
            _RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker target module "
            "globals global must be absent"
        )


def _restore_runtime_probe_runtime_mutation_globals_zero_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``globals`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe runtime mutation globals zero worker target module "
            "globals global could not be restored"
        )
    if (
        module_globals.get(
            _RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe runtime mutation globals zero worker target module "
            "globals global could not be restored"
        )
    return ValueError(
        "runtime probe runtime mutation globals zero worker target module globals "
        "global changed during execution"
    )


def _restore_runtime_probe_runtime_mutation_globals_zero_builtin(
    *,
    expected_globals: object,
    original_globals: Callable[..., dict[str, object]],
) -> ValueError | None:
    """Restore builtins.globals and report target-time hook drift."""
    current_globals = builtins.__dict__.get(
        _RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_globals is not expected_globals:
        restore_failure = ValueError(
            "runtime probe runtime mutation globals zero worker builtins.globals "
            "changed during execution"
        )
    try:
        builtins.__dict__[_RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME] = (
            original_globals
        )
    except Exception:
        return ValueError(
            "runtime probe runtime mutation globals zero worker builtins.globals "
            "could not be restored"
        )
    if (
        builtins.__dict__.get(
            _RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_globals
    ):
        return ValueError(
            "runtime probe runtime mutation globals zero worker builtins.globals "
            "could not be restored"
        )
    return restore_failure


def _runtime_probe_runtime_mutation_locals_zero_captured_lookup_outcome(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroTargetCallable,
) -> str:
    """Run a target while capturing one exact ``locals()`` call."""
    _validate_runtime_probe_runtime_mutation_locals_zero_source_global_absent(
        source_module
    )
    original_locals: Callable[..., dict[str, object]] = builtins.locals
    capture = _RuntimeProbeRuntimeMutationLocalsZeroCapture()
    controlled_locals: Callable[..., object] = capture.locals
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME] = (
            controlled_locals
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
    builtin_restore_failure = (
        _restore_runtime_probe_runtime_mutation_locals_zero_builtin(
            expected_locals=controlled_locals,
            original_locals=original_locals,
        )
    )
    source_restore_failure = (
        _restore_runtime_probe_runtime_mutation_locals_zero_source_global(source_module)
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
        _raise_runtime_probe_runtime_mutation_locals_zero_target_failure(target_failure)

    return _runtime_probe_runtime_mutation_locals_zero_capture_lookup_outcome(capture)


def _runtime_probe_runtime_mutation_locals_zero_capture_lookup_outcome(
    capture: _RuntimeProbeRuntimeMutationLocalsZeroCapture,
) -> str:
    """Return the single captured locals/0 lookup outcome after validation."""
    _validate_runtime_probe_runtime_mutation_locals_zero_intercepted_calls(
        captured_lookup_outcomes=capture.captured_lookup_outcomes,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_lookup_outcomes[0]


def _validate_runtime_probe_runtime_mutation_locals_zero_intercepted_calls(
    *,
    captured_lookup_outcomes: list[str],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted locals behavior outside the exact zero-argument form."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker form must be "
            "exactly locals()"
        )
    if len(captured_lookup_outcomes) != 1:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker target must capture "
            "exactly one locals call"
        )


def _raise_runtime_probe_runtime_mutation_locals_zero_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _RUNTIME_MUTATION_LOCALS_ZERO_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _RUNTIME_MUTATION_LOCALS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_runtime_mutation_locals_zero_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``locals`` global resolution."""
    if (
        source_module.__dict__.get(
            _RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe runtime mutation locals zero worker target module "
            "locals global must be absent"
        )


def _restore_runtime_probe_runtime_mutation_locals_zero_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``locals`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe runtime mutation locals zero worker target module "
            "locals global could not be restored"
        )
    if (
        module_globals.get(
            _RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe runtime mutation locals zero worker target module "
            "locals global could not be restored"
        )
    return ValueError(
        "runtime probe runtime mutation locals zero worker target module locals "
        "global changed during execution"
    )


def _restore_runtime_probe_runtime_mutation_locals_zero_builtin(
    *,
    expected_locals: object,
    original_locals: Callable[..., dict[str, object]],
) -> ValueError | None:
    """Restore builtins.locals and report target-time hook drift."""
    current_locals = builtins.__dict__.get(
        _RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_locals is not expected_locals:
        restore_failure = ValueError(
            "runtime probe runtime mutation locals zero worker builtins.locals "
            "changed during execution"
        )
    try:
        builtins.__dict__[_RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME] = original_locals
    except Exception:
        return ValueError(
            "runtime probe runtime mutation locals zero worker builtins.locals "
            "could not be restored"
        )
    if (
        builtins.__dict__.get(
            _RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_locals
    ):
        return ValueError(
            "runtime probe runtime mutation locals zero worker builtins.locals "
            "could not be restored"
        )
    return restore_failure


def _runtime_probe_runtime_mutation_setattr_captured_outcome(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonRuntimeMutationSetattrTargetCallable,
    *,
    target_args: tuple[object, ...],
    exact_replay_inputs: Mapping[str, str] | None,
) -> str:
    """Run a target while capturing one exact ``setattr`` mutation."""
    _validate_runtime_probe_runtime_mutation_setattr_source_global_absent(source_module)
    original_setattr: Callable[[object, str, object], object] = builtins.setattr
    capture = _RuntimeProbeRuntimeMutationSetattrCapture(
        original_setattr=original_setattr
    )
    controlled_setattr: Callable[..., None] = capture.setattr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME] = (
            controlled_setattr
        )
        try:
            sys.stdout = shielded_stdout
            sys.stderr = shielded_stderr
            target(*target_args)
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_runtime_mutation_setattr_builtin(
        expected_setattr=controlled_setattr,
        original_setattr=original_setattr,
    )
    source_restore_failure = (
        _restore_runtime_probe_runtime_mutation_setattr_source_global(source_module)
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
        _raise_runtime_probe_runtime_mutation_setattr_target_failure(target_failure)

    return _runtime_probe_runtime_mutation_setattr_capture_outcome(
        capture,
        exact_replay_inputs=exact_replay_inputs,
    )


def _runtime_probe_runtime_mutation_setattr_capture_outcome(
    capture: _RuntimeProbeRuntimeMutationSetattrCapture,
    *,
    exact_replay_inputs: Mapping[str, str] | None,
) -> str:
    """Return the single captured setattr mutation outcome after validation."""
    _validate_runtime_probe_runtime_mutation_setattr_intercepted_calls(
        captured_mutation_outcomes=capture.captured_mutation_outcomes,
        captured_objects=tuple(capture.captured_objects),
        captured_object_types=tuple(capture.captured_object_types),
        captured_attribute_names=tuple(capture.captured_attribute_names),
        captured_assigned_value_types=tuple(capture.captured_assigned_value_types),
        captured_assigned_value_literals=tuple(
            capture.captured_assigned_value_literals
        ),
        captured_rejections=tuple(capture.captured_rejections),
        exact_replay_inputs=exact_replay_inputs,
    )
    return capture.captured_mutation_outcomes[0]


def _validate_runtime_probe_runtime_mutation_setattr_intercepted_calls(
    *,
    captured_mutation_outcomes: list[str],
    captured_objects: tuple[object, ...],
    captured_object_types: tuple[str, ...],
    captured_attribute_names: tuple[str, ...],
    captured_assigned_value_types: tuple[str, ...],
    captured_assigned_value_literals: tuple[str, ...],
    captured_rejections: tuple[str, ...],
    exact_replay_inputs: Mapping[str, str] | None,
) -> None:
    """Reject intercepted setattr behavior outside exact successful assignment."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe runtime mutation setattr worker form must be exactly "
            "setattr(obj, name, value)"
        )
    if "name" in captured_rejections:
        raise ValueError(
            "runtime probe runtime mutation setattr worker attribute name must be "
            "a string"
        )
    if "mutation" in captured_rejections:
        raise ValueError(_RUNTIME_MUTATION_SETATTR_WORKER_MUTATION_FAILED_MESSAGE)
    if len(captured_mutation_outcomes) != 1:
        raise ValueError(
            "runtime probe runtime mutation setattr worker target must capture "
            "exactly one setattr call"
        )
    if (
        len(captured_objects) != 1
        or len(captured_object_types) != 1
        or len(captured_attribute_names) != 1
        or len(captured_assigned_value_types) != 1
        or len(captured_assigned_value_literals) != 1
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker target must capture "
            "exactly one setattr call"
        )
    if exact_replay_inputs is None:
        return
    expected_object_type = exact_replay_inputs[
        _RUNTIME_MUTATION_SETATTR_OBJECT_TYPE_REPLAY_KEY
    ]
    expected_attribute_name = exact_replay_inputs[
        _RUNTIME_MUTATION_SETATTR_ATTRIBUTE_NAME_REPLAY_KEY
    ]
    expected_assigned_value_type = exact_replay_inputs[
        _RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_TYPE_REPLAY_KEY
    ]
    expected_assigned_value_literal = exact_replay_inputs[
        _RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_LITERAL_REPLAY_KEY
    ]
    if (
        captured_object_types[0] != expected_object_type
        or captured_attribute_names[0] != expected_attribute_name
        or captured_assigned_value_types[0] != expected_assigned_value_type
        or captured_assigned_value_literals[0] != expected_assigned_value_literal
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker exact replay inputs "
            "must match captured object_type attribute_name assigned_value_type "
            "and assigned_value_literal"
        )
    try:
        assigned_attribute_value = getattr(
            captured_objects[0],
            expected_attribute_name,
        )
    except AttributeError as error:
        raise ValueError(
            "runtime probe runtime mutation setattr worker exact replay must assign "
            "flag=ready"
        ) from error
    if assigned_attribute_value != expected_assigned_value_literal:
        raise ValueError(
            "runtime probe runtime mutation setattr worker exact replay must assign "
            "flag=ready"
        )


def _raise_runtime_probe_runtime_mutation_setattr_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _RUNTIME_MUTATION_SETATTR_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _RUNTIME_MUTATION_SETATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_runtime_mutation_setattr_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``setattr`` global resolution."""
    if (
        source_module.__dict__.get(
            _RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker target module "
            "setattr global must be absent"
        )


def _restore_runtime_probe_runtime_mutation_setattr_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``setattr`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe runtime mutation setattr worker target module setattr "
            "global could not be restored"
        )
    if (
        module_globals.get(
            _RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe runtime mutation setattr worker target module setattr "
            "global could not be restored"
        )
    return ValueError(
        "runtime probe runtime mutation setattr worker target module setattr "
        "global changed during execution"
    )


def _restore_runtime_probe_runtime_mutation_setattr_builtin(
    *,
    expected_setattr: object,
    original_setattr: Callable[[object, str, object], object],
) -> ValueError | None:
    """Restore builtins.setattr and report target-time hook drift."""
    current_setattr = builtins.__dict__.get(
        _RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_setattr is not expected_setattr:
        restore_failure = ValueError(
            "runtime probe runtime mutation setattr worker builtins.setattr "
            "changed during execution"
        )
    try:
        builtins.__dict__[_RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME] = (
            original_setattr
        )
    except Exception:
        return ValueError(
            "runtime probe runtime mutation setattr worker builtins.setattr "
            "could not be restored"
        )
    if (
        builtins.__dict__.get(
            _RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_setattr
    ):
        return ValueError(
            "runtime probe runtime mutation setattr worker builtins.setattr "
            "could not be restored"
        )
    return restore_failure


def _runtime_probe_runtime_mutation_delattr_captured_outcome(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonRuntimeMutationDelattrTargetCallable,
    *,
    target_args: tuple[object, ...],
    exact_replay_inputs: Mapping[str, str] | None,
) -> str:
    """Run a target while capturing one exact ``delattr`` deletion."""
    _validate_runtime_probe_runtime_mutation_delattr_source_global_absent(source_module)
    original_delattr: Callable[[object, str], None] = builtins.delattr
    capture = _RuntimeProbeRuntimeMutationDelattrCapture(
        original_delattr=original_delattr
    )
    controlled_delattr: Callable[..., None] = capture.delattr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME] = (
            controlled_delattr
        )
        try:
            sys.stdout = shielded_stdout
            sys.stderr = shielded_stderr
            target(*target_args)
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_runtime_mutation_delattr_builtin(
        expected_delattr=controlled_delattr,
        original_delattr=original_delattr,
    )
    source_restore_failure = (
        _restore_runtime_probe_runtime_mutation_delattr_source_global(source_module)
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
        _raise_runtime_probe_runtime_mutation_delattr_target_failure(target_failure)

    return _runtime_probe_runtime_mutation_delattr_capture_outcome(
        capture,
        exact_replay_inputs=exact_replay_inputs,
    )


def _runtime_probe_runtime_mutation_delattr_capture_outcome(
    capture: _RuntimeProbeRuntimeMutationDelattrCapture,
    *,
    exact_replay_inputs: Mapping[str, str] | None,
) -> str:
    """Return the single captured delattr mutation outcome after validation."""
    _validate_runtime_probe_runtime_mutation_delattr_intercepted_calls(
        captured_mutation_outcomes=capture.captured_mutation_outcomes,
        captured_object_types=tuple(capture.captured_object_types),
        captured_attribute_names=tuple(capture.captured_attribute_names),
        captured_rejections=tuple(capture.captured_rejections),
        exact_replay_inputs=exact_replay_inputs,
    )
    return capture.captured_mutation_outcomes[0]


def _validate_runtime_probe_runtime_mutation_delattr_intercepted_calls(
    *,
    captured_mutation_outcomes: list[str],
    captured_object_types: tuple[str, ...],
    captured_attribute_names: tuple[str, ...],
    captured_rejections: tuple[str, ...],
    exact_replay_inputs: Mapping[str, str] | None,
) -> None:
    """Reject intercepted delattr behavior outside exact successful deletion."""
    if "arity" in captured_rejections:
        raise ValueError(
            "runtime probe runtime mutation delattr worker form must be exactly "
            "delattr(obj, name)"
        )
    if "name" in captured_rejections:
        raise ValueError(
            "runtime probe runtime mutation delattr worker attribute name must be "
            "a string"
        )
    if "deletion" in captured_rejections:
        raise ValueError(_RUNTIME_MUTATION_DELATTR_WORKER_DELETION_FAILED_MESSAGE)
    if len(captured_mutation_outcomes) != 1:
        raise ValueError(
            "runtime probe runtime mutation delattr worker target must capture "
            "exactly one delattr call"
        )
    if len(captured_object_types) != 1 or len(captured_attribute_names) != 1:
        raise ValueError(
            "runtime probe runtime mutation delattr worker target must capture "
            "exactly one delattr call"
        )
    if exact_replay_inputs is None:
        return
    if (
        captured_object_types[0]
        != exact_replay_inputs[_RUNTIME_MUTATION_DELATTR_OBJECT_TYPE_REPLAY_KEY]
        or captured_attribute_names[0]
        != exact_replay_inputs[_RUNTIME_MUTATION_DELATTR_ATTRIBUTE_NAME_REPLAY_KEY]
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker exact replay inputs "
            "must match captured object_type and attribute_name"
        )


def _raise_runtime_probe_runtime_mutation_delattr_target_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _RUNTIME_MUTATION_DELATTR_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _RUNTIME_MUTATION_DELATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_runtime_mutation_delattr_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``delattr`` global resolution."""
    if (
        source_module.__dict__.get(
            _RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker target module "
            "delattr global must be absent"
        )


def _restore_runtime_probe_runtime_mutation_delattr_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``delattr`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe runtime mutation delattr worker target module delattr "
            "global could not be restored"
        )
    if (
        module_globals.get(
            _RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe runtime mutation delattr worker target module delattr "
            "global could not be restored"
        )
    return ValueError(
        "runtime probe runtime mutation delattr worker target module delattr "
        "global changed during execution"
    )


def _restore_runtime_probe_runtime_mutation_delattr_builtin(
    *,
    expected_delattr: object,
    original_delattr: Callable[[object, str], None],
) -> ValueError | None:
    """Restore builtins.delattr and report target-time hook drift."""
    current_delattr = builtins.__dict__.get(
        _RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_delattr is not expected_delattr:
        restore_failure = ValueError(
            "runtime probe runtime mutation delattr worker builtins.delattr "
            "changed during execution"
        )
    try:
        builtins.__dict__[_RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME] = (
            original_delattr
        )
    except Exception:
        return ValueError(
            "runtime probe runtime mutation delattr worker builtins.delattr "
            "could not be restored"
        )
    if (
        builtins.__dict__.get(
            _RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_delattr
    ):
        return ValueError(
            "runtime probe runtime mutation delattr worker builtins.delattr "
            "could not be restored"
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
        replay_fields_by_key
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


def _validate_runtime_probe_reflective_getattr_exact_replay_inputs_if_needed(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject drifted request replay inputs for exact getattr pilots."""
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_GETATTR_ATTRIBUTE_ERROR_CONTRACT,
        _EXACT_REPLAY_GETATTR_NAME_CONTRACT,
        _EXACT_REPLAY_GETATTR_LITERAL_CONTRACT,
    ):
        candidates = _runtime_probe_exact_replay_contract_candidates_for_replay_fields(
            replay_fields_by_key
        )
        if any(
            candidate
            in (
                _EXACT_REPLAY_GETATTR_ATTRIBUTE_ERROR_CONTRACT,
                _EXACT_REPLAY_GETATTR_NAME_CONTRACT,
                _EXACT_REPLAY_GETATTR_LITERAL_CONTRACT,
            )
            for candidate in candidates
        ):
            raise ValueError(
                "runtime probe reflective builtin getattr worker exact replay "
                "inputs must match one accepted exact replay contract"
            )
        return
    _validate_runtime_probe_reflective_getattr_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )


def _is_runtime_probe_reflective_getattr_literal_bit_length_replay_input_pilot(
    replay_fields_by_key: Mapping[str, str],
) -> bool:
    """Return whether replay identity targets ``getattr(obj, "bit_length")``."""
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    return contract is _EXACT_REPLAY_GETATTR_LITERAL_CONTRACT


def _validate_runtime_probe_reflective_getattr_exact_replay_inputs(
    fields_by_key: Mapping[str, str],
    *,
    contract: _RuntimeProbeExactReplayContract = (
        _EXACT_REPLAY_GETATTR_LITERAL_CONTRACT
    ),
) -> None:
    """Require exact getattr pilots to carry only the accepted replay pair."""
    if set(fields_by_key) != _runtime_probe_worker_exact_replay_input_keys(contract):
        raise ValueError(
            "runtime probe reflective builtin getattr worker exact replay inputs "
            "must contain only object_type and attribute_name"
        )
    if not _runtime_probe_worker_exact_replay_payload_matches_contract(
        fields_by_key,
        contract,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr worker exact replay inputs "
            "must match one accepted object_type and attribute_name contract"
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
    _validate_runtime_probe_reflective_getattr_default_exact_replay_inputs_if_needed(
        payload.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
    _validate_runtime_probe_reflective_getattr_default_exact_replay_inputs_if_needed(
        request.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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


def _runtime_probe_reflective_getattr_default_exact_replay_inputs(
    request: RuntimeProbeLocalPythonReflectiveGetattrDefaultWorkerRequest,
) -> Mapping[str, str] | None:
    """Return exact replay inputs for accepted getattr/3 pilots, if present."""
    _validate_runtime_probe_reflective_getattr_default_worker_request(request)
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        request.request_replay_payload_fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_GETATTR_DEFAULT_MISSING_CONTRACT,
        _EXACT_REPLAY_GETATTR_DEFAULT_VALUE_CONTRACT,
    ):
        return None
    _validate_runtime_probe_reflective_getattr_default_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )
    return exact_fields_by_key


def _runtime_probe_reflective_getattr_default_target_args(
    exact_replay_inputs: Mapping[str, str] | None,
) -> tuple[object, ...]:
    """Return target arguments for exact getattr/3 pilots, otherwise none."""
    if exact_replay_inputs is None:
        return ()
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_replay_inputs
    )
    if contract not in (
        _EXACT_REPLAY_GETATTR_DEFAULT_MISSING_CONTRACT,
        _EXACT_REPLAY_GETATTR_DEFAULT_VALUE_CONTRACT,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker exact replay "
            "inputs are unsupported"
        )
    return (
        1,
        exact_replay_inputs[_REFLECTIVE_BUILTIN_GETATTR_ATTRIBUTE_NAME_REPLAY_KEY],
        object(),
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


def _validate_runtime_probe_reflective_getattr_default_exact_replay_inputs_if_needed(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject drifted request replay inputs for exact getattr/3 pilots."""
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_fields_by_key
    )
    accepted_contracts = (
        _EXACT_REPLAY_GETATTR_DEFAULT_MISSING_CONTRACT,
        _EXACT_REPLAY_GETATTR_DEFAULT_VALUE_CONTRACT,
    )
    if contract not in accepted_contracts:
        candidates = _runtime_probe_exact_replay_contract_candidates_for_replay_fields(
            replay_fields_by_key
        )
        if any(candidate in accepted_contracts for candidate in candidates):
            raise ValueError(
                "runtime probe reflective builtin getattr default worker exact replay "
                "inputs must match one accepted exact replay contract"
            )
        return
    _validate_runtime_probe_reflective_getattr_default_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )


def _validate_runtime_probe_reflective_getattr_default_exact_replay_inputs(
    fields_by_key: Mapping[str, str],
    *,
    contract: _RuntimeProbeExactReplayContract = (
        _EXACT_REPLAY_GETATTR_DEFAULT_MISSING_CONTRACT
    ),
) -> None:
    """Require exact getattr/3 pilots to carry only the accepted replay pair."""
    if set(fields_by_key) != _runtime_probe_worker_exact_replay_input_keys(contract):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker exact replay "
            "inputs must contain only object_type and attribute_name"
        )
    if not _runtime_probe_worker_exact_replay_payload_matches_contract(
        fields_by_key,
        contract,
    ):
        raise ValueError(
            "runtime probe reflective builtin getattr default worker exact replay "
            "inputs must match one accepted object_type and attribute_name contract"
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
    _validate_runtime_probe_reflective_vars_exact_replay_inputs_if_needed(
        payload.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
    _validate_runtime_probe_reflective_vars_exact_replay_inputs_if_needed(
        request.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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


def _validate_runtime_probe_reflective_vars_exact_replay_inputs_if_needed(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject drifted request replay inputs for exact vars pilots."""
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_VARS_TYPE_ERROR_CONTRACT,
        _EXACT_REPLAY_VARS_RETURNED_NAMESPACE_CONTRACT,
    ):
        candidates = _runtime_probe_exact_replay_contract_candidates_for_replay_fields(
            replay_fields_by_key
        )
        if any(
            candidate
            in (
                _EXACT_REPLAY_VARS_TYPE_ERROR_CONTRACT,
                _EXACT_REPLAY_VARS_RETURNED_NAMESPACE_CONTRACT,
            )
            for candidate in candidates
        ):
            raise ValueError(
                "runtime probe reflective builtin vars worker exact replay inputs "
                "must match one accepted exact replay contract"
            )
        return
    _validate_runtime_probe_reflective_vars_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )


def _validate_runtime_probe_reflective_vars_exact_replay_inputs(
    fields_by_key: Mapping[str, str],
    *,
    contract: _RuntimeProbeExactReplayContract = (
        _EXACT_REPLAY_VARS_TYPE_ERROR_CONTRACT
    ),
) -> None:
    """Require exact vars pilots to carry only accepted object_type input."""
    if set(fields_by_key) != _runtime_probe_worker_exact_replay_input_keys(contract):
        raise ValueError(
            "runtime probe reflective builtin vars worker exact replay inputs "
            "must contain only object_type"
        )
    if not _runtime_probe_worker_exact_replay_payload_matches_contract(
        fields_by_key,
        contract,
    ):
        raise ValueError(
            "runtime probe reflective builtin vars worker exact replay inputs "
            "must match one accepted object_type contract"
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


def _validate_runtime_probe_reflective_dir_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local dir request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe reflective builtin dir worker payload must be typed"
        )
    _validate_runtime_probe_reflective_dir_payload_family_form(
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
    _validate_runtime_probe_reflective_dir_replay_metadata(
        replay_fields_by_key,
        plan_id=payload.plan_id,
        request_id=payload.request_id,
        family_label=payload.family_label,
        form_label=payload.form_label,
        replay_target_seed=payload.replay_target_seed,
        replay_selector_seed=payload.replay_selector_seed,
    )
    _validate_runtime_probe_reflective_dir_exact_replay_inputs_if_needed(
        payload.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
            "runtime probe reflective builtin dir worker invocation_identity must "
            "match payload replay identity"
        )


def _validate_runtime_probe_reflective_dir_worker_request(
    request: RuntimeProbeLocalPythonReflectiveDirWorkerRequest,
) -> None:
    """Reject exact-dir worker requests whose copied metadata drifted."""
    if not isinstance(request, RuntimeProbeLocalPythonReflectiveDirWorkerRequest):
        raise ValueError(
            "runtime probe reflective builtin dir worker request must be typed"
        )
    _validate_runtime_probe_reflective_dir_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe reflective builtin dir worker subject_kind is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin dir worker reason_code is unsupported"
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
    _validate_runtime_probe_reflective_dir_worker_request_boundary_text(
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
    _validate_runtime_probe_reflective_dir_replay_metadata(
        replay_fields_by_key,
        plan_id=request.plan_id,
        request_id=request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
    )
    _validate_runtime_probe_reflective_dir_exact_replay_inputs_if_needed(
        request.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
        _validate_runtime_probe_reflective_dir_replay_field_match(
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
            "runtime probe reflective builtin dir worker invocation_identity must "
            "match request replay identity"
        )


def _validate_runtime_probe_reflective_dir_worker_request_boundary_text(
    *,
    form_label: str,
    boundary_text: str,
) -> None:
    """Reject exact-dir requests that do not carry the approved boundary."""
    expected_boundary_text = _runtime_probe_reflective_dir_boundary_text_for_form_label(
        form_label
    )
    if boundary_text != expected_boundary_text:
        raise ValueError(
            "runtime probe reflective builtin dir worker boundary_text must be "
            f"{expected_boundary_text}"
        )


def _validate_runtime_probe_reflective_dir_worker_observer(
    observer: RuntimeProbeLocalPythonReflectiveDirWorkerObserver,
) -> None:
    """Reject non-callable exact-dir observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe reflective builtin dir worker observer must be callable"
        )


def _validate_runtime_probe_reflective_dir_target_callable(target: object) -> None:
    """Reject non-callable target injections before dir interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe reflective builtin dir worker target must be callable"
        )


def _runtime_probe_reflective_dir_exact_replay_inputs(
    request: RuntimeProbeLocalPythonReflectiveDirWorkerRequest,
) -> Mapping[str, str] | None:
    """Return exact replay inputs for the accepted int-directory pilot."""
    _validate_runtime_probe_reflective_dir_worker_request(request)
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        request.request_replay_payload_fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_fields_by_key
    )
    if contract is not _EXACT_REPLAY_DIR_INT_DIRECTORY_CONTRACT:
        return None
    _validate_runtime_probe_reflective_dir_exact_replay_inputs(
        exact_fields_by_key,
    )
    return exact_fields_by_key


def _runtime_probe_reflective_dir_target_args(
    exact_replay_inputs: Mapping[str, str] | None,
) -> tuple[object, ...]:
    """Return target arguments for the exact dir pilot, otherwise none."""
    if exact_replay_inputs is None:
        return ()
    _validate_runtime_probe_reflective_dir_exact_replay_inputs(exact_replay_inputs)
    return (1,)


def _validate_runtime_probe_reflective_dir_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonReflectiveDirReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the dir replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe reflective builtin dir replay target source module "
            "must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe reflective builtin dir replay target source module "
            "must match source_module_name"
        )


def _validate_runtime_probe_reflective_dir_worker_observation_for_request(
    observation: RuntimeProbeLocalPythonReflectiveDirWorkerObservation,
    request: RuntimeProbeLocalPythonReflectiveDirWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted dir request."""
    _validate_runtime_probe_reflective_dir_worker_request(request)
    _validate_runtime_probe_reflective_dir_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe reflective builtin dir worker observation request must "
            "match adapted request"
        )


def _validate_runtime_probe_reflective_dir_worker_observation(
    observation: RuntimeProbeLocalPythonReflectiveDirWorkerObservation,
) -> None:
    """Reject exact-dir observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonReflectiveDirWorkerObservation,
    ):
        raise ValueError(
            "runtime probe reflective builtin dir worker observation must be typed"
        )
    _validate_runtime_probe_reflective_dir_worker_request(observation.request)
    if (
        not isinstance(observation.listing_entry_count, int)
        or isinstance(observation.listing_entry_count, bool)
        or observation.listing_entry_count < 0
    ):
        raise ValueError(
            "runtime probe reflective builtin dir worker listing_entry_count "
            "must be a non-negative int"
        )
    expected_artifact_reference = (
        _runtime_probe_reflective_dir_listing_artifact_reference(
            observation.request.request_id
        )
    )
    _validate_runtime_probe_worker_durable_artifact_reference(
        observation.durable_artifact_reference
    )
    if observation.durable_artifact_reference != expected_artifact_reference:
        raise ValueError(
            "runtime probe reflective builtin dir worker durable_artifact_reference "
            "must match request"
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
        _validate_runtime_probe_reflective_dir_observation_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin dir worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_reflective_dir_replay_target(
    replay_target: RuntimeProbeLocalPythonReflectiveDirReplayTarget,
) -> None:
    """Reject non-executing dir replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonReflectiveDirReplayTarget,
    ):
        raise ValueError(
            "runtime probe reflective builtin dir replay target must be typed"
        )
    request = replay_target.request
    _validate_runtime_probe_reflective_dir_worker_request(request)
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
        _validate_runtime_probe_reflective_dir_replay_target_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe reflective builtin dir replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe reflective builtin dir replay target "
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
            "runtime probe reflective builtin dir replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_reflective_dir_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied dir replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin dir replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_dir_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied dir observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe reflective builtin dir worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_reflective_dir_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported reflective-builtin dir family/form labels."""
    if family_label is not RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin dir worker family_label is unsupported"
        )
    _validate_runtime_probe_reflective_dir_form_label(form_label)


def _validate_runtime_probe_reflective_dir_form_label(form_label: str) -> None:
    """Reject reflective-dir forms outside the selected local-Python handlers."""
    if form_label not in _REFLECTIVE_BUILTIN_DIR_WORKER_BOUNDARY_TEXT_BY_FORM_LABEL:
        raise ValueError(
            "runtime probe reflective builtin dir worker form_label is unsupported"
        )


def _runtime_probe_reflective_dir_boundary_text_for_form_label(
    form_label: str,
) -> str:
    """Return the exact source boundary for a selected reflective-dir form."""
    _validate_runtime_probe_reflective_dir_form_label(form_label)
    return _REFLECTIVE_BUILTIN_DIR_WORKER_BOUNDARY_TEXT_BY_FORM_LABEL[form_label]


def _validate_runtime_probe_reflective_dir_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-dir worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_reflective_dir_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe reflective builtin dir worker subject_kind is unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN.value
    ):
        raise ValueError(
            "runtime probe reflective builtin dir worker reason_code is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_reflective_dir_reason_code_from_replay_field(
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
    _validate_runtime_probe_reflective_dir_worker_request_boundary_text(
        form_label=form_label,
        boundary_text=replay_fields_by_key["boundary_text"],
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


def _validate_runtime_probe_reflective_dir_exact_replay_inputs_if_needed(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject drifted request replay inputs for the exact dir/1 pilot."""
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        fields,
        field_name="request_replay_payload_fields",
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        exact_fields_by_key
    )
    if contract is not _EXACT_REPLAY_DIR_INT_DIRECTORY_CONTRACT:
        candidates = _runtime_probe_exact_replay_contract_candidates_for_replay_fields(
            replay_fields_by_key
        )
        if _EXACT_REPLAY_DIR_INT_DIRECTORY_CONTRACT in candidates:
            raise ValueError(
                "runtime probe reflective builtin dir worker exact replay inputs "
                "must match the accepted int-directory replay contract"
            )
        return
    _validate_runtime_probe_reflective_dir_exact_replay_inputs(exact_fields_by_key)


def _validate_runtime_probe_reflective_dir_exact_replay_inputs(
    fields_by_key: Mapping[str, str],
) -> None:
    """Require the exact int-directory pilot to carry only object_type."""
    contract = _EXACT_REPLAY_DIR_INT_DIRECTORY_CONTRACT
    if set(fields_by_key) != _runtime_probe_worker_exact_replay_input_keys(contract):
        raise ValueError(
            "runtime probe reflective builtin dir worker exact replay inputs "
            "must contain only object_type"
        )
    if not _runtime_probe_worker_exact_replay_payload_matches_contract(
        fields_by_key,
        contract,
    ):
        raise ValueError(
            "runtime probe reflective builtin dir worker exact replay inputs "
            "must be object_type=builtins.int"
        )


def _validate_runtime_probe_reflective_dir_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-dir request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe reflective builtin dir worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_reflective_dir_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the reflective-builtin reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe reflective builtin dir worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
        raise ValueError(
            "runtime probe reflective builtin dir worker reason_code is unsupported"
        )
    return reason_code


def _runtime_probe_reflective_dir_listing_artifact_reference(request_id: str) -> str:
    """Return the deterministic durable reference for a captured dir listing."""
    _validate_runtime_probe_worker_metadata_text(request_id, field_name="request_id")
    return f"artifact://runtime-probe/dir-listing/{request_id}.json"


def _validate_runtime_probe_runtime_mutation_globals_zero_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local globals/0 request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker payload must be typed"
        )
    _validate_runtime_probe_runtime_mutation_globals_zero_payload_family_form(
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
    _validate_runtime_probe_runtime_mutation_globals_zero_replay_metadata(
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
            "runtime probe runtime mutation globals zero worker invocation_identity "
            "must match payload replay identity"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_worker_request(
    request: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest,
) -> None:
    """Reject exact-globals/0 worker requests whose copied metadata drifted."""
    if not isinstance(
        request,
        RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest,
    ):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker request must be typed"
        )
    _validate_runtime_probe_runtime_mutation_globals_zero_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker subject_kind "
            "is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker reason_code "
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
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_request_boundary_text(
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
    _validate_runtime_probe_runtime_mutation_globals_zero_replay_metadata(
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
        _validate_runtime_probe_runtime_mutation_globals_zero_replay_field_match(
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
            "runtime probe runtime mutation globals zero worker invocation_identity "
            "must match request replay identity"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_worker_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject exact-globals/0 requests that do not carry the approved boundary."""
    if boundary_text != _RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker boundary_text must be "
            f"{_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_worker_observer(
    observer: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObserver,
) -> None:
    """Reject non-callable exact-globals/0 observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker observer must "
            "be callable"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_target_callable(
    target: object,
) -> None:
    """Reject non-callable target injections before globals/0 interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker target must be callable"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the globals/0 replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe runtime mutation globals zero replay target source module "
            "must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe runtime mutation globals zero replay target source module "
            "must match source_module_name"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_observation_for_request(
    observation: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation,
    request: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted globals/0 request."""
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_request(request)
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_observation(
        observation
    )
    if observation.request != request:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker observation request "
            "must match adapted request"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_worker_observation(
    observation: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation,
) -> None:
    """Reject exact-globals/0 observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroWorkerObservation,
    ):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker observation must "
            "be typed"
        )
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_request(
        observation.request
    )
    if (
        observation.lookup_outcome
        != _RUNTIME_MUTATION_GLOBALS_WORKER_RETURNED_NAMESPACE
    ):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker lookup_outcome "
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
        _validate_runtime_probe_runtime_mutation_globals_zero_observation_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_replay_target(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroReplayTarget,
) -> None:
    """Reject non-executing globals/0 replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonRuntimeMutationGlobalsZeroReplayTarget,
    ):
        raise ValueError(
            "runtime probe runtime mutation globals zero replay target must be typed"
        )
    request = replay_target.request
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_request(request)
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
        _validate_runtime_probe_runtime_mutation_globals_zero_replay_target_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe runtime mutation globals zero replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe runtime mutation globals zero replay target "
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
            "runtime probe runtime mutation globals zero replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied globals/0 replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe runtime mutation globals zero replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied globals/0 observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported runtime-mutation globals/0 family/form labels."""
    if family_label is not RuntimeProbeFamily.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker family_label "
            "is unsupported"
        )
    if form_label != _RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker form_label "
            "is unsupported"
        )


def _validate_runtime_probe_runtime_mutation_globals_zero_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-globals/0 worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_runtime_mutation_globals_zero_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker subject_kind "
            "is unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.RUNTIME_MUTATION.value
    ):
        raise ValueError(
            "runtime probe runtime mutation globals zero worker reason_code "
            "is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_runtime_mutation_globals_zero_reason_code_from_replay_field(
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
    _validate_runtime_probe_runtime_mutation_globals_zero_worker_request_boundary_text(
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


def _validate_runtime_probe_runtime_mutation_globals_zero_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-globals/0 request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_runtime_mutation_globals_zero_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the runtime-mutation reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker reason_code "
            "is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation globals zero worker reason_code "
            "is unsupported"
        )
    return reason_code


def _validate_runtime_probe_runtime_mutation_locals_zero_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local locals/0 request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe runtime mutation locals zero worker payload must be typed"
        )
    _validate_runtime_probe_runtime_mutation_locals_zero_payload_family_form(
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
    _validate_runtime_probe_runtime_mutation_locals_zero_replay_metadata(
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
            "runtime probe runtime mutation locals zero worker invocation_identity "
            "must match payload replay identity"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_worker_request(
    request: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest,
) -> None:
    """Reject exact-locals/0 worker requests whose copied metadata drifted."""
    if not isinstance(
        request,
        RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest,
    ):
        raise ValueError(
            "runtime probe runtime mutation locals zero worker request must be typed"
        )
    _validate_runtime_probe_runtime_mutation_locals_zero_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker subject_kind "
            "is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker reason_code "
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
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_request_boundary_text(
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
    _validate_runtime_probe_runtime_mutation_locals_zero_replay_metadata(
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
        _validate_runtime_probe_runtime_mutation_locals_zero_replay_field_match(
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
            "runtime probe runtime mutation locals zero worker invocation_identity "
            "must match request replay identity"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_worker_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject exact-locals/0 requests that do not carry the approved boundary."""
    if boundary_text != _RUNTIME_MUTATION_LOCALS_ZERO_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker boundary_text must be "
            f"{_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_worker_observer(
    observer: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObserver,
) -> None:
    """Reject non-callable exact-locals/0 observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe runtime mutation locals zero worker observer must "
            "be callable"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_target_callable(
    target: object,
) -> None:
    """Reject non-callable target injections before locals/0 interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe runtime mutation locals zero worker target must be callable"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the locals/0 replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe runtime mutation locals zero replay target source module "
            "must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe runtime mutation locals zero replay target source module "
            "must match source_module_name"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_observation_for_request(
    observation: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation,
    request: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted locals/0 request."""
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_request(request)
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker observation request "
            "must match adapted request"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_worker_observation(
    observation: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation,
) -> None:
    """Reject exact-locals/0 observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonRuntimeMutationLocalsZeroWorkerObservation,
    ):
        raise ValueError(
            "runtime probe runtime mutation locals zero worker observation must "
            "be typed"
        )
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_request(
        observation.request
    )
    if observation.lookup_outcome != _RUNTIME_MUTATION_LOCALS_WORKER_RETURNED_NAMESPACE:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker lookup_outcome "
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
        _validate_runtime_probe_runtime_mutation_locals_zero_observation_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe runtime mutation locals zero worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_replay_target(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationLocalsZeroReplayTarget,
) -> None:
    """Reject non-executing locals/0 replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonRuntimeMutationLocalsZeroReplayTarget,
    ):
        raise ValueError(
            "runtime probe runtime mutation locals zero replay target must be typed"
        )
    request = replay_target.request
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_request(request)
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
        _validate_runtime_probe_runtime_mutation_locals_zero_replay_target_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe runtime mutation locals zero replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe runtime mutation locals zero replay target "
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
            "runtime probe runtime mutation locals zero replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied locals/0 replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe runtime mutation locals zero replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied locals/0 observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported runtime-mutation locals/0 family/form labels."""
    if family_label is not RuntimeProbeFamily.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker family_label "
            "is unsupported"
        )
    if form_label != _RUNTIME_MUTATION_LOCALS_ZERO_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker form_label "
            "is unsupported"
        )


def _validate_runtime_probe_runtime_mutation_locals_zero_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-locals/0 worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_runtime_mutation_locals_zero_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe runtime mutation locals zero worker subject_kind "
            "is unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.RUNTIME_MUTATION.value
    ):
        raise ValueError(
            "runtime probe runtime mutation locals zero worker reason_code "
            "is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_runtime_mutation_locals_zero_reason_code_from_replay_field(
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
    _validate_runtime_probe_runtime_mutation_locals_zero_worker_request_boundary_text(
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


def _validate_runtime_probe_runtime_mutation_locals_zero_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-locals/0 request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_runtime_mutation_locals_zero_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the runtime-mutation reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker reason_code "
            "is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation locals zero worker reason_code "
            "is unsupported"
        )
    return reason_code


def _validate_runtime_probe_runtime_mutation_setattr_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local setattr request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe runtime mutation setattr worker payload must be typed"
        )
    _validate_runtime_probe_runtime_mutation_setattr_payload_family_form(
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
    _validate_runtime_probe_runtime_mutation_setattr_replay_metadata(
        replay_fields_by_key,
        plan_id=payload.plan_id,
        request_id=payload.request_id,
        family_label=payload.family_label,
        form_label=payload.form_label,
        replay_target_seed=payload.replay_target_seed,
        replay_selector_seed=payload.replay_selector_seed,
    )
    _validate_runtime_probe_runtime_mutation_setattr_exact_replay_inputs_if_needed(
        payload.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
            "runtime probe runtime mutation setattr worker invocation_identity "
            "must match payload replay identity"
        )


def _validate_runtime_probe_runtime_mutation_setattr_worker_request(
    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest,
) -> None:
    """Reject exact-setattr worker requests whose copied metadata drifted."""
    if not isinstance(
        request,
        RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest,
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker request must be typed"
        )
    _validate_runtime_probe_runtime_mutation_setattr_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe runtime mutation setattr worker subject_kind is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation setattr worker reason_code is unsupported"
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
    _validate_runtime_probe_runtime_mutation_setattr_replay_metadata(
        replay_fields_by_key,
        plan_id=request.plan_id,
        request_id=request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
    )
    _validate_runtime_probe_runtime_mutation_setattr_exact_replay_inputs_if_needed(
        request.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
        _validate_runtime_probe_runtime_mutation_setattr_replay_field_match(
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
            "runtime probe runtime mutation setattr worker invocation_identity "
            "must match request replay identity"
        )


def _validate_runtime_probe_runtime_mutation_setattr_worker_request_boundary_text(
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject setattr requests outside approved boundary identities."""
    boundary_text = replay_fields_by_key["boundary_text"]
    if boundary_text == _RUNTIME_MUTATION_SETATTR_WORKER_BOUNDARY_TEXT:
        return
    if (
        boundary_text == _RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT
        and _is_runtime_probe_runtime_mutation_setattr_literal_flag_replay_input_pilot(
            replay_fields_by_key
        )
    ):
        return
    if boundary_text == _RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe runtime mutation setattr worker boundary_text must match "
            "the exact direct-literal flag replay identity"
        )
    raise ValueError(
        "runtime probe runtime mutation setattr worker boundary_text must be "
        f"{_RUNTIME_MUTATION_SETATTR_WORKER_BOUNDARY_TEXT}"
    )


def _validate_runtime_probe_runtime_mutation_setattr_worker_observer(
    observer: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObserver,
) -> None:
    """Reject non-callable exact-setattr observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe runtime mutation setattr worker observer must be callable"
        )


def _validate_runtime_probe_runtime_mutation_setattr_target_callable(
    target: object,
) -> None:
    """Reject non-callable target injections before setattr interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe runtime mutation setattr worker target must be callable"
        )


def _runtime_probe_runtime_mutation_setattr_exact_replay_inputs(
    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest,
) -> Mapping[str, str] | None:
    """Return exact setattr replay inputs for accepted pilots."""
    _validate_runtime_probe_runtime_mutation_setattr_worker_request(request)
    contract = _runtime_probe_runtime_mutation_setattr_exact_replay_contract(request)
    if contract is None:
        return None
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        request.request_replay_payload_fields,
        field_name="request_replay_payload_fields",
    )
    _validate_runtime_probe_runtime_mutation_setattr_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )
    return exact_fields_by_key


def _runtime_probe_runtime_mutation_setattr_exact_replay_contract(
    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest,
) -> _RuntimeProbeExactReplayContract | None:
    """Return the exact setattr replay contract for accepted worker requests."""
    _validate_runtime_probe_runtime_mutation_setattr_worker_request(request)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        request.request_replay_payload_fields
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_SETATTR_NAME_CONTRACT,
        _EXACT_REPLAY_SETATTR_LITERAL_CONTRACT,
    ):
        return None
    return contract


def _runtime_probe_runtime_mutation_setattr_target_args(
    source_module: ModuleType,
    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest,
    exact_replay_inputs: Mapping[str, str] | None,
) -> tuple[object, ...]:
    """Return target args for exact setattr pilots, otherwise none."""
    if exact_replay_inputs is None:
        return ()
    _validate_runtime_probe_runtime_mutation_setattr_worker_request(request)
    contract = _runtime_probe_runtime_mutation_setattr_exact_replay_contract(request)
    _validate_runtime_probe_runtime_mutation_setattr_exact_replay_inputs(
        exact_replay_inputs,
        contract=contract
        if contract is not None
        else _EXACT_REPLAY_SETATTR_LITERAL_CONTRACT,
    )
    probe_target = _runtime_probe_runtime_mutation_setattr_exact_probe_target(
        source_module
    )
    if contract is _EXACT_REPLAY_SETATTR_NAME_CONTRACT:
        return (
            probe_target,
            exact_replay_inputs[_RUNTIME_MUTATION_SETATTR_ATTRIBUTE_NAME_REPLAY_KEY],
            exact_replay_inputs[
                _RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_LITERAL_REPLAY_KEY
            ],
        )
    if contract is _EXACT_REPLAY_SETATTR_LITERAL_CONTRACT:
        return (
            probe_target,
            exact_replay_inputs[
                _RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_LITERAL_REPLAY_KEY
            ],
        )
    raise ValueError(
        "runtime probe runtime mutation setattr worker exact replay contract "
        "is unsupported"
    )


def _runtime_probe_runtime_mutation_setattr_exact_probe_target(
    source_module: ModuleType,
) -> object:
    """Instantiate the accepted setattr replay object."""
    if source_module.__name__ != "main":
        raise ValueError(
            "runtime probe runtime mutation setattr worker exact replay source "
            "module is unsupported"
        )
    probe_target_class = source_module.__dict__.get(
        _RUNTIME_MUTATION_SETATTR_NAME_FLAG_CLASS_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if not isinstance(probe_target_class, type):
        raise ValueError(
            "runtime probe runtime mutation setattr worker exact replay target "
            "class is unsupported"
        )
    probe_target = probe_target_class()
    if (
        _runtime_probe_worker_object_type_name(probe_target)
        != _RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_OBJECT_TYPE
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker exact replay target "
            "object type is unsupported"
        )
    return probe_target


def _validate_runtime_probe_runtime_mutation_setattr_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationSetattrReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the setattr replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe runtime mutation setattr replay target source module "
            "must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe runtime mutation setattr replay target source module "
            "must match source_module_name"
        )


def _validate_runtime_probe_runtime_mutation_setattr_observation_for_request(
    observation: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation,
    request: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted setattr request."""
    _validate_runtime_probe_runtime_mutation_setattr_worker_request(request)
    _validate_runtime_probe_runtime_mutation_setattr_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe runtime mutation setattr worker observation request "
            "must match adapted request"
        )


def _validate_runtime_probe_runtime_mutation_setattr_worker_observation(
    observation: RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation,
) -> None:
    """Reject exact-setattr observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonRuntimeMutationSetattrWorkerObservation,
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker observation must be typed"
        )
    _validate_runtime_probe_runtime_mutation_setattr_worker_request(observation.request)
    if observation.mutation_outcome != _RUNTIME_MUTATION_SETATTR_WORKER_RETURNED_NONE:
        raise ValueError(
            "runtime probe runtime mutation setattr worker mutation_outcome "
            "is unsupported"
        )
    expected_artifact_reference = (
        _runtime_probe_runtime_mutation_setattr_value_artifact_reference(
            observation.request.request_id
        )
    )
    _validate_runtime_probe_worker_durable_artifact_reference(
        observation.durable_artifact_reference
    )
    if observation.durable_artifact_reference != expected_artifact_reference:
        raise ValueError(
            "runtime probe runtime mutation setattr worker "
            "durable_artifact_reference must match request"
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
        _validate_runtime_probe_runtime_mutation_setattr_observation_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_runtime_mutation_setattr_replay_target(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationSetattrReplayTarget,
) -> None:
    """Reject non-executing setattr replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonRuntimeMutationSetattrReplayTarget,
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr replay target must be typed"
        )
    request = replay_target.request
    _validate_runtime_probe_runtime_mutation_setattr_worker_request(request)
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
        _validate_runtime_probe_runtime_mutation_setattr_replay_target_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe runtime mutation setattr replay target "
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
            "runtime probe runtime mutation setattr replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_runtime_mutation_setattr_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied setattr replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe runtime mutation setattr replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_runtime_mutation_setattr_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied setattr observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe runtime mutation setattr worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_runtime_mutation_setattr_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported runtime-mutation setattr family/form labels."""
    if family_label is not RuntimeProbeFamily.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation setattr worker family_label is unsupported"
        )
    if form_label != _RUNTIME_MUTATION_SETATTR_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe runtime mutation setattr worker form_label is unsupported"
        )


def _validate_runtime_probe_runtime_mutation_setattr_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-setattr worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_runtime_mutation_setattr_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker subject_kind is unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.RUNTIME_MUTATION.value
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker reason_code is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_runtime_mutation_setattr_reason_code_from_replay_field(
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
    _validate_runtime_probe_runtime_mutation_setattr_worker_request_boundary_text(
        replay_fields_by_key
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


def _validate_runtime_probe_runtime_mutation_setattr_exact_replay_inputs_if_needed(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject drifted replay inputs for exact setattr pilots."""
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_SETATTR_NAME_CONTRACT,
        _EXACT_REPLAY_SETATTR_LITERAL_CONTRACT,
    ):
        return
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        fields,
        field_name="request_replay_payload_fields",
    )
    _validate_runtime_probe_runtime_mutation_setattr_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )


def _is_runtime_probe_runtime_mutation_setattr_literal_flag_replay_input_pilot(
    replay_fields_by_key: Mapping[str, str],
) -> bool:
    """Return whether replay identity targets ``setattr(obj, "flag", value)``."""
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    return contract is _EXACT_REPLAY_SETATTR_LITERAL_CONTRACT


def _validate_runtime_probe_runtime_mutation_setattr_exact_replay_inputs(
    fields_by_key: Mapping[str, str],
    *,
    contract: _RuntimeProbeExactReplayContract = (
        _EXACT_REPLAY_SETATTR_LITERAL_CONTRACT
    ),
) -> None:
    """Require the exact literal pilot to carry only the accepted replay fields."""
    if set(fields_by_key) != _runtime_probe_worker_exact_replay_input_keys(contract):
        raise ValueError(
            "runtime probe runtime mutation setattr worker exact replay inputs "
            "must contain only object_type, attribute_name, assigned_value_type, "
            "and assigned_value_literal"
        )
    if not _runtime_probe_worker_exact_replay_payload_matches_contract(
        fields_by_key,
        contract,
    ):
        raise ValueError(
            "runtime probe runtime mutation setattr worker exact replay inputs "
            "must be object_type=main.ProbeTarget, attribute_name=flag, "
            "assigned_value_type=builtins.str, and assigned_value_literal=ready"
        )


def _validate_runtime_probe_runtime_mutation_setattr_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-setattr request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe runtime mutation setattr worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_runtime_mutation_setattr_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the runtime-mutation reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe runtime mutation setattr worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation setattr worker reason_code is unsupported"
        )
    return reason_code


def _runtime_probe_runtime_mutation_setattr_value_artifact_reference(
    request_id: str,
) -> str:
    """Return the deterministic durable reference for the assigned value argument."""
    _validate_runtime_probe_worker_metadata_text(request_id, field_name="request_id")
    return f"artifact://runtime-probe/setattr-value/{request_id}.json"


def _validate_runtime_probe_runtime_mutation_delattr_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local delattr request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe runtime mutation delattr worker payload must be typed"
        )
    _validate_runtime_probe_runtime_mutation_delattr_payload_family_form(
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
    _validate_runtime_probe_runtime_mutation_delattr_replay_metadata(
        replay_fields_by_key,
        plan_id=payload.plan_id,
        request_id=payload.request_id,
        family_label=payload.family_label,
        form_label=payload.form_label,
        replay_target_seed=payload.replay_target_seed,
        replay_selector_seed=payload.replay_selector_seed,
    )
    _validate_runtime_probe_runtime_mutation_delattr_exact_replay_inputs_if_needed(
        payload.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
            "runtime probe runtime mutation delattr worker invocation_identity "
            "must match payload replay identity"
        )


def _validate_runtime_probe_runtime_mutation_delattr_worker_request(
    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest,
) -> None:
    """Reject exact-delattr worker requests whose copied metadata drifted."""
    if not isinstance(
        request,
        RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest,
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker request must be typed"
        )
    _validate_runtime_probe_runtime_mutation_delattr_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe runtime mutation delattr worker subject_kind is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation delattr worker reason_code is unsupported"
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
    _validate_runtime_probe_runtime_mutation_delattr_replay_metadata(
        replay_fields_by_key,
        plan_id=request.plan_id,
        request_id=request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
    )
    _validate_runtime_probe_runtime_mutation_delattr_exact_replay_inputs_if_needed(
        request.request_replay_payload_fields,
        replay_fields_by_key=replay_fields_by_key,
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
        _validate_runtime_probe_runtime_mutation_delattr_replay_field_match(
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
            "runtime probe runtime mutation delattr worker invocation_identity "
            "must match request replay identity"
        )


def _validate_runtime_probe_runtime_mutation_delattr_worker_request_boundary_text(
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject delattr requests outside approved boundary identities."""
    boundary_text = replay_fields_by_key["boundary_text"]
    if boundary_text == _RUNTIME_MUTATION_DELATTR_WORKER_BOUNDARY_TEXT:
        return
    if (
        boundary_text == _RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT
        and _is_runtime_probe_runtime_mutation_delattr_literal_flag_replay_input_pilot(
            replay_fields_by_key
        )
    ):
        return
    if boundary_text == _RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe runtime mutation delattr worker boundary_text must match "
            "the exact direct-literal flag replay identity"
        )
    raise ValueError(
        "runtime probe runtime mutation delattr worker boundary_text must be "
        f"{_RUNTIME_MUTATION_DELATTR_WORKER_BOUNDARY_TEXT}"
    )


def _validate_runtime_probe_runtime_mutation_delattr_worker_observer(
    observer: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObserver,
) -> None:
    """Reject non-callable exact-delattr observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe runtime mutation delattr worker observer must be callable"
        )


def _validate_runtime_probe_runtime_mutation_delattr_target_callable(
    target: object,
) -> None:
    """Reject non-callable target injections before delattr interception."""
    if not callable(target):
        raise ValueError(
            "runtime probe runtime mutation delattr worker target must be callable"
        )


def _runtime_probe_runtime_mutation_delattr_exact_replay_inputs(
    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest,
) -> Mapping[str, str] | None:
    """Return exact delattr replay inputs for accepted pilots."""
    _validate_runtime_probe_runtime_mutation_delattr_worker_request(request)
    contract = _runtime_probe_runtime_mutation_delattr_exact_replay_contract(request)
    if contract is None:
        return None
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        request.request_replay_payload_fields,
        field_name="request_replay_payload_fields",
    )
    _validate_runtime_probe_runtime_mutation_delattr_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )
    return exact_fields_by_key


def _runtime_probe_runtime_mutation_delattr_exact_replay_contract(
    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest,
) -> _RuntimeProbeExactReplayContract | None:
    """Return the exact delattr replay contract for accepted worker requests."""
    _validate_runtime_probe_runtime_mutation_delattr_worker_request(request)
    replay_fields_by_key = _runtime_probe_worker_required_replay_fields_by_key(
        request.request_replay_payload_fields
    )
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_DELATTR_NAME_CONTRACT,
        _EXACT_REPLAY_DELATTR_LITERAL_CONTRACT,
    ):
        return None
    return contract


def _runtime_probe_runtime_mutation_delattr_target_args(
    source_module: ModuleType,
    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest,
    exact_replay_inputs: Mapping[str, str] | None,
) -> tuple[object, ...]:
    """Return target args for exact delattr pilots, otherwise none."""
    if exact_replay_inputs is None:
        return ()
    _validate_runtime_probe_runtime_mutation_delattr_worker_request(request)
    contract = _runtime_probe_runtime_mutation_delattr_exact_replay_contract(request)
    _validate_runtime_probe_runtime_mutation_delattr_exact_replay_inputs(
        exact_replay_inputs,
        contract=contract
        if contract is not None
        else _EXACT_REPLAY_DELATTR_LITERAL_CONTRACT,
    )
    probe_target = _runtime_probe_runtime_mutation_delattr_exact_probe_target(
        source_module
    )
    if contract is _EXACT_REPLAY_DELATTR_NAME_CONTRACT:
        return (
            probe_target,
            exact_replay_inputs[_RUNTIME_MUTATION_DELATTR_ATTRIBUTE_NAME_REPLAY_KEY],
        )
    if contract is _EXACT_REPLAY_DELATTR_LITERAL_CONTRACT:
        return (probe_target,)
    raise ValueError(
        "runtime probe runtime mutation delattr worker exact replay contract "
        "is unsupported"
    )


def _runtime_probe_runtime_mutation_delattr_exact_probe_target(
    source_module: ModuleType,
) -> object:
    """Instantiate the accepted delattr replay object."""
    if source_module.__name__ != "main":
        raise ValueError(
            "runtime probe runtime mutation delattr worker exact replay source "
            "module is unsupported"
        )
    probe_target_class = source_module.__dict__.get(
        _RUNTIME_MUTATION_DELATTR_PROBE_TARGET_CLASS_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if not isinstance(probe_target_class, type):
        raise ValueError(
            "runtime probe runtime mutation delattr worker exact replay target "
            "class is unsupported"
        )
    probe_target = probe_target_class()
    if (
        _runtime_probe_worker_object_type_name(probe_target)
        != _RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_OBJECT_TYPE
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker exact replay target "
            "object type is unsupported"
        )
    return probe_target


def _validate_runtime_probe_runtime_mutation_delattr_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationDelattrReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the delattr replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe runtime mutation delattr replay target source module "
            "must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe runtime mutation delattr replay target source module "
            "must match source_module_name"
        )


def _validate_runtime_probe_runtime_mutation_delattr_observation_for_request(
    observation: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation,
    request: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted delattr request."""
    _validate_runtime_probe_runtime_mutation_delattr_worker_request(request)
    _validate_runtime_probe_runtime_mutation_delattr_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe runtime mutation delattr worker observation request "
            "must match adapted request"
        )


def _validate_runtime_probe_runtime_mutation_delattr_worker_observation(
    observation: RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation,
) -> None:
    """Reject exact-delattr observation metadata that drifted from its request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonRuntimeMutationDelattrWorkerObservation,
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker observation must be typed"
        )
    _validate_runtime_probe_runtime_mutation_delattr_worker_request(observation.request)
    if (
        observation.mutation_outcome
        != _RUNTIME_MUTATION_DELATTR_WORKER_DELETED_ATTRIBUTE
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker mutation_outcome "
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
        _validate_runtime_probe_runtime_mutation_delattr_observation_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_runtime_mutation_delattr_replay_target(
    replay_target: RuntimeProbeLocalPythonRuntimeMutationDelattrReplayTarget,
) -> None:
    """Reject non-executing delattr replay targets that drift from their request."""
    if not isinstance(
        replay_target,
        RuntimeProbeLocalPythonRuntimeMutationDelattrReplayTarget,
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr replay target must be typed"
        )
    request = replay_target.request
    _validate_runtime_probe_runtime_mutation_delattr_worker_request(request)
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
        _validate_runtime_probe_runtime_mutation_delattr_replay_target_field_match(
            field_name=field_name,
            value=value,
            expected_value=expected_value,
        )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe runtime mutation delattr replay target "
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
            "runtime probe runtime mutation delattr replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )


def _validate_runtime_probe_runtime_mutation_delattr_replay_target_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied delattr replay-target identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe runtime mutation delattr replay target "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_runtime_mutation_delattr_observation_field_match(
    *,
    field_name: str,
    value: str,
    expected_value: str,
) -> None:
    """Require a copied delattr observation identity field to match its request."""
    if value != expected_value:
        raise ValueError(
            "runtime probe runtime mutation delattr worker observation "
            f"{field_name} must match request"
        )


def _validate_runtime_probe_runtime_mutation_delattr_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported runtime-mutation delattr family/form labels."""
    if family_label is not RuntimeProbeFamily.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation delattr worker family_label is unsupported"
        )
    if form_label != _RUNTIME_MUTATION_DELATTR_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe runtime mutation delattr worker form_label is unsupported"
        )


def _validate_runtime_probe_runtime_mutation_delattr_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-delattr worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_runtime_mutation_delattr_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker subject_kind is unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.RUNTIME_MUTATION.value
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker reason_code is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_runtime_mutation_delattr_reason_code_from_replay_field(
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
    _validate_runtime_probe_runtime_mutation_delattr_worker_request_boundary_text(
        replay_fields_by_key
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


def _validate_runtime_probe_runtime_mutation_delattr_exact_replay_inputs_if_needed(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    replay_fields_by_key: Mapping[str, str],
) -> None:
    """Reject drifted replay inputs for exact delattr pilots."""
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    if contract not in (
        _EXACT_REPLAY_DELATTR_NAME_CONTRACT,
        _EXACT_REPLAY_DELATTR_LITERAL_CONTRACT,
    ):
        return
    exact_fields_by_key = _runtime_probe_worker_replay_fields_by_key(
        fields,
        field_name="request_replay_payload_fields",
    )
    _validate_runtime_probe_runtime_mutation_delattr_exact_replay_inputs(
        exact_fields_by_key,
        contract=contract,
    )


def _is_runtime_probe_runtime_mutation_delattr_literal_flag_replay_input_pilot(
    replay_fields_by_key: Mapping[str, str],
) -> bool:
    """Return whether replay identity targets ``delattr(obj, "flag")``."""
    contract = _runtime_probe_exact_replay_contract_for_replay_fields(
        replay_fields_by_key
    )
    return contract is _EXACT_REPLAY_DELATTR_LITERAL_CONTRACT


def _validate_runtime_probe_runtime_mutation_delattr_exact_replay_inputs(
    fields_by_key: Mapping[str, str],
    *,
    contract: _RuntimeProbeExactReplayContract = (
        _EXACT_REPLAY_DELATTR_LITERAL_CONTRACT
    ),
) -> None:
    """Require exact delattr pilots to carry only the accepted replay pair."""
    if set(fields_by_key) != _runtime_probe_worker_exact_replay_input_keys(contract):
        raise ValueError(
            "runtime probe runtime mutation delattr worker exact replay inputs "
            "must contain only object_type and attribute_name"
        )
    if not _runtime_probe_worker_exact_replay_payload_matches_contract(
        fields_by_key,
        contract,
    ):
        raise ValueError(
            "runtime probe runtime mutation delattr worker exact replay inputs "
            "must be object_type=main.ProbeTarget and attribute_name=flag"
        )


def _validate_runtime_probe_runtime_mutation_delattr_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-delattr request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe runtime mutation delattr worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_runtime_mutation_delattr_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the runtime-mutation reason copied into replay."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe runtime mutation delattr worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
        raise ValueError(
            "runtime probe runtime mutation delattr worker reason_code is unsupported"
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
    *,
    support_root_literal_render_card_fixture: bool = False,
    support_root_name_render_card_fixture: bool = False,
    support_root_alias_render_card_fixture: bool = False,
) -> str:
    """Run a target while capturing one importlib.import_module module name."""
    capture = _RuntimeProbeDynamicImportCapture(
        support_root_literal_render_card_fixture=(
            support_root_literal_render_card_fixture
        ),
        support_root_name_render_card_fixture=support_root_name_render_card_fixture,
        support_root_alias_render_card_fixture=support_root_alias_render_card_fixture,
    )
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


def _is_runtime_probe_dynamic_import_root_literal_render_card_fixture_request(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> bool:
    """Return whether the request is the exact root-literal render_card replay."""
    return _is_runtime_probe_dynamic_import_render_card_fixture_request(
        request,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["root_literal"],
    )


def _runtime_probe_dynamic_import_root_literal_render_card_module_stub(
    name: str,
) -> ModuleType | None:
    """Return the one exact dynamic-import fixture stub, or no stub."""
    return _runtime_probe_dynamic_import_render_card_module_stub(
        name,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["root_literal"],
    )


def _is_runtime_probe_dynamic_import_root_name_render_card_fixture_request(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> bool:
    """Return whether the request is the exact root-name render_card replay."""
    return _is_runtime_probe_dynamic_import_render_card_fixture_request(
        request,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["root_name"],
    )


def _runtime_probe_dynamic_import_root_name_render_card_module_stub(
    name: str,
) -> ModuleType | None:
    """Return the one exact root-name dynamic-import fixture stub, or no stub."""
    return _runtime_probe_dynamic_import_render_card_module_stub(
        name,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["root_name"],
    )


def _is_runtime_probe_dynamic_import_root_alias_render_card_fixture_request(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> bool:
    """Return whether the request is the exact root-alias render_card replay."""
    return _is_runtime_probe_dynamic_import_render_card_fixture_request(
        request,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["root_alias"],
    )


def _runtime_probe_dynamic_import_root_alias_render_card_module_stub(
    name: str,
) -> ModuleType | None:
    """Return the one exact root-alias dynamic-import fixture stub, or no stub."""
    return _runtime_probe_dynamic_import_render_card_module_stub(
        name,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["root_alias"],
    )


def _is_runtime_probe_dynamic_import_builtin_render_card_fixture_request(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> bool:
    """Return whether the request is the exact builtin render_card replay."""
    return _is_runtime_probe_dynamic_import_render_card_fixture_request(
        request,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["builtin"],
    )


def _runtime_probe_dynamic_import_builtin_render_card_module_stub(
    name: str,
) -> ModuleType | None:
    """Return the one exact builtin dynamic-import fixture stub, or no stub."""
    return _runtime_probe_dynamic_import_render_card_module_stub(
        name,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["builtin"],
    )


def _is_runtime_probe_dynamic_import_builtins_attr_render_card_fixture_request(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> bool:
    """Return whether the request is the exact builtins-attribute replay."""
    return _is_runtime_probe_dynamic_import_render_card_fixture_request(
        request,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["builtins_attr"],
    )


def _runtime_probe_dynamic_import_builtins_attr_render_card_module_stub(
    name: str,
) -> ModuleType | None:
    """Return the one exact builtins-attribute fixture stub, or no stub."""
    return _runtime_probe_dynamic_import_render_card_module_stub(
        name,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["builtins_attr"],
    )


def _is_runtime_probe_dynamic_import_builtins_alias_render_card_fixture_request(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> bool:
    """Return whether the request is the exact builtins-alias replay."""
    return _is_runtime_probe_dynamic_import_render_card_fixture_request(
        request,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["builtins_alias"],
    )


def _runtime_probe_dynamic_import_builtins_alias_render_card_module_stub(
    name: str,
) -> ModuleType | None:
    """Return the one exact builtins-alias fixture stub, or no stub."""
    return _runtime_probe_dynamic_import_render_card_module_stub(
        name,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["builtins_alias"],
    )


def _supports_imported_literal_fixture(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> bool:
    """Return whether the request is the exact imported-literal replay."""
    return _is_runtime_probe_dynamic_import_render_card_fixture_request(
        request,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["imported_literal"],
    )


def _supports_imported_name_fixture(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> bool:
    """Return whether the request is the exact imported-name replay."""
    return _is_runtime_probe_dynamic_import_render_card_fixture_request(
        request,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["imported_name"],
    )


def _supports_imported_alias_fixture(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
) -> bool:
    """Return whether the request is the exact imported-alias replay."""
    return _is_runtime_probe_dynamic_import_render_card_fixture_request(
        request,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["imported_alias"],
    )


def _is_runtime_probe_dynamic_import_render_card_fixture_request(
    request: RuntimeProbeLocalPythonDynamicImportWorkerRequest,
    contract: _DynamicImportWorkerRenderCardContract,
) -> bool:
    """Return whether ``request`` exactly matches one render_card contract."""
    return (
        request.subject_id == contract.subject_id
        and request.source_site_id == contract.source_site_id
        and request.source_file_path == contract.source_file_path
        and request.source_start_line == contract.source_start_line
        and request.source_start_column == contract.source_start_column
        and request.source_end_line == contract.source_end_line
        and request.source_end_column == contract.source_end_column
        and request.reason_code is UnresolvedReasonCode.DYNAMIC_IMPORT
        and request.boundary_text == contract.boundary_text
        and request.family_label is RuntimeProbeFamily.DYNAMIC_IMPORT
        and request.form_label == contract.form_label
        and request.replay_target_seed == contract.replay_target_seed
        and request.replay_selector_seed == contract.replay_selector_seed
    )


def _runtime_probe_dynamic_import_render_card_module_stub(
    name: str,
    contract: _DynamicImportWorkerRenderCardContract,
) -> ModuleType | None:
    """Return a render_card stub for one exact contract, or no stub."""
    if name != contract.imported_module:
        return None
    module = ModuleType(name)

    def render_card() -> str:
        return "forecast-ready"

    module.__dict__["render_card"] = render_card
    return module


def _runtime_probe_dynamic_import_imported_name_render_card_module_stub(
    name: str,
) -> ModuleType | None:
    """Return the one exact imported-name fixture stub, or no stub."""
    return _runtime_probe_dynamic_import_render_card_module_stub(
        name,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["imported_name"],
    )


def _runtime_probe_dynamic_import_imported_alias_render_card_module_stub(
    name: str,
) -> ModuleType | None:
    """Return the one exact imported-alias fixture stub, or no stub."""
    return _runtime_probe_dynamic_import_render_card_module_stub(
        name,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["imported_alias"],
    )


def _runtime_probe_dynamic_import_imported_literal_render_card_module_stub(
    name: str,
) -> ModuleType | None:
    """Return the one exact imported-literal fixture stub, or no stub."""
    return _runtime_probe_dynamic_import_render_card_module_stub(
        name,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["imported_literal"],
    )


def _validate_runtime_probe_dynamic_import_root_literal_render_card_imported_module(
    imported_module: str,
) -> None:
    """Reject exact fixture executions that captured any other module name."""
    _validate_runtime_probe_dynamic_import_render_card_imported_module(
        imported_module,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["root_literal"],
    )


def _validate_runtime_probe_dynamic_import_root_name_render_card_imported_module(
    imported_module: str,
) -> None:
    """Reject exact root-name executions that captured another module."""
    _validate_runtime_probe_dynamic_import_render_card_imported_module(
        imported_module,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["root_name"],
    )


def _validate_runtime_probe_dynamic_import_root_alias_render_card_imported_module(
    imported_module: str,
) -> None:
    """Reject exact root-alias executions that captured another module."""
    _validate_runtime_probe_dynamic_import_render_card_imported_module(
        imported_module,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["root_alias"],
    )


def _validate_runtime_probe_dynamic_import_builtin_render_card_imported_module(
    imported_module: str,
) -> None:
    """Reject exact builtin executions that captured another module."""
    _validate_runtime_probe_dynamic_import_render_card_imported_module(
        imported_module,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["builtin"],
    )


def _validate_runtime_probe_dynamic_import_builtins_attr_render_card_imported_module(
    imported_module: str,
) -> None:
    """Reject exact builtins-attribute executions that captured another module."""
    _validate_runtime_probe_dynamic_import_render_card_imported_module(
        imported_module,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["builtins_attr"],
    )


def _validate_runtime_probe_dynamic_import_builtins_alias_render_card_imported_module(
    imported_module: str,
) -> None:
    """Reject exact builtins-alias executions that captured another module."""
    _validate_runtime_probe_dynamic_import_render_card_imported_module(
        imported_module,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["builtins_alias"],
    )


def _validate_runtime_probe_dynamic_import_imported_literal_render_card_imported_module(
    imported_module: str,
) -> None:
    """Reject exact imported-literal executions that captured another module."""
    _validate_runtime_probe_dynamic_import_render_card_imported_module(
        imported_module,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["imported_literal"],
    )


def _validate_runtime_probe_dynamic_import_imported_name_render_card_imported_module(
    imported_module: str,
) -> None:
    """Reject exact imported-name executions that captured another module."""
    _validate_runtime_probe_dynamic_import_render_card_imported_module(
        imported_module,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["imported_name"],
    )


def _validate_runtime_probe_dynamic_import_imported_alias_render_card_imported_module(
    imported_module: str,
) -> None:
    """Reject exact imported-alias executions that captured another module."""
    _validate_runtime_probe_dynamic_import_render_card_imported_module(
        imported_module,
        _DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS["imported_alias"],
    )


def _validate_runtime_probe_dynamic_import_render_card_imported_module(
    imported_module: str,
    contract: _DynamicImportWorkerRenderCardContract,
) -> None:
    """Reject exact render_card fixture executions with another module."""
    if imported_module != contract.imported_module:
        raise ValueError(
            "runtime probe dynamic import worker imported_module must match exact "
            f"{contract.error_label} fixture"
        )


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
    supports_builtin_render_card_fixture = (
        _is_runtime_probe_dynamic_import_builtin_render_card_fixture_request(
            replay_target.request
        )
    )
    imported_module = _runtime_probe_dynamic_import_captured_builtin_import_name(
        target,
        support_builtin_render_card_fixture=supports_builtin_render_card_fixture,
    )
    if supports_builtin_render_card_fixture:
        _validate_runtime_probe_dynamic_import_builtin_render_card_imported_module(
            imported_module
        )
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
    supports_builtins_attr_render_card_fixture = (
        _is_runtime_probe_dynamic_import_builtins_attr_render_card_fixture_request(
            replay_target.request
        )
    )
    supports_builtins_alias_render_card_fixture = (
        _is_runtime_probe_dynamic_import_builtins_alias_render_card_fixture_request(
            replay_target.request
        )
    )
    imported_module = _runtime_probe_dynamic_import_captured_builtins_import_name(
        source_module,
        target,
        global_name=global_name,
        support_builtins_attr_render_card_fixture=(
            supports_builtins_attr_render_card_fixture
        ),
        support_builtins_alias_render_card_fixture=(
            supports_builtins_alias_render_card_fixture
        ),
    )
    if supports_builtins_attr_render_card_fixture:
        _validate_runtime_probe_dynamic_import_builtins_attr_render_card_imported_module(
            imported_module
        )
    if supports_builtins_alias_render_card_fixture:
        _validate_runtime_probe_dynamic_import_builtins_alias_render_card_imported_module(
            imported_module
        )
    return materialize_runtime_probe_dynamic_import_worker_observation(
        replay_target.request,
        imported_module=imported_module,
    )


def _runtime_probe_dynamic_import_captured_builtin_import_name(
    target: RuntimeProbeLocalPythonDynamicImportTargetCallable,
    *,
    support_builtin_render_card_fixture: bool = False,
    support_builtins_attr_render_card_fixture: bool = False,
    support_builtins_alias_render_card_fixture: bool = False,
) -> str:
    """Run a target while capturing one exact bare __import__(name) call."""
    capture = _RuntimeProbeDynamicImportCapture(
        support_builtin_render_card_fixture=support_builtin_render_card_fixture,
        support_builtins_attr_render_card_fixture=(
            support_builtins_attr_render_card_fixture
        ),
        support_builtins_alias_render_card_fixture=(
            support_builtins_alias_render_card_fixture
        ),
    )
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
    support_builtins_attr_render_card_fixture: bool = False,
    support_builtins_alias_render_card_fixture: bool = False,
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
            target,
            support_builtins_attr_render_card_fixture=(
                support_builtins_attr_render_card_fixture
            ),
            support_builtins_alias_render_card_fixture=(
                support_builtins_alias_render_card_fixture
            ),
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
    support_imported_literal_render_card_fixture: bool = False,
    support_imported_name_render_card_fixture: bool = False,
    support_imported_alias_render_card_fixture: bool = False,
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
        support_imported_literal_render_card_fixture=(
            support_imported_literal_render_card_fixture
        ),
        support_imported_name_render_card_fixture=(
            support_imported_name_render_card_fixture
        ),
        support_imported_alias_render_card_fixture=(
            support_imported_alias_render_card_fixture
        ),
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
    support_imported_literal_render_card_fixture: bool = False,
    support_imported_name_render_card_fixture: bool = False,
    support_imported_alias_render_card_fixture: bool = False,
) -> str:
    """Run a target while capturing one exact import_module/load_module global."""
    original_import_module = _runtime_probe_dynamic_import_source_import_module_global(
        source_module,
        global_name=global_name,
    )
    capture = _RuntimeProbeDynamicImportCapture(
        support_imported_name_render_card_fixture=(
            support_imported_name_render_card_fixture
        ),
        support_imported_alias_render_card_fixture=(
            support_imported_alias_render_card_fixture
        ),
        support_imported_literal_render_card_fixture=(
            support_imported_literal_render_card_fixture
        ),
    )
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


_runtime_probe_worker_required_replay_fields_by_key = (
    _metadata_protocol._runtime_probe_worker_required_replay_fields_by_key
)
_validate_runtime_probe_worker_replay_field_match = (
    _metadata_protocol._validate_runtime_probe_worker_replay_field_match
)
_runtime_probe_worker_subject_kind_from_replay_field = (
    _metadata_protocol._runtime_probe_worker_subject_kind_from_replay_field
)


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


_runtime_probe_worker_replay_span_value = (
    _metadata_protocol._runtime_probe_worker_replay_span_value
)
_validate_runtime_probe_worker_source_span = (
    _metadata_protocol._validate_runtime_probe_worker_source_span
)
_validate_runtime_probe_worker_metadata_text = (
    _metadata_protocol._validate_runtime_probe_worker_metadata_text
)
_validate_runtime_probe_worker_path_text = (
    _metadata_protocol._validate_runtime_probe_worker_path_text
)
_validate_runtime_probe_worker_argv = (
    _metadata_protocol._validate_runtime_probe_worker_argv
)
_validate_runtime_probe_worker_python_path_entries = (
    _metadata_protocol._validate_runtime_probe_worker_python_path_entries
)
_validate_runtime_probe_worker_timeout_seconds = (
    _metadata_protocol._validate_runtime_probe_worker_timeout_seconds
)
_validate_runtime_probe_worker_invocation_identity = (
    _metadata_protocol._validate_runtime_probe_worker_invocation_identity
)
_runtime_probe_worker_invocation_identity_from_parts = (
    _metadata_protocol._runtime_probe_worker_invocation_identity_from_parts
)


def _validate_runtime_probe_exec_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local exec request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError("runtime probe exec worker payload must be typed")
    _validate_runtime_probe_exec_payload_family_form(
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
    _validate_runtime_probe_exec_replay_metadata(
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
            "runtime probe exec worker invocation_identity must match payload "
            "replay identity"
        )


def _validate_runtime_probe_exec_worker_request(
    request: RuntimeProbeLocalPythonExecWorkerRequest,
) -> None:
    """Reject exact-exec worker requests whose copied metadata drifted."""
    if not isinstance(request, RuntimeProbeLocalPythonExecWorkerRequest):
        raise ValueError("runtime probe exec worker request must be typed")
    _validate_runtime_probe_exec_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError("runtime probe exec worker subject_kind is unsupported")
    if request.reason_code is not UnresolvedReasonCode.EXEC_OR_EVAL:
        raise ValueError("runtime probe exec worker reason_code is unsupported")
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
    _validate_runtime_probe_exec_worker_request_boundary_text(request.boundary_text)
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
    _validate_runtime_probe_exec_replay_metadata(
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
        _validate_runtime_probe_exec_replay_field_match(
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
            "runtime probe exec worker invocation_identity must match request "
            "replay identity"
        )


def _validate_runtime_probe_exec_worker_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject exec requests that do not carry the approved boundary text."""
    if boundary_text != _EXEC_OR_EVAL_EXEC_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe exec worker boundary_text must be "
            f"{_EXEC_OR_EVAL_EXEC_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_exec_worker_observer(
    observer: RuntimeProbeLocalPythonExecWorkerObserver,
) -> None:
    """Reject non-callable exact-exec observer injections."""
    if not callable(observer):
        raise ValueError("runtime probe exec worker observer must be callable")


def _validate_runtime_probe_exec_target_callable(target: object) -> None:
    """Reject non-zero-argument target injections before exec interception."""
    if not callable(target):
        raise ValueError("runtime probe exec worker target must be callable")
    try:
        signature = inspect.signature(target)
        signature.bind()
    except TypeError as error:
        raise ValueError(
            "runtime probe exec worker target must accept zero arguments"
        ) from error
    except ValueError as error:
        raise ValueError(
            "runtime probe exec worker target signature is unavailable"
        ) from error


def _validate_runtime_probe_exec_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonExecReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the exec replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError("runtime probe exec replay target source module must be typed")
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe exec replay target source module must match "
            "source_module_name"
        )


def _validate_runtime_probe_exec_observation_for_request(
    observation: RuntimeProbeLocalPythonExecWorkerObservation,
    request: RuntimeProbeLocalPythonExecWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted exec request."""
    _validate_runtime_probe_exec_worker_request(request)
    _validate_runtime_probe_exec_worker_observation(observation)
    if observation.request != request:
        raise ValueError("runtime probe exec worker observation request must match")


def _validate_runtime_probe_exec_worker_observation(
    observation: RuntimeProbeLocalPythonExecWorkerObservation,
) -> None:
    """Reject exact-exec observation metadata that drifted from its request."""
    if not isinstance(observation, RuntimeProbeLocalPythonExecWorkerObservation):
        raise ValueError("runtime probe exec worker observation must be typed")
    _validate_runtime_probe_exec_worker_request(observation.request)
    if observation.source_shape != _EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHAPE:
        raise ValueError("runtime probe exec worker source_shape is unsupported")
    if observation.source_sha256 != _EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHA256:
        raise ValueError("runtime probe exec worker source_sha256 is unsupported")
    if observation.execution_outcome != _EXEC_OR_EVAL_EXEC_WORKER_EXECUTION_OUTCOME:
        raise ValueError("runtime probe exec worker execution_outcome is unsupported")
    if observation.statement_kind != _EXEC_OR_EVAL_EXEC_WORKER_STATEMENT_KIND:
        raise ValueError("runtime probe exec worker statement_kind is unsupported")
    expected_artifact_reference = _runtime_probe_exec_source_artifact_reference(
        observation.request.request_id
    )
    _validate_runtime_probe_worker_durable_artifact_reference(
        observation.durable_artifact_reference
    )
    if observation.durable_artifact_reference != expected_artifact_reference:
        raise ValueError(
            "runtime probe exec worker durable_artifact_reference must match request"
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
        if value != expected_value:
            raise ValueError(
                f"runtime probe exec worker observation {field_name} must match request"
            )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe exec worker observation request_replay_payload_fields "
            "must match request"
        )


def _validate_runtime_probe_exec_replay_target(
    replay_target: RuntimeProbeLocalPythonExecReplayTarget,
) -> None:
    """Reject non-executing exec replay targets that drift from their request."""
    if not isinstance(replay_target, RuntimeProbeLocalPythonExecReplayTarget):
        raise ValueError("runtime probe exec replay target must be typed")
    request = replay_target.request
    _validate_runtime_probe_exec_worker_request(request)
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
        if value != expected_value:
            raise ValueError(
                f"runtime probe exec replay target {field_name} must match request"
            )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe exec replay target request_replay_payload_fields must "
            "match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe exec replay target source_module_name must match "
            "request source_file_path"
        )
    expected_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=expected_source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    if replay_target.replay_target_attribute_path != expected_attribute_path:
        raise ValueError(
            "runtime probe exec replay target replay_target_attribute_path must "
            "match request replay_target_seed"
        )


def _runtime_probe_exec_captured_source(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonExecTargetCallable,
) -> str:
    """Run a target while capturing one exact bare ``exec(source)`` call."""
    _validate_runtime_probe_exec_source_global_absent(source_module)
    original_exec = builtins.__dict__.get(
        _EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if original_exec is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        raise ValueError("runtime probe exec worker builtins.exec is missing")
    capture = _RuntimeProbeExecCapture(
        original_exec=cast(Callable[..., object], original_exec)
    )
    controlled_exec: Callable[..., object] = capture.exec
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME] = controlled_exec
        try:
            sys.stdout = shielded_stdout
            sys.stderr = shielded_stderr
            target()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_exec_builtin(
        expected_exec=controlled_exec,
        original_exec=original_exec,
    )
    source_restore_failure = _restore_runtime_probe_exec_source_global(source_module)

    if builtin_restore_failure is not None:
        if target_failure is not None:
            raise builtin_restore_failure from target_failure
        raise builtin_restore_failure
    if source_restore_failure is not None:
        if target_failure is not None:
            raise source_restore_failure from target_failure
        raise source_restore_failure
    if target_failure is not None:
        _raise_runtime_probe_exec_target_failure(target_failure)

    return _runtime_probe_exec_capture_source(capture)


def _runtime_probe_exec_capture_source(capture: _RuntimeProbeExecCapture) -> str:
    """Return the single captured exec source after validation."""
    _validate_runtime_probe_exec_intercepted_calls(
        captured_sources=capture.captured_sources,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_sources[0]


def _validate_runtime_probe_exec_intercepted_calls(
    *,
    captured_sources: list[str],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted exec behavior outside the exact one-argument form."""
    if "arity" in captured_rejections:
        raise ValueError("runtime probe exec worker form must be exactly exec(source)")
    if "source_type" in captured_rejections:
        raise ValueError("runtime probe exec worker source must be a string")
    if "source" in captured_rejections:
        raise ValueError("runtime probe exec worker source must be exactly pass")
    if len(captured_sources) != 1:
        raise ValueError(
            "runtime probe exec worker target must capture exactly one exec call"
        )


def _raise_runtime_probe_exec_target_failure(error: BaseException) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _EXEC_OR_EVAL_EXEC_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _EXEC_OR_EVAL_EXEC_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_exec_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``exec`` global resolution."""
    if (
        source_module.__dict__.get(
            _EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe exec worker target module exec global must be absent"
        )


def _restore_runtime_probe_exec_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``exec`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe exec worker target module exec global could not be restored"
        )
    if (
        module_globals.get(
            _EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe exec worker target module exec global could not be restored"
        )
    return ValueError(
        "runtime probe exec worker target module exec global changed during execution"
    )


def _restore_runtime_probe_exec_builtin(
    *,
    expected_exec: object,
    original_exec: object,
) -> ValueError | None:
    """Restore builtins.exec and report target-time hook drift."""
    current_exec = builtins.__dict__.get(
        _EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_exec is not expected_exec:
        restore_failure = ValueError(
            "runtime probe exec worker builtins.exec changed during execution"
        )
    try:
        builtins.__dict__[_EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME] = original_exec
    except Exception:
        return ValueError(
            "runtime probe exec worker builtins.exec could not be restored"
        )
    if (
        builtins.__dict__.get(
            _EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_exec
    ):
        return ValueError(
            "runtime probe exec worker builtins.exec could not be restored"
        )
    return restore_failure


def _validate_runtime_probe_exec_observed_source(source: str) -> None:
    """Reject executed source outside the exact admitted pass statement."""
    if source != "pass":
        raise ValueError("runtime probe exec worker source must be exactly pass")
    parsed_source = ast.parse(source, mode="exec")
    if len(parsed_source.body) != 1 or not isinstance(parsed_source.body[0], ast.Pass):
        raise ValueError(
            "runtime probe exec worker source must parse as exactly one pass statement"
        )
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != (
        _EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHA256
    ):
        raise ValueError("runtime probe exec worker source_sha256 is unsupported")


def _validate_runtime_probe_exec_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported exec worker request family/form labels."""
    if family_label is not RuntimeProbeFamily.EXEC_OR_EVAL:
        raise ValueError("runtime probe exec worker family_label is unsupported")
    if form_label != _EXEC_OR_EVAL_EXEC_WORKER_FORM_LABEL:
        raise ValueError("runtime probe exec worker form_label is unsupported")


def _validate_runtime_probe_exec_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-exec worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_exec_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError("runtime probe exec worker subject_kind is unsupported")
    if replay_fields_by_key["reason_code"] != UnresolvedReasonCode.EXEC_OR_EVAL.value:
        raise ValueError("runtime probe exec worker reason_code is unsupported")
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_exec_reason_code_from_replay_field(
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
    _validate_runtime_probe_exec_worker_request_boundary_text(
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


def _validate_runtime_probe_exec_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-exec request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            f"runtime probe exec worker {field_key} must match request replay "
            "payload fields"
        )


def _runtime_probe_worker_exec_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the exec/eval reason copied into replay metadata."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe exec worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.EXEC_OR_EVAL:
        raise ValueError("runtime probe exec worker reason_code is unsupported")
    return reason_code


def _runtime_probe_exec_source_artifact_reference(request_id: str) -> str:
    """Return the deterministic durable artifact reference for exec source proof."""
    _validate_runtime_probe_worker_metadata_text(request_id, field_name="request_id")
    return f"artifact://runtime-probe/exec-source/{request_id}.json"


def _validate_runtime_probe_eval_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the worker-local eval request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError("runtime probe eval worker payload must be typed")
    _validate_runtime_probe_eval_payload_family_form(
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
    _validate_runtime_probe_eval_replay_metadata(
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
            "runtime probe eval worker invocation_identity must match payload "
            "replay identity"
        )


def _validate_runtime_probe_eval_worker_request(
    request: RuntimeProbeLocalPythonEvalWorkerRequest,
) -> None:
    """Reject exact-eval worker requests whose copied metadata drifted."""
    if not isinstance(request, RuntimeProbeLocalPythonEvalWorkerRequest):
        raise ValueError("runtime probe eval worker request must be typed")
    _validate_runtime_probe_eval_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError("runtime probe eval worker subject_kind is unsupported")
    if request.reason_code is not UnresolvedReasonCode.EXEC_OR_EVAL:
        raise ValueError("runtime probe eval worker reason_code is unsupported")
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
    _validate_runtime_probe_eval_worker_request_boundary_text(request.boundary_text)
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
    _validate_runtime_probe_eval_replay_metadata(
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
        _validate_runtime_probe_eval_replay_field_match(
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
            "runtime probe eval worker invocation_identity must match request "
            "replay identity"
        )


def _validate_runtime_probe_eval_worker_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject eval requests that do not carry the approved boundary text."""
    if boundary_text != _EXEC_OR_EVAL_EVAL_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe eval worker boundary_text must be "
            f"{_EXEC_OR_EVAL_EVAL_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_eval_worker_observer(
    observer: RuntimeProbeLocalPythonEvalWorkerObserver,
) -> None:
    """Reject non-callable exact-eval observer injections."""
    if not callable(observer):
        raise ValueError("runtime probe eval worker observer must be callable")


def _validate_runtime_probe_eval_target_callable(target: object) -> None:
    """Reject non-zero-argument target injections before eval interception."""
    if not callable(target):
        raise ValueError("runtime probe eval worker target must be callable")
    try:
        signature = inspect.signature(target)
        signature.bind()
    except TypeError as error:
        raise ValueError(
            "runtime probe eval worker target must accept zero arguments"
        ) from error
    except ValueError as error:
        raise ValueError(
            "runtime probe eval worker target signature is unavailable"
        ) from error


def _validate_runtime_probe_eval_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonEvalReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject injected source modules that do not match the eval replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError("runtime probe eval replay target source module must be typed")
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe eval replay target source module must match "
            "source_module_name"
        )


def _validate_runtime_probe_eval_observation_for_request(
    observation: RuntimeProbeLocalPythonEvalWorkerObservation,
    request: RuntimeProbeLocalPythonEvalWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted eval request."""
    _validate_runtime_probe_eval_worker_request(request)
    _validate_runtime_probe_eval_worker_observation(observation)
    if observation.request != request:
        raise ValueError("runtime probe eval worker observation request must match")


def _validate_runtime_probe_eval_worker_observation(
    observation: RuntimeProbeLocalPythonEvalWorkerObservation,
) -> None:
    """Reject exact-eval observation metadata that drifted from its request."""
    if not isinstance(observation, RuntimeProbeLocalPythonEvalWorkerObservation):
        raise ValueError("runtime probe eval worker observation must be typed")
    _validate_runtime_probe_eval_worker_request(observation.request)
    if observation.source_shape != _EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHAPE:
        raise ValueError("runtime probe eval worker source_shape is unsupported")
    if observation.source_sha256 != _EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHA256:
        raise ValueError("runtime probe eval worker source_sha256 is unsupported")
    if observation.evaluation_outcome != _EXEC_OR_EVAL_EVAL_WORKER_EVALUATION_OUTCOME:
        raise ValueError("runtime probe eval worker evaluation_outcome is unsupported")
    if observation.result_type != _EXEC_OR_EVAL_EVAL_WORKER_RESULT_TYPE:
        raise ValueError("runtime probe eval worker result_type is unsupported")
    expected_artifact_reference = _runtime_probe_eval_source_artifact_reference(
        observation.request.request_id
    )
    _validate_runtime_probe_worker_durable_artifact_reference(
        observation.durable_artifact_reference
    )
    if observation.durable_artifact_reference != expected_artifact_reference:
        raise ValueError(
            "runtime probe eval worker durable_artifact_reference must match request"
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
        if value != expected_value:
            raise ValueError(
                f"runtime probe eval worker observation {field_name} must match request"
            )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe eval worker observation request_replay_payload_fields "
            "must match request"
        )


def _validate_runtime_probe_eval_replay_target(
    replay_target: RuntimeProbeLocalPythonEvalReplayTarget,
) -> None:
    """Reject non-executing eval replay targets that drift from their request."""
    if not isinstance(replay_target, RuntimeProbeLocalPythonEvalReplayTarget):
        raise ValueError("runtime probe eval replay target must be typed")
    request = replay_target.request
    _validate_runtime_probe_eval_worker_request(request)
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
        if value != expected_value:
            raise ValueError(
                f"runtime probe eval replay target {field_name} must match request"
            )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe eval replay target request_replay_payload_fields must "
            "match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe eval replay target source_module_name must match "
            "request source_file_path"
        )
    expected_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=expected_source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    if replay_target.replay_target_attribute_path != expected_attribute_path:
        raise ValueError(
            "runtime probe eval replay target replay_target_attribute_path must "
            "match request replay_target_seed"
        )


def _runtime_probe_eval_captured_source(
    source_module: ModuleType,
    target: RuntimeProbeLocalPythonEvalTargetCallable,
) -> str:
    """Run a target while capturing one exact bare ``eval(source)`` call."""
    _validate_runtime_probe_eval_source_global_absent(source_module)
    original_eval = builtins.__dict__.get(
        _EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if original_eval is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        raise ValueError("runtime probe eval worker builtins.eval is missing")
    capture = _RuntimeProbeEvalCapture(
        original_eval=cast(Callable[..., object], original_eval)
    )
    controlled_eval: Callable[..., object] = capture.eval
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    shielded_stdout = io.StringIO()
    shielded_stderr = io.StringIO()
    target_failure: BaseException | None = None

    try:
        builtins.__dict__[_EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME] = controlled_eval
        try:
            sys.stdout = shielded_stdout
            sys.stderr = shielded_stderr
            target()
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    except BaseException as error:
        target_failure = error
    builtin_restore_failure = _restore_runtime_probe_eval_builtin(
        expected_eval=controlled_eval,
        original_eval=original_eval,
    )
    source_restore_failure = _restore_runtime_probe_eval_source_global(source_module)

    if builtin_restore_failure is not None:
        if target_failure is not None:
            raise builtin_restore_failure from target_failure
        raise builtin_restore_failure
    if source_restore_failure is not None:
        if target_failure is not None:
            raise source_restore_failure from target_failure
        raise source_restore_failure
    if target_failure is not None:
        _raise_runtime_probe_eval_target_failure(target_failure)

    return _runtime_probe_eval_capture_source(capture)


def _runtime_probe_eval_capture_source(capture: _RuntimeProbeEvalCapture) -> str:
    """Return the single captured eval source after validation."""
    _validate_runtime_probe_eval_intercepted_calls(
        captured_sources=capture.captured_sources,
        captured_rejections=tuple(capture.captured_rejections),
    )
    return capture.captured_sources[0]


def _validate_runtime_probe_eval_intercepted_calls(
    *,
    captured_sources: list[str],
    captured_rejections: tuple[str, ...],
) -> None:
    """Reject intercepted eval behavior outside the exact one-argument form."""
    if "arity" in captured_rejections:
        raise ValueError("runtime probe eval worker form must be exactly eval(source)")
    if "source_type" in captured_rejections:
        raise ValueError("runtime probe eval worker source must be a string")
    if "source" in captured_rejections:
        raise ValueError(
            'runtime probe eval worker source must be exactly "eval-probe-value"'
        )
    if "result_type" in captured_rejections:
        raise ValueError("runtime probe eval worker result must be a string")
    if len(captured_sources) != 1:
        raise ValueError(
            "runtime probe eval worker target must capture exactly one eval call"
        )


def _raise_runtime_probe_eval_target_failure(error: BaseException) -> None:
    """Raise a sanitized target failure unless the error is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _EXEC_OR_EVAL_EVAL_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _EXEC_OR_EVAL_EVAL_WORKER_TARGET_EXECUTION_FAILED_MESSAGE
    ) from error


def _validate_runtime_probe_eval_source_global_absent(
    source_module: ModuleType,
) -> None:
    """Reject source modules that shadow bare ``eval`` global resolution."""
    if (
        source_module.__dict__.get(
            _EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        raise ValueError(
            "runtime probe eval worker target module eval global must be absent"
        )


def _restore_runtime_probe_eval_source_global(
    source_module: ModuleType,
) -> ValueError | None:
    """Remove any target-time source ``eval`` global and report drift."""
    module_globals = source_module.__dict__
    current_global = module_globals.get(
        _EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if current_global is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        return None
    try:
        del module_globals[_EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME]
    except Exception:
        return ValueError(
            "runtime probe eval worker target module eval global could not be restored"
        )
    if (
        module_globals.get(
            _EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL
    ):
        return ValueError(
            "runtime probe eval worker target module eval global could not be restored"
        )
    return ValueError(
        "runtime probe eval worker target module eval global changed during execution"
    )


def _restore_runtime_probe_eval_builtin(
    *,
    expected_eval: object,
    original_eval: object,
) -> ValueError | None:
    """Restore builtins.eval and report target-time hook drift."""
    current_eval = builtins.__dict__.get(
        _EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_eval is not expected_eval:
        restore_failure = ValueError(
            "runtime probe eval worker builtins.eval changed during execution"
        )
    try:
        builtins.__dict__[_EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME] = original_eval
    except Exception:
        return ValueError(
            "runtime probe eval worker builtins.eval could not be restored"
        )
    if (
        builtins.__dict__.get(
            _EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_eval
    ):
        return ValueError(
            "runtime probe eval worker builtins.eval could not be restored"
        )
    return restore_failure


def _validate_runtime_probe_eval_observed_source(source: str) -> None:
    """Reject evaluated source outside the exact admitted string expression."""
    if source != _EXEC_OR_EVAL_EVAL_WORKER_SOURCE_TEXT:
        raise ValueError(
            'runtime probe eval worker source must be exactly "eval-probe-value"'
        )
    parsed_source = ast.parse(source, mode="eval")
    if not isinstance(parsed_source, ast.Expression):
        raise ValueError(
            "runtime probe eval worker source must parse as exactly one string "
            "literal expression"
        )
    body = parsed_source.body
    if not (
        isinstance(body, ast.Constant)
        and isinstance(body.value, str)
        and body.value == "eval-probe-value"
    ):
        raise ValueError(
            "runtime probe eval worker source must parse as exactly one string "
            "literal expression"
        )
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != (
        _EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHA256
    ):
        raise ValueError("runtime probe eval worker source_sha256 is unsupported")


def _validate_runtime_probe_eval_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported eval worker request family/form labels."""
    if family_label is not RuntimeProbeFamily.EXEC_OR_EVAL:
        raise ValueError("runtime probe eval worker family_label is unsupported")
    if form_label != _EXEC_OR_EVAL_EVAL_WORKER_FORM_LABEL:
        raise ValueError("runtime probe eval worker form_label is unsupported")


def _validate_runtime_probe_eval_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from exact-eval worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_eval_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError("runtime probe eval worker subject_kind is unsupported")
    if replay_fields_by_key["reason_code"] != UnresolvedReasonCode.EXEC_OR_EVAL.value:
        raise ValueError("runtime probe eval worker reason_code is unsupported")
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_eval_reason_code_from_replay_field(
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
    _validate_runtime_probe_eval_worker_request_boundary_text(
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


def _validate_runtime_probe_eval_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match a copied exact-eval request field."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            f"runtime probe eval worker {field_key} must match request replay "
            "payload fields"
        )


def _runtime_probe_worker_eval_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the eval reason copied into replay metadata."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe eval worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.EXEC_OR_EVAL:
        raise ValueError("runtime probe eval worker reason_code is unsupported")
    return reason_code


def _runtime_probe_eval_source_artifact_reference(request_id: str) -> str:
    """Return the deterministic durable artifact reference for eval source proof."""
    _validate_runtime_probe_worker_metadata_text(request_id, field_name="request_id")
    return f"artifact://runtime-probe/eval-source/{request_id}.json"


def _validate_runtime_probe_metaclass_keyword_worker_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Reject payloads that cannot become the metaclass-keyword request."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError(
            "runtime probe metaclass behavior worker payload must be typed"
        )
    _validate_runtime_probe_metaclass_keyword_payload_family_form(
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
    _validate_runtime_probe_metaclass_keyword_replay_metadata(
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
            "runtime probe metaclass behavior worker invocation_identity must "
            "match payload replay identity"
        )


def _validate_runtime_probe_metaclass_keyword_worker_request(
    request: RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest,
) -> None:
    """Reject metaclass-keyword worker requests whose metadata drifted."""
    if not isinstance(request, RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest):
        raise ValueError(
            "runtime probe metaclass behavior worker request must be typed"
        )
    _validate_runtime_probe_metaclass_keyword_payload_family_form(
        family_label=request.family_label,
        form_label=request.form_label,
    )
    if request.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
        raise ValueError(
            "runtime probe metaclass behavior worker subject_kind is unsupported"
        )
    if request.reason_code is not UnresolvedReasonCode.METACLASS_BEHAVIOR:
        raise ValueError(
            "runtime probe metaclass behavior worker reason_code is unsupported"
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
    _validate_runtime_probe_metaclass_keyword_request_boundary_text(
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
    _validate_runtime_probe_metaclass_keyword_replay_metadata(
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
        _validate_runtime_probe_metaclass_keyword_replay_field_match(
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
            "runtime probe metaclass behavior worker invocation_identity must "
            "match request replay identity"
        )


def _validate_runtime_probe_metaclass_keyword_request_boundary_text(
    boundary_text: str,
) -> None:
    """Reject metaclass requests outside the exact admitted boundary text."""
    if boundary_text != _METACLASS_BEHAVIOR_KEYWORD_WORKER_BOUNDARY_TEXT:
        raise ValueError(
            "runtime probe metaclass behavior worker boundary_text must be "
            f"{_METACLASS_BEHAVIOR_KEYWORD_WORKER_BOUNDARY_TEXT}"
        )


def _validate_runtime_probe_metaclass_keyword_worker_observer(
    observer: RuntimeProbeLocalPythonMetaclassKeywordWorkerObserver,
) -> None:
    """Reject non-callable metaclass-keyword observer injections."""
    if not callable(observer):
        raise ValueError(
            "runtime probe metaclass behavior worker observer must be callable"
        )


def _validate_runtime_probe_metaclass_keyword_observation_for_request(
    observation: RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation,
    request: RuntimeProbeLocalPythonMetaclassKeywordWorkerRequest,
) -> None:
    """Reject observer results that do not belong to the adapted request."""
    _validate_runtime_probe_metaclass_keyword_worker_request(request)
    _validate_runtime_probe_metaclass_keyword_worker_observation(observation)
    if observation.request != request:
        raise ValueError(
            "runtime probe metaclass behavior worker observation request must match"
        )


def _validate_runtime_probe_metaclass_keyword_worker_observation(
    observation: RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation,
) -> None:
    """Reject metaclass observations that drifted from their request."""
    if not isinstance(
        observation,
        RuntimeProbeLocalPythonMetaclassKeywordWorkerObservation,
    ):
        raise ValueError(
            "runtime probe metaclass behavior worker observation must be typed"
        )
    _validate_runtime_probe_metaclass_keyword_worker_request(observation.request)
    if observation.class_creation_outcome != (
        _METACLASS_BEHAVIOR_KEYWORD_WORKER_CLASS_CREATION_OUTCOME
    ):
        raise ValueError(
            "runtime probe metaclass behavior worker class_creation_outcome is "
            "unsupported"
        )
    replay_target = materialize_runtime_probe_metaclass_keyword_replay_target(
        observation.request
    )
    expected_created_class = observation.request.replay_target_seed
    expected_selected_metaclass = (
        _runtime_probe_metaclass_keyword_expected_selected_metaclass_qualified_name(
            replay_target
        )
    )
    if observation.created_class_qualified_name != expected_created_class:
        raise ValueError(
            "runtime probe metaclass behavior worker created_class_qualified_name "
            "must match request"
        )
    if observation.selected_metaclass_qualified_name != expected_selected_metaclass:
        raise ValueError(
            "runtime probe metaclass behavior worker selected_metaclass_qualified_name "
            "must match request"
        )
    expected_artifact_reference = _runtime_probe_metaclass_selection_artifact_reference(
        observation.request.request_id
    )
    _validate_runtime_probe_worker_durable_artifact_reference(
        observation.durable_artifact_reference
    )
    if observation.durable_artifact_reference != expected_artifact_reference:
        raise ValueError(
            "runtime probe metaclass behavior worker durable_artifact_reference "
            "must match request"
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
        if value != expected_value:
            raise ValueError(
                "runtime probe metaclass behavior worker observation "
                f"{field_name} must match request"
            )
    if (
        observation.request_replay_payload_fields
        != observation.request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe metaclass behavior worker observation "
            "request_replay_payload_fields must match request"
        )


def _validate_runtime_probe_metaclass_keyword_replay_target(
    replay_target: RuntimeProbeLocalPythonMetaclassKeywordReplayTarget,
) -> None:
    """Reject non-executing metaclass replay targets that drift from request."""
    if not isinstance(
        replay_target, RuntimeProbeLocalPythonMetaclassKeywordReplayTarget
    ):
        raise ValueError("runtime probe metaclass behavior replay target must be typed")
    request = replay_target.request
    _validate_runtime_probe_metaclass_keyword_worker_request(request)
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
        if value != expected_value:
            raise ValueError(
                "runtime probe metaclass behavior replay target "
                f"{field_name} must match request"
            )
    if (
        replay_target.request_replay_payload_fields
        != request.request_replay_payload_fields
    ):
        raise ValueError(
            "runtime probe metaclass behavior replay target "
            "request_replay_payload_fields must match request"
        )

    expected_source_module_name = (
        _runtime_probe_dynamic_import_source_module_name_from_path(
            request.source_file_path
        )
    )
    if replay_target.source_module_name != expected_source_module_name:
        raise ValueError(
            "runtime probe metaclass behavior replay target source_module_name "
            "must match request source_file_path"
        )
    expected_attribute_path = (
        _runtime_probe_dynamic_import_replay_target_attribute_path(
            source_module_name=expected_source_module_name,
            replay_target_seed=request.replay_target_seed,
        )
    )
    if replay_target.replay_target_attribute_path != expected_attribute_path:
        raise ValueError(
            "runtime probe metaclass behavior replay target "
            "replay_target_attribute_path must match request replay_target_seed"
        )
    _runtime_probe_metaclass_keyword_target_class_name(replay_target)


def _runtime_probe_metaclass_keyword_capture_source_module_import(
    replay_target: RuntimeProbeLocalPythonMetaclassKeywordReplayTarget,
) -> _RuntimeProbeMetaclassKeywordCaptureResult:
    """Import the source module while capturing the exact target class creation."""
    _validate_runtime_probe_metaclass_keyword_replay_target(replay_target)
    request = replay_target.request
    original_build_class = builtins.__dict__.get(
        _METACLASS_BEHAVIOR_KEYWORD_WORKER_BUILD_CLASS_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    if original_build_class is _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL:
        raise ValueError(
            "runtime probe metaclass behavior worker builtins.__build_class__ is "
            "missing"
        )
    capture = _RuntimeProbeMetaclassKeywordBuildClassCapture(
        original_build_class=cast(Callable[..., object], original_build_class),
        target_class_name=_runtime_probe_metaclass_keyword_target_class_name(
            replay_target
        ),
        target_class_qualified_name=request.replay_target_seed,
        selected_metaclass_qualified_name=(
            _runtime_probe_metaclass_keyword_expected_selected_metaclass_qualified_name(
                replay_target
            )
        ),
    )
    controlled_build_class: Callable[..., object] = capture.build_class
    original_sys_path = list(sys.path)
    original_working_directory = os.getcwd()
    imported_module: ModuleType | None = None
    target_failure: BaseException | None = None
    build_class_restore_failure: ValueError | None = None
    build_class_installed = False

    try:
        os.chdir(request.working_directory)
        sys.path[:] = [
            request.working_directory,
            *request.python_path_entries,
            *original_sys_path,
        ]
        builtins.__dict__[
            _METACLASS_BEHAVIOR_KEYWORD_WORKER_BUILD_CLASS_GLOBAL_NAME
        ] = controlled_build_class
        build_class_installed = True
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            imported_module = importlib.import_module(replay_target.source_module_name)
    except BaseException as error:
        target_failure = error
    finally:
        if build_class_installed:
            build_class_restore_failure = (
                _restore_runtime_probe_metaclass_keyword_build_class(
                    expected_build_class=controlled_build_class,
                    original_build_class=original_build_class,
                )
            )
        sys.path[:] = original_sys_path
        os.chdir(original_working_directory)

    if build_class_restore_failure is not None:
        if target_failure is not None:
            raise build_class_restore_failure from target_failure
        raise build_class_restore_failure
    if target_failure is not None:
        _raise_runtime_probe_metaclass_keyword_import_failure(target_failure)
    if imported_module is None:
        raise ValueError(
            _METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_IMPORT_FAILED_MESSAGE
        )
    _validate_runtime_probe_metaclass_keyword_replay_target_source_module(
        replay_target,
        imported_module,
    )
    return _runtime_probe_metaclass_keyword_capture_result(capture)


def _validate_runtime_probe_metaclass_keyword_replay_target_source_module(
    replay_target: RuntimeProbeLocalPythonMetaclassKeywordReplayTarget,
    source_module: ModuleType,
) -> None:
    """Reject imported source modules that do not match the replay target."""
    if not isinstance(source_module, ModuleType):
        raise ValueError(
            "runtime probe metaclass behavior replay target source module must be typed"
        )
    if source_module.__name__ != replay_target.source_module_name:
        raise ValueError(
            "runtime probe metaclass behavior replay target source module must "
            "match source_module_name"
        )


def _runtime_probe_metaclass_keyword_capture_result(
    capture: _RuntimeProbeMetaclassKeywordBuildClassCapture,
) -> _RuntimeProbeMetaclassKeywordCaptureResult:
    """Return the single captured target class creation after validation."""
    if len(capture.captured_classes) != 1:
        raise ValueError(
            "runtime probe metaclass behavior worker target must capture exactly "
            "one class creation"
        )
    return capture.captured_classes[0]


def _raise_runtime_probe_metaclass_keyword_import_failure(
    error: BaseException,
) -> None:
    """Raise a sanitized target import failure unless it is a known shape reject."""
    if (
        isinstance(error, ValueError)
        and str(error) in _METACLASS_BEHAVIOR_KEYWORD_WORKER_SHAPE_ERROR_MESSAGES
    ):
        raise error
    raise ValueError(
        _METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_IMPORT_FAILED_MESSAGE
    ) from error


def _restore_runtime_probe_metaclass_keyword_build_class(
    *,
    expected_build_class: object,
    original_build_class: object,
) -> ValueError | None:
    """Restore builtins.__build_class__ and report import-time hook drift."""
    current_build_class = builtins.__dict__.get(
        _METACLASS_BEHAVIOR_KEYWORD_WORKER_BUILD_CLASS_GLOBAL_NAME,
        _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
    )
    restore_failure: ValueError | None = None
    if current_build_class is not expected_build_class:
        restore_failure = ValueError(
            "runtime probe metaclass behavior worker builtins.__build_class__ "
            "changed during import"
        )
    try:
        builtins.__dict__[
            _METACLASS_BEHAVIOR_KEYWORD_WORKER_BUILD_CLASS_GLOBAL_NAME
        ] = original_build_class
    except Exception:
        return ValueError(
            "runtime probe metaclass behavior worker builtins.__build_class__ "
            "could not be restored"
        )
    if (
        builtins.__dict__.get(
            _METACLASS_BEHAVIOR_KEYWORD_WORKER_BUILD_CLASS_GLOBAL_NAME,
            _DYNAMIC_IMPORT_WORKER_MISSING_GLOBAL,
        )
        is not original_build_class
    ):
        return ValueError(
            "runtime probe metaclass behavior worker builtins.__build_class__ "
            "could not be restored"
        )
    return restore_failure


def _validate_runtime_probe_metaclass_keyword_payload_family_form(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Reject unsupported metaclass worker request family/form labels."""
    if family_label is not RuntimeProbeFamily.METACLASS_BEHAVIOR:
        raise ValueError(
            "runtime probe metaclass behavior worker family_label is unsupported"
        )
    if form_label != _METACLASS_BEHAVIOR_KEYWORD_WORKER_FORM_LABEL:
        raise ValueError(
            "runtime probe metaclass behavior worker form_label is unsupported"
        )


def _validate_runtime_probe_metaclass_keyword_replay_metadata(
    replay_fields_by_key: Mapping[str, str],
    *,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
) -> None:
    """Reject replay fields that drift from metaclass worker metadata."""
    for field_key, expected_value in (
        ("plan_id", plan_id),
        ("request_id", request_id),
        ("family_label", family_label.value),
        ("form_label", form_label),
        ("replay_target_seed", replay_target_seed),
        ("replay_selector_seed", replay_selector_seed),
    ):
        _validate_runtime_probe_metaclass_keyword_replay_field_match(
            replay_fields_by_key,
            field_key=field_key,
            expected_value=expected_value,
        )
    if replay_fields_by_key["subject_kind"] != (
        SemanticSubjectKind.UNSUPPORTED_FINDING.value
    ):
        raise ValueError(
            "runtime probe metaclass behavior worker subject_kind is unsupported"
        )
    if replay_fields_by_key["reason_code"] != (
        UnresolvedReasonCode.METACLASS_BEHAVIOR.value
    ):
        raise ValueError(
            "runtime probe metaclass behavior worker reason_code is unsupported"
        )
    _runtime_probe_worker_subject_kind_from_replay_field(
        replay_fields_by_key["subject_kind"]
    )
    _runtime_probe_worker_metaclass_reason_code_from_replay_field(
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
    _validate_runtime_probe_metaclass_keyword_request_boundary_text(
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


def _validate_runtime_probe_metaclass_keyword_replay_field_match(
    replay_fields_by_key: Mapping[str, str],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require a replay field to match copied metaclass request metadata."""
    if replay_fields_by_key[field_key] != expected_value:
        raise ValueError(
            "runtime probe metaclass behavior worker "
            f"{field_key} must match request replay payload fields"
        )


def _runtime_probe_worker_metaclass_reason_code_from_replay_field(
    value: str,
) -> UnresolvedReasonCode:
    """Parse and validate the metaclass reason copied into replay metadata."""
    try:
        reason_code = UnresolvedReasonCode(value)
    except ValueError as error:
        raise ValueError(
            "runtime probe metaclass behavior worker reason_code is unsupported"
        ) from error
    if reason_code is not UnresolvedReasonCode.METACLASS_BEHAVIOR:
        raise ValueError(
            "runtime probe metaclass behavior worker reason_code is unsupported"
        )
    return reason_code


def _runtime_probe_metaclass_selection_artifact_reference(request_id: str) -> str:
    """Return the deterministic durable artifact reference for metaclass proof."""
    _validate_runtime_probe_worker_metadata_text(request_id, field_name="request_id")
    return f"artifact://runtime-probe/metaclass-selection/{request_id}.json"


def _runtime_probe_metaclass_keyword_target_class_name(
    replay_target: RuntimeProbeLocalPythonMetaclassKeywordReplayTarget,
) -> str:
    """Return the exact top-level class name supported by this worker form."""
    if replay_target.replay_target_attribute_path != (
        _METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_CLASS_NAME,
    ):
        raise ValueError(
            "runtime probe metaclass behavior worker target class must be "
            "top-level Example"
        )
    return _METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_CLASS_NAME


def _runtime_probe_metaclass_keyword_expected_selected_metaclass_qualified_name(
    replay_target: RuntimeProbeLocalPythonMetaclassKeywordReplayTarget,
) -> str:
    """Return the only selected metaclass admitted by the exact keyword form."""
    selected_metaclass_name = _METACLASS_BEHAVIOR_KEYWORD_WORKER_SELECTED_METACLASS_NAME
    return f"{replay_target.source_module_name}.{selected_metaclass_name}"


def _runtime_probe_metaclass_keyword_optional_qualified_name(
    value: object,
) -> str | None:
    """Return a dotted qualified name when one is available and well-formed."""
    module = getattr(value, "__module__", None)
    qualname = getattr(value, "__qualname__", None)
    if not isinstance(module, str) or not isinstance(qualname, str):
        return None
    qualified_name = f"{module}.{qualname}"
    try:
        _validate_runtime_probe_metaclass_keyword_qualified_name(qualified_name)
    except ValueError:
        return None
    return qualified_name


def _runtime_probe_metaclass_keyword_qualified_name(
    value: object,
    *,
    field_name: str,
) -> str:
    """Return a strict dotted qualified name for a class-like object."""
    module = getattr(value, "__module__", None)
    qualname = getattr(value, "__qualname__", None)
    if not isinstance(module, str) or not isinstance(qualname, str):
        _raise_runtime_probe_metaclass_keyword_qualified_name_error(field_name)
    qualified_name = f"{module}.{qualname}"
    try:
        _validate_runtime_probe_metaclass_keyword_qualified_name(qualified_name)
    except ValueError as error:
        raise _runtime_probe_metaclass_keyword_qualified_name_error(
            field_name
        ) from error
    return qualified_name


def _validate_runtime_probe_metaclass_keyword_qualified_name(value: str) -> None:
    """Reject qualified names outside dotted identifier class paths."""
    _validate_runtime_probe_worker_metadata_text(
        value,
        field_name="qualified_name",
    )
    _validate_runtime_probe_dynamic_import_dotted_identifier_segments(
        tuple(value.split(".")),
        field_name="qualified_name",
    )


def _raise_runtime_probe_metaclass_keyword_qualified_name_error(
    field_name: str,
) -> NoReturn:
    """Raise the stable error for malformed metaclass capture names."""
    raise _runtime_probe_metaclass_keyword_qualified_name_error(field_name)


def _runtime_probe_metaclass_keyword_qualified_name_error(
    field_name: str,
) -> ValueError:
    """Return the stable error for malformed metaclass capture names."""
    if field_name == "selected_metaclass":
        return ValueError(
            "runtime probe metaclass behavior worker selected metaclass is unsupported"
        )
    return ValueError(
        "runtime probe metaclass behavior worker created class is unsupported"
    )


_is_runtime_probe_worker_absolute_path_metadata = (
    _metadata_protocol._is_runtime_probe_worker_absolute_path_metadata
)


_validate_runtime_probe_worker_response = (
    _response_protocol._validate_runtime_probe_worker_response
)
_validate_runtime_probe_worker_success_response = (
    _response_protocol._validate_runtime_probe_worker_success_response
)
_validate_runtime_probe_worker_handler_response = (
    _response_protocol._validate_runtime_probe_worker_handler_response
)
_validate_runtime_probe_worker_replay_fields = (
    _response_protocol._validate_runtime_probe_worker_replay_fields
)
_validate_runtime_probe_worker_durable_artifact_reference = (
    _response_protocol._validate_runtime_probe_worker_durable_artifact_reference
)
_validate_runtime_probe_worker_observed_replay_inputs = (
    _response_protocol._validate_runtime_probe_worker_observed_replay_inputs
)
_runtime_probe_worker_replay_fields_by_key = (
    _response_protocol._runtime_probe_worker_replay_fields_by_key
)
_runtime_probe_worker_replay_fields_json_array = (
    _response_protocol._runtime_probe_worker_replay_fields_json_array
)
_contains_control_character = _response_protocol._contains_control_character


if __name__ == "__main__":
    raise SystemExit(main())

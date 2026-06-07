"""Private reflective-builtin worker contract constants."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

_REFLECTIVE_BUILTIN_HASATTR_WORKER_FORM_LABEL = "reflective_builtin:hasattr/2"
_REFLECTIVE_BUILTIN_HASATTR_WORKER_BOUNDARY_TEXT = "hasattr(obj, name)"
_REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT = (
    'hasattr(obj, "bit_length")'
)
_REFLECTIVE_BUILTIN_HASATTR_WORKER_GLOBAL_NAME = "hasattr"
_REFLECTIVE_BUILTIN_HASATTR_OBJECT_TYPE_REPLAY_KEY = "object_type"
_REFLECTIVE_BUILTIN_HASATTR_ATTRIBUTE_NAME_REPLAY_KEY = "attribute_name"
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SUBJECT_ID = "unsupported:call:main.py:2:11"
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_FILE_PATH = "main.py"
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_START_LINE = "2"
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_START_COLUMN = "11"
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_END_LINE = "2"
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_SOURCE_END_COLUMN = "29"
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_REPLAY_TARGET_SEED = "main.probe_attribute"
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_REPLAY_SELECTOR_SEED = (
    "call:main.probe_attribute:reflective_builtin:hasattr/2@main.py:2:11:2:29"
)
_REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_SOURCE_END_COLUMN = "37"
_REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_REPLAY_TARGET_SEED = (
    "main.probe_literal_attribute"
)
_REFLECTIVE_BUILTIN_HASATTR_LITERAL_BIT_LENGTH_REPLAY_SELECTOR_SEED = (
    "call:main.probe_literal_attribute:reflective_builtin:hasattr/2@main.py:2:11:2:37"
)
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_OBJECT_TYPE = "builtins.int"
_REFLECTIVE_BUILTIN_HASATTR_INT_BIT_LENGTH_ATTRIBUTE_NAME = "bit_length"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_FORM_LABEL = "reflective_builtin:getattr/2"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_BOUNDARY_TEXT = "getattr(obj, name)"
_REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_WORKER_BOUNDARY_TEXT = (
    'getattr(obj, "bit_length")'
)
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_FORM_LABEL = "reflective_builtin:getattr/3"
_REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_BOUNDARY_TEXT = "getattr(obj, name, default)"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_GLOBAL_NAME = "getattr"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_VALUE = "returned_value"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_RAISED_ATTRIBUTE_ERROR = "raised_attribute_error"
_REFLECTIVE_BUILTIN_GETATTR_WORKER_RETURNED_DEFAULT_VALUE = "returned_default_value"
_REFLECTIVE_BUILTIN_GETATTR_OBJECT_TYPE_REPLAY_KEY = "object_type"
_REFLECTIVE_BUILTIN_GETATTR_ATTRIBUTE_NAME_REPLAY_KEY = "attribute_name"
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SUBJECT_ID = "unsupported:call:main.py:2:11"
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_FILE_PATH = "main.py"
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_START_LINE = "2"
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_START_COLUMN = "11"
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_SOURCE_END_LINE = "2"
_REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_SOURCE_END_COLUMN = "37"
_REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_REPLAY_TARGET_SEED = (
    "main.probe_literal_attribute"
)
_REFLECTIVE_BUILTIN_GETATTR_LITERAL_BIT_LENGTH_REPLAY_SELECTOR_SEED = (
    "call:main.probe_literal_attribute:reflective_builtin:getattr/2@main.py:2:11:2:37"
)
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_OBJECT_TYPE = "builtins.int"
_REFLECTIVE_BUILTIN_GETATTR_INT_BIT_LENGTH_ATTRIBUTE_NAME = "bit_length"
_REFLECTIVE_BUILTIN_VARS_WORKER_FORM_LABEL = "reflective_builtin:vars/1"
_REFLECTIVE_BUILTIN_VARS_WORKER_BOUNDARY_TEXT = "vars(obj)"
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_FORM_LABEL = "reflective_builtin:vars/0"
_REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_BOUNDARY_TEXT = "vars()"
_REFLECTIVE_BUILTIN_VARS_WORKER_GLOBAL_NAME = "vars"
_REFLECTIVE_BUILTIN_VARS_WORKER_RETURNED_NAMESPACE = "returned_namespace"
_REFLECTIVE_BUILTIN_VARS_WORKER_RAISED_TYPE_ERROR = "raised_type_error"
_REFLECTIVE_BUILTIN_VARS_OBJECT_TYPE_REPLAY_KEY = "object_type"
_REFLECTIVE_BUILTIN_VARS_TYPE_ERROR_OBJECT_TYPE = "builtins.int"
_REFLECTIVE_BUILTIN_VARS_RETURNED_NAMESPACE_OBJECT_TYPE = "main.ProbeRecord"
_REFLECTIVE_BUILTIN_VARS_PROBE_RECORD_CLASS_NAME = "ProbeRecord"
_REFLECTIVE_BUILTIN_VARS_PROBE_RECORD_LABEL = "ready"
_REFLECTIVE_BUILTIN_DIR_WORKER_FORM_LABEL = "reflective_builtin:dir/1"
_REFLECTIVE_BUILTIN_DIR_WORKER_BOUNDARY_TEXT = "dir(obj)"
_REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_FORM_LABEL = "reflective_builtin:dir/0"
_REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_BOUNDARY_TEXT = "dir()"
_REFLECTIVE_BUILTIN_DIR_WORKER_BOUNDARY_TEXT_BY_FORM_LABEL: Mapping[str, str] = (
    MappingProxyType(
        {
            _REFLECTIVE_BUILTIN_DIR_WORKER_FORM_LABEL: (
                _REFLECTIVE_BUILTIN_DIR_WORKER_BOUNDARY_TEXT
            ),
            _REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_FORM_LABEL: (
                _REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_BOUNDARY_TEXT
            ),
        }
    )
)
_REFLECTIVE_BUILTIN_DIR_WORKER_GLOBAL_NAME = "dir"
_REFLECTIVE_BUILTIN_DIR_OBJECT_TYPE_REPLAY_KEY = "object_type"
_REFLECTIVE_BUILTIN_DIR_INT_DIRECTORY_OBJECT_TYPE = "builtins.int"
_REFLECTIVE_BUILTIN_WORKER_FORM_LABELS = (
    _REFLECTIVE_BUILTIN_HASATTR_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_GETATTR_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_GETATTR_DEFAULT_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_VARS_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_VARS_ZERO_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_DIR_WORKER_FORM_LABEL,
    _REFLECTIVE_BUILTIN_DIR_ZERO_WORKER_FORM_LABEL,
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
_REFLECTIVE_BUILTIN_DIR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe reflective builtin dir worker target execution failed"
)
_REFLECTIVE_BUILTIN_DIR_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe reflective builtin dir worker form must be exactly dir(obj)",
        "runtime probe reflective builtin dir worker form must be exactly dir()",
    )
)

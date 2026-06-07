"""Private runtime-mutation worker contract constants."""

from __future__ import annotations

_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_FORM_LABEL = "runtime_mutation:globals/0"
_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_BOUNDARY_TEXT = "globals()"
_RUNTIME_MUTATION_GLOBALS_WORKER_GLOBAL_NAME = "globals"
_RUNTIME_MUTATION_GLOBALS_WORKER_RETURNED_NAMESPACE = "returned_namespace"
_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe runtime mutation globals zero worker target execution failed"
)
_RUNTIME_MUTATION_GLOBALS_ZERO_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe runtime mutation globals zero worker form must be exactly "
        "globals()",
    )
)
_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_FORM_LABEL = "runtime_mutation:locals/0"
_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_BOUNDARY_TEXT = "locals()"
_RUNTIME_MUTATION_LOCALS_WORKER_GLOBAL_NAME = "locals"
_RUNTIME_MUTATION_LOCALS_WORKER_RETURNED_NAMESPACE = "returned_namespace"
_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe runtime mutation locals zero worker target execution failed"
)
_RUNTIME_MUTATION_LOCALS_ZERO_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    ("runtime probe runtime mutation locals zero worker form must be exactly locals()",)
)
_RUNTIME_MUTATION_SETATTR_WORKER_FORM_LABEL = "runtime_mutation:setattr/3"
_RUNTIME_MUTATION_SETATTR_WORKER_BOUNDARY_TEXT = "setattr(obj, name, value)"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT = (
    'setattr(obj, "flag", value)'
)
_RUNTIME_MUTATION_SETATTR_WORKER_GLOBAL_NAME = "setattr"
_RUNTIME_MUTATION_SETATTR_WORKER_RETURNED_NONE = "returned_none"
_RUNTIME_MUTATION_SETATTR_OBJECT_TYPE_REPLAY_KEY = "object_type"
_RUNTIME_MUTATION_SETATTR_ATTRIBUTE_NAME_REPLAY_KEY = "attribute_name"
_RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_TYPE_REPLAY_KEY = "assigned_value_type"
_RUNTIME_MUTATION_SETATTR_ASSIGNED_VALUE_LITERAL_REPLAY_KEY = "assigned_value_literal"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SUBJECT_ID = "unsupported:call:main.py:7:4"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_FILE_PATH = "main.py"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_START_LINE = "7"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_START_COLUMN = "4"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_END_LINE = "7"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_SOURCE_END_COLUMN = "31"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_REPLAY_TARGET_SEED = (
    "main.probe_set_literal_attribute"
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_REPLAY_SELECTOR_SEED = (
    "call:main.probe_set_literal_attribute:runtime_mutation:setattr/3@main.py:7:4:7:31"
)
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_OBJECT_TYPE = "main.ProbeTarget"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_ATTRIBUTE_NAME = "flag"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_ASSIGNED_VALUE_TYPE = "builtins.str"
_RUNTIME_MUTATION_SETATTR_LITERAL_FLAG_ASSIGNED_VALUE_LITERAL = "ready"
_RUNTIME_MUTATION_SETATTR_NAME_FLAG_CLASS_NAME = "ProbeTarget"
_RUNTIME_MUTATION_SETATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe runtime mutation setattr worker target execution failed"
)
_RUNTIME_MUTATION_SETATTR_WORKER_MUTATION_FAILED_MESSAGE = (
    "runtime probe runtime mutation setattr worker setattr call must assign "
    "an attribute"
)
_RUNTIME_MUTATION_SETATTR_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe runtime mutation setattr worker form must be exactly "
        "setattr(obj, name, value)",
        "runtime probe runtime mutation setattr worker attribute name must be a string",
        _RUNTIME_MUTATION_SETATTR_WORKER_MUTATION_FAILED_MESSAGE,
    )
)
_RUNTIME_MUTATION_DELATTR_WORKER_FORM_LABEL = "runtime_mutation:delattr/2"
_RUNTIME_MUTATION_DELATTR_WORKER_BOUNDARY_TEXT = "delattr(obj, name)"
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_WORKER_BOUNDARY_TEXT = 'delattr(obj, "flag")'
_RUNTIME_MUTATION_DELATTR_WORKER_GLOBAL_NAME = "delattr"
_RUNTIME_MUTATION_DELATTR_WORKER_DELETED_ATTRIBUTE = "deleted_attribute"
_RUNTIME_MUTATION_DELATTR_OBJECT_TYPE_REPLAY_KEY = "object_type"
_RUNTIME_MUTATION_DELATTR_ATTRIBUTE_NAME_REPLAY_KEY = "attribute_name"
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SUBJECT_ID = "unsupported:call:main.py:7:4"
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_FILE_PATH = "main.py"
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_START_LINE = "7"
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_START_COLUMN = "4"
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_END_LINE = "7"
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_SOURCE_END_COLUMN = "24"
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_REPLAY_TARGET_SEED = (
    "main.probe_delete_literal_attribute"
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_REPLAY_SELECTOR_SEED = (
    "call:main.probe_delete_literal_attribute:runtime_mutation:delattr/2"
    "@main.py:7:4:7:24"
)
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_OBJECT_TYPE = "main.ProbeTarget"
_RUNTIME_MUTATION_DELATTR_LITERAL_FLAG_ATTRIBUTE_NAME = "flag"
_RUNTIME_MUTATION_DELATTR_PROBE_TARGET_CLASS_NAME = "ProbeTarget"
_RUNTIME_MUTATION_DELATTR_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe runtime mutation delattr worker target execution failed"
)
_RUNTIME_MUTATION_DELATTR_WORKER_DELETION_FAILED_MESSAGE = (
    "runtime probe runtime mutation delattr worker delattr call must delete "
    "an attribute"
)
_RUNTIME_MUTATION_DELATTR_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe runtime mutation delattr worker form must be exactly "
        "delattr(obj, name)",
        "runtime probe runtime mutation delattr worker attribute name must be a string",
        _RUNTIME_MUTATION_DELATTR_WORKER_DELETION_FAILED_MESSAGE,
    )
)

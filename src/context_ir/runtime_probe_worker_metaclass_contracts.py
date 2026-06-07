"""Private metaclass behavior worker contract constants."""

from __future__ import annotations

_METACLASS_BEHAVIOR_KEYWORD_WORKER_FORM_LABEL = "metaclass_behavior:keyword"
_METACLASS_BEHAVIOR_KEYWORD_WORKER_BOUNDARY_TEXT = "metaclass=Meta"
_METACLASS_BEHAVIOR_KEYWORD_WORKER_BUILD_CLASS_GLOBAL_NAME = "__build_class__"
_METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_CLASS_NAME = "Example"
_METACLASS_BEHAVIOR_KEYWORD_WORKER_SELECTED_METACLASS_NAME = "Meta"
_METACLASS_BEHAVIOR_KEYWORD_WORKER_CLASS_CREATION_OUTCOME = "created_class"
_METACLASS_BEHAVIOR_KEYWORD_WORKER_TARGET_IMPORT_FAILED_MESSAGE = (
    "runtime probe metaclass behavior worker source module import failed"
)
_METACLASS_BEHAVIOR_KEYWORD_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe metaclass behavior worker target must capture exactly one "
        "class creation",
        "runtime probe metaclass behavior worker target class must be top-level "
        "Example",
        "runtime probe metaclass behavior worker target class must use exact "
        "metaclass keyword",
        "runtime probe metaclass behavior worker selected metaclass is unsupported",
        "runtime probe metaclass behavior worker created class is unsupported",
    )
)

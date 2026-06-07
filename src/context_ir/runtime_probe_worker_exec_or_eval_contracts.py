"""Private exec/eval worker contract constants."""

from __future__ import annotations

_EXEC_OR_EVAL_EXEC_WORKER_FORM_LABEL = "exec_or_eval:exec/1"
_EXEC_OR_EVAL_EXEC_WORKER_BOUNDARY_TEXT = "exec(source)"
_EXEC_OR_EVAL_EXEC_WORKER_GLOBAL_NAME = "exec"
_EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHAPE = "literal_statement"
_EXEC_OR_EVAL_EXEC_WORKER_SOURCE_SHA256 = (
    "d74ff0ee8da3b9806b18c877dbf29bbde50b5bd8e4dad7a3a725000feb82e8f1"
)
_EXEC_OR_EVAL_EXEC_WORKER_EXECUTION_OUTCOME = "completed"
_EXEC_OR_EVAL_EXEC_WORKER_STATEMENT_KIND = "pass"
_EXEC_OR_EVAL_EXEC_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe exec worker target execution failed"
)
_EXEC_OR_EVAL_EXEC_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe exec worker form must be exactly exec(source)",
        "runtime probe exec worker source must be a string",
        "runtime probe exec worker source must be exactly pass",
        "runtime probe exec worker source must parse as exactly one pass statement",
    )
)
_EXEC_OR_EVAL_EVAL_WORKER_FORM_LABEL = "exec_or_eval:eval/1"
_EXEC_OR_EVAL_EVAL_WORKER_BOUNDARY_TEXT = "eval(source)"
_EXEC_OR_EVAL_EVAL_WORKER_GLOBAL_NAME = "eval"
_EXEC_OR_EVAL_EVAL_WORKER_SOURCE_TEXT = '"eval-probe-value"'
_EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHAPE = "literal_expression"
_EXEC_OR_EVAL_EVAL_WORKER_SOURCE_SHA256 = (
    "c40df915dac30fcea0f6f3394139e5608eb1e7af6f94838bd401ce1370856199"
)
_EXEC_OR_EVAL_EVAL_WORKER_EVALUATION_OUTCOME = "returned_value"
_EXEC_OR_EVAL_EVAL_WORKER_RESULT_TYPE = "builtins.str"
_EXEC_OR_EVAL_EVAL_WORKER_TARGET_EXECUTION_FAILED_MESSAGE = (
    "runtime probe eval worker target execution failed"
)
_EXEC_OR_EVAL_EVAL_WORKER_SHAPE_ERROR_MESSAGES = frozenset(
    (
        "runtime probe eval worker form must be exactly eval(source)",
        "runtime probe eval worker source must be a string",
        'runtime probe eval worker source must be exactly "eval-probe-value"',
        "runtime probe eval worker source must parse as exactly one string "
        "literal expression",
        "runtime probe eval worker result must be a string",
    )
)

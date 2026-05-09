"""Fail-closed local Python runtime probe worker ingress."""

from __future__ import annotations

import sys
from typing import TextIO

from context_ir.runtime_probe_execution import (
    parse_runtime_probe_local_python_worker_request_payload,
)

_MALFORMED_REQUEST_EXIT_CODE = 64
_REJECTED_REQUEST_EXIT_CODE = 78
_MALFORMED_REQUEST_MESSAGE = "runtime_probe_worker: rejected malformed worker request\n"
_REJECTED_REQUEST_MESSAGE = (
    "runtime_probe_worker: rejected worker request without executing probe\n"
)


def main(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Read one worker request from stdin and reject it without probe execution."""
    input_stream = sys.stdin if stdin is None else stdin
    error_stream = sys.stderr if stderr is None else stderr
    del stdout

    stdin_text = input_stream.read()
    try:
        parse_runtime_probe_local_python_worker_request_payload(stdin_text)
    except Exception:
        error_stream.write(_MALFORMED_REQUEST_MESSAGE)
        return _MALFORMED_REQUEST_EXIT_CODE

    error_stream.write(_REJECTED_REQUEST_MESSAGE)
    return _REJECTED_REQUEST_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())

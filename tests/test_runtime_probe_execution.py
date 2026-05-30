"""Tests for internal runtime probe execution input materialization."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import context_ir
import context_ir.runtime_probe_execution as runtime_probe_execution
import context_ir.runtime_probe_requests as runtime_probe_requests
import context_ir.runtime_probe_results as runtime_probe_results
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.runtime_probe_execution import (
    assemble_runtime_probe_result_batch_from_execution_attempts,
    assemble_runtime_probe_result_batch_from_runner_request_attempts,
    collect_runtime_probe_execution_attempts_from_runner_requests,
    execute_runtime_probe_local_python_subprocess_invocation,
    execute_runtime_probe_local_python_subprocess_invocation_attempt,
    make_runtime_probe_default_local_python_subprocess_runner,
    make_runtime_probe_dynamic_import_local_python_subprocess_runner,
    make_runtime_probe_exec_or_eval_eval_local_python_subprocess_runner,
    make_runtime_probe_exec_or_eval_exec_local_python_subprocess_runner,
    make_runtime_probe_metaclass_behavior_keyword_local_python_subprocess_runner,
    make_runtime_probe_reflective_dir_local_python_subprocess_runner,
    make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner,
    make_runtime_probe_reflective_getattr_default_local_python_subprocess_runner,
    make_runtime_probe_reflective_getattr_local_python_subprocess_runner,
    make_runtime_probe_reflective_hasattr_local_python_subprocess_runner,
    make_runtime_probe_reflective_vars_local_python_subprocess_runner,
    make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner,
    make_runtime_probe_runtime_mutation_delattr_local_python_subprocess_runner,
    make_runtime_probe_runtime_mutation_globals_zero_local_python_subprocess_runner,
    make_runtime_probe_runtime_mutation_locals_zero_local_python_subprocess_runner,
    make_runtime_probe_runtime_mutation_setattr_local_python_subprocess_runner,
    materialize_runtime_probe_local_python_process_completion,
    materialize_runtime_probe_local_python_process_completion_attempt,
    materialize_runtime_probe_local_python_stdout_protocol_attempt,
    materialize_runtime_probe_local_python_stdout_protocol_failure_attempt,
    materialize_runtime_probe_local_python_stdout_protocol_result,
    materialize_runtime_probe_local_python_subprocess_exception_attempt,
    materialize_runtime_probe_local_python_subprocess_invocation,
    materialize_runtime_probe_local_python_worker_request_payload,
    materialize_runtime_probe_local_python_worker_request_stdin_transport,
    parse_runtime_probe_local_python_worker_request_payload,
    serialize_runtime_probe_local_python_worker_request_payload,
)
from context_ir.semantic_types import (
    CapabilityTier,
    RepositorySnapshotBasis,
    SemanticDiagnosticBoundary,
    SemanticDiagnosticBoundaryKind,
    SemanticDiagnosticResult,
    SemanticDiagnosticUnitStatus,
    SemanticProgram,
    SemanticSubjectKind,
    SourceSite,
    SourceSpan,
    UnresolvedReasonCode,
)

_EXPECTED_REPLAY_INPUT_KEYS = (
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

_IMPORTLIB_IMPORT_MODULE_FORM_LABEL = "dynamic_import:importlib.import_module/1"
_LOADER_IMPORT_MODULE_FORM_LABEL = "dynamic_import:loader.import_module/1"
_IMPORTED_IMPORT_MODULE_FORM_LABEL = "dynamic_import:import_module/1"
_LOAD_MODULE_FORM_LABEL = "dynamic_import:load_module/1"
_BUILTIN_IMPORT_FORM_LABEL = "dynamic_import:__import__/1"
_BUILTINS_IMPORT_FORM_LABEL = "dynamic_import:builtins.__import__/1"
_LOADER_BUILTIN_IMPORT_FORM_LABEL = "dynamic_import:loader.__import__/1"
_REFLECTIVE_HASATTR_FORM_LABEL = "reflective_builtin:hasattr/2"
_REFLECTIVE_GETATTR_TWO_FORM_LABEL = "reflective_builtin:getattr/2"
_REFLECTIVE_GETATTR_THREE_FORM_LABEL = "reflective_builtin:getattr/3"
_REFLECTIVE_VARS_ONE_FORM_LABEL = "reflective_builtin:vars/1"
_REFLECTIVE_VARS_ZERO_FORM_LABEL = "reflective_builtin:vars/0"
_REFLECTIVE_DIR_ONE_FORM_LABEL = "reflective_builtin:dir/1"
_REFLECTIVE_DIR_ZERO_FORM_LABEL = "reflective_builtin:dir/0"
_RUNTIME_MUTATION_GLOBALS_ZERO_FORM_LABEL = "runtime_mutation:globals/0"
_RUNTIME_MUTATION_LOCALS_ZERO_FORM_LABEL = "runtime_mutation:locals/0"
_RUNTIME_MUTATION_SETATTR_FORM_LABEL = "runtime_mutation:setattr/3"
_RUNTIME_MUTATION_DELATTR_FORM_LABEL = "runtime_mutation:delattr/2"
_EXEC_OR_EVAL_EXEC_FORM_LABEL = "exec_or_eval:exec/1"
_EXEC_OR_EVAL_EVAL_FORM_LABEL = "exec_or_eval:eval/1"
_METACLASS_KEYWORD_FORM_LABEL = "metaclass_behavior:keyword"
_EXEC_PASS_SOURCE_SHA256 = (
    "d74ff0ee8da3b9806b18c877dbf29bbde50b5bd8e4dad7a3a725000feb82e8f1"
)
_EVAL_SOURCE_SHA256 = "c40df915dac30fcea0f6f3394139e5608eb1e7af6f94838bd401ce1370856199"

_EXPECTED_DEFAULT_LOCAL_PYTHON_RUNNER_HANDLER_KEYS = (
    (
        runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        _LOADER_IMPORT_MODULE_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        _IMPORTED_IMPORT_MODULE_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        _LOAD_MODULE_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        _BUILTINS_IMPORT_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        _LOADER_BUILTIN_IMPORT_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        _BUILTIN_IMPORT_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        _REFLECTIVE_HASATTR_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        _REFLECTIVE_GETATTR_THREE_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        _REFLECTIVE_VARS_ONE_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        _REFLECTIVE_VARS_ZERO_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        _REFLECTIVE_DIR_ONE_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        _REFLECTIVE_DIR_ZERO_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        _RUNTIME_MUTATION_GLOBALS_ZERO_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        _RUNTIME_MUTATION_LOCALS_ZERO_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        _RUNTIME_MUTATION_SETATTR_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        _RUNTIME_MUTATION_DELATTR_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL,
        _EXEC_OR_EVAL_EXEC_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL,
        _EXEC_OR_EVAL_EVAL_FORM_LABEL,
    ),
    (
        runtime_probe_requests.RuntimeProbeFamily.METACLASS_BEHAVIOR,
        _METACLASS_KEYWORD_FORM_LABEL,
    ),
)

_EXPECTED_CURRENT_FORMS = {
    _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
    _LOAD_MODULE_FORM_LABEL,
    _BUILTINS_IMPORT_FORM_LABEL,
    _LOADER_BUILTIN_IMPORT_FORM_LABEL,
    "dynamic_import:__import__/1",
    "reflective_builtin:getattr/2",
    "reflective_builtin:getattr/3",
    "reflective_builtin:hasattr/2",
    "reflective_builtin:vars/1",
    "reflective_builtin:vars/0",
    "reflective_builtin:dir/1",
    "reflective_builtin:dir/0",
    "runtime_mutation:globals/0",
    "runtime_mutation:locals/0",
    "runtime_mutation:setattr/3",
    "runtime_mutation:delattr/2",
    "exec_or_eval:exec/1",
    "exec_or_eval:eval/1",
    "metaclass_behavior:keyword",
}


def _derived_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted semantic pipeline through frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _write_runtime_probe_program(tmp_path: Path) -> None:
    """Write source that exercises every currently planned probe family/form."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import builtins
            import builtins as loader
            import importlib
            from importlib import import_module as load_module

            class Meta(type):
                pass

            class Example(metaclass=Meta):
                pass

            def run(
                obj: object,
                name: str,
                value: object,
                source: str,
                default: object,
            ) -> None:
                importlib.import_module(name)
                load_module(name)
                builtins.__import__(name)
                loader.__import__(name)
                __import__(name)
                getattr(obj, name)
                getattr(obj, name, default)
                hasattr(obj, name)
                vars(obj)
                vars()
                dir(obj)
                dir()
                globals()
                locals()
                setattr(obj, name, value)
                delattr(obj, name)
                exec(source)
                eval(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _source_site(
    start_line: int = 3,
    *,
    snippet: str = "importlib.import_module(name)",
) -> SourceSite:
    """Return a stable source site for a synthetic runtime probe request."""
    return SourceSite(
        site_id=f"site:main.py:{start_line}:4",
        file_path="main.py",
        span=SourceSpan(
            start_line=start_line,
            start_column=4,
            end_line=start_line,
            end_column=28,
        ),
        snippet=snippet,
    )


def _request(
    start_line: int = 3,
    *,
    form_label: str = _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
    boundary_text: str = "importlib.import_module(name)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned runtime probe request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:main.py:{start_line}:4",
        source_site=_source_site(start_line, snippet=boundary_text),
        reason_code=UnresolvedReasonCode.DYNAMIC_IMPORT,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label=form_label,
        replay_target_seed="main.run",
        replay_selector_seed=(
            f"call:main.run:dynamic_import@main.py:{start_line}:4:{start_line}:28"
        ),
    )


def _reflective_hasattr_request(
    start_line: int = 3,
    *,
    form_label: str = _REFLECTIVE_HASATTR_FORM_LABEL,
    boundary_text: str = "hasattr(obj, name)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned reflective-builtin request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:main.py:{start_line}:4",
        source_site=_source_site(start_line, snippet=boundary_text),
        reason_code=UnresolvedReasonCode.REFLECTIVE_BUILTIN,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=form_label,
        replay_target_seed="main.run",
        replay_selector_seed=(
            f"call:main.run:{form_label}@main.py:{start_line}:4:{start_line}:28"
        ),
    )


def _reflective_hasattr_exact_replay_input_request() -> (
    runtime_probe_requests.RuntimeProbeRequest
):
    """Return the exact hasattr pilot request that carries replay inputs."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id="unsupported:call:main.py:2:11",
        source_site=SourceSite(
            site_id="site:main.py:2:11",
            file_path="main.py",
            span=SourceSpan(
                start_line=2,
                start_column=11,
                end_line=2,
                end_column=29,
            ),
            snippet="hasattr(obj, name)",
        ),
        reason_code=UnresolvedReasonCode.REFLECTIVE_BUILTIN,
        boundary_text="hasattr(obj, name)",
        family_label=runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_REFLECTIVE_HASATTR_FORM_LABEL,
        replay_target_seed="main.probe_attribute",
        replay_selector_seed=(
            "call:main.probe_attribute:"
            f"{_REFLECTIVE_HASATTR_FORM_LABEL}@main.py:2:11:2:29"
        ),
    )


def _reflective_hasattr_literal_exact_replay_input_request() -> (
    runtime_probe_requests.RuntimeProbeRequest
):
    """Return the exact literal-hasattr pilot request that carries replay inputs."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id="unsupported:call:main.py:2:11",
        source_site=SourceSite(
            site_id="site:main.py:2:11",
            file_path="main.py",
            span=SourceSpan(
                start_line=2,
                start_column=11,
                end_line=2,
                end_column=37,
            ),
            snippet='hasattr(obj, "bit_length")',
        ),
        reason_code=UnresolvedReasonCode.REFLECTIVE_BUILTIN,
        boundary_text='hasattr(obj, "bit_length")',
        family_label=runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_REFLECTIVE_HASATTR_FORM_LABEL,
        replay_target_seed="main.probe_literal_attribute",
        replay_selector_seed=(
            "call:main.probe_literal_attribute:"
            f"{_REFLECTIVE_HASATTR_FORM_LABEL}@main.py:2:11:2:37"
        ),
    )


def _reflective_getattr_request(
    start_line: int = 3,
    *,
    form_label: str = _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
    boundary_text: str = "getattr(obj, name)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned reflective-getattr request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:main.py:{start_line}:4",
        source_site=_source_site(start_line, snippet=boundary_text),
        reason_code=UnresolvedReasonCode.REFLECTIVE_BUILTIN,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=form_label,
        replay_target_seed="main.run",
        replay_selector_seed=(
            f"call:main.run:{form_label}@main.py:{start_line}:4:{start_line}:28"
        ),
    )


def _reflective_getattr_literal_exact_replay_input_request() -> (
    runtime_probe_requests.RuntimeProbeRequest
):
    """Return the exact literal-getattr pilot request that carries replay inputs."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id="unsupported:call:main.py:2:11",
        source_site=SourceSite(
            site_id="site:main.py:2:11",
            file_path="main.py",
            span=SourceSpan(
                start_line=2,
                start_column=11,
                end_line=2,
                end_column=37,
            ),
            snippet='getattr(obj, "bit_length")',
        ),
        reason_code=UnresolvedReasonCode.REFLECTIVE_BUILTIN,
        boundary_text='getattr(obj, "bit_length")',
        family_label=runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_REFLECTIVE_GETATTR_TWO_FORM_LABEL,
        replay_target_seed="main.probe_literal_attribute",
        replay_selector_seed=(
            "call:main.probe_literal_attribute:"
            f"{_REFLECTIVE_GETATTR_TWO_FORM_LABEL}@main.py:2:11:2:37"
        ),
    )


def _reflective_getattr_default_request(
    start_line: int = 3,
    *,
    form_label: str = _REFLECTIVE_GETATTR_THREE_FORM_LABEL,
    boundary_text: str = "getattr(obj, name, default)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned reflective-getattr/3 request."""
    return _reflective_getattr_request(
        start_line,
        form_label=form_label,
        boundary_text=boundary_text,
    )


def _reflective_vars_request(
    start_line: int = 3,
    *,
    form_label: str = _REFLECTIVE_VARS_ONE_FORM_LABEL,
    boundary_text: str = "vars(obj)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned reflective-vars request."""
    return _reflective_getattr_request(
        start_line,
        form_label=form_label,
        boundary_text=boundary_text,
    )


def _reflective_vars_zero_request(
    start_line: int = 3,
    *,
    form_label: str = _REFLECTIVE_VARS_ZERO_FORM_LABEL,
    boundary_text: str = "vars()",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned reflective-vars/0 request."""
    return _reflective_getattr_request(
        start_line,
        form_label=form_label,
        boundary_text=boundary_text,
    )


def _reflective_dir_request(
    start_line: int = 3,
    *,
    form_label: str = _REFLECTIVE_DIR_ONE_FORM_LABEL,
    boundary_text: str = "dir(obj)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned reflective-dir request."""
    return _reflective_getattr_request(
        start_line,
        form_label=form_label,
        boundary_text=boundary_text,
    )


def _runtime_mutation_globals_zero_request(
    start_line: int = 3,
    *,
    form_label: str = _RUNTIME_MUTATION_GLOBALS_ZERO_FORM_LABEL,
    boundary_text: str = "globals()",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned runtime-mutation globals/0 request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:main.py:{start_line}:4",
        source_site=_source_site(start_line, snippet=boundary_text),
        reason_code=UnresolvedReasonCode.RUNTIME_MUTATION,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=form_label,
        replay_target_seed="main.run",
        replay_selector_seed=(
            f"call:main.run:{form_label}@main.py:{start_line}:4:{start_line}:28"
        ),
    )


def _runtime_mutation_locals_zero_request(
    start_line: int = 3,
    *,
    form_label: str = _RUNTIME_MUTATION_LOCALS_ZERO_FORM_LABEL,
    boundary_text: str = "locals()",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned runtime-mutation locals/0 request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:main.py:{start_line}:4",
        source_site=_source_site(start_line, snippet=boundary_text),
        reason_code=UnresolvedReasonCode.RUNTIME_MUTATION,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=form_label,
        replay_target_seed="main.run",
        replay_selector_seed=(
            f"call:main.run:{form_label}@main.py:{start_line}:4:{start_line}:28"
        ),
    )


def _runtime_mutation_delattr_request(
    start_line: int = 3,
    *,
    form_label: str = _RUNTIME_MUTATION_DELATTR_FORM_LABEL,
    boundary_text: str = "delattr(obj, name)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned runtime-mutation delattr request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:main.py:{start_line}:4",
        source_site=_source_site(start_line, snippet=boundary_text),
        reason_code=UnresolvedReasonCode.RUNTIME_MUTATION,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=form_label,
        replay_target_seed="main.run",
        replay_selector_seed=(
            f"call:main.run:{form_label}@main.py:{start_line}:4:{start_line}:28"
        ),
    )


def _runtime_mutation_delattr_literal_exact_replay_input_request() -> (
    runtime_probe_requests.RuntimeProbeRequest
):
    """Return the exact literal-delattr pilot request that carries replay inputs."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id="unsupported:call:main.py:7:4",
        source_site=SourceSite(
            site_id="site:main.py:7:4",
            file_path="main.py",
            span=SourceSpan(
                start_line=7,
                start_column=4,
                end_line=7,
                end_column=24,
            ),
            snippet='delattr(obj, "flag")',
        ),
        reason_code=UnresolvedReasonCode.RUNTIME_MUTATION,
        boundary_text='delattr(obj, "flag")',
        family_label=runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=_RUNTIME_MUTATION_DELATTR_FORM_LABEL,
        replay_target_seed="main.probe_delete_literal_attribute",
        replay_selector_seed=(
            "call:main.probe_delete_literal_attribute:"
            f"{_RUNTIME_MUTATION_DELATTR_FORM_LABEL}@main.py:7:4:7:24"
        ),
    )


def _runtime_mutation_setattr_request(
    start_line: int = 3,
    *,
    form_label: str = _RUNTIME_MUTATION_SETATTR_FORM_LABEL,
    boundary_text: str = "setattr(obj, name, value)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned runtime-mutation setattr request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:main.py:{start_line}:4",
        source_site=_source_site(start_line, snippet=boundary_text),
        reason_code=UnresolvedReasonCode.RUNTIME_MUTATION,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=form_label,
        replay_target_seed="main.run",
        replay_selector_seed=(
            f"call:main.run:{form_label}@main.py:{start_line}:4:{start_line}:28"
        ),
    )


def _exec_request(
    start_line: int = 3,
    *,
    form_label: str = _EXEC_OR_EVAL_EXEC_FORM_LABEL,
    boundary_text: str = "exec(source)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned exec request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:call:main.py:{start_line}:4",
        source_site=_source_site(start_line, snippet=boundary_text),
        reason_code=UnresolvedReasonCode.EXEC_OR_EVAL,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL,
        form_label=form_label,
        replay_target_seed="main.run",
        replay_selector_seed=(
            f"call:main.run:{form_label}@main.py:{start_line}:4:{start_line}:28"
        ),
    )


def _eval_request(
    start_line: int = 3,
    *,
    form_label: str = _EXEC_OR_EVAL_EVAL_FORM_LABEL,
    boundary_text: str = "eval(source)",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned eval request."""
    return _exec_request(
        start_line,
        form_label=form_label,
        boundary_text=boundary_text,
    )


def _metaclass_keyword_request(
    start_line: int = 3,
    *,
    form_label: str = _METACLASS_KEYWORD_FORM_LABEL,
    boundary_text: str = "metaclass=Meta",
    replay_target_seed: str = "main.Example",
) -> runtime_probe_requests.RuntimeProbeRequest:
    """Return one synthetic planned metaclass-keyword request."""
    return runtime_probe_requests.RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=f"unsupported:metaclass:main.py:{start_line}:4",
        source_site=_source_site(start_line, snippet=boundary_text),
        reason_code=UnresolvedReasonCode.METACLASS_BEHAVIOR,
        boundary_text=boundary_text,
        family_label=runtime_probe_requests.RuntimeProbeFamily.METACLASS_BEHAVIOR,
        form_label=form_label,
        replay_target_seed=replay_target_seed,
        replay_selector_seed=(
            f"class:{replay_target_seed}:metaclass@main.py:"
            f"{start_line}:4:{start_line}:28"
        ),
    )


def _plan(
    *requests: runtime_probe_requests.RuntimeProbeRequest,
) -> runtime_probe_requests.RuntimeProbeRequestPlan:
    """Build a request plan around supplied synthetic probe requests."""
    return runtime_probe_requests.build_runtime_probe_request_plan(requests)


def _snapshot_basis() -> RepositorySnapshotBasis:
    """Return stable repository snapshot metadata for replay artifacts."""
    return RepositorySnapshotBasis(
        snapshot_kind="git_commit",
        snapshot_id="abc123def456",
        is_dirty_worktree=False,
    )


def _field(
    key: str = "python_version",
    value: str = "3.11",
) -> runtime_probe_results.RuntimeProbeReplayField:
    """Return one typed replay/runtime assumption field."""
    return runtime_probe_results.RuntimeProbeReplayField(key=key, value=value)


def _runtime_assumptions() -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return the explicit runtime assumptions for materialized input tests."""
    return (
        _field("python_version", "3.11"),
        _field("dependency_mode", "offline-fixture"),
    )


def _source_site_identity(
    request: runtime_probe_requests.RuntimeProbeRequest,
) -> tuple[str, int, int, int, int]:
    """Return the stable source-site identity for one planned request."""
    span = request.source_site.span
    return (
        request.source_site.file_path,
        span.start_line,
        span.start_column,
        span.end_line,
        span.end_column,
    )


def _materialized_batch(
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
) -> runtime_probe_execution.RuntimeProbeExecutionInputBatch:
    """Return a materialized execution-input batch for validation tests."""
    return runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
        plan,
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision="runtime-probe-contract:test.1",
        runtime_assumptions=_runtime_assumptions(),
    )


def _runner_environment() -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return explicit environment fields for non-executing runner requests."""
    return (
        _field("python_version", "3.11"),
        _field("platform", "linux-x86_64"),
    )


def _runner_assumptions() -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return explicit assumption fields for non-executing runner requests."""
    return (
        _field("network", "disabled"),
        _field("filesystem_mode", "read_only_fixture"),
    )


def _local_python_runner_environment() -> tuple[
    runtime_probe_results.RuntimeProbeReplayField,
    ...,
]:
    """Return local-Python environment fields for context derivation tests."""
    return (
        _field("python_version", "3.11"),
        _field("repository_root", "/workspace/context-ir"),
        _field("platform", "linux-x86_64"),
        _field("python_path_entry", "/workspace/context-ir/src"),
        _field("working_directory", "/workspace/context-ir"),
        _field("python_path_entry", "/workspace/context-ir/tests/fixtures"),
        _field("python_path_entry", "/opt/context-ir/support"),
    )


def _runner_request_batch(
    input_batch: runtime_probe_execution.RuntimeProbeExecutionInputBatch,
) -> runtime_probe_execution.RuntimeProbeRunnerRequestBatch:
    """Return a runner-request batch for a materialized input batch."""
    return runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
        input_batch,
        runner_contract_revision="runtime-probe-runner:test.1",
        timeout_seconds=30,
        runner_environment=_runner_environment(),
        runner_assumptions=_runner_assumptions(),
    )


def _local_python_runner_request(
    runner_environment: tuple[
        runtime_probe_results.RuntimeProbeReplayField,
        ...,
    ]
    | None = None,
    *,
    timeout_seconds: int = 30,
    request: runtime_probe_requests.RuntimeProbeRequest | None = None,
) -> runtime_probe_execution.RuntimeProbeRunnerRequest:
    """Return one runner request carrying local-Python environment metadata."""
    selected_request = _request() if request is None else request
    runner_batch = (
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            _materialized_batch(_plan(selected_request)),
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=timeout_seconds,
            runner_environment=(
                _local_python_runner_environment()
                if runner_environment is None
                else runner_environment
            ),
            runner_assumptions=_runner_assumptions(),
        )
    )
    return runner_batch.runner_requests[0]


def _local_python_worker_request_payload(
    invocation: (
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation | None
    ) = None,
) -> runtime_probe_execution.RuntimeProbeLocalPythonWorkerRequestPayload:
    """Return one strict JSON worker request payload for local-Python tests."""
    selected_invocation = (
        _local_python_subprocess_invocation() if invocation is None else invocation
    )
    return materialize_runtime_probe_local_python_worker_request_payload(
        selected_invocation
    )


def _local_python_worker_request_stdin_transport(
    invocation: (
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation | None
    ) = None,
) -> runtime_probe_execution.RuntimeProbeLocalPythonWorkerRequestStdinTransport:
    """Return one deterministic stdin transport for local-Python worker tests."""
    selected_invocation = (
        _local_python_subprocess_invocation() if invocation is None else invocation
    )
    return materialize_runtime_probe_local_python_worker_request_stdin_transport(
        selected_invocation
    )


def _assert_local_python_worker_stdin_input(
    invocation: runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation,
    stdin_text: str,
) -> None:
    """Assert subprocess stdin carries exactly the deterministic worker payload."""
    expected_transport = _local_python_worker_request_stdin_transport(invocation)
    assert stdin_text == expected_transport.stdin_text
    assert not stdin_text.endswith("\n")
    assert parse_runtime_probe_local_python_worker_request_payload(stdin_text) == (
        expected_transport.payload
    )


def _rebuild_local_python_worker_request_stdin_transport(
    transport: (
        runtime_probe_execution.RuntimeProbeLocalPythonWorkerRequestStdinTransport
    ),
    **overrides: object,
) -> runtime_probe_execution.RuntimeProbeLocalPythonWorkerRequestStdinTransport:
    """Reconstruct a stdin transport with targeted field overrides."""
    values: dict[str, object] = {
        "invocation": transport.invocation,
        "payload": transport.payload,
        "stdin_text": transport.stdin_text,
        "invocation_identity": transport.invocation_identity,
        "argv": transport.argv,
        "working_directory": transport.working_directory,
        "python_path_entries": transport.python_path_entries,
        "timeout_seconds": transport.timeout_seconds,
        "plan_id": transport.plan_id,
        "request_id": transport.request_id,
        "family_label": transport.family_label,
        "form_label": transport.form_label,
        "replay_target_seed": transport.replay_target_seed,
        "replay_selector_seed": transport.replay_selector_seed,
        "request_replay_payload_fields": transport.request_replay_payload_fields,
        "stdin_transport_contract_revision": (
            transport.stdin_transport_contract_revision
        ),
    }
    values.update(overrides)
    return runtime_probe_execution.RuntimeProbeLocalPythonWorkerRequestStdinTransport(
        **values
    )


def _local_python_subprocess_invocation(
    runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest | None = None,
    *,
    python_executable: str = "/workspace/context-ir/.venv/bin/python",
    module_name: str = "context_ir.runtime_probe_worker",
    module_argv: tuple[str, ...] = ("--request", "runtime-probe-request.json"),
    invocation_contract_revision: str = "runtime-probe-local-python-subprocess:test.1",
) -> runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation:
    """Return one frozen, non-executing local-Python subprocess invocation."""
    selected_runner_request = (
        _local_python_runner_request() if runner_request is None else runner_request
    )
    return materialize_runtime_probe_local_python_subprocess_invocation(
        selected_runner_request,
        python_executable=python_executable,
        module_name=module_name,
        invocation_contract_revision=invocation_contract_revision,
        module_argv=module_argv,
    )


def _local_python_subprocess_handler_entry(
    *,
    family_label: runtime_probe_requests.RuntimeProbeFamily = (
        runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    ),
    form_label: str = "dynamic_import:importlib.import_module/1",
    python_executable: str = "/workspace/context-ir/.venv/bin/python",
    module_name: str = "context_ir.runtime_probe_worker",
    invocation_contract_revision: str = "runtime-probe-local-python-subprocess:test.1",
    completion_contract_revision: str = (
        "runtime-probe-local-python-process-completion:test.1"
    ),
    module_argv: tuple[str, ...] = ("--request", "runtime-probe-request.json"),
) -> runtime_probe_execution.RuntimeProbeRunnerHandlerEntry:
    """Return one dispatch entry backed by the local-Python handler adapter."""
    make_entry = (
        runtime_probe_execution.make_runtime_probe_local_python_subprocess_handler_entry
    )
    return make_entry(
        family_label=family_label,
        form_label=form_label,
        python_executable=python_executable,
        module_name=module_name,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
        module_argv=module_argv,
    )


def _local_python_process_completion(
    invocation: runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation
    | None = None,
    *,
    returncode: int = 0,
    stdout_text: str = '{"status":"ok"}\n',
    stderr_text: str = "",
    completion_contract_revision: str = (
        "runtime-probe-local-python-process-completion:test.1"
    ),
) -> runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion:
    """Return one frozen raw local-Python process completion."""
    selected_invocation = (
        _local_python_subprocess_invocation() if invocation is None else invocation
    )
    return materialize_runtime_probe_local_python_process_completion(
        selected_invocation,
        returncode=returncode,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        completion_contract_revision=completion_contract_revision,
    )


def _local_python_stdout_protocol_text(
    *,
    revision: str = "runtime_probe_local_python_stdout_protocol:v1",
    normalized_payload: list[dict[str, str]] | None = None,
    durable_artifact_reference: str | None = None,
    observed_replay_inputs: list[dict[str, str]] | None = None,
) -> str:
    """Return one strict local-Python success stdout protocol document."""
    protocol: dict[str, object] = {
        "runtime_probe_stdout_protocol_revision": revision,
        "normalized_payload": (
            [{"key": "observed_module", "value": "plugins.weather"}]
            if normalized_payload is None
            else normalized_payload
        ),
    }
    if durable_artifact_reference is not None:
        protocol["durable_artifact_reference"] = durable_artifact_reference
    if observed_replay_inputs is not None:
        protocol["observed_replay_inputs"] = observed_replay_inputs
    return json.dumps(protocol, separators=(",", ":"))


def _assert_attempt_identity(
    attempt: runtime_probe_execution.RuntimeProbeExecutionAttempt,
    invocation: runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation,
) -> None:
    """Assert that an attempt preserves its source runner request identity."""
    runner_request = invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input


def _attempt_failure_text(
    attempt: runtime_probe_execution.RuntimeProbeExecutionAttempt,
) -> str:
    """Return the exposed failure fields as one searchable string."""
    parts = [field.value for field in attempt.failure_detail_fields]
    if attempt.failure_summary is not None:
        parts.insert(0, attempt.failure_summary)
    return "\n".join(parts)


def _diagnostic_for_plan(
    plan: runtime_probe_requests.RuntimeProbeRequestPlan,
) -> SemanticDiagnosticResult:
    """Return a diagnostic with the supplied runtime request plan attached."""
    boundaries = tuple(
        SemanticDiagnosticBoundary(
            unit_id=request.subject_id,
            status=SemanticDiagnosticUnitStatus.OMITTED,
            boundary_kind=(
                SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
            ),
            primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            has_attached_runtime_provenance=False,
        )
        for request in plan.requests
    )
    planned_subject_ids = tuple(request.subject_id for request in plan.requests)
    return SemanticDiagnosticResult(
        grounded_unit_ids=planned_subject_ids,
        omitted_unit_ids=planned_subject_ids,
        too_shallow_unit_ids=(),
        sufficiently_represented_unit_ids=(),
        recommended_expansions=(),
        reason="Test diagnostic with an attached runtime request plan.",
        boundary_classifications=boundaries,
        planned_runtime_probe_requests=plan.requests,
        planned_runtime_probe_request_plan=plan,
    )


def _prepare_runner_requests(
    diagnostic: SemanticDiagnosticResult,
    *,
    probe_contract_revision: str = "runtime-probe-contract:test.1",
    runtime_assumptions: tuple[
        runtime_probe_results.RuntimeProbeReplayField,
        ...,
    ]
    | None = None,
    runner_contract_revision: str = "runtime-probe-runner:test.1",
    timeout_seconds: int = 30,
    runner_environment: tuple[
        runtime_probe_results.RuntimeProbeReplayField,
        ...,
    ]
    | None = None,
    runner_assumptions: tuple[
        runtime_probe_results.RuntimeProbeReplayField,
        ...,
    ]
    | None = None,
) -> runtime_probe_execution.RuntimeProbeDiagnosticRunnerRequestPreparation:
    """Prepare the diagnostic-gated runner request boundary for tests."""
    return runtime_probe_execution.prepare_runtime_probe_runner_requests_for_diagnostic(
        diagnostic,
        repository_snapshot_basis=_snapshot_basis(),
        probe_contract_revision=probe_contract_revision,
        runtime_assumptions=(
            _runtime_assumptions()
            if runtime_assumptions is None
            else runtime_assumptions
        ),
        runner_contract_revision=runner_contract_revision,
        timeout_seconds=timeout_seconds,
        runner_environment=(
            _runner_environment() if runner_environment is None else runner_environment
        ),
        runner_assumptions=(
            _runner_assumptions() if runner_assumptions is None else runner_assumptions
        ),
    )


def _execution_attempt(
    input_item: runtime_probe_execution.RuntimeProbeExecutionInput,
    *,
    outcome: runtime_probe_results.RuntimeProbeResultOutcome = (
        runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    ),
    normalized_payload: tuple[runtime_probe_results.RuntimeProbeReplayField, ...] = (),
    durable_artifact_reference: str | None = None,
    observed_replay_inputs: tuple[
        runtime_probe_results.RuntimeProbeReplayField,
        ...,
    ] = (),
    failure_summary: str | None = None,
    failure_detail_fields: tuple[
        runtime_probe_results.RuntimeProbeReplayField, ...
    ] = (),
) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
    """Return one normalized executor-output attempt tied to an input item."""
    return runtime_probe_execution.RuntimeProbeExecutionAttempt(
        plan_id=input_item.plan_id,
        request_id=input_item.request_id,
        request=input_item.request,
        execution_input=input_item,
        outcome=outcome,
        normalized_payload=normalized_payload,
        durable_artifact_reference=durable_artifact_reference,
        observed_replay_inputs=observed_replay_inputs,
        failure_summary=failure_summary,
        failure_detail_fields=failure_detail_fields,
    )


def _assemble_result_batch(
    input_batch: runtime_probe_execution.RuntimeProbeExecutionInputBatch,
    attempts: tuple[runtime_probe_execution.RuntimeProbeExecutionAttempt, ...],
) -> runtime_probe_results.RuntimeProbeResultBatch:
    """Assemble execution attempts through the public module-local helper."""
    return assemble_runtime_probe_result_batch_from_execution_attempts(
        input_batch,
        attempts,
    )


def _assemble_runner_request_result_batch(
    runner_request_batch: runtime_probe_execution.RuntimeProbeRunnerRequestBatch,
    attempts: tuple[runtime_probe_execution.RuntimeProbeExecutionAttempt, ...],
) -> runtime_probe_results.RuntimeProbeResultBatch:
    """Assemble attempts through the runner-request gate."""
    return assemble_runtime_probe_result_batch_from_runner_request_attempts(
        runner_request_batch,
        attempts,
    )


def test_materialize_runtime_probe_execution_inputs_preserves_plan_order_and_replay(
    tmp_path: Path,
) -> None:
    """Materialized inputs are replay-ready work items for all current forms."""
    _write_runtime_probe_program(tmp_path)
    program = _derived_program(tmp_path)
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)
    requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    plan = runtime_probe_requests.build_runtime_probe_request_plan(requests)
    original_plan_requests = plan.requests
    original_plan_request_ids = plan.request_ids
    original_plan_id = plan.plan_id
    snapshot_basis = _snapshot_basis()
    assumptions = _runtime_assumptions()

    first_batch = (
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            plan,
            repository_snapshot_basis=snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=assumptions,
        )
    )
    second_batch = (
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            plan,
            repository_snapshot_basis=snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=assumptions,
        )
    )

    assert first_batch == second_batch
    assert first_batch.contract_version == "runtime_probe_execution_input_batch:v1"
    assert first_batch.plan_id == plan.plan_id
    assert first_batch.request_ids == plan.request_ids
    assert tuple(input_item.request for input_item in first_batch.inputs) == requests
    assert [input_item.request_id for input_item in first_batch.inputs] == list(
        plan.request_ids
    )
    assert {input_item.form_label for input_item in first_batch.inputs} == (
        _EXPECTED_CURRENT_FORMS
    )
    assert {input_item.family_label for input_item in first_batch.inputs} == set(
        runtime_probe_requests.RuntimeProbeFamily
    )

    for input_item, request, request_id in zip(
        first_batch.inputs,
        plan.requests,
        plan.request_ids,
        strict=True,
    ):
        replay_artifact = input_item.replay_artifact
        replay_inputs = replay_artifact.replay_inputs
        replay_input_values = {field.key: field.value for field in replay_inputs}
        span = request.source_site.span

        assert input_item.plan_id == plan.plan_id
        assert input_item.request_id == request_id
        assert input_item.request is request
        assert input_item.source_site_identity == _source_site_identity(request)
        assert input_item.family_label is request.family_label
        assert input_item.form_label == request.form_label
        assert input_item.replay_target_seed == request.replay_target_seed
        assert input_item.replay_selector_seed == request.replay_selector_seed
        assert replay_artifact.probe_identifier.startswith(
            "runtime_probe_execution_input:"
        )
        assert replay_artifact.probe_contract_revision == (
            "runtime-probe-contract:test.1"
        )
        assert replay_artifact.repository_snapshot_basis is snapshot_basis
        assert replay_artifact.replay_target == request.replay_target_seed
        assert replay_artifact.replay_selector == request.replay_selector_seed
        assert replay_artifact.runtime_assumptions == assumptions
        assert (
            tuple(field.key for field in replay_inputs) == _EXPECTED_REPLAY_INPUT_KEYS
        )
        assert len(replay_input_values) == len(_EXPECTED_REPLAY_INPUT_KEYS)
        assert replay_input_values["plan_id"] == plan.plan_id
        assert replay_input_values["request_id"] == request_id
        assert replay_input_values["subject_kind"] == request.subject_kind.value
        assert replay_input_values["subject_id"] == request.subject_id
        assert replay_input_values["source_site_id"] == request.source_site.site_id
        assert replay_input_values["source_file_path"] == request.source_site.file_path
        assert replay_input_values["source_start_line"] == str(span.start_line)
        assert replay_input_values["source_start_column"] == str(span.start_column)
        assert replay_input_values["source_end_line"] == str(span.end_line)
        assert replay_input_values["source_end_column"] == str(span.end_column)
        assert replay_input_values["reason_code"] == request.reason_code.value
        assert replay_input_values["boundary_text"] == request.boundary_text
        assert replay_input_values["family_label"] == request.family_label.value
        assert replay_input_values["form_label"] == request.form_label
        assert replay_input_values["replay_target_seed"] == request.replay_target_seed
        assert (
            replay_input_values["replay_selector_seed"] == request.replay_selector_seed
        )

    assert plan.requests == original_plan_requests
    assert plan.request_ids == original_plan_request_ids
    assert plan.plan_id == original_plan_id
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records


@pytest.mark.parametrize(
    "source_request",
    (
        _reflective_hasattr_exact_replay_input_request(),
        _reflective_hasattr_literal_exact_replay_input_request(),
    ),
)
def test_exact_hasattr_probe_appends_request_replay_payload_fields(
    source_request: runtime_probe_requests.RuntimeProbeRequest,
) -> None:
    """The exact hasattr pilot appends pre-observation replay inputs."""
    runner_request = _local_python_runner_request(request=source_request)
    invocation = _local_python_subprocess_invocation(runner_request)
    payload = _local_python_worker_request_payload(invocation)
    transport = _local_python_worker_request_stdin_transport(invocation)
    expected_replay_inputs = (
        *_EXPECTED_REPLAY_INPUT_KEYS,
        "object_type",
        "attribute_name",
    )

    assert (
        tuple(field.key for field in runner_request.replay_artifact.replay_inputs)
        == expected_replay_inputs
    )
    assert runner_request.replay_artifact.replay_inputs[-2:] == (
        _field("object_type", "builtins.int"),
        _field("attribute_name", "bit_length"),
    )
    assert invocation.request_replay_payload_fields is (
        runner_request.replay_artifact.replay_inputs
    )
    assert payload.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )
    assert transport.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )
    assert transport.payload.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )


def test_exact_literal_getattr_probe_appends_request_replay_payload_fields() -> None:
    """The exact literal getattr pilot appends pre-observation replay inputs."""
    source_request = _reflective_getattr_literal_exact_replay_input_request()
    runner_request = _local_python_runner_request(request=source_request)
    invocation = _local_python_subprocess_invocation(runner_request)
    payload = _local_python_worker_request_payload(invocation)
    transport = _local_python_worker_request_stdin_transport(invocation)
    expected_replay_inputs = (
        *_EXPECTED_REPLAY_INPUT_KEYS,
        "object_type",
        "attribute_name",
    )

    assert (
        tuple(field.key for field in runner_request.replay_artifact.replay_inputs)
        == expected_replay_inputs
    )
    assert runner_request.replay_artifact.replay_inputs[-2:] == (
        _field("object_type", "builtins.int"),
        _field("attribute_name", "bit_length"),
    )
    assert invocation.request_replay_payload_fields is (
        runner_request.replay_artifact.replay_inputs
    )
    assert payload.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )
    assert transport.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )
    assert transport.payload.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )


def test_exact_literal_delattr_probe_appends_request_replay_payload_fields() -> None:
    """The exact literal delattr pilot appends pre-observation replay inputs."""
    source_request = _runtime_mutation_delattr_literal_exact_replay_input_request()
    runner_request = _local_python_runner_request(request=source_request)
    invocation = _local_python_subprocess_invocation(runner_request)
    payload = _local_python_worker_request_payload(invocation)
    transport = _local_python_worker_request_stdin_transport(invocation)
    expected_replay_inputs = (
        *_EXPECTED_REPLAY_INPUT_KEYS,
        "object_type",
        "attribute_name",
    )

    assert (
        tuple(field.key for field in runner_request.replay_artifact.replay_inputs)
        == expected_replay_inputs
    )
    assert runner_request.replay_artifact.replay_inputs[-2:] == (
        _field("object_type", "main.ProbeTarget"),
        _field("attribute_name", "flag"),
    )
    assert invocation.request_replay_payload_fields is (
        runner_request.replay_artifact.replay_inputs
    )
    assert payload.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )
    assert transport.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )
    assert transport.payload.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )


def test_materialize_runtime_probe_runner_requests_preserves_order_and_identities() -> (
    None
):
    """Runner handoff requests preserve the replay-ready execution inputs exactly."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    plan = _plan(first_request, second_request, third_request)
    input_batch = _materialized_batch(plan)
    original_inputs = input_batch.inputs
    runner_environment = _runner_environment()
    runner_assumptions = _runner_assumptions()

    first_batch = (
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )
    )
    second_batch = (
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )
    )

    assert first_batch == second_batch
    assert first_batch.contract_version == "runtime_probe_runner_request_batch:v1"
    assert first_batch.plan_id == input_batch.plan_id
    assert first_batch.request_ids == input_batch.request_ids
    assert first_batch.runner_contract_revision == "runtime-probe-runner:test.1"
    assert first_batch.timeout_seconds == 30
    assert first_batch.runner_environment == runner_environment
    assert first_batch.runner_assumptions == runner_assumptions
    assert input_batch.inputs is original_inputs
    assert (
        tuple(
            runner_request.execution_input
            for runner_request in first_batch.runner_requests
        )
        == input_batch.inputs
    )
    assert [
        runner_request.request_id for runner_request in first_batch.runner_requests
    ] == list(input_batch.request_ids)

    for runner_request, input_item in zip(
        first_batch.runner_requests,
        input_batch.inputs,
        strict=True,
    ):
        assert runner_request.plan_id == input_batch.plan_id
        assert runner_request.request_id == input_item.request_id
        assert runner_request.request is input_item.request
        assert runner_request.execution_input is input_item
        assert runner_request.replay_artifact is input_item.replay_artifact
        assert runner_request.runner_contract_revision == "runtime-probe-runner:test.1"
        assert runner_request.timeout_seconds == 30
        assert runner_request.runner_environment == runner_environment
        assert runner_request.runner_assumptions == runner_assumptions


def test_derive_local_python_environment_context_preserves_runner_metadata() -> None:
    """Local-Python context derivation preserves path order and replay metadata."""
    runner_request = _local_python_runner_request()

    context = (
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )
    )

    assert isinstance(
        context,
        runtime_probe_execution.RuntimeProbeLocalPythonEnvironmentContext,
    )
    assert context.repository_root == "/workspace/context-ir"
    assert context.working_directory == "/workspace/context-ir"
    assert context.python_path_entries == (
        "/workspace/context-ir/src",
        "/workspace/context-ir/tests/fixtures",
        "/opt/context-ir/support",
    )
    assert context.runner_contract_revision == (runner_request.runner_contract_revision)
    assert context.timeout_seconds == runner_request.timeout_seconds
    assert context.runner_environment is runner_request.runner_environment
    assert context.runner_assumptions is runner_request.runner_assumptions

    with pytest.raises(FrozenInstanceError):
        context.repository_root = "/tmp/context-ir"


def test_derive_local_python_environment_context_revalidates_runner_request() -> None:
    """Context derivation rejects runner requests that drift after construction."""
    runner_request = _local_python_runner_request()
    object.__setattr__(runner_request, "request_id", "runtime_probe:wrong")

    with pytest.raises(ValueError, match="request_id must match execution input"):
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )


def test_materialize_local_python_worker_request_payload_is_deterministic() -> None:
    """Worker request payloads are frozen execution-free JSON handoff contracts."""
    runner_request = _local_python_runner_request(timeout_seconds=47)
    invocation = _local_python_subprocess_invocation(runner_request)

    first_payload = _local_python_worker_request_payload(invocation)
    second_payload = _local_python_worker_request_payload(invocation)

    assert first_payload == second_payload
    assert isinstance(
        first_payload,
        runtime_probe_execution.RuntimeProbeLocalPythonWorkerRequestPayload,
    )
    assert first_payload.contract_version == (
        "runtime_probe_local_python_worker_request_payload:v1"
    )
    assert first_payload.plan_id == runner_request.plan_id
    assert first_payload.request_id == runner_request.request_id
    assert first_payload.family_label is runner_request.request.family_label
    assert first_payload.form_label == runner_request.request.form_label
    assert first_payload.replay_target_seed == runner_request.request.replay_target_seed
    assert (
        first_payload.replay_selector_seed
        == runner_request.request.replay_selector_seed
    )
    assert first_payload.request_replay_payload_fields is (
        runner_request.replay_artifact.replay_inputs
    )
    assert first_payload.runtime_assumptions is (
        runner_request.replay_artifact.runtime_assumptions
    )
    assert first_payload.runner_contract_revision == (
        runner_request.runner_contract_revision
    )
    assert first_payload.runner_environment is runner_request.runner_environment
    assert first_payload.runner_assumptions is runner_request.runner_assumptions
    assert first_payload.invocation_contract_revision == (
        invocation.invocation_contract_revision
    )
    assert first_payload.invocation_identity.startswith(
        "runtime_probe_local_python_subprocess_invocation:"
    )
    assert first_payload.argv is invocation.argv
    assert first_payload.working_directory == invocation.working_directory
    assert first_payload.python_path_entries is invocation.python_path_entries
    assert first_payload.timeout_seconds == 47

    with pytest.raises(FrozenInstanceError):
        first_payload.plan_id = "runtime_probe_request_plan:mutated"


def test_materialize_local_python_worker_request_payload_revalidates_invocation() -> (
    None
):
    """Payload materialization rejects invocations that drifted in memory."""
    invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        invocation,
        "argv",
        ("/workspace/other/python", *invocation.argv[1:]),
    )

    with pytest.raises(ValueError, match="argv executable"):
        _local_python_worker_request_payload(invocation)


def test_local_python_worker_request_payload_serializes_strict_json() -> None:
    """Worker request payload JSON serialization is deterministic and strict."""
    payload = _local_python_worker_request_payload()

    first_serialized = serialize_runtime_probe_local_python_worker_request_payload(
        payload
    )
    second_serialized = serialize_runtime_probe_local_python_worker_request_payload(
        payload
    )
    parsed_payload = parse_runtime_probe_local_python_worker_request_payload(
        first_serialized
    )

    assert first_serialized == second_serialized
    assert ", " not in first_serialized
    assert ": " not in first_serialized
    assert parsed_payload == payload
    assert (
        serialize_runtime_probe_local_python_worker_request_payload(parsed_payload)
        == first_serialized
    )
    decoded = json.loads(first_serialized)
    assert list(decoded) == [
        "contract_version",
        "plan_id",
        "request_id",
        "family_label",
        "form_label",
        "replay_target_seed",
        "replay_selector_seed",
        "request_replay_payload_fields",
        "runtime_assumptions",
        "runner_contract_revision",
        "runner_environment",
        "runner_assumptions",
        "invocation_contract_revision",
        "invocation_identity",
        "argv",
        "working_directory",
        "python_path_entries",
        "timeout_seconds",
    ]
    assert decoded["family_label"] == "dynamic_import"
    assert decoded["invocation_identity"] == payload.invocation_identity
    assert decoded["argv"] == list(payload.argv)
    assert decoded["working_directory"] == payload.working_directory
    assert decoded["python_path_entries"] == list(payload.python_path_entries)
    assert decoded["timeout_seconds"] == 30
    assert decoded["request_replay_payload_fields"][0] == {
        "key": "plan_id",
        "value": payload.plan_id,
    }
    assert [field["key"] for field in decoded["request_replay_payload_fields"]] == list(
        _EXPECTED_REPLAY_INPUT_KEYS
    )


def test_parse_local_python_worker_request_payload_rejects_bad_keys() -> None:
    """Worker request payload JSON must use exactly the versioned key set."""
    payload_object = json.loads(
        serialize_runtime_probe_local_python_worker_request_payload(
            _local_python_worker_request_payload()
        )
    )
    unknown_payload_object = dict(payload_object)
    unknown_payload_object["extra"] = "unplanned"
    missing_payload_object = dict(payload_object)
    del missing_payload_object["request_id"]

    with pytest.raises(ValueError, match="unknown keys"):
        parse_runtime_probe_local_python_worker_request_payload(
            json.dumps(unknown_payload_object, separators=(",", ":"))
        )
    with pytest.raises(ValueError, match="missing required keys"):
        parse_runtime_probe_local_python_worker_request_payload(
            json.dumps(missing_payload_object, separators=(",", ":"))
        )
    with pytest.raises(ValueError, match="duplicate JSON keys"):
        parse_runtime_probe_local_python_worker_request_payload(
            '{"contract_version":"first","contract_version":"second"}'
        )


@pytest.mark.parametrize(
    ("field_name", "field_value", "error_match"),
    (
        (
            "contract_version",
            "runtime_probe_local_python_worker_request_payload:v2",
            "contract_version is unsupported",
        ),
        ("family_label", "unplanned_family", "family_label is unsupported"),
        ("timeout_seconds", 0, "timeout_seconds"),
        ("timeout_seconds", True, "timeout_seconds"),
        ("timeout_seconds", 31, "invocation_identity"),
        (
            "invocation_identity",
            "runtime_probe_local_python_subprocess_invocation:wrong",
            "invocation_identity",
        ),
        (
            "argv",
            [
                "/workspace/context-ir/.venv/bin/python",
                "--not-module-mode",
                "context_ir.runtime_probe_worker",
            ],
            "argv",
        ),
        ("working_directory", "/workspace/other", "working_directory"),
        (
            "python_path_entries",
            [
                "/opt/context-ir/support",
                "/workspace/context-ir/tests/fixtures",
                "/workspace/context-ir/src",
            ],
            "python_path_entries",
        ),
        (
            "request_replay_payload_fields",
            [{"key": "plan_id", "value": "runtime_probe_request_plan:wrong"}],
            "plan_id must match request replay",
        ),
        (
            "runner_environment",
            [{"key": "repository_root", "value": "/workspace/context-ir"}],
            "missing required singleton",
        ),
    ),
)
def test_parse_local_python_worker_request_payload_rejects_bad_values(
    field_name: str,
    field_value: object,
    error_match: str,
) -> None:
    """Worker request payload parsing validates primitive and replay field values."""
    payload_object = json.loads(
        serialize_runtime_probe_local_python_worker_request_payload(
            _local_python_worker_request_payload()
        )
    )
    payload_object[field_name] = field_value

    with pytest.raises(ValueError, match=error_match):
        parse_runtime_probe_local_python_worker_request_payload(
            json.dumps(payload_object, separators=(",", ":"))
        )


@pytest.mark.parametrize(
    "missing_field_key",
    (
        "source_site_id",
        "source_file_path",
        "source_start_line",
        "source_start_column",
        "source_end_line",
        "source_end_column",
        "reason_code",
        "boundary_text",
    ),
)
def test_local_python_worker_request_payload_rejects_missing_required_replay_fields(
    missing_field_key: str,
) -> None:
    """Direct and parsed payload validation require replay request identity fields."""
    payload = _local_python_worker_request_payload()
    fields_without_key = tuple(
        field
        for field in payload.request_replay_payload_fields
        if field.key != missing_field_key
    )
    error_match = f"exactly one {missing_field_key}"

    with pytest.raises(ValueError, match=error_match):
        replace(payload, request_replay_payload_fields=fields_without_key)

    payload_object = json.loads(
        serialize_runtime_probe_local_python_worker_request_payload(payload)
    )
    payload_object["request_replay_payload_fields"] = [
        field
        for field in payload_object["request_replay_payload_fields"]
        if field["key"] != missing_field_key
    ]

    with pytest.raises(ValueError, match=error_match):
        parse_runtime_probe_local_python_worker_request_payload(
            json.dumps(payload_object, separators=(",", ":"))
        )


def test_local_python_worker_request_payload_rejects_drift_before_serialize() -> None:
    """Serialization revalidates frozen payloads before emitting JSON."""
    payload = _local_python_worker_request_payload()
    object.__setattr__(payload, "plan_id", "runtime_probe_request_plan:wrong")

    with pytest.raises(ValueError, match="plan_id must match request replay"):
        serialize_runtime_probe_local_python_worker_request_payload(payload)

    identity_drifted_payload = _local_python_worker_request_payload()
    object.__setattr__(
        identity_drifted_payload,
        "invocation_identity",
        "runtime_probe_local_python_subprocess_invocation:wrong",
    )

    with pytest.raises(ValueError, match="invocation_identity"):
        serialize_runtime_probe_local_python_worker_request_payload(
            identity_drifted_payload
        )

    path_order_drifted_payload = _local_python_worker_request_payload()
    object.__setattr__(
        path_order_drifted_payload,
        "python_path_entries",
        tuple(reversed(path_order_drifted_payload.python_path_entries)),
    )

    with pytest.raises(ValueError, match="python_path_entries"):
        serialize_runtime_probe_local_python_worker_request_payload(
            path_order_drifted_payload
        )


def test_materialize_local_python_worker_request_stdin_transport_is_deterministic() -> (
    None
):
    """Stdin transports freeze deterministic request JSON without execution."""
    runner_request = _local_python_runner_request(timeout_seconds=47)
    invocation = _local_python_subprocess_invocation(
        runner_request,
        module_argv=("--request-from-stdin",),
    )

    first_transport = _local_python_worker_request_stdin_transport(invocation)
    second_transport = _local_python_worker_request_stdin_transport(invocation)

    assert first_transport == second_transport
    assert isinstance(
        first_transport,
        runtime_probe_execution.RuntimeProbeLocalPythonWorkerRequestStdinTransport,
    )
    assert first_transport.stdin_transport_contract_revision == (
        "runtime_probe_local_python_worker_request_stdin_transport:v1"
    )
    assert first_transport.invocation is invocation
    assert first_transport.payload == _local_python_worker_request_payload(invocation)
    assert first_transport.stdin_text == (
        serialize_runtime_probe_local_python_worker_request_payload(
            first_transport.payload
        )
    )
    assert first_transport.stdin_text.endswith("\n") is False
    assert (
        parse_runtime_probe_local_python_worker_request_payload(
            first_transport.stdin_text
        )
        == first_transport.payload
    )
    assert first_transport.invocation_identity == (
        first_transport.payload.invocation_identity
    )
    assert first_transport.argv is invocation.argv
    assert first_transport.working_directory == invocation.working_directory
    assert first_transport.python_path_entries is invocation.python_path_entries
    assert first_transport.timeout_seconds == 47
    assert first_transport.plan_id == runner_request.plan_id
    assert first_transport.request_id == runner_request.request_id
    assert first_transport.family_label is runner_request.request.family_label
    assert first_transport.form_label == runner_request.request.form_label
    assert first_transport.replay_target_seed == (
        runner_request.request.replay_target_seed
    )
    assert first_transport.replay_selector_seed == (
        runner_request.request.replay_selector_seed
    )
    assert first_transport.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )
    assert first_transport.python_path_entries == (
        "/workspace/context-ir/src",
        "/workspace/context-ir/tests/fixtures",
        "/opt/context-ir/support",
    )

    decoded = json.loads(first_transport.stdin_text)
    assert [field["key"] for field in decoded["request_replay_payload_fields"]] == (
        list(_EXPECTED_REPLAY_INPUT_KEYS)
    )
    assert decoded["python_path_entries"] == list(invocation.python_path_entries)
    assert decoded["timeout_seconds"] == 47

    with pytest.raises(FrozenInstanceError):
        first_transport.stdin_text = "{}"


def test_stdin_transport_materialization_revalidates_invocation() -> None:
    """Transport materialization rejects invocations drifted in memory."""
    invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        invocation,
        "argv",
        ("/workspace/other/python", *invocation.argv[1:]),
    )

    with pytest.raises(ValueError, match="argv executable"):
        _local_python_worker_request_stdin_transport(invocation)


def test_stdin_transport_rejects_direct_payload_bypass() -> None:
    """Direct construction still revalidates the strict worker payload contract."""
    transport = _local_python_worker_request_stdin_transport()
    payload = transport.payload
    object.__setattr__(payload, "plan_id", "runtime_probe_request_plan:wrong")

    with pytest.raises(ValueError, match="plan_id must match request replay"):
        _rebuild_local_python_worker_request_stdin_transport(
            transport,
            payload=payload,
        )


def test_local_python_worker_request_stdin_transport_rejects_payload_drift() -> None:
    """The carried payload must be the exact payload derived from invocation."""
    transport = _local_python_worker_request_stdin_transport()
    other_invocation = _local_python_subprocess_invocation(
        _local_python_runner_request(timeout_seconds=47),
    )
    other_payload = _local_python_worker_request_payload(other_invocation)
    other_stdin_text = serialize_runtime_probe_local_python_worker_request_payload(
        other_payload
    )

    with pytest.raises(ValueError, match="payload must match invocation"):
        _rebuild_local_python_worker_request_stdin_transport(
            transport,
            payload=other_payload,
            stdin_text=other_stdin_text,
        )


@pytest.mark.parametrize(
    ("field_name", "field_value", "error_match"),
    (
        (
            "stdin_text",
            '{"not":"the payload"}',
            "unknown keys",
        ),
        (
            "stdin_text",
            "not json",
            "valid JSON",
        ),
        (
            "stdin_text",
            None,
            "stdin_text must be non-empty text",
        ),
        (
            "stdin_text",
            "__append_newline__",
            "deterministic serialized payload",
        ),
        (
            "invocation_identity",
            "runtime_probe_local_python_subprocess_invocation:wrong",
            "invocation_identity",
        ),
        (
            "python_path_entries",
            (
                "/opt/context-ir/support",
                "/workspace/context-ir/tests/fixtures",
                "/workspace/context-ir/src",
            ),
            "python_path_entries",
        ),
        (
            "request_replay_payload_fields",
            (_field("plan_id", "runtime_probe_request_plan:wrong"),),
            "request_replay_payload_fields",
        ),
    ),
)
def test_local_python_worker_request_stdin_transport_rejects_drifted_fields(
    field_name: str,
    field_value: object,
    error_match: str,
) -> None:
    """Direct stdin transport construction rejects copied metadata drift."""
    transport = _local_python_worker_request_stdin_transport()
    selected_value = (
        f"{transport.stdin_text}\n"
        if field_value == "__append_newline__"
        else field_value
    )

    with pytest.raises(ValueError, match=error_match):
        _rebuild_local_python_worker_request_stdin_transport(
            transport,
            **{field_name: selected_value},
        )


@pytest.mark.parametrize(
    ("transport_revision", "error_match"),
    (
        ("", "contract revision must be non-empty"),
        (
            "runtime_probe_local_python_worker_request_stdin_transport:v2",
            "contract revision is unsupported",
        ),
    ),
)
def test_local_python_worker_request_stdin_transport_rejects_bad_revision(
    transport_revision: str,
    error_match: str,
) -> None:
    """The stdin transport contract revision is closed and versioned."""
    transport = _local_python_worker_request_stdin_transport()

    with pytest.raises(ValueError, match=error_match):
        _rebuild_local_python_worker_request_stdin_transport(
            transport,
            stdin_transport_contract_revision=transport_revision,
        )


def test_local_python_worker_request_stdin_transport_exports_module_local_only() -> (
    None
):
    """The stdin transport is exported only from the runtime execution module."""
    transport_type_name = "RuntimeProbeLocalPythonWorkerRequestStdinTransport"
    materializer_name = (
        "materialize_runtime_probe_local_python_worker_request_stdin_transport"
    )

    assert transport_type_name in runtime_probe_execution.__all__
    assert materializer_name in runtime_probe_execution.__all__
    assert hasattr(runtime_probe_execution, transport_type_name)
    assert hasattr(runtime_probe_execution, materializer_name)
    assert transport_type_name not in context_ir.__all__
    assert materializer_name not in context_ir.__all__
    assert not hasattr(context_ir, transport_type_name)
    assert not hasattr(context_ir, materializer_name)


def test_materialize_local_python_subprocess_invocation_is_deterministic() -> None:
    """Local-Python subprocess contracts are frozen execution-free request specs."""
    runner_request = _local_python_runner_request()
    module_argv = (
        "--plan-id",
        runner_request.plan_id,
        "--request-id",
        runner_request.request_id,
    )

    first_invocation = _local_python_subprocess_invocation(
        runner_request,
        module_argv=module_argv,
    )
    second_invocation = _local_python_subprocess_invocation(
        runner_request,
        module_argv=module_argv,
    )

    assert first_invocation == second_invocation
    assert isinstance(
        first_invocation,
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation,
    )
    assert first_invocation.runner_request is runner_request
    assert first_invocation.environment_context == (
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )
    )
    assert first_invocation.python_executable == (
        "/workspace/context-ir/.venv/bin/python"
    )
    assert first_invocation.argv == (
        "/workspace/context-ir/.venv/bin/python",
        "-m",
        "context_ir.runtime_probe_worker",
        "--plan-id",
        runner_request.plan_id,
        "--request-id",
        runner_request.request_id,
    )
    assert first_invocation.working_directory == "/workspace/context-ir"
    assert first_invocation.python_path_entries == (
        "/workspace/context-ir/src",
        "/workspace/context-ir/tests/fixtures",
        "/opt/context-ir/support",
    )
    assert first_invocation.timeout_seconds == runner_request.timeout_seconds
    assert first_invocation.invocation_contract_revision == (
        "runtime-probe-local-python-subprocess:test.1"
    )
    assert first_invocation.request_replay_payload_fields is (
        runner_request.replay_artifact.replay_inputs
    )
    assert (
        tuple(field.key for field in first_invocation.request_replay_payload_fields)
        == _EXPECTED_REPLAY_INPUT_KEYS
    )

    with pytest.raises(FrozenInstanceError):
        first_invocation.python_executable = "/tmp/python"


def test_materialize_local_python_subprocess_invocation_revalidates_runner() -> None:
    """Invocation materialization rejects runner requests that drifted in memory."""
    runner_request = _local_python_runner_request()
    object.__setattr__(runner_request, "request_id", "runtime_probe:wrong")

    with pytest.raises(ValueError, match="request_id must match execution input"):
        _local_python_subprocess_invocation(runner_request)


@pytest.mark.parametrize(
    ("python_executable", "error_match"),
    (
        ("workspace/context-ir/.venv/bin/python", "python_executable.*absolute"),
        (" /workspace/context-ir/.venv/bin/python", "python_executable.*malformed"),
        ("/workspace/context-ir/.venv/bin/python\nbad", "python_executable.*malformed"),
    ),
)
def test_materialize_local_python_subprocess_invocation_rejects_bad_executable(
    python_executable: str,
    error_match: str,
) -> None:
    """Python executable metadata must be absolute and shell-token safe."""
    with pytest.raises(ValueError, match=error_match):
        _local_python_subprocess_invocation(
            python_executable=python_executable,
        )


@pytest.mark.parametrize(
    ("module_name", "module_argv", "error_match"),
    (
        (" ", (), "module name"),
        (" context_ir.worker", (), "module name is malformed"),
        ("context_ir.runtime-probe-worker", (), "dotted identifier"),
        ("context_ir.worker", ("",), "module_argv"),
        ("context_ir.worker", ("--payload\nbad",), "module_argv.*malformed"),
    ),
)
def test_materialize_local_python_subprocess_invocation_rejects_bad_module_or_argv(
    module_name: str,
    module_argv: tuple[str, ...],
    error_match: str,
) -> None:
    """Module names and argv tokens are validated before any future execution."""
    with pytest.raises(ValueError, match=error_match):
        _local_python_subprocess_invocation(
            module_name=module_name,
            module_argv=module_argv,
        )


@pytest.mark.parametrize(
    "invocation_contract_revision",
    ("", " \t\n"),
)
def test_materialize_local_python_subprocess_invocation_rejects_blank_revision(
    invocation_contract_revision: str,
) -> None:
    """Invocation materialization rejects blank contract revisions."""
    with pytest.raises(ValueError, match="invocation_contract_revision"):
        _local_python_subprocess_invocation(
            invocation_contract_revision=invocation_contract_revision,
        )


def test_local_python_subprocess_invocation_preserves_path_order_and_timeout() -> None:
    """Invocation contracts keep Python path ordering and timeout metadata intact."""
    runner_request = _local_python_runner_request(timeout_seconds=47)

    invocation = _local_python_subprocess_invocation(runner_request)

    assert invocation.python_path_entries == (
        "/workspace/context-ir/src",
        "/workspace/context-ir/tests/fixtures",
        "/opt/context-ir/support",
    )
    assert invocation.timeout_seconds == 47
    assert invocation.timeout_seconds == invocation.environment_context.timeout_seconds


def test_local_python_subprocess_invocation_rejects_contract_drift() -> None:
    """The frozen invocation type revalidates path, argv, and replay identities."""
    invocation = _local_python_subprocess_invocation()
    other_runner_request = _local_python_runner_request(
        runner_environment=(
            _field("python_version", "3.11"),
            _field("repository_root", "/workspace/context-ir"),
            _field("platform", "linux-x86_64"),
            _field("python_path_entry", "/workspace/context-ir/src"),
            _field("working_directory", "/workspace/other"),
        )
    )
    other_context = (
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            other_runner_request
        )
    )

    with pytest.raises(ValueError, match="environment_context"):
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation(
            runner_request=invocation.runner_request,
            environment_context=other_context,
            python_executable=invocation.python_executable,
            argv=invocation.argv,
            working_directory=invocation.working_directory,
            python_path_entries=invocation.python_path_entries,
            timeout_seconds=invocation.timeout_seconds,
            invocation_contract_revision=invocation.invocation_contract_revision,
            request_replay_payload_fields=invocation.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="argv executable"):
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation(
            runner_request=invocation.runner_request,
            environment_context=invocation.environment_context,
            python_executable=invocation.python_executable,
            argv=("/workspace/other/python", *invocation.argv[1:]),
            working_directory=invocation.working_directory,
            python_path_entries=invocation.python_path_entries,
            timeout_seconds=invocation.timeout_seconds,
            invocation_contract_revision=invocation.invocation_contract_revision,
            request_replay_payload_fields=invocation.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="replay payload fields"):
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation(
            runner_request=invocation.runner_request,
            environment_context=invocation.environment_context,
            python_executable=invocation.python_executable,
            argv=invocation.argv,
            working_directory=invocation.working_directory,
            python_path_entries=invocation.python_path_entries,
            timeout_seconds=invocation.timeout_seconds,
            invocation_contract_revision=invocation.invocation_contract_revision,
            request_replay_payload_fields=(
                _field("plan_id", invocation.runner_request.plan_id),
            ),
        )


def test_materialize_local_python_process_completion_preserves_raw_fields() -> None:
    """Raw local-Python process completions preserve process fields verbatim."""
    runner_request = _local_python_runner_request(timeout_seconds=47)
    module_argv = (
        "--plan-id",
        runner_request.plan_id,
        "--request-id",
        runner_request.request_id,
    )
    invocation = _local_python_subprocess_invocation(
        runner_request,
        module_argv=module_argv,
    )

    first_completion = _local_python_process_completion(
        invocation,
        returncode=17,
        stdout_text="",
        stderr_text="warning: fixture used\nline 2\n",
    )
    second_completion = _local_python_process_completion(
        invocation,
        returncode=17,
        stdout_text="",
        stderr_text="warning: fixture used\nline 2\n",
    )

    assert first_completion == second_completion
    assert isinstance(
        first_completion,
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion,
    )
    assert first_completion.invocation is invocation
    assert first_completion.invocation_identity.startswith(
        "runtime_probe_local_python_subprocess_invocation:"
    )
    assert first_completion.argv is invocation.argv
    assert first_completion.working_directory == invocation.working_directory
    assert first_completion.python_path_entries is invocation.python_path_entries
    assert first_completion.timeout_seconds == 47
    assert first_completion.returncode == 17
    assert first_completion.stdout_text == ""
    assert first_completion.stderr_text == "warning: fixture used\nline 2\n"
    assert first_completion.completion_contract_revision == (
        "runtime-probe-local-python-process-completion:test.1"
    )
    assert first_completion.request_replay_payload_fields is (
        invocation.request_replay_payload_fields
    )

    with pytest.raises(FrozenInstanceError):
        first_completion.returncode = 0


def test_materialize_local_python_process_completion_revalidates_invocation() -> None:
    """Completion materialization rejects invocation contracts drifted in memory."""
    argv_drifted_invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        argv_drifted_invocation,
        "argv",
        ("/workspace/other/python", *argv_drifted_invocation.argv[1:]),
    )
    request_drifted_invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        request_drifted_invocation.runner_request,
        "request_id",
        "runtime_probe:wrong",
    )

    with pytest.raises(ValueError, match="argv executable"):
        _local_python_process_completion(argv_drifted_invocation)
    with pytest.raises(ValueError, match="request_id must match execution input"):
        _local_python_process_completion(request_drifted_invocation)


def test_execute_local_python_subprocess_invocation_preserves_raw_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The execution boundary captures raw process fields without interpretation."""
    invocation = _local_python_subprocess_invocation()
    monkeypatch.setenv("CONTEXT_IR_RUNTIME_PROBE_TEST", "ambient-preserved")
    monkeypatch.setenv("PYTHONPATH", "/ambient/path")
    calls: list[dict[str, object]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(
            {
                "args": args,
                "cwd": cwd,
                "env": env,
                "input": input,
                "timeout": timeout,
                "shell": shell,
                "capture_output": capture_output,
                "text": text,
                "check": check,
            }
        )
        return subprocess.CompletedProcess(
            args=args,
            returncode=23,
            stdout="raw stdout\n",
            stderr="raw stderr\n",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    completion = execute_runtime_probe_local_python_subprocess_invocation(
        invocation,
        completion_contract_revision=(
            "runtime-probe-local-python-process-completion:test.1"
        ),
    )

    assert len(calls) == 1
    call = calls[0]
    child_environment = call["env"]
    assert call["args"] is invocation.argv
    assert call["cwd"] == invocation.working_directory
    call_stdin_text = call["input"]
    assert isinstance(call_stdin_text, str)
    _assert_local_python_worker_stdin_input(invocation, call_stdin_text)
    assert call["timeout"] == invocation.timeout_seconds
    assert call["shell"] is False
    assert call["capture_output"] is True
    assert call["text"] is True
    assert call["check"] is False
    assert isinstance(child_environment, dict)
    assert child_environment is not os.environ
    assert child_environment["CONTEXT_IR_RUNTIME_PROBE_TEST"] == "ambient-preserved"
    assert child_environment["PYTHONPATH"] == os.pathsep.join(
        invocation.python_path_entries
    )
    assert os.environ["PYTHONPATH"] == "/ambient/path"
    assert completion == _local_python_process_completion(
        invocation,
        returncode=23,
        stdout_text="raw stdout\n",
        stderr_text="raw stderr\n",
    )


def test_execute_local_python_subprocess_invocation_revalidates_before_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invocation drift is rejected before reaching the subprocess boundary."""
    invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        invocation,
        "argv",
        ("/workspace/other/python", *invocation.argv[1:]),
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, timeout, shell, capture_output, text, check
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="argv executable"):
        execute_runtime_probe_local_python_subprocess_invocation(
            invocation,
            completion_contract_revision=(
                "runtime-probe-local-python-process-completion:test.1"
            ),
        )

    assert calls == []


@pytest.mark.parametrize(
    ("completion_contract_revision", "error_match"),
    (
        ("", "completion_contract_revision"),
        (
            " runtime-probe-local-python-process-completion:test.1",
            "completion_contract_revision.*malformed",
        ),
    ),
)
def test_execute_subprocess_rejects_bad_completion_revision_before_run(
    monkeypatch: pytest.MonkeyPatch,
    completion_contract_revision: str,
    error_match: str,
) -> None:
    """Completion revision metadata is validated before subprocess execution."""
    invocation = _local_python_subprocess_invocation()
    calls: list[tuple[str, ...]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, timeout, shell, capture_output, text, check
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match=error_match):
        execute_runtime_probe_local_python_subprocess_invocation(
            invocation,
            completion_contract_revision=completion_contract_revision,
        )

    assert calls == []


@pytest.mark.parametrize(
    ("drift_field", "error_match"),
    (
        (
            "stdin_text",
            "stdin_text must match deterministic serialized payload",
        ),
        ("payload", "payload must match invocation"),
    ),
)
def test_execute_subprocess_rejects_stdin_transport_drift_before_run(
    monkeypatch: pytest.MonkeyPatch,
    drift_field: str,
    error_match: str,
) -> None:
    """Worker stdin transport drift is rejected before subprocess execution."""
    invocation = _local_python_subprocess_invocation()
    transport = _local_python_worker_request_stdin_transport(invocation)
    if drift_field == "stdin_text":
        object.__setattr__(transport, "stdin_text", f"{transport.stdin_text}\n")
    else:
        other_invocation = _local_python_subprocess_invocation(
            module_argv=("--request", "other-runtime-probe-request.json"),
        )
        object.__setattr__(
            transport,
            "payload",
            _local_python_worker_request_payload(other_invocation),
        )

    def fake_transport_materializer(
        materialized_invocation: (
            runtime_probe_execution.RuntimeProbeLocalPythonSubprocessInvocation
        ),
    ) -> runtime_probe_execution.RuntimeProbeLocalPythonWorkerRequestStdinTransport:
        assert materialized_invocation is invocation
        return transport

    calls: list[tuple[str, ...]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, timeout, shell, capture_output, text, check
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(
        runtime_probe_execution,
        "materialize_runtime_probe_local_python_worker_request_stdin_transport",
        fake_transport_materializer,
    )
    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match=error_match):
        execute_runtime_probe_local_python_subprocess_invocation(
            invocation,
            completion_contract_revision=(
                "runtime-probe-local-python-process-completion:test.1"
            ),
        )

    assert calls == []


def test_execute_local_python_subprocess_invocation_propagates_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Subprocess exceptions stay raw for later execution-attempt mapping slices."""
    invocation = _local_python_subprocess_invocation()

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, shell, capture_output, text, check
        raise subprocess.TimeoutExpired(cmd=args, timeout=timeout)

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(subprocess.TimeoutExpired):
        execute_runtime_probe_local_python_subprocess_invocation(
            invocation,
            completion_contract_revision=(
                "runtime-probe-local-python-process-completion:test.1"
            ),
        )


def test_execute_local_python_subprocess_invocation_attempt_observes_stdout_protocol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The attempt wrapper converts valid zero-exit stdout into observed proof."""
    invocation = _local_python_subprocess_invocation()
    calls: list[tuple[tuple[str, ...], str]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, timeout, shell, capture_output, text, check
        calls.append((args, input))
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=_local_python_stdout_protocol_text(
                normalized_payload=[
                    {"key": "first_observed_module", "value": "plugins.weather"},
                    {"key": "second_observed_module", "value": "plugins.forecast"},
                ],
                durable_artifact_reference="runtime-artifact:local-python:abc123",
            ),
            stderr="raw stderr warning is ignored for success semantics\n",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = execute_runtime_probe_local_python_subprocess_invocation_attempt(
        invocation,
        completion_contract_revision=(
            "runtime-probe-local-python-process-completion:test.1"
        ),
    )

    assert len(calls) == 1
    call_args, call_stdin_text = calls[0]
    assert call_args is invocation.argv
    _assert_local_python_worker_stdin_input(invocation, call_stdin_text)
    _assert_attempt_identity(attempt, invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("first_observed_module", "plugins.weather"),
        _field("second_observed_module", "plugins.forecast"),
    )
    assert attempt.durable_artifact_reference == "runtime-artifact:local-python:abc123"
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_execute_local_python_subprocess_invocation_attempt_maps_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Subprocess timeouts become sanitized timed-out attempts."""
    invocation = _local_python_subprocess_invocation()

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, shell, capture_output, text, check
        raise subprocess.TimeoutExpired(
            cmd=args,
            timeout=timeout,
            output="raw stdout proof payload /private/tmp/runtime-probe",
            stderr="raw stderr traceback pid=12345",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = execute_runtime_probe_local_python_subprocess_invocation_attempt(
        invocation,
        completion_contract_revision=(
            "runtime-probe-local-python-process-completion:test.1"
        ),
    )

    _assert_attempt_identity(attempt, invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_subprocess_timeout"),
        _field("normalized_outcome", "timed_out"),
        _field("exception_type", "subprocess.TimeoutExpired"),
        _field("timeout_seconds", str(invocation.timeout_seconds)),
    )
    failure_text = _attempt_failure_text(attempt)
    assert "raw stdout" not in failure_text
    assert "raw stderr" not in failure_text
    assert "traceback" not in failure_text
    assert "pid=12345" not in failure_text
    assert "/private/tmp" not in failure_text


def test_execute_local_python_subprocess_invocation_attempt_maps_generic_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generic subprocess exceptions become sanitized crashed attempts."""
    invocation = _local_python_subprocess_invocation()

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del args, cwd, env, input, timeout, shell, capture_output, text, check
        raise RuntimeError(
            "raw exception proof payload traceback pid=12345 /private/tmp/probe"
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = execute_runtime_probe_local_python_subprocess_invocation_attempt(
        invocation,
        completion_contract_revision=(
            "runtime-probe-local-python-process-completion:test.1"
        ),
    )

    _assert_attempt_identity(attempt, invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_subprocess_exception"),
        _field("normalized_outcome", "crashed"),
        _field("exception_type", "builtins.RuntimeError"),
    )
    failure_text = _attempt_failure_text(attempt)
    assert "raw exception" not in failure_text
    assert "proof payload" not in failure_text
    assert "traceback" not in failure_text
    assert "pid=12345" not in failure_text
    assert "/private/tmp" not in failure_text


def test_execute_local_python_subprocess_invocation_attempt_maps_nonzero_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nonzero raw completions become sanitized non-proof attempts."""
    invocation = _local_python_subprocess_invocation()

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, timeout, shell, capture_output, text, check
        return subprocess.CompletedProcess(
            args=args,
            returncode=42,
            stdout='{"observed_module":"plugins.weather"}\n',
            stderr="raw stderr traceback pid=12345 /private/tmp/probe\n",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = execute_runtime_probe_local_python_subprocess_invocation_attempt(
        invocation,
        completion_contract_revision=(
            "runtime-probe-local-python-process-completion:test.1"
        ),
    )

    _assert_attempt_identity(attempt, invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_process_completion"),
        _field("normalized_outcome", "crashed"),
        _field("returncode", "42"),
    )
    failure_text = _attempt_failure_text(attempt)
    assert "observed_module" not in failure_text
    assert "raw stderr" not in failure_text
    assert "traceback" not in failure_text
    assert "pid=12345" not in failure_text
    assert "/private/tmp" not in failure_text


def test_execute_local_python_subprocess_invocation_attempt_maps_malformed_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed zero-exit stdout becomes a sanitized setup-failed attempt."""
    invocation = _local_python_subprocess_invocation()

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, timeout, shell, capture_output, text, check
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout="raw stdout observed_module pid=12345 /private/tmp/probe\n",
            stderr="raw stderr traceback pid=12345 /private/tmp/probe\n",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = execute_runtime_probe_local_python_subprocess_invocation_attempt(
        invocation,
        completion_contract_revision=(
            "runtime-probe-local-python-process-completion:test.1"
        ),
    )

    _assert_attempt_identity(attempt, invocation)
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_stdout_protocol_failure"),
        _field("normalized_outcome", "setup_failed"),
        _field("returncode", "0"),
        _field("exception_type", "builtins.ValueError"),
    )
    failure_text = _attempt_failure_text(attempt)
    assert "observed_module" not in failure_text
    assert "raw stdout" not in failure_text
    assert "raw stderr" not in failure_text
    assert "traceback" not in failure_text
    assert "pid=12345" not in failure_text
    assert "/private/tmp" not in failure_text


def test_execute_local_python_subprocess_invocation_attempt_validates_before_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invocation and completion revision drift are rejected before subprocess use."""
    invocation = _local_python_subprocess_invocation()
    calls: list[tuple[str, ...]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, timeout, shell, capture_output, text, check
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="completion_contract_revision"):
        execute_runtime_probe_local_python_subprocess_invocation_attempt(
            invocation,
            completion_contract_revision="",
        )

    object.__setattr__(
        invocation,
        "argv",
        ("/workspace/other/python", *invocation.argv[1:]),
    )
    with pytest.raises(ValueError, match="argv executable"):
        execute_runtime_probe_local_python_subprocess_invocation_attempt(
            invocation,
            completion_contract_revision=(
                "runtime-probe-local-python-process-completion:test.1"
            ),
        )

    assert calls == []


def test_make_local_python_subprocess_handler_entry_returns_dispatch_entry() -> None:
    """The factory exposes a dispatchable entry for the configured family/form."""
    entry = _local_python_subprocess_handler_entry(
        module_argv=("--first", "1", "--second", "2"),
    )

    assert isinstance(entry, runtime_probe_execution.RuntimeProbeRunnerHandlerEntry)
    assert (
        entry.family_label is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert entry.form_label == "dynamic_import:importlib.import_module/1"
    assert callable(entry.handler)


def test_local_python_subprocess_handler_observes_success_and_preserves_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct handler calls delegate through invocation and attempt execution."""
    runner_request = _local_python_runner_request()
    module_argv = ("--first", "1", "--second", runner_request.request_id)
    entry = _local_python_subprocess_handler_entry(module_argv=module_argv)
    calls: list[tuple[tuple[str, ...], str]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, timeout, shell, capture_output, text, check
        calls.append((args, input))
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=_local_python_stdout_protocol_text(
                normalized_payload=[
                    {"key": "handler_observed", "value": "plugins.weather"},
                ],
                durable_artifact_reference="runtime-artifact:local-python:handler",
            ),
            stderr="",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = entry.handler(runner_request)

    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        module_argv=module_argv,
    )
    assert len(calls) == 1
    call_args, call_stdin_text = calls[0]
    assert call_args == (
        "/workspace/context-ir/.venv/bin/python",
        "-m",
        "context_ir.runtime_probe_worker",
        "--first",
        "1",
        "--second",
        runner_request.request_id,
    )
    _assert_local_python_worker_stdin_input(expected_invocation, call_stdin_text)
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("handler_observed", "plugins.weather"),
    )
    assert attempt.durable_artifact_reference == (
        "runtime-artifact:local-python:handler"
    )


@pytest.mark.parametrize(
    ("exception", "returncode", "stdout_text", "expected_outcome", "failure_source"),
    (
        (
            None,
            17,
            _local_python_stdout_protocol_text(),
            runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
            "local_python_process_completion",
        ),
        (
            subprocess.TimeoutExpired(cmd=("python",), timeout=30),
            0,
            _local_python_stdout_protocol_text(),
            runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
            "local_python_subprocess_timeout",
        ),
        (
            None,
            0,
            "not json",
            runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
            "local_python_stdout_protocol_failure",
        ),
    ),
)
def test_local_python_subprocess_handler_preserves_attempt_normalization(
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception | None,
    returncode: int,
    stdout_text: str,
    expected_outcome: runtime_probe_results.RuntimeProbeResultOutcome,
    failure_source: str,
) -> None:
    """Subprocess failure paths still flow through existing attempt normalization."""
    runner_request = _local_python_runner_request()
    entry = _local_python_subprocess_handler_entry()

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, timeout, shell, capture_output, text, check
        if exception is not None:
            raise exception
        return subprocess.CompletedProcess(
            args=args,
            returncode=returncode,
            stdout=stdout_text,
            stderr="raw stderr is not propagated into failure metadata",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = entry.handler(runner_request)

    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is expected_outcome
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        failure_source,
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            "dynamic_import:importlib.import_module/1",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            "dynamic_import:other_form/1",
        ),
    ),
)
def test_local_python_subprocess_handler_rejects_family_form_drift_before_run(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """Configured handlers reject family/form drift before subprocess execution."""
    runner_request = _local_python_runner_request()
    entry = _local_python_subprocess_handler_entry(
        family_label=family_label,
        form_label=form_label,
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, timeout, shell, capture_output, text, check
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="family/form"):
        entry.handler(runner_request)

    assert calls == []


def test_local_python_subprocess_handler_revalidates_runner_before_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runner request drift is rejected before adapter subprocess execution."""
    runner_request = _local_python_runner_request()
    entry = _local_python_subprocess_handler_entry()
    object.__setattr__(runner_request, "request_id", "runtime_probe:wrong")
    calls: list[tuple[str, ...]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, input, timeout, shell, capture_output, text, check
        calls.append(args)
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="request_id must match execution input"):
        entry.handler(runner_request)

    assert calls == []


def test_local_python_subprocess_handler_rejects_invalid_config_metadata() -> None:
    """Handler config rejects malformed local-Python subprocess metadata."""
    with pytest.raises(ValueError, match="family_label"):
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessHandlerConfig(
            family_label="dynamic_import",
            form_label="dynamic_import:importlib.import_module/1",
            python_executable="/workspace/context-ir/.venv/bin/python",
            module_name="context_ir.runtime_probe_worker",
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-process-completion:test.1"
            ),
        )
    with pytest.raises(ValueError, match="form_label"):
        _local_python_subprocess_handler_entry(form_label=" ")
    with pytest.raises(ValueError, match="python_executable.*absolute"):
        _local_python_subprocess_handler_entry(python_executable="python")
    with pytest.raises(ValueError, match="module name"):
        _local_python_subprocess_handler_entry(module_name="context_ir.worker-bad")
    with pytest.raises(ValueError, match="invocation_contract_revision"):
        _local_python_subprocess_handler_entry(invocation_contract_revision="")
    with pytest.raises(ValueError, match="completion_contract_revision"):
        _local_python_subprocess_handler_entry(completion_contract_revision=" ")
    with pytest.raises(ValueError, match="module_argv"):
        runtime_probe_execution.make_runtime_probe_local_python_subprocess_handler_entry(
            family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            form_label="dynamic_import:importlib.import_module/1",
            python_executable="/workspace/context-ir/.venv/bin/python",
            module_name="context_ir.runtime_probe_worker",
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-process-completion:test.1"
            ),
            module_argv="--request",
        )


def test_dispatching_runner_consumes_local_python_subprocess_handler_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dispatching runners can consume the factory-produced handler entry."""
    runner_request = _local_python_runner_request()
    entry = _local_python_subprocess_handler_entry()
    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (entry,)
    )
    calls: list[tuple[tuple[str, ...], str]] = []

    def fake_run(
        args: tuple[str, ...],
        *,
        cwd: str,
        env: dict[str, str],
        input: str,
        timeout: int,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, env, timeout, shell, capture_output, text, check
        calls.append((args, input))
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=_local_python_stdout_protocol_text(
                normalized_payload=[
                    {"key": "dispatch_observed", "value": "plugins.weather"},
                ],
            ),
            stderr="",
        )

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = dispatching_runner(runner_request)

    expected_invocation = _local_python_subprocess_invocation(runner_request)
    assert len(calls) == 1
    call_args, call_stdin_text = calls[0]
    assert call_args == (
        "/workspace/context-ir/.venv/bin/python",
        "-m",
        "context_ir.runtime_probe_worker",
        "--request",
        "runtime-probe-request.json",
    )
    _assert_local_python_worker_stdin_input(expected_invocation, call_stdin_text)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("dispatch_observed", "plugins.weather"),
    )


def test_dispatching_runner_executes_default_worker_in_local_python_subprocess(
    tmp_path: Path,
) -> None:
    """The parent handler can observe proof from the worker's default handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run() -> object:
                return importlib.import_module("plugins.parent_subprocess")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
    )
    entry = _local_python_subprocess_handler_entry(
        python_executable=sys.executable,
        module_argv=(),
    )
    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (entry,)
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = dispatching_runner(runner_request)

    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("imported_module", "plugins.parent_subprocess"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_dynamic_import_local_python_runner_executes_default_worker_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's default dynamic-import handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run() -> object:
                return importlib.import_module("plugins.helper_subprocess")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("imported_module", "plugins.helper_subprocess"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_exec_local_python_runner_executes_pass_source_subprocess(
    tmp_path: Path,
) -> None:
    """The exact-exec helper captures only observed pass-source proof."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> None:
                source = "pass"
                exec(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _exec_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_exec_or_eval_exec_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("execution_outcome", "completed"),
        _field("statement_kind", "pass"),
    )
    assert attempt.observed_replay_inputs == (
        _field("source_shape", "literal_statement"),
        _field("source_sha256", _EXEC_PASS_SOURCE_SHA256),
    )
    assert attempt.durable_artifact_reference == (
        f"artifact://runtime-probe/exec-source/{request.request_id}.json"
    )
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_eval_local_python_runner_executes_literal_source_subprocess(
    tmp_path: Path,
) -> None:
    """The exact-eval helper captures only observed literal-expression proof."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> str:
                source = '"eval-probe-value"'
                return eval(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _eval_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_exec_or_eval_eval_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("evaluation_outcome", "returned_value"),
        _field("result_type", "builtins.str"),
    )
    assert attempt.observed_replay_inputs == (
        _field("source_shape", "literal_expression"),
        _field("source_sha256", _EVAL_SOURCE_SHA256),
    )
    assert attempt.durable_artifact_reference == (
        f"artifact://runtime-probe/eval-source/{request.request_id}.json"
    )
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_metaclass_keyword_local_python_runner_executes_source_import_subprocess(
    tmp_path: Path,
) -> None:
    """The exact metaclass helper captures class creation during module import."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Meta(type):
                pass

            class Example(metaclass=Meta):
                pass

            def run() -> None:
                raise AssertionError("metaclass probe must not call run")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _metaclass_keyword_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = (
        make_runtime_probe_metaclass_behavior_keyword_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision="runtime-probe-local-python-completion:test.1",
        )
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("class_creation_outcome", "created_class"),
        _field("created_class_qualified_name", "main.Example"),
        _field("selected_metaclass_qualified_name", "main.Meta"),
    )
    assert attempt.observed_replay_inputs == ()
    assert attempt.durable_artifact_reference == (
        f"artifact://runtime-probe/metaclass-selection/{request.request_id}.json"
    )
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_metaclass_keyword_local_python_runner_executes_base_class_subprocess(
    tmp_path: Path,
) -> None:
    """The parent runner accepts the canonical base-plus-keyword class form."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Meta(type):
                pass

            class Base:
                pass

            class Example(Base, metaclass=Meta):
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _metaclass_keyword_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = (
        make_runtime_probe_metaclass_behavior_keyword_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision="runtime-probe-local-python-completion:test.1",
        )
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("class_creation_outcome", "created_class"),
        _field("created_class_qualified_name", "main.Example"),
        _field("selected_metaclass_qualified_name", "main.Meta"),
    )
    assert attempt.observed_replay_inputs == ()
    assert attempt.durable_artifact_reference == (
        f"artifact://runtime-probe/metaclass-selection/{request.request_id}.json"
    )
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


@pytest.mark.parametrize("source_text", ("print(1)", "pass\npass"))
def test_exec_local_python_runner_rejects_non_pass_source_subprocess(
    tmp_path: Path,
    source_text: str,
) -> None:
    """The exec worker fails closed unless the captured source is exactly pass."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            f"""
            def run() -> None:
                source = {source_text!r}
                exec(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=_exec_request(),
    )
    runner = make_runtime_probe_exec_or_eval_exec_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.observed_replay_inputs == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


@pytest.mark.parametrize("source_text", ('"other-value"', "7"))
def test_eval_local_python_runner_rejects_non_literal_source_subprocess(
    tmp_path: Path,
    source_text: str,
) -> None:
    """The eval worker fails closed unless the captured source is exact."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            f"""
            def run() -> object:
                source = {source_text!r}
                return eval(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=_eval_request(),
    )
    runner = make_runtime_probe_exec_or_eval_eval_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.observed_replay_inputs == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


def test_dynamic_import_local_python_runner_executes_loader_alias_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper registers loader.import_module for the worker."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib as loader

            def run() -> object:
                return loader.import_module("plugins.loader_helper_subprocess")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _request(
        form_label=_LOADER_IMPORT_MODULE_FORM_LABEL,
        boundary_text="loader.import_module(name)",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("imported_module", "plugins.loader_helper_subprocess"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_dynamic_import_local_python_runner_executes_imported_name_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper registers imported import_module for the worker."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from importlib import import_module

            def run() -> object:
                return import_module("plugins.imported_name_helper_subprocess")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _request(
        form_label=_IMPORTED_IMPORT_MODULE_FORM_LABEL,
        boundary_text="import_module(name)",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("imported_module", "plugins.imported_name_helper_subprocess"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_dynamic_import_local_python_runner_executes_load_module_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper registers imported load_module for the worker."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from importlib import import_module as load_module

            def run() -> object:
                return load_module("plugins.load_module_helper_subprocess")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _request(
        form_label=_LOAD_MODULE_FORM_LABEL,
        boundary_text="load_module(name)",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("imported_module", "plugins.load_module_helper_subprocess"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_dynamic_import_local_python_runner_executes_builtin_import_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper registers exact bare __import__ for the worker."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    observed_module_name = "plugins.builtin_import_helper_subprocess"
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            f"""
            import sys

            def run() -> object:
                imported_module = __import__("{observed_module_name}")
                assert sys.modules["{observed_module_name}"] is imported_module
                return imported_module
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _request(
        form_label=_BUILTIN_IMPORT_FORM_LABEL,
        boundary_text="__import__(name)",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("imported_module", observed_module_name),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_dynamic_import_local_python_runner_executes_builtins_import_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper registers exact builtins.__import__ for the worker."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    observed_module_name = "plugins.builtins_import_helper_subprocess"
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            f"""
            import builtins
            import sys

            def run() -> object:
                imported_module = builtins.__import__("{observed_module_name}")
                assert sys.modules["{observed_module_name}"] is imported_module
                return imported_module
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _request(
        form_label=_BUILTINS_IMPORT_FORM_LABEL,
        boundary_text="builtins.__import__(name)",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("imported_module", observed_module_name),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_dynamic_import_local_python_runner_executes_loader_builtin_import_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper registers exact loader.__import__ for the worker."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    observed_module_name = "plugins.loader_builtin_import_helper_subprocess"
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            f"""
            import builtins as loader
            import sys

            def run() -> object:
                imported_module = loader.__import__("{observed_module_name}")
                assert sys.modules["{observed_module_name}"] is imported_module
                return imported_module
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _request(
        form_label=_LOADER_BUILTIN_IMPORT_FORM_LABEL,
        boundary_text="loader.__import__(name)",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("imported_module", observed_module_name),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_dynamic_import_local_python_runner_rejects_builtin_import_literal_boundary(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects __import__ requests outside __import__(name)."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    observed_module_name = "plugins.builtin_import_literal_subprocess"
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            f"""
            def run() -> object:
                return __import__("{observed_module_name}")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _request(
        form_label=_BUILTIN_IMPORT_FORM_LABEL,
        boundary_text=f'__import__("{observed_module_name}")',
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


def test_dynamic_import_local_python_runner_rejects_builtins_import_literal_boundary(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects builtins.__import__ literal requests."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    observed_module_name = "plugins.builtins_import_literal_subprocess"
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            f"""
            import builtins

            def run() -> object:
                return builtins.__import__("{observed_module_name}")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _request(
        form_label=_BUILTINS_IMPORT_FORM_LABEL,
        boundary_text=f'builtins.__import__("{observed_module_name}")',
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


def test_dynamic_import_local_python_runner_rejects_loader_builtin_literal(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects loader.__import__ literal requests."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    observed_module_name = "plugins.loader_builtin_import_literal_subprocess"
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            f"""
            import builtins as loader

            def run() -> object:
                return loader.__import__("{observed_module_name}")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _request(
        form_label=_LOADER_BUILTIN_IMPORT_FORM_LABEL,
        boundary_text=f'loader.__import__("{observed_module_name}")',
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


@pytest.mark.parametrize(
    ("attribute_name", "expected_value"),
    (("value", "true"), ("missing", "false")),
)
def test_reflective_hasattr_local_python_runner_executes_hasattr_subprocess(
    attribute_name: str,
    expected_value: str,
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact hasattr handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            f"""
            class Example:
                value = 1

            def run() -> object:
                obj = Example()
                name = "{attribute_name}"
                return hasattr(obj, name)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_hasattr_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_hasattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("attribute_present", expected_value),)
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_default_local_python_subprocess_runner_executes_exact_hasattr_replay_inputs(
    tmp_path: Path,
) -> None:
    """The default runner observes the exact hasattr/2 replay-input pilot."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def probe_attribute(obj: object, name: str) -> bool:
                return hasattr(obj, name)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_hasattr_exact_replay_input_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_default_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("attribute_present", "true"),)
    assert attempt.observed_replay_inputs == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_default_local_python_subprocess_runner_executes_exact_literal_hasattr(
    tmp_path: Path,
) -> None:
    """The default runner calls ``main.probe_literal_attribute(1)``."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def probe_literal_attribute(obj: object) -> bool:
                assert obj == 1
                return hasattr(obj, "bit_length")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_hasattr_literal_exact_replay_input_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_default_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("attribute_present", "true"),)
    assert attempt.observed_replay_inputs == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_reflective_hasattr_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects exact-form requests with drifted boundary text."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                value = 1

            def run() -> object:
                obj = Example()
                name = "value"
                return hasattr(obj, name)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_hasattr_request(
        boundary_text='hasattr(obj, "value")',
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_hasattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


def test_reflective_hasattr_local_python_runner_rejects_unapproved_literal(
    tmp_path: Path,
) -> None:
    """The literal boundary is accepted only for the exact replay identity."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> bool:
                obj = 1
                return hasattr(obj, "bit_length")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_hasattr_request(
        boundary_text='hasattr(obj, "bit_length")',
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_hasattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


@pytest.mark.parametrize(
    ("source_text", "expected_outcome"),
    (
        (
            """
            class Example:
                value = 1

            def run() -> object:
                obj = Example()
                name = "value"
                return getattr(obj, name)
            """,
            "returned_value",
        ),
        (
            """
            class Example:
                pass

            def run() -> object:
                obj = Example()
                name = "missing"
                try:
                    getattr(obj, name)
                except AttributeError:
                    return None
                raise AssertionError("expected missing attribute")
            """,
            "raised_attribute_error",
        ),
    ),
)
def test_reflective_getattr_local_python_runner_executes_getattr_subprocess(
    source_text: str,
    expected_outcome: str,
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact getattr handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(source_text).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_getattr_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_getattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("lookup_outcome", expected_outcome),)
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_default_local_python_subprocess_runner_executes_exact_literal_getattr(
    tmp_path: Path,
) -> None:
    """The default runner calls ``main.probe_literal_attribute(1)`` for getattr."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def probe_literal_attribute(obj: object) -> object:
                assert obj == 1
                return getattr(obj, "bit_length")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_getattr_literal_exact_replay_input_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_default_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("lookup_outcome", "returned_value"),)
    assert attempt.observed_replay_inputs == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_reflective_getattr_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects exact-form requests with drifted boundary text."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                value = 1

            def run() -> object:
                obj = Example()
                name = "value"
                return getattr(obj, name)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_getattr_request(
        boundary_text='getattr(obj, "value")',
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_getattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


@pytest.mark.parametrize(
    ("source_text", "expected_outcome"),
    (
        (
            """
            class Example:
                value = 1

            def run() -> object:
                obj = Example()
                name = "value"
                default = object()
                return getattr(obj, name, default)
            """,
            "returned_value",
        ),
        (
            """
            class Example:
                pass

            def run() -> object:
                obj = Example()
                name = "missing"
                default = object()
                result = getattr(obj, name, default)
                assert result is default
                return result
            """,
            "returned_default_value",
        ),
    ),
)
def test_reflective_getattr_default_local_python_runner_executes_getattr_subprocess(
    source_text: str,
    expected_outcome: str,
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact getattr/3 handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(source_text).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_getattr_default_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = (
        make_runtime_probe_reflective_getattr_default_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
        )
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("lookup_outcome", expected_outcome),)
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_reflective_getattr_default_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects exact-form requests with drifted boundary text."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                value = 1

            def run() -> object:
                obj = Example()
                name = "value"
                return getattr(obj, name, None)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_getattr_default_request(
        boundary_text='getattr(obj, "value", None)',
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = (
        make_runtime_probe_reflective_getattr_default_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
        )
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


@pytest.mark.parametrize(
    ("source_text", "expected_outcome"),
    (
        (
            """
            class Example:
                def __init__(self) -> None:
                    self.value = 1

            def run() -> object:
                obj = Example()
                namespace = vars(obj)
                assert namespace == {"value": 1}
                return namespace
            """,
            "returned_namespace",
        ),
        (
            """
            def run() -> object:
                obj = object()
                try:
                    vars(obj)
                except TypeError:
                    return None
                raise AssertionError("expected TypeError")
            """,
            "raised_type_error",
        ),
    ),
)
def test_reflective_vars_local_python_runner_executes_vars_subprocess(
    source_text: str,
    expected_outcome: str,
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact vars/1 handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(source_text).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_vars_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_vars_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("lookup_outcome", expected_outcome),)
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_reflective_vars_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects exact vars requests with drifted boundaries."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                pass

            def run() -> object:
                obj = Example()
                return vars(obj)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_vars_request(
        boundary_text="vars()",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_vars_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


def test_reflective_vars_zero_local_python_runner_executes_vars_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact vars/0 handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> object:
                local_value = 1
                namespace = vars()
                assert namespace == {"local_value": 1}
                return namespace
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_vars_zero_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("lookup_outcome", "returned_namespace"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_reflective_vars_zero_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects vars/0 requests with drifted boundaries."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> object:
                return vars()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_vars_zero_request(
        boundary_text="vars(obj)",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


def test_reflective_dir_local_python_runner_executes_dir_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact dir/1 handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                def __dir__(self) -> list[str]:
                    return ["beta", "alpha"]

            def run() -> object:
                obj = Example()
                listing = dir(obj)
                assert listing == ["alpha", "beta"]
                return listing
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_dir_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_dir_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("listing_entry_count", "2"),)
    assert attempt.durable_artifact_reference == (
        f"artifact://runtime-probe/dir-listing/{runner_request.request_id}.json"
    )
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_reflective_dir_zero_local_python_runner_executes_dir_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact dir/0 handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> object:
                alpha = 1
                beta = 2
                listing = dir()
                assert listing == ["alpha", "beta"]
                return listing
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_dir_request(
        form_label=_REFLECTIVE_DIR_ZERO_FORM_LABEL,
        boundary_text="dir()",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("listing_entry_count", "2"),)
    assert attempt.durable_artifact_reference == (
        f"artifact://runtime-probe/dir-listing/{runner_request.request_id}.json"
    )
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_reflective_dir_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects dir/1 requests with drifted boundaries."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> object:
                obj = object()
                return dir(obj)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_dir_request(boundary_text="dir()")
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_dir_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


def test_reflective_dir_zero_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects dir/0 requests with drifted boundaries."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> object:
                return dir()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _reflective_dir_request(
        form_label=_REFLECTIVE_DIR_ZERO_FORM_LABEL,
        boundary_text="dir(obj)",
    )
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


def test_runtime_mutation_globals_zero_local_python_runner_executes_globals_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact globals/0 handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            MODULE_VALUE = object()

            def run() -> object:
                local_value = object()
                namespace = globals()
                assert namespace["MODULE_VALUE"] is MODULE_VALUE
                assert namespace["__name__"] == "main"
                assert "local_value" not in namespace
                return namespace
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_globals_zero_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = (
        make_runtime_probe_runtime_mutation_globals_zero_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
        )
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("lookup_outcome", "returned_namespace"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_runtime_mutation_globals_zero_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects globals/0 requests with drifted boundaries."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> object:
                return globals()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_globals_zero_request(boundary_text="globals( )")
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = (
        make_runtime_probe_runtime_mutation_globals_zero_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
        )
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


@pytest.mark.parametrize(
    ("family_label", "form_label", "boundary_text"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            "runtime_mutation:locals/0",
            "locals()",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            "runtime_mutation:setattr/3",
            "setattr(obj, name, value)",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            "runtime_mutation:delattr/2",
            "delattr(obj, name)",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_DIR_ZERO_FORM_LABEL,
            "dir()",
        ),
    ),
)
def test_runtime_mutation_globals_zero_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
    boundary_text: str,
) -> None:
    """The exact-globals/0 helper does not register adjacent handlers."""
    request = replace(
        _runtime_mutation_globals_zero_request(
            form_label=form_label,
            boundary_text=boundary_text,
        ),
        family_label=family_label,
    )
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = (
        make_runtime_probe_runtime_mutation_globals_zero_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
        )
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


def test_runtime_mutation_locals_zero_local_python_runner_executes_locals_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact locals/0 handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            MODULE_VALUE = object()

            def run() -> object:
                local_value = object()
                namespace = locals()
                assert type(namespace) is dict
                assert namespace["local_value"] is local_value
                assert "MODULE_VALUE" not in namespace
                assert "namespace" not in namespace
                assert "self" not in namespace
                assert "args" not in namespace
                assert "kwargs" not in namespace
                return namespace
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_locals_zero_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = (
        make_runtime_probe_runtime_mutation_locals_zero_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
        )
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("lookup_outcome", "returned_namespace"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_runtime_mutation_locals_zero_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects locals/0 requests with drifted boundaries."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> object:
                return locals()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_locals_zero_request(boundary_text="locals( )")
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = (
        make_runtime_probe_runtime_mutation_locals_zero_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
        )
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


@pytest.mark.parametrize(
    ("family_label", "form_label", "boundary_text"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            _RUNTIME_MUTATION_GLOBALS_ZERO_FORM_LABEL,
            "globals()",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            "runtime_mutation:setattr/3",
            "setattr(obj, name, value)",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            "runtime_mutation:delattr/2",
            "delattr(obj, name)",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_DIR_ZERO_FORM_LABEL,
            "dir()",
        ),
    ),
)
def test_runtime_mutation_locals_zero_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
    boundary_text: str,
) -> None:
    """The exact-locals/0 helper does not register adjacent handlers."""
    request = replace(
        _runtime_mutation_locals_zero_request(
            form_label=form_label,
            boundary_text=boundary_text,
        ),
        family_label=family_label,
    )
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = (
        make_runtime_probe_runtime_mutation_locals_zero_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
        )
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


def test_runtime_mutation_setattr_local_python_runner_executes_setattr_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact setattr/3 handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                pass

            def run() -> object:
                obj = Example()
                name = "value"
                assigned = object()
                result = setattr(obj, name, assigned)
                assert result is None
                return obj
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_setattr_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_runtime_mutation_setattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (_field("mutation_outcome", "returned_none"),)
    assert attempt.durable_artifact_reference == (
        f"artifact://runtime-probe/setattr-value/{runner_request.request_id}.json"
    )
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_runtime_mutation_setattr_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects setattr/3 requests with drifted boundaries."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                pass

            def run() -> object:
                obj = Example()
                return setattr(obj, "value", 1)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_setattr_request(boundary_text="setattr(obj,name,value)")
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_runtime_mutation_setattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


@pytest.mark.parametrize(
    ("family_label", "form_label", "boundary_text"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            _RUNTIME_MUTATION_GLOBALS_ZERO_FORM_LABEL,
            "globals()",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            _RUNTIME_MUTATION_LOCALS_ZERO_FORM_LABEL,
            "locals()",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            _RUNTIME_MUTATION_DELATTR_FORM_LABEL,
            "delattr(obj, name)",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
            "getattr(obj, name)",
        ),
    ),
)
def test_runtime_mutation_setattr_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
    boundary_text: str,
) -> None:
    """The exact-setattr helper does not register adjacent handlers."""
    request = replace(
        _runtime_mutation_setattr_request(
            form_label=form_label,
            boundary_text=boundary_text,
        ),
        family_label=family_label,
    )
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_runtime_mutation_setattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


def test_runtime_mutation_delattr_local_python_runner_executes_delattr_subprocess(
    tmp_path: Path,
) -> None:
    """The composed helper reaches the worker's exact delattr/2 handler."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                pass

            def run() -> object:
                obj = Example()
                obj.value = 1
                name = "value"
                result = delattr(obj, name)
                assert result is None
                assert not hasattr(obj, name)
                return obj
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_delattr_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_runtime_mutation_delattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("mutation_outcome", "deleted_attribute"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_default_local_python_subprocess_runner_executes_exact_literal_delattr(
    tmp_path: Path,
) -> None:
    """The default runner calls the exact literal-delattr target with ProbeTarget."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class ProbeTarget:
                def __init__(self) -> None:
                    self.flag = "ready"


            def probe_delete_literal_attribute(obj: object) -> None:
                delattr(obj, "flag")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_delattr_literal_exact_replay_input_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_default_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("mutation_outcome", "deleted_attribute"),
    )
    assert attempt.observed_replay_inputs == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_runtime_mutation_delattr_local_python_runner_rejects_boundary_drift(
    tmp_path: Path,
) -> None:
    """The subprocess worker rejects delattr/2 requests with drifted boundaries."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Example:
                pass

            def run() -> object:
                obj = Example()
                obj.value = 1
                return delattr(obj, "value")
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_delattr_request(boundary_text="delattr(obj,name)")
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_runtime_mutation_delattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    attempt = runner(runner_request)

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields[0] == _field(
        "failure_source",
        "local_python_process_completion",
    )


@pytest.mark.parametrize(
    ("family_label", "form_label", "boundary_text"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            _RUNTIME_MUTATION_GLOBALS_ZERO_FORM_LABEL,
            "globals()",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            _RUNTIME_MUTATION_LOCALS_ZERO_FORM_LABEL,
            "locals()",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            "runtime_mutation:setattr/3",
            "setattr(obj, name, value)",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
            "getattr(obj, name)",
        ),
    ),
)
def test_runtime_mutation_delattr_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
    boundary_text: str,
) -> None:
    """The exact-delattr helper does not register adjacent handlers."""
    request = replace(
        _runtime_mutation_delattr_request(
            form_label=form_label,
            boundary_text=boundary_text,
        ),
        family_label=family_label,
    )
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_runtime_mutation_delattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_HASATTR_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            "reflective_builtin:getattr/2",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            "dynamic_import:other.__import__/1",
        ),
    ),
)
def test_dynamic_import_local_python_runner_registers_only_exact_supported_forms(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The composed helper does not register adjacent family/form handlers."""
    request = replace(_request(), family_label=family_label, form_label=form_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL,
            "exec_or_eval:eval/1",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            _RUNTIME_MUTATION_SETATTR_FORM_LABEL,
        ),
    ),
)
def test_exec_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The exact-exec helper does not register adjacent exec/eval handlers."""
    request = replace(_exec_request(form_label=form_label), family_label=family_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_exec_or_eval_exec_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL,
            _EXEC_OR_EVAL_EXEC_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION,
            _RUNTIME_MUTATION_SETATTR_FORM_LABEL,
        ),
    ),
)
def test_eval_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The exact-eval helper does not register adjacent exec/eval handlers."""
    request = replace(_eval_request(form_label=form_label), family_label=family_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_exec_or_eval_eval_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.METACLASS_BEHAVIOR,
            "metaclass_behavior:base",
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL,
            _EXEC_OR_EVAL_EXEC_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
    ),
)
def test_metaclass_keyword_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The metaclass helper does not register adjacent family/form handlers."""
    request = replace(
        _metaclass_keyword_request(form_label=form_label),
        family_label=family_label,
    )
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = (
        make_runtime_probe_metaclass_behavior_keyword_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision="runtime-probe-local-python-completion:test.1",
        )
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_THREE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_VARS_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_DIR_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
    ),
)
def test_reflective_hasattr_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The exact-hasattr helper does not register adjacent family/form handlers."""
    if family_label is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        request = _reflective_hasattr_request(
            form_label=form_label,
            boundary_text=(
                "getattr(obj, name)"
                if form_label == _REFLECTIVE_GETATTR_TWO_FORM_LABEL
                else "getattr(obj, name, default)"
                if form_label == _REFLECTIVE_GETATTR_THREE_FORM_LABEL
                else "dir(obj)"
                if form_label == _REFLECTIVE_DIR_ONE_FORM_LABEL
                else "vars(obj)"
            ),
        )
    else:
        request = _request(form_label=form_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_reflective_hasattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_HASATTR_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_THREE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_VARS_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_DIR_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
    ),
)
def test_reflective_getattr_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The exact-getattr helper does not register adjacent family/form handlers."""
    if family_label is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        request = _reflective_getattr_request(
            form_label=form_label,
            boundary_text=(
                "hasattr(obj, name)"
                if form_label == _REFLECTIVE_HASATTR_FORM_LABEL
                else "getattr(obj, name, default)"
                if form_label == _REFLECTIVE_GETATTR_THREE_FORM_LABEL
                else "dir(obj)"
                if form_label == _REFLECTIVE_DIR_ONE_FORM_LABEL
                else "vars(obj)"
            ),
        )
    else:
        request = _request(form_label=form_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_reflective_getattr_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_HASATTR_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_VARS_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_DIR_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
    ),
)
def test_reflective_getattr_default_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The exact-getattr/3 helper does not register adjacent family/form handlers."""
    if family_label is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        request = _reflective_getattr_default_request(
            form_label=form_label,
            boundary_text=(
                "hasattr(obj, name)"
                if form_label == _REFLECTIVE_HASATTR_FORM_LABEL
                else "getattr(obj, name)"
                if form_label == _REFLECTIVE_GETATTR_TWO_FORM_LABEL
                else "dir(obj)"
                if form_label == _REFLECTIVE_DIR_ONE_FORM_LABEL
                else "vars(obj)"
            ),
        )
    else:
        request = _request(form_label=form_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = (
        make_runtime_probe_reflective_getattr_default_local_python_subprocess_runner(
            python_executable=sys.executable,
            invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
        )
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_HASATTR_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_THREE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_VARS_ZERO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_DIR_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
    ),
)
def test_reflective_vars_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The exact-vars helper does not register adjacent family/form handlers."""
    if family_label is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        request = _reflective_vars_request(
            form_label=form_label,
            boundary_text=(
                "hasattr(obj, name)"
                if form_label == _REFLECTIVE_HASATTR_FORM_LABEL
                else "getattr(obj, name)"
                if form_label == _REFLECTIVE_GETATTR_TWO_FORM_LABEL
                else "getattr(obj, name, default)"
                if form_label == _REFLECTIVE_GETATTR_THREE_FORM_LABEL
                else "dir(obj)"
                if form_label == _REFLECTIVE_DIR_ONE_FORM_LABEL
                else "vars()"
            ),
        )
    else:
        request = _request(form_label=form_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_reflective_vars_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_HASATTR_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_THREE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_VARS_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_DIR_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
    ),
)
def test_reflective_vars_zero_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The exact-vars/0 helper does not register adjacent family/form handlers."""
    if family_label is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        request = _reflective_vars_zero_request(
            form_label=form_label,
            boundary_text=(
                "hasattr(obj, name)"
                if form_label == _REFLECTIVE_HASATTR_FORM_LABEL
                else "getattr(obj, name)"
                if form_label == _REFLECTIVE_GETATTR_TWO_FORM_LABEL
                else "getattr(obj, name, default)"
                if form_label == _REFLECTIVE_GETATTR_THREE_FORM_LABEL
                else "dir(obj)"
                if form_label == _REFLECTIVE_DIR_ONE_FORM_LABEL
                else "vars(obj)"
            ),
        )
    else:
        request = _request(form_label=form_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_HASATTR_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_THREE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_VARS_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_VARS_ZERO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_DIR_ZERO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
    ),
)
def test_reflective_dir_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The exact-dir helper does not register adjacent family/form handlers."""
    if family_label is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        request = _reflective_dir_request(
            form_label=form_label,
            boundary_text=(
                "hasattr(obj, name)"
                if form_label == _REFLECTIVE_HASATTR_FORM_LABEL
                else "getattr(obj, name)"
                if form_label == _REFLECTIVE_GETATTR_TWO_FORM_LABEL
                else "getattr(obj, name, default)"
                if form_label == _REFLECTIVE_GETATTR_THREE_FORM_LABEL
                else "vars(obj)"
                if form_label == _REFLECTIVE_VARS_ONE_FORM_LABEL
                else "vars()"
                if form_label == _REFLECTIVE_VARS_ZERO_FORM_LABEL
                else "dir()"
            ),
        )
    else:
        request = _request(form_label=form_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_reflective_dir_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


@pytest.mark.parametrize(
    ("family_label", "form_label"),
    (
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_HASATTR_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_TWO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_GETATTR_THREE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_VARS_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_VARS_ZERO_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            _REFLECTIVE_DIR_ONE_FORM_LABEL,
        ),
        (
            runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            _IMPORTLIB_IMPORT_MODULE_FORM_LABEL,
        ),
    ),
)
def test_reflective_dir_zero_local_python_runner_registers_only_exact_form(
    monkeypatch: pytest.MonkeyPatch,
    family_label: runtime_probe_requests.RuntimeProbeFamily,
    form_label: str,
) -> None:
    """The exact-dir/0 helper does not register adjacent family/form handlers."""
    if family_label is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN:
        request = _reflective_dir_request(
            form_label=form_label,
            boundary_text=(
                "hasattr(obj, name)"
                if form_label == _REFLECTIVE_HASATTR_FORM_LABEL
                else "getattr(obj, name)"
                if form_label == _REFLECTIVE_GETATTR_TWO_FORM_LABEL
                else "getattr(obj, name, default)"
                if form_label == _REFLECTIVE_GETATTR_THREE_FORM_LABEL
                else "vars(obj)"
                if form_label == _REFLECTIVE_VARS_ONE_FORM_LABEL
                else "vars()"
                if form_label == _REFLECTIVE_VARS_ZERO_FORM_LABEL
                else "dir(obj)"
            ),
        )
    else:
        request = _request(form_label=form_label)
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported helper request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", family_label.value),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


def test_default_local_python_runner_registers_exact_current_forms() -> None:
    """The default local-Python helper registers only pushed exact handlers."""
    runner = make_runtime_probe_default_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )

    assert isinstance(runner, runtime_probe_execution.RuntimeProbeDispatchingRunner)
    handler_keys = tuple(
        (handler_entry.family_label, handler_entry.form_label)
        for handler_entry in runner.handler_entries
    )
    assert handler_keys == _EXPECTED_DEFAULT_LOCAL_PYTHON_RUNNER_HANDLER_KEYS
    assert len(set(handler_keys)) == len(handler_keys)


def test_default_local_python_runner_executes_non_dynamic_subprocess(
    tmp_path: Path,
) -> None:
    """The default helper routes non-dynamic exact forms to the worker."""
    project_source_path = str(Path(__file__).resolve().parents[1] / "src")
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> object:
                local_value = object()
                namespace = locals()
                assert type(namespace) is dict
                assert namespace["local_value"] is local_value
                assert "namespace" not in namespace
                return namespace
            """
        ).lstrip(),
        encoding="utf-8",
    )
    request = _runtime_mutation_locals_zero_request()
    runner_request = _local_python_runner_request(
        (
            _field("repository_root", str(tmp_path)),
            _field("working_directory", str(tmp_path)),
            _field("python_path_entry", project_source_path),
        ),
        timeout_seconds=10,
        request=request,
    )
    runner = make_runtime_probe_default_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    expected_invocation = _local_python_subprocess_invocation(
        runner_request,
        python_executable=sys.executable,
        module_argv=(),
    )

    attempt = runner(runner_request)

    assert expected_invocation.argv == (
        sys.executable,
        "-m",
        "context_ir.runtime_probe_worker",
    )
    _assert_attempt_identity(attempt, expected_invocation)
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == (
        _field("lookup_outcome", "returned_namespace"),
    )
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_default_local_python_runner_materializes_missing_handler_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default helper still fails closed for unsupported forms."""
    form_label = "runtime_mutation:other/0"
    request = _runtime_mutation_globals_zero_request(
        form_label=form_label,
        boundary_text="other()",
    )
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    runner = make_runtime_probe_default_local_python_subprocess_runner(
        python_executable=sys.executable,
        invocation_contract_revision="runtime-probe-local-python-subprocess:test.1",
        completion_contract_revision="runtime-probe-local-python-completion:test.1",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(str(arg) for arg in args))
        raise AssertionError("unsupported default request reached subprocess")

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", fake_run)

    attempt = runner(runner_request)

    assert calls == []
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field(
            "family_label",
            runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION.value,
        ),
        _field("form_label", form_label),
        _field("missing_handler_outcome", "setup_failed"),
    )


def test_default_local_python_runner_exports_module_local_only() -> None:
    """The default local-Python factory is exported only from this module."""
    helper_name = "make_runtime_probe_default_local_python_subprocess_runner"

    assert helper_name in runtime_probe_execution.__all__
    assert hasattr(runtime_probe_execution, helper_name)
    assert helper_name not in context_ir.__all__
    assert not hasattr(context_ir, helper_name)


def test_materialize_local_python_timeout_attempt_is_sanitized() -> None:
    """Timeout exceptions become deterministic non-proof attempts without raw data."""
    invocation = _local_python_subprocess_invocation()
    exception = subprocess.TimeoutExpired(
        cmd=invocation.argv,
        timeout=invocation.timeout_seconds,
        output="raw stdout proof payload /private/tmp/runtime-probe",
        stderr="raw stderr traceback pid=12345",
    )

    attempt = materialize_runtime_probe_local_python_subprocess_exception_attempt(
        invocation,
        exception,
    )

    runner_request = invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "local Python subprocess timed out; recorded as timed_out"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_subprocess_timeout"),
        _field("normalized_outcome", "timed_out"),
        _field("exception_type", "subprocess.TimeoutExpired"),
        _field("timeout_seconds", str(invocation.timeout_seconds)),
    )
    failure_text = "\n".join(
        (
            attempt.failure_summary,
            *(field.value for field in attempt.failure_detail_fields),
        )
    )
    assert "raw stdout" not in failure_text
    assert "raw stderr" not in failure_text
    assert "/private/tmp" not in failure_text
    assert "pid=12345" not in failure_text
    assert "traceback" not in failure_text
    assert invocation.working_directory not in failure_text


def test_materialize_local_python_exception_attempt_is_sanitized() -> None:
    """Generic local subprocess exceptions default to sanitized crashed attempts."""
    invocation = _local_python_subprocess_invocation()
    exception = RuntimeError(
        "raw stderr traceback pid=12345 from /private/tmp/runtime-probe"
    )

    attempt = materialize_runtime_probe_local_python_subprocess_exception_attempt(
        invocation,
        exception,
    )

    runner_request = invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "local Python subprocess raised RuntimeError; recorded as crashed"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_subprocess_exception"),
        _field("normalized_outcome", "crashed"),
        _field("exception_type", "builtins.RuntimeError"),
    )
    failure_text = "\n".join(
        (
            attempt.failure_summary,
            *(field.value for field in attempt.failure_detail_fields),
        )
    )
    assert "raw stderr" not in failure_text
    assert "traceback" not in failure_text
    assert "pid=12345" not in failure_text
    assert "/private/tmp" not in failure_text
    assert invocation.working_directory not in failure_text


def test_materialize_nonzero_local_python_completion_attempt_is_non_proof() -> None:
    """Nonzero completions become non-proof attempts without parsing raw output."""
    completion = _local_python_process_completion(
        returncode=17,
        stdout_text='{"observed_module":"plugins.weather"}\n',
        stderr_text="Traceback raw stderr pid=12345 /private/tmp/runtime-probe\n",
    )

    attempt = materialize_runtime_probe_local_python_process_completion_attempt(
        completion
    )

    runner_request = completion.invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "local Python subprocess exited with returncode 17; recorded as crashed"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_process_completion"),
        _field("normalized_outcome", "crashed"),
        _field("returncode", "17"),
    )
    result_batch = _assemble_result_batch(
        runtime_probe_execution.RuntimeProbeExecutionInputBatch(
            plan_id=runner_request.plan_id,
            request_ids=(runner_request.request_id,),
            inputs=(runner_request.execution_input,),
        ),
        (attempt,),
    )
    result = result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert result.is_admissible_runtime_backed_proof is False

    failure_text = "\n".join(
        (
            attempt.failure_summary,
            *(field.value for field in attempt.failure_detail_fields),
        )
    )
    assert "observed_module" not in failure_text
    assert "raw stderr" not in failure_text
    assert "pid=12345" not in failure_text
    assert "/private/tmp" not in failure_text
    assert completion.stdout_text not in failure_text
    assert completion.stderr_text not in failure_text


def test_nonzero_local_python_completion_attempt_supports_configured_outcome() -> None:
    """Nonzero completions can be mapped to a configured non-proof outcome."""
    setup_failed = runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    completion = _local_python_process_completion(
        returncode=64,
        stdout_text='{"observed_module":"plugins.weather"}\n',
        stderr_text="missing setup variable from raw stderr\n",
    )

    attempt = materialize_runtime_probe_local_python_process_completion_attempt(
        completion,
        outcome=setup_failed,
    )

    runner_request = completion.invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.outcome is setup_failed
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "local Python subprocess exited with returncode 64; recorded as setup_failed"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_process_completion"),
        _field("normalized_outcome", "setup_failed"),
        _field("returncode", "64"),
    )


def test_nonzero_local_python_completion_attempt_rejects_observed_outcome() -> None:
    """Nonzero completion failure materialization cannot produce proof outcomes."""
    completion = _local_python_process_completion(returncode=17)

    with pytest.raises(ValueError, match="non-proof outcome"):
        materialize_runtime_probe_local_python_process_completion_attempt(
            completion,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
        )


def test_materialize_zero_returncode_completion_attempt_rejects_deferred_success() -> (
    None
):
    """Zero-returncode completions are not interpreted by the failure boundary."""
    completion = _local_python_process_completion(
        returncode=0,
        stdout_text='{"observed_module":"plugins.weather"}\n',
        stderr_text="",
    )

    with pytest.raises(ValueError, match="deferred"):
        materialize_runtime_probe_local_python_process_completion_attempt(completion)


def test_materialize_stdout_protocol_failure_attempt_is_non_proof() -> None:
    """Malformed zero-exit stdout becomes a sanitized non-proof attempt."""
    completion = _local_python_process_completion(
        returncode=0,
        stdout_text="raw stdout observed_module pid=12345 /private/tmp/probe\n",
        stderr_text="raw stderr traceback pid=12345 /private/tmp/probe\n",
    )
    exception = ValueError(
        "raw stdout observed_module raw stderr traceback pid=12345 /private/tmp"
    )

    attempt = materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
        completion,
        exception,
    )

    runner_request = completion.invocation.runner_request
    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "local Python stdout protocol failed after zero returncode; recorded as "
        "setup_failed"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_stdout_protocol_failure"),
        _field("normalized_outcome", "setup_failed"),
        _field("returncode", "0"),
        _field("exception_type", "builtins.ValueError"),
    )
    result_batch = _assemble_result_batch(
        runtime_probe_execution.RuntimeProbeExecutionInputBatch(
            plan_id=runner_request.plan_id,
            request_ids=(runner_request.request_id,),
            inputs=(runner_request.execution_input,),
        ),
        (attempt,),
    )
    result = result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert result.is_admissible_runtime_backed_proof is False

    failure_text = "\n".join(
        (
            attempt.failure_summary,
            *(field.value for field in attempt.failure_detail_fields),
        )
    )
    assert "observed_module" not in failure_text
    assert "raw stdout" not in failure_text
    assert "raw stderr" not in failure_text
    assert "traceback" not in failure_text
    assert "pid=12345" not in failure_text
    assert "/private/tmp" not in failure_text
    assert completion.stdout_text not in failure_text
    assert completion.stderr_text not in failure_text
    assert str(exception) not in failure_text


def test_stdout_protocol_failure_attempt_rejects_nonzero_completion() -> None:
    """The stdout protocol failure boundary is only for zero-exit completions."""
    completion = _local_python_process_completion(returncode=17)

    with pytest.raises(ValueError, match="zero returncode"):
        materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
            completion,
            ValueError("malformed stdout"),
        )


def test_stdout_protocol_failure_attempt_supports_configured_outcome() -> None:
    """Malformed stdout can be mapped to a configured non-proof outcome."""
    missing_environment = (
        runtime_probe_results.RuntimeProbeResultOutcome.MISSING_ENVIRONMENT
    )
    completion = _local_python_process_completion(returncode=0)

    attempt = materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
        completion,
        ValueError("malformed stdout"),
        outcome=missing_environment,
    )

    assert attempt.outcome is missing_environment
    assert attempt.failure_summary == (
        "local Python stdout protocol failed after zero returncode; recorded as "
        "missing_environment"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "local_python_stdout_protocol_failure"),
        _field("normalized_outcome", "missing_environment"),
        _field("returncode", "0"),
        _field("exception_type", "builtins.ValueError"),
    )


def test_stdout_protocol_failure_attempt_rejects_observed_outcome() -> None:
    """Malformed stdout failure materialization cannot produce proof outcomes."""
    completion = _local_python_process_completion(returncode=0)

    with pytest.raises(ValueError, match="non-proof outcome"):
        materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
            completion,
            ValueError("malformed stdout"),
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
        )


def test_stdout_protocol_failure_attempt_revalidates_completion() -> None:
    """Malformed stdout failure materialization re-checks completion identity."""
    completion = _local_python_process_completion(returncode=0)
    object.__setattr__(completion, "argv", ("/workspace/context-ir/.venv/bin/python",))

    with pytest.raises(ValueError, match="argv must match invocation"):
        materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
            completion,
            ValueError("malformed stdout"),
        )


def test_stdout_protocol_failure_attempt_revalidates_invocation() -> None:
    """Malformed stdout failure materialization re-checks invocation identity."""
    invocation = _local_python_subprocess_invocation()
    completion = _local_python_process_completion(invocation, returncode=0)
    object.__setattr__(invocation, "working_directory", "/tmp/context-ir-mutated")

    with pytest.raises(ValueError, match="working_directory must match environment"):
        materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
            completion,
            ValueError("malformed stdout"),
        )


def test_stdout_protocol_failure_attempt_revalidates_runner_request() -> None:
    """Malformed stdout failure materialization re-checks runner request identity."""
    runner_request = _local_python_runner_request()
    invocation = _local_python_subprocess_invocation(runner_request)
    completion = _local_python_process_completion(invocation, returncode=0)
    object.__setattr__(runner_request, "request_id", "runtime-probe-request:mutated")

    with pytest.raises(ValueError, match="request_id must match execution input"):
        materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
            completion,
            ValueError("malformed stdout"),
        )


def test_stdout_protocol_failure_attempt_rejects_non_exception_failure() -> None:
    """Malformed stdout failure materialization requires a typed Exception."""
    completion = _local_python_process_completion(returncode=0)

    with pytest.raises(ValueError, match="must be an Exception"):
        materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
            completion,
            "malformed stdout",  # type: ignore[arg-type]
        )


def test_materialize_local_python_stdout_protocol_result_parses_success() -> None:
    """Zero-returncode stdout JSON materializes an ordered typed success protocol."""
    completion = _local_python_process_completion(
        returncode=0,
        stdout_text=_local_python_stdout_protocol_text(
            normalized_payload=[
                {"key": "first_observed_module", "value": "plugins.weather"},
                {"key": "second_observed_module", "value": "plugins.forecast"},
            ],
            durable_artifact_reference="runtime-artifact:local-python:abc123",
        ),
        stderr_text="raw stderr warning is ignored for success semantics\n",
    )

    result = materialize_runtime_probe_local_python_stdout_protocol_result(completion)
    second_result = materialize_runtime_probe_local_python_stdout_protocol_result(
        completion
    )

    assert result == second_result
    assert isinstance(
        result,
        runtime_probe_execution.RuntimeProbeLocalPythonStdoutProtocolResult,
    )
    assert result.completion is completion
    assert result.stdout_protocol_revision == (
        "runtime_probe_local_python_stdout_protocol:v1"
    )
    assert result.normalized_payload == (
        _field("first_observed_module", "plugins.weather"),
        _field("second_observed_module", "plugins.forecast"),
    )
    assert result.durable_artifact_reference == "runtime-artifact:local-python:abc123"
    assert result.observed_replay_inputs == ()

    with pytest.raises(FrozenInstanceError):
        result.durable_artifact_reference = "runtime-artifact:mutated"


def test_materialize_exec_stdout_protocol_result_parses_observed_replay_inputs() -> (
    None
):
    """Exact exec stdout can carry runtime-observed source replay proof."""
    invocation = _local_python_subprocess_invocation(
        _local_python_runner_request(request=_exec_request())
    )
    completion = _local_python_process_completion(
        invocation,
        returncode=0,
        stdout_text=_local_python_stdout_protocol_text(
            normalized_payload=[
                {"key": "execution_outcome", "value": "completed"},
                {"key": "statement_kind", "value": "pass"},
            ],
            durable_artifact_reference=(
                f"artifact://runtime-probe/exec-source/"
                f"{invocation.runner_request.request_id}.json"
            ),
            observed_replay_inputs=[
                {"key": "source_shape", "value": "literal_statement"},
                {"key": "source_sha256", "value": _EXEC_PASS_SOURCE_SHA256},
            ],
        ),
    )

    result = materialize_runtime_probe_local_python_stdout_protocol_result(completion)
    attempt = materialize_runtime_probe_local_python_stdout_protocol_attempt(result)

    assert result.observed_replay_inputs == (
        _field("source_shape", "literal_statement"),
        _field("source_sha256", _EXEC_PASS_SOURCE_SHA256),
    )
    assert attempt.observed_replay_inputs == result.observed_replay_inputs


def test_materialize_eval_stdout_protocol_result_parses_observed_replay_inputs() -> (
    None
):
    """Exact eval stdout can carry runtime-observed source replay proof."""
    invocation = _local_python_subprocess_invocation(
        _local_python_runner_request(request=_eval_request())
    )
    completion = _local_python_process_completion(
        invocation,
        returncode=0,
        stdout_text=_local_python_stdout_protocol_text(
            normalized_payload=[
                {"key": "evaluation_outcome", "value": "returned_value"},
                {"key": "result_type", "value": "builtins.str"},
            ],
            durable_artifact_reference=(
                f"artifact://runtime-probe/eval-source/"
                f"{invocation.runner_request.request_id}.json"
            ),
            observed_replay_inputs=[
                {"key": "source_shape", "value": "literal_expression"},
                {"key": "source_sha256", "value": _EVAL_SOURCE_SHA256},
            ],
        ),
    )

    result = materialize_runtime_probe_local_python_stdout_protocol_result(completion)
    attempt = materialize_runtime_probe_local_python_stdout_protocol_attempt(result)

    assert result.observed_replay_inputs == (
        _field("source_shape", "literal_expression"),
        _field("source_sha256", _EVAL_SOURCE_SHA256),
    )
    assert attempt.observed_replay_inputs == result.observed_replay_inputs


def test_local_python_stdout_protocol_result_allows_durable_only_success() -> None:
    """A durable artifact reference is a valid proof channel without payload."""
    completion = _local_python_process_completion(
        returncode=0,
        stdout_text=_local_python_stdout_protocol_text(
            normalized_payload=[],
            durable_artifact_reference="runtime-artifact:local-python:durable-only",
        ),
    )

    result = materialize_runtime_probe_local_python_stdout_protocol_result(completion)

    assert result.normalized_payload == ()
    assert result.durable_artifact_reference == (
        "runtime-artifact:local-python:durable-only"
    )


@pytest.mark.parametrize(
    "durable_artifact_reference",
    (
        " runtime-artifact:local-python:abc123",
        "runtime-artifact:local-python:abc123 ",
        "runtime-artifact:local-python:\nabc123",
    ),
)
def test_local_python_stdout_protocol_result_rejects_malformed_durable_reference(
    durable_artifact_reference: str,
) -> None:
    """Direct result construction enforces stdout durable-reference rules."""
    completion = _local_python_process_completion(
        returncode=0,
        stdout_text=_local_python_stdout_protocol_text(
            normalized_payload=[],
            durable_artifact_reference="runtime-artifact:local-python:abc123",
        ),
    )

    with pytest.raises(ValueError, match="durable_artifact_reference is malformed"):
        runtime_probe_execution.RuntimeProbeLocalPythonStdoutProtocolResult(
            completion=completion,
            stdout_protocol_revision=("runtime_probe_local_python_stdout_protocol:v1"),
            normalized_payload=(),
            durable_artifact_reference=durable_artifact_reference,
        )


def test_local_python_stdout_protocol_rejects_observed_replay_inputs_for_non_exec() -> (
    None
):
    """Observed replay-input proof is scoped to exact exec observations."""
    completion = _local_python_process_completion(
        returncode=0,
        stdout_text=_local_python_stdout_protocol_text(
            observed_replay_inputs=[
                {"key": "source_shape", "value": "literal_statement"},
                {"key": "source_sha256", "value": _EXEC_PASS_SOURCE_SHA256},
            ],
        ),
    )

    with pytest.raises(ValueError, match="only for exact exec/eval"):
        materialize_runtime_probe_local_python_stdout_protocol_result(completion)


def test_local_python_stdout_protocol_rejects_metaclass_observed_replay_inputs() -> (
    None
):
    """Metaclass observations must not widen the exec/eval replay-input channel."""
    invocation = _local_python_subprocess_invocation(
        _local_python_runner_request(request=_metaclass_keyword_request())
    )
    completion = _local_python_process_completion(
        invocation,
        returncode=0,
        stdout_text=_local_python_stdout_protocol_text(
            normalized_payload=[
                {"key": "class_creation_outcome", "value": "created_class"},
            ],
            durable_artifact_reference="artifact://runtime-probe/metaclass/main.json",
            observed_replay_inputs=[
                {"key": "source_shape", "value": "literal_statement"},
                {"key": "source_sha256", "value": _EXEC_PASS_SOURCE_SHA256},
            ],
        ),
    )

    with pytest.raises(ValueError, match="only for exact exec/eval"):
        materialize_runtime_probe_local_python_stdout_protocol_result(completion)


def test_local_python_stdout_protocol_rejects_exec_observed_replay_input_drift() -> (
    None
):
    """Exec observed replay inputs are exact singleton source proof fields."""
    invocation = _local_python_subprocess_invocation(
        _local_python_runner_request(request=_exec_request())
    )
    completion = _local_python_process_completion(
        invocation,
        returncode=0,
        stdout_text=_local_python_stdout_protocol_text(
            normalized_payload=[
                {"key": "execution_outcome", "value": "completed"},
            ],
            observed_replay_inputs=[
                {"key": "source_shape", "value": "literal_statement"},
                {"key": "source_shape", "value": "literal_statement"},
            ],
        ),
    )

    with pytest.raises(ValueError, match="duplicate"):
        materialize_runtime_probe_local_python_stdout_protocol_result(completion)


def test_local_python_stdout_protocol_rejects_eval_observed_replay_input_drift() -> (
    None
):
    """Eval observed replay inputs must be exact singleton source proof fields."""
    invocation = _local_python_subprocess_invocation(
        _local_python_runner_request(request=_eval_request())
    )
    completion = _local_python_process_completion(
        invocation,
        returncode=0,
        stdout_text=_local_python_stdout_protocol_text(
            normalized_payload=[
                {"key": "evaluation_outcome", "value": "returned_value"},
            ],
            observed_replay_inputs=[
                {"key": "source_shape", "value": "literal_statement"},
                {"key": "source_sha256", "value": _EVAL_SOURCE_SHA256},
            ],
        ),
    )

    with pytest.raises(ValueError, match="literal expression"):
        materialize_runtime_probe_local_python_stdout_protocol_result(completion)


@pytest.mark.parametrize(
    ("stdout_text", "error_match"),
    (
        ("not json raw stdout secret", "valid JSON object"),
        ('["not", "object"]', "JSON object"),
        (
            json.dumps(
                {
                    "normalized_payload": [
                        {"key": "observed_module", "value": "plugins.weather"}
                    ],
                }
            ),
            "revision",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": " ",
                    "normalized_payload": [
                        {"key": "observed_module", "value": "plugins.weather"}
                    ],
                }
            ),
            "revision",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": (
                        "runtime_probe_local_python_stdout_protocol:v2"
                    ),
                    "normalized_payload": [
                        {"key": "observed_module", "value": "plugins.weather"}
                    ],
                }
            ),
            "revision is unsupported",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": (
                        "runtime_probe_local_python_stdout_protocol:v1"
                    ),
                    "normalized_payload": [],
                    "raw_stdout": "secret",
                }
            ),
            "unknown keys",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": (
                        "runtime_probe_local_python_stdout_protocol:v1"
                    ),
                    "normalized_payload": {"key": "observed_module"},
                }
            ),
            "normalized_payload must be a list",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": (
                        "runtime_probe_local_python_stdout_protocol:v1"
                    ),
                    "normalized_payload": [["observed_module", "plugins.weather"]],
                }
            ),
            "normalized_payload entries must be objects",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": (
                        "runtime_probe_local_python_stdout_protocol:v1"
                    ),
                    "normalized_payload": [
                        {
                            "key": "observed_module",
                            "value": "plugins.weather",
                            "extra": "nope",
                        }
                    ],
                }
            ),
            "key and value",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": (
                        "runtime_probe_local_python_stdout_protocol:v1"
                    ),
                    "normalized_payload": [{"key": "", "value": "plugins.weather"}],
                }
            ),
            "blank fields",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": (
                        "runtime_probe_local_python_stdout_protocol:v1"
                    ),
                    "normalized_payload": [],
                    "durable_artifact_reference": "",
                }
            ),
            "durable_artifact_reference",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": (
                        "runtime_probe_local_python_stdout_protocol:v1"
                    ),
                    "normalized_payload": [],
                    "durable_artifact_reference": " runtime-artifact:abc",
                }
            ),
            "durable_artifact_reference is malformed",
        ),
        (
            json.dumps(
                {
                    "runtime_probe_stdout_protocol_revision": (
                        "runtime_probe_local_python_stdout_protocol:v1"
                    ),
                    "normalized_payload": [],
                    "durable_artifact_reference": None,
                }
            ),
            "normalized_payload or durable_artifact_reference",
        ),
    ),
)
def test_local_python_stdout_protocol_rejects_malformed_stdout_without_leakage(
    stdout_text: str,
    error_match: str,
) -> None:
    """Malformed success stdout is rejected without reflecting raw streams."""
    completion = _local_python_process_completion(
        returncode=0,
        stdout_text=stdout_text,
        stderr_text="raw stderr pid=12345 /private/tmp/runtime-probe\n",
    )

    with pytest.raises(ValueError, match=error_match) as exc_info:
        materialize_runtime_probe_local_python_stdout_protocol_result(completion)

    error_text = str(exc_info.value)
    assert "secret" not in error_text
    assert "pid=12345" not in error_text
    assert "/private/tmp" not in error_text
    assert stdout_text not in error_text
    assert completion.stderr_text not in error_text


def test_local_python_stdout_protocol_rejects_nonzero_completion() -> None:
    """The success protocol is scoped only to zero-returncode completions."""
    completion = _local_python_process_completion(
        returncode=2,
        stdout_text=_local_python_stdout_protocol_text(),
    )

    with pytest.raises(ValueError, match="zero returncode"):
        materialize_runtime_probe_local_python_stdout_protocol_result(completion)


def test_local_python_stdout_protocol_result_revalidates_carried_contracts() -> None:
    """Success protocol materialization revalidates completion and request identity."""
    completion = _local_python_process_completion(
        stdout_text=_local_python_stdout_protocol_text()
    )
    object.__setattr__(completion, "invocation_identity", "wrong")

    with pytest.raises(ValueError, match="invocation_identity"):
        materialize_runtime_probe_local_python_stdout_protocol_result(completion)

    invocation_drifted_completion = _local_python_process_completion(
        stdout_text=_local_python_stdout_protocol_text()
    )
    object.__setattr__(
        invocation_drifted_completion.invocation,
        "working_directory",
        "/workspace/other",
    )

    with pytest.raises(ValueError, match="working_directory"):
        materialize_runtime_probe_local_python_stdout_protocol_result(
            invocation_drifted_completion
        )

    request_drifted_completion = _local_python_process_completion(
        stdout_text=_local_python_stdout_protocol_text()
    )
    object.__setattr__(
        request_drifted_completion.invocation.runner_request,
        "request_id",
        "runtime_probe:wrong",
    )

    with pytest.raises(ValueError, match="request_id must match execution input"):
        materialize_runtime_probe_local_python_stdout_protocol_result(
            request_drifted_completion
        )


def test_local_python_stdout_protocol_result_dataclass_rejects_contract_drift() -> None:
    """The frozen result contract rechecks completion, proof, and revision fields."""
    completion = _local_python_process_completion(
        stdout_text=_local_python_stdout_protocol_text()
    )
    result = materialize_runtime_probe_local_python_stdout_protocol_result(completion)

    with pytest.raises(ValueError, match="revision is unsupported"):
        runtime_probe_execution.RuntimeProbeLocalPythonStdoutProtocolResult(
            completion=result.completion,
            stdout_protocol_revision="runtime_probe_local_python_stdout_protocol:v2",
            normalized_payload=result.normalized_payload,
            durable_artifact_reference=result.durable_artifact_reference,
        )
    blank_payload_field = _field("observed_module", "plugins.weather")
    object.__setattr__(blank_payload_field, "value", "")
    with pytest.raises(ValueError, match="normalized_payload"):
        runtime_probe_execution.RuntimeProbeLocalPythonStdoutProtocolResult(
            completion=result.completion,
            stdout_protocol_revision=result.stdout_protocol_revision,
            normalized_payload=(blank_payload_field,),
            durable_artifact_reference=None,
        )
    with pytest.raises(ValueError, match="normalized_payload or durable"):
        runtime_probe_execution.RuntimeProbeLocalPythonStdoutProtocolResult(
            completion=result.completion,
            stdout_protocol_revision=result.stdout_protocol_revision,
            normalized_payload=(),
            durable_artifact_reference=None,
        )


def test_materialize_local_python_stdout_protocol_attempt_observes_success() -> None:
    """A typed stdout success protocol materializes an observed attempt."""
    invocation = _local_python_subprocess_invocation()
    completion = _local_python_process_completion(
        invocation,
        stdout_text=_local_python_stdout_protocol_text(
            normalized_payload=[
                {"key": "first_observed_module", "value": "plugins.weather"},
                {"key": "second_observed_module", "value": "plugins.forecast"},
            ],
            durable_artifact_reference="runtime-artifact:local-python:abc123",
        ),
    )
    protocol_result = materialize_runtime_probe_local_python_stdout_protocol_result(
        completion
    )

    attempt = materialize_runtime_probe_local_python_stdout_protocol_attempt(
        protocol_result
    )

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.plan_id == invocation.runner_request.plan_id
    assert attempt.request_id == invocation.runner_request.request_id
    assert attempt.request is invocation.runner_request.request
    assert attempt.execution_input is invocation.runner_request.execution_input
    assert attempt.normalized_payload == (
        _field("first_observed_module", "plugins.weather"),
        _field("second_observed_module", "plugins.forecast"),
    )
    assert attempt.durable_artifact_reference == "runtime-artifact:local-python:abc123"
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_materialize_local_python_stdout_protocol_attempt_preserves_durable_only() -> (
    None
):
    """Durable-only stdout proof remains durable-only on the observed attempt."""
    protocol_result = materialize_runtime_probe_local_python_stdout_protocol_result(
        _local_python_process_completion(
            stdout_text=_local_python_stdout_protocol_text(
                normalized_payload=[],
                durable_artifact_reference=(
                    "runtime-artifact:local-python:durable-only"
                ),
            )
        )
    )

    attempt = materialize_runtime_probe_local_python_stdout_protocol_attempt(
        protocol_result
    )

    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference == (
        "runtime-artifact:local-python:durable-only"
    )
    assert attempt.failure_summary is None
    assert attempt.failure_detail_fields == ()


def test_local_python_stdout_protocol_attempt_revalidates_carried_contracts() -> None:
    """Attempt materialization rejects drift in result, completion, and request data."""
    protocol_result = materialize_runtime_probe_local_python_stdout_protocol_result(
        _local_python_process_completion(
            stdout_text=_local_python_stdout_protocol_text()
        )
    )
    object.__setattr__(
        protocol_result,
        "stdout_protocol_revision",
        "runtime_probe_local_python_stdout_protocol:v2",
    )

    with pytest.raises(ValueError, match="revision is unsupported"):
        materialize_runtime_probe_local_python_stdout_protocol_attempt(protocol_result)

    completion_drifted_result = (
        materialize_runtime_probe_local_python_stdout_protocol_result(
            _local_python_process_completion(
                stdout_text=_local_python_stdout_protocol_text()
            )
        )
    )
    object.__setattr__(
        completion_drifted_result.completion,
        "invocation_identity",
        "wrong",
    )

    with pytest.raises(ValueError, match="invocation_identity"):
        materialize_runtime_probe_local_python_stdout_protocol_attempt(
            completion_drifted_result
        )

    invocation_drifted_result = (
        materialize_runtime_probe_local_python_stdout_protocol_result(
            _local_python_process_completion(
                stdout_text=_local_python_stdout_protocol_text()
            )
        )
    )
    object.__setattr__(
        invocation_drifted_result.completion.invocation,
        "timeout_seconds",
        999,
    )

    with pytest.raises(ValueError, match="timeout_seconds"):
        materialize_runtime_probe_local_python_stdout_protocol_attempt(
            invocation_drifted_result
        )

    request_drifted_result = (
        materialize_runtime_probe_local_python_stdout_protocol_result(
            _local_python_process_completion(
                stdout_text=_local_python_stdout_protocol_text()
            )
        )
    )
    object.__setattr__(
        request_drifted_result.completion.invocation.runner_request,
        "request_id",
        "runtime_probe:wrong",
    )

    with pytest.raises(ValueError, match="request_id must match execution input"):
        materialize_runtime_probe_local_python_stdout_protocol_attempt(
            request_drifted_result
        )


def test_materialize_local_python_failure_attempts_revalidate_carried_contracts() -> (
    None
):
    """Local-Python failure materializers revalidate carried request contracts."""
    invocation = _local_python_subprocess_invocation()
    object.__setattr__(
        invocation.runner_request,
        "plan_id",
        "runtime_probe_request_plan:wrong",
    )

    with pytest.raises(ValueError, match="plan_id"):
        materialize_runtime_probe_local_python_subprocess_exception_attempt(
            invocation,
            RuntimeError("local failure"),
        )

    completion = _local_python_process_completion(returncode=5)
    object.__setattr__(completion, "returncode", True)

    with pytest.raises(ValueError, match="returncode"):
        materialize_runtime_probe_local_python_process_completion_attempt(completion)


@pytest.mark.parametrize(
    ("primitive_overrides", "error_match"),
    (
        ({"returncode": True}, "returncode"),
        ({"returncode": "0"}, "returncode"),
        ({"stdout_text": b""}, "stdout_text"),
        ({"stderr_text": None}, "stderr_text"),
        ({"completion_contract_revision": ""}, "completion_contract_revision"),
        (
            {"completion_contract_revision": " runtime-probe-completion:test.1"},
            "completion_contract_revision.*malformed",
        ),
        (
            {"completion_contract_revision": "runtime-probe-completion:test.1\nbad"},
            "completion_contract_revision.*malformed",
        ),
    ),
)
def test_materialize_local_python_process_completion_rejects_bad_primitives(
    primitive_overrides: dict[str, object],
    error_match: str,
) -> None:
    """Raw completion materialization requires typed primitive fields."""
    invocation = _local_python_subprocess_invocation()
    primitives: dict[str, object] = {
        "returncode": 0,
        "stdout_text": "",
        "stderr_text": "",
        "completion_contract_revision": (
            "runtime-probe-local-python-process-completion:test.1"
        ),
    }
    primitives.update(primitive_overrides)

    with pytest.raises(ValueError, match=error_match):
        materialize_runtime_probe_local_python_process_completion(
            invocation,
            returncode=primitives["returncode"],
            stdout_text=primitives["stdout_text"],
            stderr_text=primitives["stderr_text"],
            completion_contract_revision=primitives["completion_contract_revision"],
        )


def test_local_python_process_completion_rejects_contract_drift() -> None:
    """The frozen completion type rechecks invocation and copied metadata."""
    completion = _local_python_process_completion()

    with pytest.raises(ValueError, match="invocation_identity"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity="runtime_probe_local_python_subprocess_invocation:wrong",
            argv=completion.argv,
            working_directory=completion.working_directory,
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="argv"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=(*completion.argv, "--mutated"),
            working_directory=completion.working_directory,
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="working_directory"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=completion.argv,
            working_directory="/workspace/other",
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="python_path_entries"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=completion.argv,
            working_directory=completion.working_directory,
            python_path_entries=("/workspace/other/src",),
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="timeout_seconds"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=completion.argv,
            working_directory=completion.working_directory,
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds + 1,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=completion.request_replay_payload_fields,
        )

    with pytest.raises(ValueError, match="replay payload fields"):
        runtime_probe_execution.RuntimeProbeLocalPythonProcessCompletion(
            invocation=completion.invocation,
            invocation_identity=completion.invocation_identity,
            argv=completion.argv,
            working_directory=completion.working_directory,
            python_path_entries=completion.python_path_entries,
            timeout_seconds=completion.timeout_seconds,
            returncode=completion.returncode,
            stdout_text=completion.stdout_text,
            stderr_text=completion.stderr_text,
            completion_contract_revision=completion.completion_contract_revision,
            request_replay_payload_fields=(
                _field("plan_id", completion.invocation.runner_request.plan_id),
            ),
        )


@pytest.mark.parametrize(
    ("runner_environment", "error_match"),
    (
        (
            tuple(
                field
                for field in _local_python_runner_environment()
                if field.key != "repository_root"
            ),
            "repository_root",
        ),
        (
            tuple(
                field
                for field in _local_python_runner_environment()
                if field.key != "working_directory"
            ),
            "working_directory",
        ),
        (
            _local_python_runner_environment()
            + (_field("repository_root", "/workspace/other"),),
            "duplicate singleton",
        ),
        (
            _local_python_runner_environment() + (_field("platform", "darwin-arm64"),),
            "duplicate singleton",
        ),
    ),
)
def test_derive_local_python_environment_context_rejects_singleton_metadata_drift(
    runner_environment: tuple[runtime_probe_results.RuntimeProbeReplayField, ...],
    error_match: str,
) -> None:
    """Local-Python context derivation requires unique singleton metadata."""
    runner_request = _local_python_runner_request(
        runner_environment=runner_environment,
    )

    with pytest.raises(ValueError, match=error_match):
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )


@pytest.mark.parametrize(
    ("field_key", "bad_value", "error_match"),
    (
        ("repository_root", " ", "runner_environment"),
        ("repository_root", "workspace/context-ir", "absolute"),
        ("working_directory", "workspace/context-ir", "absolute"),
        ("python_path_entry", "src", "absolute"),
        ("python_path_entry", "/workspace/context-ir/src\nbad", "malformed"),
        ("working_directory", " /workspace/context-ir", "malformed"),
        ("repository_root", "/workspace/context-ir\x00bad", "malformed"),
    ),
)
def test_derive_local_python_environment_context_rejects_bad_path_metadata(
    field_key: str,
    bad_value: str,
    error_match: str,
) -> None:
    """Local-Python path metadata must be non-blank, absolute, and parseable."""
    runner_request = _local_python_runner_request()
    field = next(
        field for field in runner_request.runner_environment if field.key == field_key
    )
    object.__setattr__(field, "value", bad_value)

    with pytest.raises(ValueError, match=error_match):
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            runner_request
        )


def test_prepare_runtime_probe_runner_requests_for_diagnostic_preserves_boundary() -> (
    None
):
    """Diagnostic preparation preserves the planned input and runner identities."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    plan = _plan(first_request, second_request, third_request)
    diagnostic = _diagnostic_for_plan(plan)
    snapshot_basis = _snapshot_basis()
    runtime_assumptions = _runtime_assumptions()
    runner_environment = _runner_environment()
    runner_assumptions = _runner_assumptions()

    preparation = (
        runtime_probe_execution.prepare_runtime_probe_runner_requests_for_diagnostic(
            diagnostic,
            repository_snapshot_basis=snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=runtime_assumptions,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )
    )

    input_batch = preparation.execution_input_batch
    runner_batch = preparation.runner_request_batch
    assert preparation.diagnostic is diagnostic
    assert preparation.request_plan is plan
    assert input_batch.plan_id == plan.plan_id
    assert runner_batch.plan_id == plan.plan_id
    assert input_batch.request_ids == plan.request_ids
    assert runner_batch.request_ids == plan.request_ids
    assert [input_item.request_id for input_item in input_batch.inputs] == list(
        plan.request_ids
    )
    assert [
        runner_request.request_id for runner_request in runner_batch.runner_requests
    ] == list(plan.request_ids)
    assert runner_batch.runner_contract_revision == "runtime-probe-runner:test.1"
    assert runner_batch.timeout_seconds == 30
    assert runner_batch.runner_environment is runner_environment
    assert runner_batch.runner_assumptions is runner_assumptions

    for request, input_item, runner_request in zip(
        plan.requests,
        input_batch.inputs,
        runner_batch.runner_requests,
        strict=True,
    ):
        assert input_item.request is request
        assert input_item.plan_id == plan.plan_id
        assert input_item.request_id == request.request_id
        assert input_item.replay_artifact.repository_snapshot_basis is snapshot_basis
        assert input_item.replay_artifact.runtime_assumptions is runtime_assumptions
        assert runner_request.request is request
        assert runner_request.execution_input is input_item
        assert runner_request.replay_artifact is input_item.replay_artifact
        assert runner_request.runner_environment is runner_environment
        assert runner_request.runner_assumptions is runner_assumptions


def test_prepare_runtime_probe_runner_requests_for_diagnostic_rejects_plan_drift() -> (
    None
):
    """Diagnostic preparation rejects missing, detached, or drifted request plans."""
    request = _request()
    plan = _plan(request)
    diagnostic = _diagnostic_for_plan(plan)
    missing_plan = replace(diagnostic, planned_runtime_probe_request_plan=None)
    drifted_diagnostic = _diagnostic_for_plan(plan)
    object.__setattr__(drifted_diagnostic, "planned_runtime_probe_requests", ())
    identity_drifted_diagnostic = _diagnostic_for_plan(plan)
    object.__setattr__(
        identity_drifted_diagnostic,
        "planned_runtime_probe_requests",
        (_request(),),
    )
    drifted_plan = _plan(request)
    object.__setattr__(drifted_plan, "request_ids", ("runtime_probe:wrong",))
    drifted_plan_diagnostic = _diagnostic_for_plan(drifted_plan)
    preparation = _prepare_runner_requests(diagnostic)
    equivalent_plan = _plan(request)

    with pytest.raises(ValueError, match="planned_runtime_probe_request_plan"):
        _prepare_runner_requests(missing_plan)
    with pytest.raises(ValueError, match="requests must match"):
        _prepare_runner_requests(drifted_diagnostic)
    with pytest.raises(ValueError, match="request identities"):
        _prepare_runner_requests(identity_drifted_diagnostic)
    with pytest.raises(ValueError, match="request_ids must match requests"):
        _prepare_runner_requests(drifted_plan_diagnostic)
    with pytest.raises(ValueError, match="request_plan must be diagnostic"):
        runtime_probe_execution.RuntimeProbeDiagnosticRunnerRequestPreparation(
            diagnostic=diagnostic,
            request_plan=equivalent_plan,
            execution_input_batch=preparation.execution_input_batch,
            runner_request_batch=preparation.runner_request_batch,
        )


def test_prepare_runner_requests_for_diagnostic_rejects_bad_metadata() -> None:
    """Diagnostic preparation propagates input and runner metadata validation."""
    diagnostic = _diagnostic_for_plan(_plan(_request()))

    with pytest.raises(ValueError, match="probe_contract_revision"):
        _prepare_runner_requests(diagnostic, probe_contract_revision=" ")
    with pytest.raises(ValueError, match="runtime_assumptions"):
        _prepare_runner_requests(diagnostic, runtime_assumptions=())
    with pytest.raises(ValueError, match="runner_contract_revision"):
        _prepare_runner_requests(diagnostic, runner_contract_revision=" ")
    with pytest.raises(ValueError, match="timeout_seconds"):
        _prepare_runner_requests(diagnostic, timeout_seconds=0)
    with pytest.raises(ValueError, match="runner_environment"):
        _prepare_runner_requests(diagnostic, runner_environment=())
    with pytest.raises(ValueError, match="runner_assumptions"):
        _prepare_runner_requests(diagnostic, runner_assumptions=())


def test_materialize_runtime_probe_runner_requests_supports_empty_input_batch() -> None:
    """Empty execution-input batches materialize to empty runner-request batches."""
    input_batch = _materialized_batch(
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )

    runner_batch = _runner_request_batch(input_batch)

    assert runner_batch.plan_id == input_batch.plan_id
    assert runner_batch.request_ids == ()
    assert runner_batch.runner_requests == ()


def test_materialize_runtime_probe_runner_requests_rejects_bad_runner_metadata() -> (
    None
):
    """Runner handoff metadata must be explicit, non-blank, and bounded."""
    input_batch = _materialized_batch(_plan(_request()))
    blank_environment = _field("platform", "linux-x86_64")
    object.__setattr__(blank_environment, "value", " ")
    blank_assumption = _field("network", "disabled")
    object.__setattr__(blank_assumption, "key", " ")

    with pytest.raises(ValueError, match="runner_contract_revision"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision=" ",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="timeout_seconds"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=0,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="runner_environment"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="runner_assumptions"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=(),
        )
    with pytest.raises(ValueError, match="runner_environment"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=(blank_environment,),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="runner_assumptions"):
        runtime_probe_execution.materialize_runtime_probe_runner_request_batch(
            input_batch,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=(blank_assumption,),
        )


def test_materialize_runtime_probe_runner_requests_rejects_input_batch_drift() -> None:
    """Runner materialization revalidates execution-input batch completeness."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    drifted_batch = _materialized_batch(_plan(first_request, second_request))
    object.__setattr__(drifted_batch, "request_ids", ("runtime_probe:wrong",))
    duplicate_batch = _materialized_batch(_plan(first_request, second_request))
    object.__setattr__(
        duplicate_batch,
        "request_ids",
        (duplicate_batch.inputs[0].request_id, duplicate_batch.inputs[0].request_id),
    )
    object.__setattr__(
        duplicate_batch,
        "inputs",
        (duplicate_batch.inputs[0], duplicate_batch.inputs[0]),
    )

    with pytest.raises(ValueError, match="request_ids must match inputs"):
        _runner_request_batch(drifted_batch)
    with pytest.raises(ValueError, match="duplicate runtime probe execution"):
        _runner_request_batch(duplicate_batch)


def test_materialize_runtime_probe_runner_requests_rejects_blank_replay_tampering() -> (
    None
):
    """Runner handoff requests reject replay fields blanked after construction."""
    blank_replay_input_batch = _materialized_batch(_plan(_request(start_line=3)))
    blank_replay_input = blank_replay_input_batch.inputs[0]
    blank_replay_input_field = blank_replay_input.replay_artifact.replay_inputs[0]
    object.__setattr__(blank_replay_input_field, "value", " ")
    blank_assumption_batch = _materialized_batch(_plan(_request(start_line=4)))
    blank_assumption_input = blank_assumption_batch.inputs[0]
    blank_assumption_field = blank_assumption_input.replay_artifact.runtime_assumptions[
        0
    ]
    object.__setattr__(blank_assumption_field, "key", " ")

    with pytest.raises(ValueError, match="replay_inputs"):
        _runner_request_batch(blank_replay_input_batch)
    with pytest.raises(ValueError, match="runtime_assumptions"):
        _runner_request_batch(blank_assumption_batch)


def test_runtime_probe_runner_request_rejects_plan_input_and_replay_drift() -> None:
    """Runner requests must point at the exact input and replay artifact objects."""
    request = _request()
    plan = _plan(request)
    input_batch = _materialized_batch(plan)
    input_item = input_batch.inputs[0]
    equivalent_input = _materialized_batch(plan).inputs[0]

    with pytest.raises(ValueError, match="plan_id must match execution input"):
        runtime_probe_execution.RuntimeProbeRunnerRequest(
            plan_id="runtime_probe_request_plan:wrong",
            request_id=input_item.request_id,
            request=input_item.request,
            execution_input=input_item,
            replay_artifact=input_item.replay_artifact,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="request_id must match execution input"):
        runtime_probe_execution.RuntimeProbeRunnerRequest(
            plan_id=input_item.plan_id,
            request_id="runtime_probe:wrong",
            request=input_item.request,
            execution_input=input_item,
            replay_artifact=input_item.replay_artifact,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="request must be execution input request"):
        runtime_probe_execution.RuntimeProbeRunnerRequest(
            plan_id=input_item.plan_id,
            request_id=input_item.request_id,
            request=_request(start_line=8),
            execution_input=input_item,
            replay_artifact=input_item.replay_artifact,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )
    with pytest.raises(ValueError, match="replay_artifact"):
        runtime_probe_execution.RuntimeProbeRunnerRequest(
            plan_id=input_item.plan_id,
            request_id=input_item.request_id,
            request=input_item.request,
            execution_input=equivalent_input,
            replay_artifact=input_item.replay_artifact,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=_runner_environment(),
            runner_assumptions=_runner_assumptions(),
        )


def test_runtime_probe_runner_request_batch_rejects_order_and_duplicate_drift() -> None:
    """Runner-request batches reject plan, order, and duplicate identity drift."""
    input_batch = _materialized_batch(_plan(_request()))
    runner_request = _runner_request_batch(input_batch).runner_requests[0]

    with pytest.raises(ValueError, match="plan_id must match requests"):
        runtime_probe_execution.RuntimeProbeRunnerRequestBatch(
            plan_id="runtime_probe_request_plan:wrong",
            request_ids=(runner_request.request_id,),
            runner_requests=(runner_request,),
            runner_contract_revision=runner_request.runner_contract_revision,
            timeout_seconds=runner_request.timeout_seconds,
            runner_environment=runner_request.runner_environment,
            runner_assumptions=runner_request.runner_assumptions,
        )
    with pytest.raises(ValueError, match="request_ids must match requests"):
        runtime_probe_execution.RuntimeProbeRunnerRequestBatch(
            plan_id=runner_request.plan_id,
            request_ids=("runtime_probe:wrong",),
            runner_requests=(runner_request,),
            runner_contract_revision=runner_request.runner_contract_revision,
            timeout_seconds=runner_request.timeout_seconds,
            runner_environment=runner_request.runner_environment,
            runner_assumptions=runner_request.runner_assumptions,
        )
    with pytest.raises(ValueError, match="timeout_seconds must match requests"):
        runtime_probe_execution.RuntimeProbeRunnerRequestBatch(
            plan_id=runner_request.plan_id,
            request_ids=(runner_request.request_id,),
            runner_requests=(runner_request,),
            runner_contract_revision=runner_request.runner_contract_revision,
            timeout_seconds=runner_request.timeout_seconds + 1,
            runner_environment=runner_request.runner_environment,
            runner_assumptions=runner_request.runner_assumptions,
        )
    with pytest.raises(ValueError, match="duplicate runtime probe runner request_id"):
        runtime_probe_execution.RuntimeProbeRunnerRequestBatch(
            plan_id=runner_request.plan_id,
            request_ids=(runner_request.request_id, runner_request.request_id),
            runner_requests=(runner_request, runner_request),
            runner_contract_revision=runner_request.runner_contract_revision,
            timeout_seconds=runner_request.timeout_seconds,
            runner_environment=runner_request.runner_environment,
            runner_assumptions=runner_request.runner_assumptions,
        )


def test_assemble_runner_request_results_preserves_order_and_identities() -> None:
    """Runner-request-gated attempts become results in runner-request order."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    plan = _plan(first_request, second_request, third_request)
    input_batch = _materialized_batch(plan)
    runner_batch = _runner_request_batch(input_batch)
    original_runner_requests = runner_batch.runner_requests
    first_payload = (_field("observed_module", "plugins.weather"),)
    first_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=first_payload,
    )
    second_attempt = _execution_attempt(
        runner_batch.runner_requests[1].execution_input,
        durable_artifact_reference=(
            "artifact://runtime-probe-results/dynamic-import/main-run.json"
        ),
    )
    third_attempt = _execution_attempt(
        runner_batch.runner_requests[2].execution_input,
        outcome=runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        failure_summary="probe process exited non-zero",
        failure_detail_fields=(_field("exit_code", "1"),),
    )

    result_batch = _assemble_runner_request_result_batch(
        runner_batch,
        (third_attempt, first_attempt, second_attempt),
    )

    assert result_batch.plan_id == runner_batch.plan_id
    assert tuple(result.request_id for result in result_batch.results) == (
        runner_batch.request_ids
    )
    assert runner_batch.runner_requests is original_runner_requests

    for result, runner_request in zip(
        result_batch.results,
        runner_batch.runner_requests,
        strict=True,
    ):
        assert result.plan_id == runner_request.plan_id
        assert result.request_id == runner_request.request_id
        assert result.request is runner_request.request
        assert result.replay_artifact is runner_request.replay_artifact
        assert result.replay_artifact is runner_request.execution_input.replay_artifact

    first_result = result_batch.results[0]
    assert isinstance(first_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert first_result.normalized_payload == first_payload
    assert first_result.durable_artifact_reference is None
    assert first_result.is_admissible_runtime_backed_proof is True

    second_result = result_batch.results[1]
    assert isinstance(second_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert second_result.normalized_payload == ()
    assert second_result.durable_artifact_reference == (
        "artifact://runtime-probe-results/dynamic-import/main-run.json"
    )
    assert second_result.is_admissible_runtime_backed_proof is True

    third_result = result_batch.results[2]
    assert isinstance(third_result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert (
        third_result.outcome is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    )
    assert third_result.failure_summary == "probe process exited non-zero"
    assert third_result.failure_detail_fields == (_field("exit_code", "1"),)
    assert third_result.is_admissible_runtime_backed_proof is False


def test_assemble_exec_observed_result_merges_replay_proof_without_mutating_input() -> (
    None
):
    """Exec observed replay-input proof is appended only in result assembly."""
    request = _exec_request()
    plan = _plan(request)
    input_batch = _materialized_batch(plan)
    input_item = input_batch.inputs[0]
    original_replay_artifact = input_item.replay_artifact
    original_replay_inputs = original_replay_artifact.replay_inputs
    attempt = _execution_attempt(
        input_item,
        normalized_payload=(
            _field("execution_outcome", "completed"),
            _field("statement_kind", "pass"),
        ),
        durable_artifact_reference=(
            f"artifact://runtime-probe/exec-source/{request.request_id}.json"
        ),
        observed_replay_inputs=(
            _field("source_shape", "literal_statement"),
            _field("source_sha256", _EXEC_PASS_SOURCE_SHA256),
        ),
    )

    result_batch = _assemble_result_batch(input_batch, (attempt,))

    result = result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeObservedResult)
    assert result.replay_artifact is not original_replay_artifact
    assert input_item.replay_artifact is original_replay_artifact
    assert input_item.replay_artifact.replay_inputs == original_replay_inputs
    assert result.replay_artifact.replay_inputs == (
        *original_replay_inputs,
        _field("source_shape", "literal_statement"),
        _field("source_sha256", _EXEC_PASS_SOURCE_SHA256),
    )


def test_assemble_eval_observed_result_merges_replay_proof_without_mutating_input() -> (
    None
):
    """Eval observed replay-input proof is appended only in result assembly."""
    request = _eval_request()
    plan = _plan(request)
    input_batch = _materialized_batch(plan)
    input_item = input_batch.inputs[0]
    original_replay_artifact = input_item.replay_artifact
    original_replay_inputs = original_replay_artifact.replay_inputs
    attempt = _execution_attempt(
        input_item,
        normalized_payload=(
            _field("evaluation_outcome", "returned_value"),
            _field("result_type", "builtins.str"),
        ),
        durable_artifact_reference=(
            f"artifact://runtime-probe/eval-source/{request.request_id}.json"
        ),
        observed_replay_inputs=(
            _field("source_shape", "literal_expression"),
            _field("source_sha256", _EVAL_SOURCE_SHA256),
        ),
    )

    result_batch = _assemble_result_batch(input_batch, (attempt,))

    result = result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeObservedResult)
    assert result.replay_artifact is not original_replay_artifact
    assert input_item.replay_artifact is original_replay_artifact
    assert input_item.replay_artifact.replay_inputs == original_replay_inputs
    assert result.replay_artifact.replay_inputs == (
        *original_replay_inputs,
        _field("source_shape", "literal_expression"),
        _field("source_sha256", _EVAL_SOURCE_SHA256),
    )


def test_assemble_runner_request_exec_observed_result_preserves_source_proof() -> None:
    """Runner-request revalidation preserves exact-exec observed replay proof."""
    request = _exec_request()
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    input_item = runner_request.execution_input
    original_replay_artifact = input_item.replay_artifact
    original_replay_inputs = original_replay_artifact.replay_inputs
    observed_replay_inputs = (
        _field("source_shape", "literal_statement"),
        _field("source_sha256", _EXEC_PASS_SOURCE_SHA256),
    )
    attempt = _execution_attempt(
        input_item,
        normalized_payload=(
            _field("execution_outcome", "completed"),
            _field("statement_kind", "pass"),
        ),
        durable_artifact_reference=(
            f"artifact://runtime-probe/exec-source/{request.request_id}.json"
        ),
        observed_replay_inputs=observed_replay_inputs,
    )

    result_batch = _assemble_runner_request_result_batch(runner_batch, (attempt,))

    result = result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeObservedResult)
    assert result.replay_artifact is not original_replay_artifact
    assert input_item.replay_artifact is original_replay_artifact
    assert input_item.replay_artifact.replay_inputs == original_replay_inputs
    assert result.replay_artifact.replay_inputs == (
        *original_replay_inputs,
        *observed_replay_inputs,
    )


def test_assemble_runner_request_eval_observed_result_preserves_source_proof() -> None:
    """Runner-request revalidation preserves exact-eval observed replay proof."""
    request = _eval_request()
    runner_batch = _runner_request_batch(_materialized_batch(_plan(request)))
    runner_request = runner_batch.runner_requests[0]
    input_item = runner_request.execution_input
    original_replay_artifact = input_item.replay_artifact
    original_replay_inputs = original_replay_artifact.replay_inputs
    observed_replay_inputs = (
        _field("source_shape", "literal_expression"),
        _field("source_sha256", _EVAL_SOURCE_SHA256),
    )
    attempt = _execution_attempt(
        input_item,
        normalized_payload=(
            _field("evaluation_outcome", "returned_value"),
            _field("result_type", "builtins.str"),
        ),
        durable_artifact_reference=(
            f"artifact://runtime-probe/eval-source/{request.request_id}.json"
        ),
        observed_replay_inputs=observed_replay_inputs,
    )

    result_batch = _assemble_runner_request_result_batch(runner_batch, (attempt,))

    result = result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeObservedResult)
    assert result.replay_artifact is not original_replay_artifact
    assert input_item.replay_artifact is original_replay_artifact
    assert input_item.replay_artifact.replay_inputs == original_replay_inputs
    assert result.replay_artifact.replay_inputs == (
        *original_replay_inputs,
        *observed_replay_inputs,
    )


def test_assemble_runner_request_results_supports_empty_batch() -> None:
    """Empty runner-request batches assemble into empty result batches."""
    input_batch = _materialized_batch(
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )
    runner_batch = _runner_request_batch(input_batch)

    result_batch = _assemble_runner_request_result_batch(runner_batch, ())

    assert result_batch.plan_id == runner_batch.plan_id
    assert result_batch.results == ()


def test_assemble_runner_request_results_rejects_incomplete_attempt_sets() -> None:
    """Runner-request assembly requires exactly one attempt per runner request."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request))
    )
    planned_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    duplicate_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.forecast"),),
    )
    unplanned_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=8)))
    )
    unplanned_attempt = _execution_attempt(
        unplanned_runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.unplanned"),),
    )

    with pytest.raises(ValueError, match="missing runtime probe execution attempt"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (planned_attempt,),
        )
    with pytest.raises(ValueError, match="duplicate runtime probe execution attempt"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (planned_attempt, duplicate_attempt),
        )
    with pytest.raises(ValueError, match="not present in runner request batch"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (planned_attempt, unplanned_attempt),
        )


def test_assemble_runner_request_results_rejects_attempt_identity_drift() -> None:
    """Runner-request assembly rejects plan, request, and execution-input drift."""
    request = _request()
    plan = _plan(request)
    runner_batch = _runner_request_batch(_materialized_batch(plan))
    equivalent_input = _materialized_batch(plan).inputs[0]
    wrong_input_attempt = _execution_attempt(
        equivalent_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    plan_drifted_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(
        plan_drifted_attempt,
        "plan_id",
        "runtime_probe_request_plan:wrong",
    )
    request_drifted_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(request_drifted_attempt, "request", _request(start_line=8))

    with pytest.raises(ValueError, match="runner request execution input"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (wrong_input_attempt,),
        )
    with pytest.raises(ValueError, match="plan_id must match execution input"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (plan_drifted_attempt,),
        )
    with pytest.raises(ValueError, match="request must be execution input request"):
        _assemble_runner_request_result_batch(
            runner_batch,
            (request_drifted_attempt,),
        )


def test_assemble_runner_request_results_rejects_runner_request_drift() -> None:
    """Runner-request assembly revalidates the authorized runner-request batch."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    input_batch = _materialized_batch(_plan(first_request, second_request))
    runner_batch = _runner_request_batch(input_batch)
    object.__setattr__(
        runner_batch,
        "runner_requests",
        tuple(reversed(runner_batch.runner_requests)),
    )
    attempts = tuple(
        _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )
        for runner_request in runner_batch.runner_requests
    )

    with pytest.raises(ValueError, match="request_ids must match requests"):
        _assemble_runner_request_result_batch(runner_batch, attempts)


def test_assemble_runner_request_results_rejects_bad_attempt_metadata() -> None:
    """Runner-request assembly revalidates normalized attempt metadata."""
    blank_payload_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=3)))
    )
    blank_payload_field = _field("observed_module", "plugins.weather")
    blank_payload_attempt = _execution_attempt(
        blank_payload_runner_batch.runner_requests[0].execution_input,
        normalized_payload=(blank_payload_field,),
    )
    object.__setattr__(blank_payload_field, "value", " ")

    malformed_payload_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=4)))
    )
    malformed_payload_attempt = _execution_attempt(
        malformed_payload_runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(
        malformed_payload_attempt,
        "normalized_payload",
        (("observed_module", "plugins.weather"),),
    )

    blank_failure_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=5)))
    )
    blank_failure_attempt = _execution_attempt(
        blank_failure_runner_batch.runner_requests[0].execution_input,
        outcome=runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        failure_summary="probe exceeded timeout",
    )
    object.__setattr__(blank_failure_attempt, "failure_summary", " ")

    malformed_outcome_runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=6)))
    )
    malformed_outcome_attempt = _execution_attempt(
        malformed_outcome_runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(malformed_outcome_attempt, "outcome", "observed")

    with pytest.raises(ValueError, match="normalized_payload"):
        _assemble_runner_request_result_batch(
            blank_payload_runner_batch,
            (blank_payload_attempt,),
        )
    with pytest.raises(ValueError, match="normalized_payload"):
        _assemble_runner_request_result_batch(
            malformed_payload_runner_batch,
            (malformed_payload_attempt,),
        )
    with pytest.raises(ValueError, match="failure_summary"):
        _assemble_runner_request_result_batch(
            blank_failure_runner_batch,
            (blank_failure_attempt,),
        )
    with pytest.raises(ValueError, match="outcome is not supported"):
        _assemble_runner_request_result_batch(
            malformed_outcome_runner_batch,
            (malformed_outcome_attempt,),
        )


def test_collect_runtime_probe_runner_attempts_invokes_runner_once_in_order() -> None:
    """Runner-callable collection preserves request, attempt, and result identities."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request, third_request))
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []
    returned_attempts: list[runtime_probe_execution.RuntimeProbeExecutionAttempt] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        attempt = _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(
                _field("observed_request_id", runner_request.request_id),
            ),
        )
        returned_attempts.append(attempt)
        return attempt

    collection = collect_runtime_probe_execution_attempts_from_runner_requests(
        runner_batch,
        runner,
    )

    assert isinstance(
        collection,
        runtime_probe_execution.RuntimeProbeRunnerAttemptCollection,
    )
    assert collection.runner_request_batch is runner_batch
    assert tuple(calls) == runner_batch.runner_requests
    assert all(
        call is runner_request
        for call, runner_request in zip(
            calls,
            runner_batch.runner_requests,
            strict=True,
        )
    )
    assert collection.attempts == tuple(returned_attempts)
    assert all(
        attempt is returned_attempt
        for attempt, returned_attempt in zip(
            collection.attempts,
            returned_attempts,
            strict=True,
        )
    )
    assert collection.result_batch.plan_id == runner_batch.plan_id
    assert tuple(result.request_id for result in collection.result_batch.results) == (
        runner_batch.request_ids
    )

    for attempt, result, runner_request in zip(
        collection.attempts,
        collection.result_batch.results,
        runner_batch.runner_requests,
        strict=True,
    ):
        assert attempt.request_id == runner_request.request_id
        assert attempt.request is runner_request.request
        assert attempt.execution_input is runner_request.execution_input
        assert attempt.execution_input.replay_artifact is runner_request.replay_artifact
        assert result.request_id == runner_request.request_id
        assert result.request is runner_request.request
        assert result.replay_artifact is runner_request.replay_artifact


def test_collect_runtime_probe_runner_attempts_supports_empty_batch() -> None:
    """Empty runner-request batches do not invoke the runner callable."""
    input_batch = _materialized_batch(
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )
    runner_batch = _runner_request_batch(input_batch)
    was_called = False

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        nonlocal was_called
        was_called = True
        return _execution_attempt(runner_request.execution_input)

    collection = collect_runtime_probe_execution_attempts_from_runner_requests(
        runner_batch,
        runner,
    )

    assert was_called is False
    assert collection.runner_request_batch is runner_batch
    assert collection.attempts == ()
    assert collection.result_batch.plan_id == runner_batch.plan_id
    assert collection.result_batch.results == ()


def test_collect_runtime_probe_runner_attempts_revalidates_batch_before_runner() -> (
    None
):
    """Tampered runner-request batches fail before any runner invocation."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request))
    )
    object.__setattr__(
        runner_batch,
        "runner_requests",
        tuple(reversed(runner_batch.runner_requests)),
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        return _execution_attempt(runner_request.execution_input)

    with pytest.raises(ValueError, match="request_ids must match requests"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            runner,
        )

    assert calls == []


def test_collect_runtime_probe_runner_attempts_rejects_untyped_runner_output() -> None:
    """Runner-callable collection accepts only typed execution attempts."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> object:
        return {
            "plan_id": runner_request.plan_id,
            "request_id": runner_request.request_id,
        }

    with pytest.raises(ValueError, match="typed runtime probe execution attempts"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            runner,
        )


def test_collect_runtime_probe_runner_attempts_propagates_runner_exceptions() -> None:
    """Runner exceptions propagate without being synthesized into results."""
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(_request(start_line=3), _request(start_line=4)))
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        raise RuntimeError("runner failed")

    with pytest.raises(RuntimeError, match="runner failed"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            runner,
        )

    assert calls == [runner_batch.runner_requests[0]]


def test_dispatching_runtime_probe_runner_dispatches_by_family_and_form() -> None:
    """Dispatching runners select handlers by the request's family/form key."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]
    returned_attempt = _execution_attempt(
        runner_request.execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []
    wrong_key_calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def wrong_key_handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        wrong_key_calls.append(runner_request)
        return _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(_field("observed_module", "wrong"),),
        )

    def handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        return returned_attempt

    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=(
                    runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN
                ),
                form_label=runner_request.request.form_label,
                handler=wrong_key_handler,
            ),
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=runner_request.request.family_label,
                form_label="dynamic_import:other_form/1",
                handler=wrong_key_handler,
            ),
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=runner_request.request.family_label,
                form_label=runner_request.request.form_label,
                handler=handler,
            ),
        )
    )

    attempt = dispatching_runner(runner_request)

    assert isinstance(
        dispatching_runner,
        runtime_probe_execution.RuntimeProbeDispatchingRunner,
    )
    assert attempt is returned_attempt
    assert calls == [runner_request]
    assert wrong_key_calls == []


def test_dispatching_runtime_probe_runner_materializes_missing_handler_attempts() -> (
    None
):
    """Missing dispatch handlers produce deterministic non-proof attempts."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]
    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        ()
    )

    attempt = dispatching_runner(runner_request)
    collection = collect_runtime_probe_execution_attempts_from_runner_requests(
        runner_batch,
        dispatching_runner,
    )

    assert attempt.plan_id == runner_request.plan_id
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.execution_input.replay_artifact is runner_request.replay_artifact
    assert (
        attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None
    assert attempt.failure_summary == (
        "runtime probe runner has no handler for dynamic_import form "
        "dynamic_import:importlib.import_module/1; recorded as setup_failed"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_source", "missing_runtime_probe_handler"),
        _field("family_label", "dynamic_import"),
        _field("form_label", "dynamic_import:importlib.import_module/1"),
        _field("missing_handler_outcome", "setup_failed"),
    )

    result = collection.result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert result.request is runner_request.request
    assert result.replay_artifact is runner_request.replay_artifact
    assert (
        result.outcome is runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED
    )
    assert result.is_admissible_runtime_backed_proof is False


@pytest.mark.parametrize(
    "outcome",
    (
        runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        runtime_probe_results.RuntimeProbeResultOutcome.MISSING_ENVIRONMENT,
        runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
    ),
)
def test_dispatching_runtime_probe_runner_supports_non_proof_missing_outcomes(
    outcome: runtime_probe_results.RuntimeProbeResultOutcome,
) -> None:
    """Missing-handler attempts can be configured to any non-proof outcome."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (),
        missing_handler_outcome=outcome,
    )

    attempt = dispatching_runner(runner_batch.runner_requests[0])

    assert attempt.outcome is outcome
    assert attempt.failure_detail_fields[-1] == _field(
        "missing_handler_outcome",
        outcome.value,
    )


def test_dispatching_runtime_probe_runner_rejects_bad_dispatch_metadata() -> None:
    """Dispatch tables reject ambiguous keys and proof-bearing miss outcomes."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]

    def handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        return _execution_attempt(runner_request.execution_input)

    entry = runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
        family_label=runner_request.request.family_label,
        form_label=runner_request.request.form_label,
        handler=handler,
    )

    with pytest.raises(ValueError, match="form_label"):
        runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
            family_label=runner_request.request.family_label,
            form_label=" ",
            handler=handler,
        )
    with pytest.raises(ValueError, match="duplicate runtime probe runner handler key"):
        runtime_probe_execution.make_dispatching_runtime_probe_runner(
            (
                entry,
                runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                    family_label=runner_request.request.family_label,
                    form_label=runner_request.request.form_label,
                    handler=handler,
                ),
            )
        )
    with pytest.raises(ValueError, match="non-proof outcome"):
        runtime_probe_execution.make_dispatching_runtime_probe_runner(
            (),
            missing_handler_outcome=(
                runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
            ),
        )


def test_dispatching_runtime_probe_runner_rejects_untyped_handler_returns() -> None:
    """Dispatching runners keep the same strict typed return boundary."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]

    def handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> object:
        return {
            "plan_id": runner_request.plan_id,
            "request_id": runner_request.request_id,
        }

    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=runner_request.request.family_label,
                form_label=runner_request.request.form_label,
                handler=handler,
            ),
        )
    )

    with pytest.raises(ValueError, match="typed runtime probe execution attempts"):
        dispatching_runner(runner_request)


def test_dispatching_runtime_probe_runner_propagates_handler_exceptions() -> None:
    """Handler exceptions propagate unless an existing adapter wraps dispatch."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def handler(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        raise RuntimeError("handler failed")

    dispatching_runner = runtime_probe_execution.make_dispatching_runtime_probe_runner(
        (
            runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
                family_label=runner_request.request.family_label,
                form_label=runner_request.request.form_label,
                handler=handler,
            ),
        )
    )

    with pytest.raises(RuntimeError, match="handler failed"):
        dispatching_runner(runner_request)

    adapted_runner = (
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(
            dispatching_runner
        )
    )
    normalized_attempt = adapted_runner(runner_request)

    assert calls == [runner_request, runner_request]
    assert (
        normalized_attempt.outcome
        is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    )
    assert normalized_attempt.request is runner_request.request
    assert normalized_attempt.execution_input is runner_request.execution_input


def test_failure_normalizing_runner_preserves_success_and_normalizes_exception() -> (
    None
):
    """Opt-in adapter preserves successes and converts Exceptions to failures."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request, third_request))
    )
    first_attempt = _execution_attempt(
        runner_batch.runner_requests[0].execution_input,
        normalized_payload=(_field("observed_request_id", first_request.request_id),),
    )
    third_attempt = _execution_attempt(
        runner_batch.runner_requests[2].execution_input,
        normalized_payload=(_field("observed_request_id", third_request.request_id),),
    )
    calls: list[runtime_probe_execution.RuntimeProbeRunnerRequest] = []

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        calls.append(runner_request)
        if runner_request is runner_batch.runner_requests[0]:
            return first_attempt
        if runner_request is runner_batch.runner_requests[1]:
            raise RuntimeError("pid=12345 traceback frame local")
        return third_attempt

    adapted_runner = (
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(runner)
    )

    collection = collect_runtime_probe_execution_attempts_from_runner_requests(
        runner_batch,
        adapted_runner,
    )

    assert isinstance(
        adapted_runner,
        runtime_probe_execution.RuntimeProbeFailureNormalizingRunner,
    )
    assert tuple(calls) == runner_batch.runner_requests
    assert collection.attempts[0] is first_attempt
    assert collection.attempts[2] is third_attempt

    normalized_attempt = collection.attempts[1]
    assert normalized_attempt.plan_id == runner_batch.plan_id
    assert normalized_attempt.request_id == runner_batch.runner_requests[1].request_id
    assert normalized_attempt.request is runner_batch.runner_requests[1].request
    assert (
        normalized_attempt.execution_input
        is runner_batch.runner_requests[1].execution_input
    )
    assert (
        normalized_attempt.outcome
        is runtime_probe_results.RuntimeProbeResultOutcome.CRASHED
    )
    assert normalized_attempt.normalized_payload == ()
    assert normalized_attempt.durable_artifact_reference is None
    assert normalized_attempt.failure_summary == (
        "runtime probe runner raised RuntimeError; normalized as crashed"
    )
    assert normalized_attempt.failure_detail_fields == (
        _field("failure_normalization_source", "runner_exception"),
        _field("normalized_outcome", "crashed"),
        _field("exception_type", "builtins.RuntimeError"),
    )
    assert "pid=12345" not in normalized_attempt.failure_summary
    assert all(
        "pid=12345" not in detail.value
        for detail in normalized_attempt.failure_detail_fields
    )

    normalized_result = collection.result_batch.results[1]
    assert isinstance(
        normalized_result,
        runtime_probe_results.RuntimeProbeNonProofResult,
    )
    assert normalized_result.request_id == normalized_attempt.request_id
    assert normalized_result.request is normalized_attempt.request
    assert normalized_result.replay_artifact is (
        runner_batch.runner_requests[1].replay_artifact
    )
    assert normalized_result.is_admissible_runtime_backed_proof is False


@pytest.mark.parametrize(
    "outcome",
    (
        runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        runtime_probe_results.RuntimeProbeResultOutcome.MISSING_ENVIRONMENT,
        runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
    ),
)
def test_failure_normalizing_runtime_probe_runner_supports_non_proof_outcomes(
    outcome: runtime_probe_results.RuntimeProbeResultOutcome,
) -> None:
    """Failure normalization is limited to explicit non-proof outcomes."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))
    runner_request = runner_batch.runner_requests[0]

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        raise LookupError("local path /private/tmp/runtime-probe")

    adapted_runner = runtime_probe_execution.RuntimeProbeFailureNormalizingRunner(
        runner=runner,
        outcome=outcome,
    )

    attempt = adapted_runner(runner_request)

    assert attempt.outcome is outcome
    assert attempt.request_id == runner_request.request_id
    assert attempt.request is runner_request.request
    assert attempt.execution_input is runner_request.execution_input
    assert attempt.failure_summary == (
        f"runtime probe runner raised LookupError; normalized as {outcome.value}"
    )
    assert attempt.failure_detail_fields == (
        _field("failure_normalization_source", "runner_exception"),
        _field("normalized_outcome", outcome.value),
        _field("exception_type", "builtins.LookupError"),
    )
    assert attempt.normalized_payload == ()
    assert attempt.durable_artifact_reference is None


def test_failure_normalizing_runtime_probe_runner_rejects_observed_outcome() -> None:
    """Failure normalization cannot be configured to produce proof outcomes."""

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        return _execution_attempt(runner_request.execution_input)

    with pytest.raises(ValueError, match="non-proof outcome"):
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(
            runner,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
        )


def test_failure_normalizing_runtime_probe_runner_rejects_untyped_returns() -> None:
    """Malformed runner returns remain strict errors instead of normalized failures."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> object:
        return {
            "plan_id": runner_request.plan_id,
            "request_id": runner_request.request_id,
        }

    adapted_runner = (
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(runner)
    )

    with pytest.raises(ValueError, match="typed runtime probe execution attempts"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            adapted_runner,
        )


def test_failure_normalizing_runtime_probe_runner_does_not_catch_base_exception() -> (
    None
):
    """Only Exception subclasses are normalized; BaseException subclasses propagate."""
    runner_batch = _runner_request_batch(_materialized_batch(_plan(_request())))

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        raise SystemExit("runner requested shutdown")

    adapted_runner = (
        runtime_probe_execution.make_failure_normalizing_runtime_probe_runner(runner)
    )

    with pytest.raises(SystemExit, match="runner requested shutdown"):
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_batch,
            adapted_runner,
        )


def test_runtime_probe_runner_attempt_collection_rejects_order_and_result_drift() -> (
    None
):
    """The collection envelope enforces runner-request-gated assembly."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    runner_batch = _runner_request_batch(
        _materialized_batch(_plan(first_request, second_request))
    )
    attempts = tuple(
        _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(
                _field("observed_request_id", runner_request.request_id),
            ),
        )
        for runner_request in runner_batch.runner_requests
    )
    result_batch = _assemble_runner_request_result_batch(runner_batch, attempts)
    reversed_attempts = tuple(reversed(attempts))
    reversed_attempt_result_batch = _assemble_runner_request_result_batch(
        runner_batch,
        reversed_attempts,
    )
    reversed_result_batch = runtime_probe_results.RuntimeProbeResultBatch(
        plan_id=runner_batch.plan_id,
        results=tuple(reversed(result_batch.results)),
    )

    with pytest.raises(ValueError, match="runner request order"):
        runtime_probe_execution.RuntimeProbeRunnerAttemptCollection(
            runner_request_batch=runner_batch,
            attempts=reversed_attempts,
            result_batch=reversed_attempt_result_batch,
        )

    with pytest.raises(
        ValueError,
        match="result_batch must be in runner request order",
    ):
        runtime_probe_execution.RuntimeProbeRunnerAttemptCollection(
            runner_request_batch=runner_batch,
            attempts=attempts,
            result_batch=reversed_result_batch,
        )


def test_assemble_runtime_probe_result_batch_preserves_order_and_identities() -> None:
    """Complete attempts become results in input-batch order without mutation."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    third_request = _request(start_line=5)
    plan = _plan(first_request, second_request, third_request)
    batch = _materialized_batch(plan)
    original_batch_inputs = batch.inputs
    first_payload = (_field("observed_module", "plugins.weather"),)
    first_attempt = _execution_attempt(
        batch.inputs[0],
        normalized_payload=first_payload,
    )
    second_attempt = _execution_attempt(
        batch.inputs[1],
        durable_artifact_reference=(
            "artifact://runtime-probe-results/dynamic-import/main-run.json"
        ),
    )
    third_attempt = _execution_attempt(
        batch.inputs[2],
        outcome=runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        failure_summary="probe exceeded timeout",
        failure_detail_fields=(_field("timeout_seconds", "30"),),
    )

    result_batch = _assemble_result_batch(
        batch,
        (third_attempt, second_attempt, first_attempt),
    )

    assert result_batch.plan_id == batch.plan_id
    assert tuple(result.request_id for result in result_batch.results) == (
        batch.request_ids
    )
    assert batch.inputs == original_batch_inputs
    assert first_attempt.execution_input is batch.inputs[0]
    assert second_attempt.execution_input is batch.inputs[1]
    assert third_attempt.execution_input is batch.inputs[2]

    first_result = result_batch.results[0]
    assert isinstance(first_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert first_result.plan_id == batch.plan_id
    assert first_result.request_id == batch.inputs[0].request_id
    assert first_result.request is batch.inputs[0].request
    assert first_result.replay_artifact is batch.inputs[0].replay_artifact
    assert first_result.normalized_payload == first_payload
    assert first_result.durable_artifact_reference is None
    assert first_result.is_admissible_runtime_backed_proof is True

    second_result = result_batch.results[1]
    assert isinstance(second_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert second_result.request is batch.inputs[1].request
    assert second_result.replay_artifact is batch.inputs[1].replay_artifact
    assert second_result.normalized_payload == ()
    assert second_result.durable_artifact_reference == (
        "artifact://runtime-probe-results/dynamic-import/main-run.json"
    )
    assert second_result.is_admissible_runtime_backed_proof is True

    third_result = result_batch.results[2]
    assert isinstance(third_result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert third_result.request is batch.inputs[2].request
    assert third_result.replay_artifact is batch.inputs[2].replay_artifact
    assert (
        third_result.outcome
        is runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT
    )
    assert third_result.failure_summary == "probe exceeded timeout"
    assert third_result.failure_detail_fields == (_field("timeout_seconds", "30"),)
    assert third_result.is_admissible_runtime_backed_proof is False


@pytest.mark.parametrize(
    "outcome",
    (
        runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT,
        runtime_probe_results.RuntimeProbeResultOutcome.MISSING_ENVIRONMENT,
        runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
    ),
)
def test_assemble_runtime_probe_result_batch_preserves_all_non_proof_outcomes(
    outcome: runtime_probe_results.RuntimeProbeResultOutcome,
) -> None:
    """Every failed execution outcome remains non-proof in result assembly."""
    request = _request()
    batch = _materialized_batch(_plan(request))
    attempt = _execution_attempt(
        batch.inputs[0],
        outcome=outcome,
        failure_summary=f"runner reported {outcome.value}",
    )

    result_batch = _assemble_result_batch(
        batch,
        (attempt,),
    )

    result = result_batch.results[0]
    assert isinstance(result, runtime_probe_results.RuntimeProbeNonProofResult)
    assert result.outcome is outcome
    assert result.is_admissible_runtime_backed_proof is False


def test_assemble_runtime_probe_result_batch_supports_empty_input_batch() -> None:
    """Empty input batches assemble deterministically into empty result batches."""
    empty_plan = runtime_probe_requests.build_runtime_probe_request_plan(())
    batch = _materialized_batch(empty_plan)

    result_batch = _assemble_result_batch(
        batch,
        (),
    )

    assert result_batch.plan_id == batch.plan_id
    assert result_batch.results == ()


def test_assemble_runtime_probe_result_batch_rejects_incomplete_attempt_sets() -> None:
    """Attempt assembly requires exactly one attempt for every batch input."""
    first_request = _request(start_line=3)
    second_request = _request(start_line=4)
    batch = _materialized_batch(_plan(first_request, second_request))
    planned_attempt = _execution_attempt(
        batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    duplicate_attempt = _execution_attempt(
        batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.forecast"),),
    )
    unplanned_batch = _materialized_batch(_plan(_request(start_line=8)))
    unplanned_attempt = _execution_attempt(
        unplanned_batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.unplanned"),),
    )

    with pytest.raises(ValueError, match="missing runtime probe execution attempt"):
        _assemble_result_batch(
            batch,
            (planned_attempt,),
        )
    with pytest.raises(ValueError, match="duplicate runtime probe execution attempt"):
        _assemble_result_batch(
            batch,
            (planned_attempt, duplicate_attempt),
        )
    with pytest.raises(ValueError, match="not present in input batch"):
        _assemble_result_batch(
            batch,
            (planned_attempt, unplanned_attempt),
        )


def test_assemble_runtime_probe_result_batch_rejects_plan_and_input_drift() -> None:
    """Attempts must point at the exact planned batch input object."""
    request = _request()
    plan = _plan(request)
    batch = _materialized_batch(plan)
    equivalent_batch = _materialized_batch(plan)
    wrong_input_attempt = _execution_attempt(
        equivalent_batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    drifted_attempt = _execution_attempt(
        batch.inputs[0],
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    object.__setattr__(drifted_attempt, "plan_id", "runtime_probe_request_plan:wrong")

    with pytest.raises(ValueError, match="planned batch input"):
        _assemble_result_batch(
            batch,
            (wrong_input_attempt,),
        )
    with pytest.raises(ValueError, match="plan_id must match input batch"):
        _assemble_result_batch(
            batch,
            (drifted_attempt,),
        )


def test_runtime_probe_execution_attempt_rejects_plan_input_drift() -> None:
    """Attempt records cannot drift from the execution input they cite."""
    request = _request()
    batch = _materialized_batch(_plan(request))
    input_item = batch.inputs[0]

    with pytest.raises(ValueError, match="plan_id must match execution input"):
        runtime_probe_execution.RuntimeProbeExecutionAttempt(
            plan_id="runtime_probe_request_plan:wrong",
            request_id=input_item.request_id,
            request=input_item.request,
            execution_input=input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )
    with pytest.raises(ValueError, match="request_id must match execution input"):
        runtime_probe_execution.RuntimeProbeExecutionAttempt(
            plan_id=input_item.plan_id,
            request_id="runtime_probe:wrong",
            request=input_item.request,
            execution_input=input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )
    with pytest.raises(ValueError, match="request must be execution input request"):
        runtime_probe_execution.RuntimeProbeExecutionAttempt(
            plan_id=input_item.plan_id,
            request_id=input_item.request_id,
            request=_request(start_line=8),
            execution_input=input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )


def test_runtime_probe_execution_attempt_rejects_observed_failure_metadata() -> None:
    """Observed attempts need proof metadata and cannot carry failure-only fields."""
    request = _request()
    input_item = _materialized_batch(_plan(request)).inputs[0]

    with pytest.raises(ValueError, match="cannot carry failure metadata"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
            failure_summary="runner crashed after observing payload",
        )
    with pytest.raises(ValueError, match="normalized_payload or durable"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            failure_summary=None,
        )


def test_runtime_probe_execution_attempt_rejects_exec_missing_replay_inputs() -> None:
    """Exact exec observations require runtime-observed source replay proof."""
    input_item = _materialized_batch(_plan(_exec_request())).inputs[0]

    with pytest.raises(ValueError, match="observed replay inputs"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("execution_outcome", "completed"),),
        )


def test_runtime_probe_execution_attempt_rejects_eval_missing_replay_inputs() -> None:
    """Exact eval observations require runtime-observed source replay proof."""
    input_item = _materialized_batch(_plan(_eval_request())).inputs[0]

    with pytest.raises(ValueError, match="observed replay inputs"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
            normalized_payload=(_field("evaluation_outcome", "returned_value"),),
        )


def test_runtime_probe_execution_attempt_rejects_failure_without_summary() -> None:
    """Failure outcomes need a concrete failure summary and cannot carry proof."""
    request = _request()
    input_item = _materialized_batch(_plan(request)).inputs[0]

    with pytest.raises(ValueError, match="failure_summary"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
        )
    with pytest.raises(ValueError, match="failure_summary"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.SETUP_FAILED,
            failure_summary=" ",
        )
    with pytest.raises(ValueError, match="cannot carry proof metadata"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
            failure_summary="runner crashed",
        )


def test_runtime_probe_execution_attempt_rejects_blank_references_and_details() -> None:
    """Attempt metadata rejects blank durable references and tampered detail fields."""
    request = _request()
    input_item = _materialized_batch(_plan(request)).inputs[0]
    blank_detail = _field("exit_code", "1")
    object.__setattr__(blank_detail, "value", " ")

    with pytest.raises(ValueError, match="durable_artifact_reference"):
        _execution_attempt(
            input_item,
            durable_artifact_reference=" ",
        )
    with pytest.raises(ValueError, match="failure_detail_fields"):
        _execution_attempt(
            input_item,
            outcome=runtime_probe_results.RuntimeProbeResultOutcome.CRASHED,
            failure_summary="runner crashed",
            failure_detail_fields=(blank_detail,),
        )


def test_materialize_runtime_probe_execution_inputs_supports_empty_plan() -> None:
    """Empty request plans materialize to empty ordered input batches."""
    plan = runtime_probe_requests.build_runtime_probe_request_plan(())

    batch = _materialized_batch(plan)

    assert batch.plan_id == plan.plan_id
    assert batch.request_ids == ()
    assert batch.inputs == ()


def test_materialize_runtime_probe_execution_inputs_rejects_empty_assumptions() -> None:
    """Execution inputs must carry explicit runtime assumptions."""
    request = _request()
    plan = _plan(request)

    with pytest.raises(ValueError, match="runtime_assumptions"):
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            plan,
            repository_snapshot_basis=_snapshot_basis(),
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=(),
        )


def test_materialize_runtime_probe_execution_inputs_rejects_blank_probe_metadata() -> (
    None
):
    """Execution inputs reject blank probe contract metadata."""
    request = _request()
    plan = _plan(request)
    empty_plan = runtime_probe_requests.build_runtime_probe_request_plan(())

    with pytest.raises(ValueError, match="probe_contract_revision"):
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            plan,
            repository_snapshot_basis=_snapshot_basis(),
            probe_contract_revision=" ",
            runtime_assumptions=_runtime_assumptions(),
        )
    with pytest.raises(ValueError, match="probe_contract_revision"):
        runtime_probe_execution.materialize_runtime_probe_execution_input_batch(
            empty_plan,
            repository_snapshot_basis=_snapshot_basis(),
            probe_contract_revision=" ",
            runtime_assumptions=_runtime_assumptions(),
        )


def test_materialize_runtime_probe_execution_inputs_rejects_plan_request_drift() -> (
    None
):
    """Materialization revalidates request-plan envelopes before building inputs."""
    request = _request()
    plan = _plan(request)
    object.__setattr__(plan, "request_ids", ("runtime_probe:wrong",))

    with pytest.raises(ValueError, match="request_ids must match requests"):
        _materialized_batch(plan)


def test_materialize_runtime_probe_execution_inputs_rejects_duplicate_request_ids() -> (
    None
):
    """Materialization refuses tampered plans with duplicate request identities."""
    request = _request()
    plan = _plan(request)
    object.__setattr__(plan, "requests", (request, request))
    object.__setattr__(plan, "request_ids", (request.request_id, request.request_id))

    with pytest.raises(ValueError, match="duplicate runtime probe request_id"):
        _materialized_batch(plan)


def test_runtime_probe_execution_input_rejects_request_identity_drift() -> None:
    """A work item cannot carry a request ID that differs from its request object."""
    request = _request()
    plan = _plan(request)
    input_item = _materialized_batch(plan).inputs[0]

    with pytest.raises(ValueError, match="request_id must match request.request_id"):
        runtime_probe_execution.RuntimeProbeExecutionInput(
            plan_id=input_item.plan_id,
            request_id="runtime_probe:wrong",
            request=request,
            source_site_identity=input_item.source_site_identity,
            family_label=input_item.family_label,
            form_label=input_item.form_label,
            replay_target_seed=input_item.replay_target_seed,
            replay_selector_seed=input_item.replay_selector_seed,
            replay_artifact=input_item.replay_artifact,
        )


def test_runtime_probe_execution_input_rejects_replay_metadata_drift() -> None:
    """Replay artifacts must retain the planned request identity fields."""
    request = _request()
    plan = _plan(request)
    input_item = _materialized_batch(plan).inputs[0]
    replay_artifact = input_item.replay_artifact
    drifted_replay_artifact = runtime_probe_results.RuntimeProbeReplayArtifact(
        probe_identifier=replay_artifact.probe_identifier,
        probe_contract_revision=replay_artifact.probe_contract_revision,
        repository_snapshot_basis=replay_artifact.repository_snapshot_basis,
        replay_target="other.target",
        replay_selector=replay_artifact.replay_selector,
        replay_inputs=replay_artifact.replay_inputs,
        runtime_assumptions=replay_artifact.runtime_assumptions,
    )

    with pytest.raises(ValueError, match="replay_artifact target"):
        runtime_probe_execution.RuntimeProbeExecutionInput(
            plan_id=input_item.plan_id,
            request_id=input_item.request_id,
            request=request,
            source_site_identity=input_item.source_site_identity,
            family_label=input_item.family_label,
            form_label=input_item.form_label,
            replay_target_seed=input_item.replay_target_seed,
            replay_selector_seed=input_item.replay_selector_seed,
            replay_artifact=drifted_replay_artifact,
        )


def test_runtime_probe_execution_input_batch_rejects_input_plan_mismatch() -> None:
    """Ordered batches reject plan, request-order, and duplicate-input drift."""
    request = _request()
    plan = _plan(request)
    input_item = _materialized_batch(plan).inputs[0]

    with pytest.raises(ValueError, match="plan_id must match inputs"):
        runtime_probe_execution.RuntimeProbeExecutionInputBatch(
            plan_id="runtime_probe_request_plan:other",
            request_ids=(input_item.request_id,),
            inputs=(input_item,),
        )

    with pytest.raises(ValueError, match="request_ids must match inputs"):
        runtime_probe_execution.RuntimeProbeExecutionInputBatch(
            plan_id=input_item.plan_id,
            request_ids=("runtime_probe:wrong",),
            inputs=(input_item,),
        )

    with pytest.raises(ValueError, match="duplicate runtime probe execution"):
        runtime_probe_execution.RuntimeProbeExecutionInputBatch(
            plan_id=input_item.plan_id,
            request_ids=(input_item.request_id, input_item.request_id),
            inputs=(input_item, input_item),
        )


def test_runtime_probe_execution_contracts_are_frozen_and_module_local() -> None:
    """Execution records stay frozen and absent from package-root exports."""
    request = _request()
    plan = _plan(request)
    diagnostic = _diagnostic_for_plan(plan)
    preparation = _prepare_runner_requests(diagnostic)
    input_item = _materialized_batch(plan).inputs[0]
    runner_batch = _runner_request_batch(_materialized_batch(plan))
    runner_request = runner_batch.runner_requests[0]
    attempt = _execution_attempt(
        input_item,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    collection_attempt = _execution_attempt(
        runner_request.execution_input,
        normalized_payload=(_field("observed_module", "plugins.weather"),),
    )
    collection = runtime_probe_execution.RuntimeProbeRunnerAttemptCollection(
        runner_request_batch=runner_batch,
        attempts=(collection_attempt,),
        result_batch=_assemble_runner_request_result_batch(
            runner_batch,
            (collection_attempt,),
        ),
    )

    def runner(
        runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
        return _execution_attempt(
            runner_request.execution_input,
            normalized_payload=(_field("observed_module", "plugins.weather"),),
        )

    handler_entry = runtime_probe_execution.RuntimeProbeRunnerHandlerEntry(
        family_label=runner_request.request.family_label,
        form_label=runner_request.request.form_label,
        handler=runner,
    )
    dispatching_runner = runtime_probe_execution.RuntimeProbeDispatchingRunner(
        handler_entries=(handler_entry,),
    )
    normalizing_runner = runtime_probe_execution.RuntimeProbeFailureNormalizingRunner(
        runner=runner,
    )
    local_python_context = (
        runtime_probe_execution.derive_runtime_probe_local_python_environment_context(
            _local_python_runner_request()
        )
    )
    local_python_worker_payload = _local_python_worker_request_payload()
    local_python_invocation = _local_python_subprocess_invocation()
    local_python_handler_config = (
        runtime_probe_execution.RuntimeProbeLocalPythonSubprocessHandlerConfig(
            family_label=runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT,
            form_label="dynamic_import:importlib.import_module/1",
            python_executable="/workspace/context-ir/.venv/bin/python",
            module_name="context_ir.runtime_probe_worker",
            invocation_contract_revision=(
                "runtime-probe-local-python-subprocess:test.1"
            ),
            completion_contract_revision=(
                "runtime-probe-local-python-process-completion:test.1"
            ),
            module_argv=("--request", "runtime-probe-request.json"),
        )
    )
    local_python_completion = _local_python_process_completion(local_python_invocation)
    local_python_stdout_protocol_result = (
        materialize_runtime_probe_local_python_stdout_protocol_result(
            _local_python_process_completion(
                local_python_invocation,
                stdout_text=_local_python_stdout_protocol_text(),
            )
        )
    )
    local_python_stdout_protocol_attempt = (
        materialize_runtime_probe_local_python_stdout_protocol_attempt(
            local_python_stdout_protocol_result
        )
    )

    with pytest.raises(FrozenInstanceError):
        input_item.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        runner_request.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        runner_batch.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        attempt.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        collection.runner_request_batch = runner_batch
    with pytest.raises(FrozenInstanceError):
        preparation.request_plan = (
            runtime_probe_requests.build_runtime_probe_request_plan(())
        )
    with pytest.raises(FrozenInstanceError):
        normalizing_runner.outcome = (
            runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT
        )
    with pytest.raises(FrozenInstanceError):
        handler_entry.form_label = "dynamic_import:mutated/1"
    with pytest.raises(FrozenInstanceError):
        dispatching_runner.missing_handler_outcome = (
            runtime_probe_results.RuntimeProbeResultOutcome.TIMED_OUT
        )
    with pytest.raises(FrozenInstanceError):
        local_python_context.working_directory = "/tmp/context-ir"
    with pytest.raises(FrozenInstanceError):
        local_python_worker_payload.plan_id = "runtime_probe_request_plan:mutated"
    with pytest.raises(FrozenInstanceError):
        local_python_invocation.working_directory = "/tmp/context-ir"
    with pytest.raises(FrozenInstanceError):
        local_python_handler_config.form_label = "dynamic_import:mutated/1"
    with pytest.raises(FrozenInstanceError):
        local_python_completion.stdout_text = "mutated"
    with pytest.raises(FrozenInstanceError):
        local_python_stdout_protocol_result.stdout_protocol_revision = "mutated"
    with pytest.raises(FrozenInstanceError):
        local_python_stdout_protocol_attempt.plan_id = (
            "runtime_probe_request_plan:mutated"
        )

    assert (
        "RuntimeProbeDiagnosticRunnerRequestPreparation"
        in runtime_probe_execution.__all__
    )
    assert "RuntimeProbeDispatchingRunner" in runtime_probe_execution.__all__
    assert "RuntimeProbeExecutionAttempt" in runtime_probe_execution.__all__
    assert "RuntimeProbeExecutionInput" in runtime_probe_execution.__all__
    assert "RuntimeProbeExecutionInputBatch" in runtime_probe_execution.__all__
    assert "RuntimeProbeFailureNormalizingRunner" in runtime_probe_execution.__all__
    assert (
        "RuntimeProbeLocalPythonEnvironmentContext" in runtime_probe_execution.__all__
    )
    assert "RuntimeProbeLocalPythonProcessCompletion" in (
        runtime_probe_execution.__all__
    )
    assert "RuntimeProbeLocalPythonStdoutProtocolResult" in (
        runtime_probe_execution.__all__
    )
    assert (
        "RuntimeProbeLocalPythonSubprocessHandlerConfig"
        in runtime_probe_execution.__all__
    )
    assert (
        "RuntimeProbeLocalPythonSubprocessInvocation" in runtime_probe_execution.__all__
    )
    assert (
        "RuntimeProbeLocalPythonWorkerRequestPayload" in runtime_probe_execution.__all__
    )
    assert "RuntimeProbeRunnerHandlerEntry" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerHandlerKey" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerAttemptCollection" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerCallable" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerRequest" in runtime_probe_execution.__all__
    assert "RuntimeProbeRunnerRequestBatch" in runtime_probe_execution.__all__
    assert "assemble_runtime_probe_result_batch_from_execution_attempts" in (
        runtime_probe_execution.__all__
    )
    assert "assemble_runtime_probe_result_batch_from_runner_request_attempts" in (
        runtime_probe_execution.__all__
    )
    assert "collect_runtime_probe_execution_attempts_from_runner_requests" in (
        runtime_probe_execution.__all__
    )
    assert "derive_runtime_probe_local_python_environment_context" in (
        runtime_probe_execution.__all__
    )
    assert "execute_runtime_probe_local_python_subprocess_invocation" in (
        runtime_probe_execution.__all__
    )
    assert "execute_runtime_probe_local_python_subprocess_invocation_attempt" in (
        runtime_probe_execution.__all__
    )
    assert "make_dispatching_runtime_probe_runner" in runtime_probe_execution.__all__
    assert "make_failure_normalizing_runtime_probe_runner" in (
        runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_dynamic_import_local_python_subprocess_runner" in (
        runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_exec_or_eval_exec_local_python_subprocess_runner" in (
        runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_exec_or_eval_eval_local_python_subprocess_runner" in (
        runtime_probe_execution.__all__
    )
    assert (
        "make_runtime_probe_metaclass_behavior_keyword_local_python_subprocess_runner"
        in runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_reflective_dir_local_python_subprocess_runner" in (
        runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner" in (
        runtime_probe_execution.__all__
    )
    assert (
        "make_runtime_probe_reflective_getattr_default_local_python_subprocess_runner"
        in runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_reflective_getattr_local_python_subprocess_runner" in (
        runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_reflective_hasattr_local_python_subprocess_runner" in (
        runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_reflective_vars_local_python_subprocess_runner" in (
        runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner" in (
        runtime_probe_execution.__all__
    )
    assert (
        "make_runtime_probe_runtime_mutation_globals_zero_local_python_subprocess_runner"
        in runtime_probe_execution.__all__
    )
    assert (
        "make_runtime_probe_runtime_mutation_locals_zero_local_python_subprocess_runner"
        in runtime_probe_execution.__all__
    )
    assert (
        "make_runtime_probe_runtime_mutation_setattr_local_python_subprocess_runner"
        in runtime_probe_execution.__all__
    )
    assert (
        "make_runtime_probe_runtime_mutation_delattr_local_python_subprocess_runner"
        in runtime_probe_execution.__all__
    )
    assert "make_runtime_probe_local_python_subprocess_handler_entry" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_execution_input_batch" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_process_completion_attempt" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_process_completion" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_stdout_protocol_failure_attempt" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_stdout_protocol_attempt" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_stdout_protocol_result" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_subprocess_exception_attempt" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_subprocess_invocation" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_local_python_worker_request_payload" in (
        runtime_probe_execution.__all__
    )
    assert "materialize_runtime_probe_runner_request_batch" in (
        runtime_probe_execution.__all__
    )
    assert "parse_runtime_probe_local_python_worker_request_payload" in (
        runtime_probe_execution.__all__
    )
    assert "prepare_runtime_probe_runner_requests_for_diagnostic" in (
        runtime_probe_execution.__all__
    )
    assert "serialize_runtime_probe_local_python_worker_request_payload" in (
        runtime_probe_execution.__all__
    )
    assert "RuntimeProbeDiagnosticRunnerRequestPreparation" not in context_ir.__all__
    assert "RuntimeProbeDispatchingRunner" not in context_ir.__all__
    assert "RuntimeProbeExecutionAttempt" not in context_ir.__all__
    assert "RuntimeProbeExecutionInput" not in context_ir.__all__
    assert "RuntimeProbeExecutionInputBatch" not in context_ir.__all__
    assert "RuntimeProbeFailureNormalizingRunner" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonEnvironmentContext" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonProcessCompletion" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonStdoutProtocolResult" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonSubprocessHandlerConfig" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonSubprocessInvocation" not in context_ir.__all__
    assert "RuntimeProbeLocalPythonWorkerRequestPayload" not in context_ir.__all__
    assert "RuntimeProbeRunnerHandlerEntry" not in context_ir.__all__
    assert "RuntimeProbeRunnerHandlerKey" not in context_ir.__all__
    assert "RuntimeProbeRunnerAttemptCollection" not in context_ir.__all__
    assert "RuntimeProbeRunnerCallable" not in context_ir.__all__
    assert "RuntimeProbeRunnerRequest" not in context_ir.__all__
    assert "RuntimeProbeRunnerRequestBatch" not in context_ir.__all__
    assert "assemble_runtime_probe_result_batch_from_execution_attempts" not in (
        context_ir.__all__
    )
    assert "assemble_runtime_probe_result_batch_from_runner_request_attempts" not in (
        context_ir.__all__
    )
    assert (
        "collect_runtime_probe_execution_attempts_from_runner_requests"
        not in context_ir.__all__
    )
    assert "derive_runtime_probe_local_python_environment_context" not in (
        context_ir.__all__
    )
    assert (
        "execute_runtime_probe_local_python_subprocess_invocation"
        not in context_ir.__all__
    )
    assert (
        "execute_runtime_probe_local_python_subprocess_invocation_attempt"
        not in context_ir.__all__
    )
    assert "make_dispatching_runtime_probe_runner" not in context_ir.__all__
    assert "make_failure_normalizing_runtime_probe_runner" not in context_ir.__all__
    assert (
        "make_runtime_probe_dynamic_import_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_exec_or_eval_exec_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_exec_or_eval_eval_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_metaclass_behavior_keyword_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_reflective_dir_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_reflective_getattr_default_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_reflective_hasattr_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_reflective_vars_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_runtime_mutation_globals_zero_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_runtime_mutation_locals_zero_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_runtime_mutation_setattr_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_runtime_mutation_delattr_local_python_subprocess_runner"
        not in context_ir.__all__
    )
    assert (
        "make_runtime_probe_local_python_subprocess_handler_entry"
        not in context_ir.__all__
    )
    assert "materialize_runtime_probe_execution_input_batch" not in context_ir.__all__
    assert (
        "materialize_runtime_probe_local_python_process_completion_attempt"
        not in context_ir.__all__
    )
    assert (
        "materialize_runtime_probe_local_python_stdout_protocol_failure_attempt"
        not in context_ir.__all__
    )
    assert (
        "materialize_runtime_probe_local_python_subprocess_invocation"
        not in context_ir.__all__
    )
    assert (
        "materialize_runtime_probe_local_python_worker_request_payload"
        not in context_ir.__all__
    )
    assert (
        "materialize_runtime_probe_local_python_stdout_protocol_attempt"
        not in context_ir.__all__
    )
    assert (
        "materialize_runtime_probe_local_python_stdout_protocol_result"
        not in context_ir.__all__
    )
    assert (
        "materialize_runtime_probe_local_python_subprocess_exception_attempt"
        not in context_ir.__all__
    )
    assert "materialize_runtime_probe_runner_request_batch" not in context_ir.__all__
    assert (
        "parse_runtime_probe_local_python_worker_request_payload"
        not in context_ir.__all__
    )
    assert (
        "prepare_runtime_probe_runner_requests_for_diagnostic" not in context_ir.__all__
    )
    assert (
        "serialize_runtime_probe_local_python_worker_request_payload"
        not in context_ir.__all__
    )
    assert not hasattr(context_ir, "RuntimeProbeDiagnosticRunnerRequestPreparation")
    assert not hasattr(context_ir, "RuntimeProbeDispatchingRunner")
    assert not hasattr(context_ir, "RuntimeProbeExecutionAttempt")
    assert not hasattr(context_ir, "RuntimeProbeExecutionInput")
    assert not hasattr(context_ir, "RuntimeProbeExecutionInputBatch")
    assert not hasattr(context_ir, "RuntimeProbeFailureNormalizingRunner")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonEnvironmentContext")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonProcessCompletion")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonStdoutProtocolResult")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonSubprocessHandlerConfig")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonSubprocessInvocation")
    assert not hasattr(context_ir, "RuntimeProbeLocalPythonWorkerRequestPayload")
    assert not hasattr(context_ir, "RuntimeProbeRunnerHandlerEntry")
    assert not hasattr(context_ir, "RuntimeProbeRunnerHandlerKey")
    assert not hasattr(context_ir, "RuntimeProbeRunnerAttemptCollection")
    assert not hasattr(context_ir, "RuntimeProbeRunnerCallable")
    assert not hasattr(context_ir, "RuntimeProbeRunnerRequest")
    assert not hasattr(context_ir, "RuntimeProbeRunnerRequestBatch")
    assert not hasattr(
        context_ir,
        "assemble_runtime_probe_result_batch_from_execution_attempts",
    )
    assert not hasattr(
        context_ir,
        "assemble_runtime_probe_result_batch_from_runner_request_attempts",
    )
    assert not hasattr(
        context_ir,
        "collect_runtime_probe_execution_attempts_from_runner_requests",
    )
    assert not hasattr(
        context_ir,
        "derive_runtime_probe_local_python_environment_context",
    )
    assert not hasattr(
        context_ir,
        "execute_runtime_probe_local_python_subprocess_invocation",
    )
    assert not hasattr(
        context_ir,
        "execute_runtime_probe_local_python_subprocess_invocation_attempt",
    )
    assert not hasattr(
        context_ir,
        "make_dispatching_runtime_probe_runner",
    )
    assert not hasattr(
        context_ir,
        "make_failure_normalizing_runtime_probe_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_dynamic_import_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_exec_or_eval_exec_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_exec_or_eval_eval_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_metaclass_behavior_keyword_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_reflective_dir_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_reflective_getattr_default_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_reflective_getattr_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_reflective_hasattr_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_reflective_vars_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner",
    )
    assert not hasattr(
        context_ir,
        "make_runtime_probe_local_python_subprocess_handler_entry",
    )
    assert not hasattr(
        context_ir,
        "prepare_runtime_probe_runner_requests_for_diagnostic",
    )
    assert not hasattr(context_ir, "materialize_runtime_probe_execution_input_batch")
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_process_completion_attempt",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_stdout_protocol_failure_attempt",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_process_completion",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_subprocess_exception_attempt",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_stdout_protocol_attempt",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_stdout_protocol_result",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_subprocess_invocation",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_local_python_worker_request_payload",
    )
    assert not hasattr(
        context_ir,
        "materialize_runtime_probe_runner_request_batch",
    )
    assert not hasattr(
        context_ir,
        "parse_runtime_probe_local_python_worker_request_payload",
    )
    assert not hasattr(
        context_ir,
        "serialize_runtime_probe_local_python_worker_request_payload",
    )

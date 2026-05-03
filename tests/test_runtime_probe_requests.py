"""Tests for planned runtime probe request derivation."""

from __future__ import annotations

import textwrap
from pathlib import Path

import context_ir.runtime_probe_requests as runtime_probe_requests
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_types import (
    SemanticProgram,
    SemanticSubjectKind,
    UnresolvedReasonCode,
)


def _derived_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted semantic pipeline through frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def test_derive_runtime_probe_requests_plans_attachable_runtime_boundaries(
    tmp_path: Path,
) -> None:
    """Runtime probe requests cover supported attachable boundary families."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import builtins
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
                __import__(name)
                getattr(obj, name)
                getattr(obj, name, default)
                hasattr(obj, name)
                vars(obj)
                vars()
                dir(obj)
                dir()
                setattr(obj, name, value)
                delattr(obj, name)
                globals()
                locals()
                exec(source)
                eval(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)
    original_unsupported = list(program.unsupported_constructs)
    original_frontier = list(program.unresolved_frontier)
    original_provenance_records = list(program.provenance_records)

    first_requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    second_requests = runtime_probe_requests.derive_runtime_probe_requests(program)

    requests_by_text = {request.boundary_text: request for request in first_requests}
    source_site_fragments = [
        (
            request.source_site.file_path,
            request.source_site.span.start_line,
            request.source_site.span.start_column,
            request.source_site.span.end_line,
            request.source_site.span.end_column,
        )
        for request in first_requests
    ]

    assert first_requests == second_requests
    assert source_site_fragments == sorted(source_site_fragments)
    assert len(source_site_fragments) == len(set(source_site_fragments))
    assert program.unsupported_constructs == original_unsupported
    assert program.unresolved_frontier == original_frontier
    assert program.provenance_records == original_provenance_records
    assert set(requests_by_text) == {
        "metaclass=Meta",
        "importlib.import_module(name)",
        "load_module(name)",
        "builtins.__import__(name)",
        "__import__(name)",
        "getattr(obj, name)",
        "getattr(obj, name, default)",
        "hasattr(obj, name)",
        "vars(obj)",
        "vars()",
        "dir(obj)",
        "dir()",
        "setattr(obj, name, value)",
        "delattr(obj, name)",
        "globals()",
        "locals()",
        "exec(source)",
        "eval(source)",
    }

    dynamic_import = requests_by_text["importlib.import_module(name)"]
    assert dynamic_import.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert dynamic_import.reason_code is UnresolvedReasonCode.DYNAMIC_IMPORT
    assert (
        dynamic_import.family_label
        is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert dynamic_import.form_label == "dynamic_import:importlib.import_module/1"
    assert dynamic_import.replay_target_seed == "main.run"
    assert dynamic_import.replay_selector_seed.startswith(
        "call:main.run:dynamic_import:importlib.import_module/1@main.py:"
    )
    assert (
        dynamic_import.status
        is runtime_probe_requests.RuntimeProbeRequestStatus.PLANNED_NOT_EXECUTED
    )

    reflective_builtin = requests_by_text["getattr(obj, name, default)"]
    assert reflective_builtin.reason_code is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert (
        reflective_builtin.family_label
        is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN
    )
    assert reflective_builtin.form_label == "reflective_builtin:getattr/3"
    assert reflective_builtin.replay_target_seed == "main.run"
    assert (
        reflective_builtin.status
        is runtime_probe_requests.RuntimeProbeRequestStatus.PLANNED_NOT_EXECUTED
    )

    runtime_mutation = requests_by_text["setattr(obj, name, value)"]
    assert runtime_mutation.reason_code is UnresolvedReasonCode.RUNTIME_MUTATION
    assert (
        runtime_mutation.family_label
        is runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION
    )
    assert runtime_mutation.form_label == "runtime_mutation:setattr/3"
    assert runtime_mutation.replay_target_seed == "main.run"

    exec_request = requests_by_text["exec(source)"]
    assert exec_request.reason_code is UnresolvedReasonCode.EXEC_OR_EVAL
    assert (
        exec_request.family_label
        is runtime_probe_requests.RuntimeProbeFamily.EXEC_OR_EVAL
    )
    assert exec_request.form_label == "exec_or_eval:exec/1"
    assert exec_request.replay_target_seed == "main.run"

    metaclass_request = requests_by_text["metaclass=Meta"]
    assert metaclass_request.reason_code is UnresolvedReasonCode.METACLASS_BEHAVIOR
    assert (
        metaclass_request.family_label
        is runtime_probe_requests.RuntimeProbeFamily.METACLASS_BEHAVIOR
    )
    assert metaclass_request.form_label == "metaclass_behavior:keyword"
    assert metaclass_request.replay_target_seed == "main.Example"
    assert metaclass_request.replay_selector_seed.startswith(
        "class:main.Example:metaclass@main.py:"
    )


def test_derive_runtime_probe_requests_excludes_non_attachable_boundaries(
    tmp_path: Path,
) -> None:
    """Unsupported but non-attachable forms do not become runtime probe requests."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib.metadata as importlib

            def wrapper(func):
                return func

            @wrapper(factory())
            def decorated() -> None:
                pass

            def run(
                obj: object,
                name: str,
                source: str,
                globals_ns: dict[str, object],
                default: object,
            ) -> None:
                importlib.import_module(name)
                getattr()
                hasattr(obj)
                globals(obj)
                locals(obj)
                setattr(obj, name)
                delattr(obj)
                dir(obj, default)
                eval(source, globals_ns)
                eval(source=source)
                exec(source, globals_ns)
                exec(source=source)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _derived_program(tmp_path)

    requests = runtime_probe_requests.derive_runtime_probe_requests(program)
    requested_texts = {request.boundary_text for request in requests}
    unsupported_by_text = {
        construct.construct_text: construct.reason_code
        for construct in program.unsupported_constructs
    }

    assert requests == ()
    assert unsupported_by_text["getattr()"] is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert unsupported_by_text["hasattr(obj)"] is (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN
    )
    assert unsupported_by_text["globals(obj)"] is (
        UnresolvedReasonCode.RUNTIME_MUTATION
    )
    assert unsupported_by_text["locals(obj)"] is UnresolvedReasonCode.RUNTIME_MUTATION
    assert unsupported_by_text["setattr(obj, name)"] is (
        UnresolvedReasonCode.RUNTIME_MUTATION
    )
    assert unsupported_by_text["delattr(obj)"] is UnresolvedReasonCode.RUNTIME_MUTATION
    assert unsupported_by_text["dir(obj, default)"] is (
        UnresolvedReasonCode.REFLECTIVE_BUILTIN
    )
    assert unsupported_by_text["eval(source, globals_ns)"] is (
        UnresolvedReasonCode.EXEC_OR_EVAL
    )
    assert unsupported_by_text["eval(source=source)"] is (
        UnresolvedReasonCode.EXEC_OR_EVAL
    )
    assert unsupported_by_text["exec(source, globals_ns)"] is (
        UnresolvedReasonCode.EXEC_OR_EVAL
    )
    assert unsupported_by_text["exec(source=source)"] is (
        UnresolvedReasonCode.EXEC_OR_EVAL
    )
    assert unsupported_by_text["wrapper(factory())"] is (
        UnresolvedReasonCode.OPAQUE_DECORATOR
    )
    assert "importlib.import_module(name)" not in unsupported_by_text
    assert requested_texts.isdisjoint(unsupported_by_text)

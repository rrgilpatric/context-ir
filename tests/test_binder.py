"""Binder tests for the semantic-first baseline."""

from __future__ import annotations

import textwrap
from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.parser import extract_syntax
from context_ir.semantic_types import (
    BindingKind,
    DefinitionKind,
    ResolvedSymbolKind,
    SemanticProgram,
    SyntaxDiagnosticCode,
)


def test_bind_syntax_returns_semantic_program_and_preserves_syntax(
    tmp_path: Path,
) -> None:
    """The binder returns a SemanticProgram and carries syntax through unchanged."""
    (tmp_path / "example.py").write_text(
        "def run(value: int) -> int:\n    return value\n"
    )

    syntax = extract_syntax(tmp_path)
    program = bind_syntax(syntax)

    assert isinstance(program, SemanticProgram)
    assert program.syntax is syntax
    assert program.repo_root == tmp_path
    assert program.resolved_imports == []
    assert program.dataclass_models == []
    assert program.dataclass_fields == []
    assert program.resolved_references == []
    assert program.proven_dependencies == []
    assert program.unresolved_frontier == []
    assert program.unsupported_constructs == []
    assert program.diagnostics == []


def test_bind_syntax_creates_definition_symbols_and_enclosing_scope_bindings(
    tmp_path: Path,
) -> None:
    """Definitions produce stable symbols and bind into their enclosing scopes."""
    (tmp_path / "example.py").write_text(
        textwrap.dedent(
            """
            class Example:
                def method(self, value: int) -> int:
                    def inner() -> int:
                        return value
                    return inner()

            async def run(target: int) -> int:
                return target
            """
        ).lstrip()
    )

    syntax = extract_syntax(tmp_path)
    program = bind_syntax(syntax)
    definitions = {
        definition.qualified_name: definition
        for definition in syntax.definitions
        if definition.file_id == "file:example.py"
    }

    module_definition = next(
        definition
        for definition in syntax.definitions
        if definition.file_id == "file:example.py"
        and definition.kind is DefinitionKind.MODULE
    )
    class_definition = definitions["example.Example"]
    method_definition = definitions["example.Example.method"]
    inner_definition = definitions["example.Example.method.inner"]
    run_definition = definitions["example.run"]

    module_symbol = program.resolved_symbols[module_definition.definition_id]
    class_symbol = program.resolved_symbols[class_definition.definition_id]
    method_symbol = program.resolved_symbols[method_definition.definition_id]
    inner_symbol = program.resolved_symbols[inner_definition.definition_id]
    run_symbol = program.resolved_symbols[run_definition.definition_id]

    assert module_symbol.kind is ResolvedSymbolKind.MODULE
    assert module_symbol.symbol_id == module_definition.definition_id
    assert module_symbol.defining_scope_id == module_definition.definition_id

    assert class_symbol.kind is ResolvedSymbolKind.CLASS
    assert class_symbol.symbol_id == class_definition.definition_id
    assert class_symbol.defining_scope_id == module_definition.definition_id

    assert method_symbol.kind is ResolvedSymbolKind.METHOD
    assert method_symbol.symbol_id == method_definition.definition_id
    assert method_symbol.defining_scope_id == class_definition.definition_id

    assert inner_symbol.kind is ResolvedSymbolKind.FUNCTION
    assert inner_symbol.symbol_id == inner_definition.definition_id
    assert inner_symbol.defining_scope_id == method_definition.definition_id

    assert run_symbol.kind is ResolvedSymbolKind.ASYNC_FUNCTION
    assert run_symbol.symbol_id == run_definition.definition_id
    assert run_symbol.defining_scope_id == module_definition.definition_id

    definition_bindings = {
        (
            binding.scope_id,
            binding.name,
            binding.binding_kind,
            binding.symbol_id,
        )
        for binding in program.bindings
        if binding.binding_kind is BindingKind.DEFINITION
    }

    assert (
        module_definition.definition_id,
        "Example",
        BindingKind.DEFINITION,
        class_definition.definition_id,
    ) in definition_bindings
    assert (
        class_definition.definition_id,
        "method",
        BindingKind.DEFINITION,
        method_definition.definition_id,
    ) in definition_bindings
    assert (
        method_definition.definition_id,
        "inner",
        BindingKind.DEFINITION,
        inner_definition.definition_id,
    ) in definition_bindings
    assert (
        module_definition.definition_id,
        "run",
        BindingKind.DEFINITION,
        run_definition.definition_id,
    ) in definition_bindings


def test_bind_syntax_creates_parameter_import_and_assignment_history(
    tmp_path: Path,
) -> None:
    """The binder records parameters, imports, and assignments in the right scope."""
    (tmp_path / "example.py").write_text(
        textwrap.dedent(
            """
            import pkg.mod
            from pkg.base import Base as Alias
            from pkg.types import Thing
            from pkg.star import *

            class Example:
                import pkg.inner as class_mod
                value: int = 1
                value = 2
                other.attr = 3

                def method(self, item: int) -> int:
                    import pkg.local as local_mod
                    item = 4
                    other.attr = 5
                    return item
            """
        ).lstrip()
    )

    syntax = extract_syntax(tmp_path)
    program = bind_syntax(syntax)
    definitions = {
        definition.qualified_name: definition
        for definition in syntax.definitions
        if definition.file_id == "file:example.py"
    }

    module_definition = next(
        definition
        for definition in syntax.definitions
        if definition.file_id == "file:example.py"
        and definition.kind is DefinitionKind.MODULE
    )
    class_definition = definitions["example.Example"]
    method_definition = definitions["example.Example.method"]

    module_import_bindings = [
        binding
        for binding in program.bindings
        if binding.scope_id == module_definition.definition_id
        and binding.binding_kind is BindingKind.IMPORT
    ]
    assert [
        (binding.name, binding.symbol_id) for binding in module_import_bindings
    ] == [
        ("pkg", "import:example.py:1:0:1:pkg.mod:_"),
        ("Alias", "import:example.py:2:0:1:Base:Alias"),
        ("Thing", "import:example.py:3:0:1:Thing:_"),
    ]
    assert all(
        program.resolved_symbols[binding.symbol_id].kind
        is ResolvedSymbolKind.IMPORTED_NAME
        for binding in module_import_bindings
    )

    class_import_binding = next(
        binding
        for binding in program.bindings
        if binding.scope_id == class_definition.definition_id
        and binding.name == "class_mod"
    )
    method_import_binding = next(
        binding
        for binding in program.bindings
        if binding.scope_id == method_definition.definition_id
        and binding.name == "local_mod"
    )
    assert class_import_binding.binding_kind is BindingKind.IMPORT
    assert method_import_binding.binding_kind is BindingKind.IMPORT

    method_parameter_bindings = [
        binding
        for binding in program.bindings
        if binding.scope_id == method_definition.definition_id
        and binding.binding_kind is BindingKind.PARAMETER
    ]
    assert [binding.name for binding in method_parameter_bindings] == ["self", "item"]
    assert all(
        program.resolved_symbols[binding.symbol_id].kind is ResolvedSymbolKind.PARAMETER
        for binding in method_parameter_bindings
    )

    class_attribute_bindings = [
        binding
        for binding in program.bindings
        if binding.scope_id == class_definition.definition_id
        and binding.binding_kind is BindingKind.CLASS_ATTRIBUTE
    ]
    assert [binding.name for binding in class_attribute_bindings] == ["value", "value"]
    assert (
        class_attribute_bindings[0].symbol_id != class_attribute_bindings[1].symbol_id
    )
    assert all(
        program.resolved_symbols[binding.symbol_id].kind is ResolvedSymbolKind.ATTRIBUTE
        for binding in class_attribute_bindings
    )

    item_history = [
        binding
        for binding in program.bindings
        if binding.scope_id == method_definition.definition_id
        and binding.name == "item"
    ]
    assert [binding.binding_kind for binding in item_history] == [
        BindingKind.PARAMETER,
        BindingKind.ASSIGNMENT,
    ]
    assert (
        program.resolved_symbols[item_history[1].symbol_id].kind
        is ResolvedSymbolKind.LOCAL
    )

    assert not any(binding.name == "*" for binding in program.bindings)
    assert not any(binding.name == "other.attr" for binding in program.bindings)


def test_bind_syntax_excludes_parse_error_files_from_semantic_facts(
    tmp_path: Path,
) -> None:
    """Files with parse errors do not contribute binder-owned semantic facts."""
    (tmp_path / "good.py").write_text("VALUE = 1\n")
    (tmp_path / "bad.py").write_text("def broken(:\n    pass\n")

    syntax = extract_syntax(tmp_path)
    program = bind_syntax(syntax)

    assert any(
        diagnostic.code is SyntaxDiagnosticCode.PARSE_ERROR
        and diagnostic.file_id == "file:bad.py"
        for diagnostic in syntax.diagnostics
    )
    assert all(
        symbol.file_id != "file:bad.py" for symbol in program.resolved_symbols.values()
    )
    assert all(binding.site.file_path != "bad.py" for binding in program.bindings)
    assert any(
        symbol.file_id == "file:good.py" for symbol in program.resolved_symbols.values()
    )

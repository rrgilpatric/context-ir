"""Parser tests for the semantic-first syntax API and legacy graph API."""

from __future__ import annotations

import textwrap
from pathlib import Path

from context_ir.parser import (
    extract_syntax,
    extract_syntax_file,
    parse_file,
    parse_repository,
)
from context_ir.semantic_types import (
    DefinitionKind,
    ImportKind,
    ParameterKind,
    ReferenceContext,
    SourceSpan,
    SyntaxDiagnosticCode,
    SyntaxProgram,
)
from context_ir.types import EdgeKind, SymbolKind

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repo"
MODELS_PY = FIXTURES / "mypackage" / "models.py"
UTILS_PY = FIXTURES / "mypackage" / "utils.py"
MAIN_PY = FIXTURES / "main.py"


# ---------------------------------------------------------------------------
# Semantic-first syntax extraction tests
# ---------------------------------------------------------------------------


def test_extract_syntax_returns_syntax_program() -> None:
    """Repository syntax extraction returns the semantic-baseline contract type."""
    syntax = extract_syntax(FIXTURES)

    assert isinstance(syntax, SyntaxProgram)
    assert syntax.repo_root == FIXTURES
    assert set(syntax.source_files) == {
        "file:main.py",
        "file:mypackage/__init__.py",
        "file:mypackage/models.py",
        "file:mypackage/utils.py",
    }

    module_definitions = {
        definition.qualified_name
        for definition in syntax.definitions
        if definition.kind is DefinitionKind.MODULE
    }
    assert module_definitions == {
        "main",
        "mypackage",
        "mypackage.models",
        "mypackage.utils",
    }


def test_extract_syntax_captures_raw_facts_and_decorator_spans(
    tmp_path: Path,
) -> None:
    """Syntax extraction captures raw facts without inventing semantic proof."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "base.py").write_text("class Base:\n    pass\n")
    (pkg / "local.py").write_text("def helper(value: int) -> int:\n    return value\n")
    (pkg / "star.py").write_text("EXPORTED = 1\n")
    (pkg / "mod.py").write_text(
        "def factory(value: object) -> object:\n    return value\n"
    )
    example_py = pkg / "example.py"
    example_py.write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass
            from pkg.base import Base as BaseAlias
            from .local import helper as local_helper
            from pkg.star import *
            import importlib
            import pkg.mod as mod

            @dataclass
            class Example(BaseAlias):
                size: int = 1

                @classmethod
                def make(cls) -> "Example":
                    instance = cls()
                    instance.value = local_helper(instance.value)
                    return instance

            async def run(target: object) -> object:
                loaded = importlib.import_module("pkg.dynamic")
                dynamic = __import__("pkg.dynamic")
                exec("x = 1")
                return mod.factory(target).result
            """
        ).lstrip()
    )

    syntax = extract_syntax(tmp_path)
    file_id = "file:pkg/example.py"

    assert isinstance(syntax, SyntaxProgram)
    assert file_id in syntax.source_files

    definitions = {
        definition.qualified_name: definition
        for definition in syntax.definitions
        if definition.file_id == file_id
    }
    example_definition = definitions["pkg.example.Example"]
    make_definition = definitions["pkg.example.Example.make"]
    run_definition = definitions["pkg.example.run"]

    assert example_definition.kind is DefinitionKind.CLASS
    assert make_definition.kind is DefinitionKind.METHOD
    assert run_definition.kind is DefinitionKind.ASYNC_FUNCTION
    assert make_definition.parent_definition_id == example_definition.definition_id
    assert example_definition.site.span.start_line == 8
    assert example_definition.site.span.end_line == 16
    assert make_definition.site.span.start_line == 12
    assert make_definition.site.span.end_line == 16

    decorators = [
        decorator
        for decorator in syntax.decorators
        if decorator.owner_definition_id
        in {example_definition.definition_id, make_definition.definition_id}
    ]
    assert {decorator.expression_text for decorator in decorators} == {
        "dataclass",
        "classmethod",
    }

    base_expressions = [
        base_expression
        for base_expression in syntax.base_expressions
        if base_expression.owner_definition_id == example_definition.definition_id
    ]
    assert [
        base_expression.expression_text for base_expression in base_expressions
    ] == ["BaseAlias"]

    assignments = {
        assignment.target_text: assignment
        for assignment in syntax.assignments
        if assignment.scope_id
        in {
            example_definition.definition_id,
            make_definition.definition_id,
            run_definition.definition_id,
        }
    }
    assert assignments["size"].annotation_text == "int"
    assert assignments["instance"].value_text == "cls()"
    assert assignments["instance.value"].value_text == "local_helper(instance.value)"
    assert assignments["loaded"].value_text == "importlib.import_module('pkg.dynamic')"

    call_texts = {
        call_site.callee_text
        for call_site in syntax.call_sites
        if call_site.enclosing_scope_id
        in {make_definition.definition_id, run_definition.definition_id}
    }
    assert {
        "cls",
        "local_helper",
        "importlib.import_module",
        "__import__",
        "exec",
        "mod.factory",
    }.issubset(call_texts)

    attribute_sites = {
        (attribute.base_text, attribute.attribute_name, attribute.context)
        for attribute in syntax.attribute_sites
        if attribute.enclosing_scope_id
        in {make_definition.definition_id, run_definition.definition_id}
    }
    assert ("instance", "value", ReferenceContext.STORE) in attribute_sites
    assert (
        "instance",
        "value",
        ReferenceContext.ATTRIBUTE_ACCESS,
    ) in attribute_sites
    assert (
        "importlib",
        "import_module",
        ReferenceContext.ATTRIBUTE_ACCESS,
    ) in attribute_sites
    assert ("mod", "factory", ReferenceContext.ATTRIBUTE_ACCESS) in attribute_sites


def test_extract_syntax_preserves_relative_and_star_import_surfaces(
    tmp_path: Path,
) -> None:
    """Relative and star imports remain explicit syntax facts for later handling."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    example_py = pkg / "example.py"
    example_py.write_text(
        textwrap.dedent(
            """
            from .local import helper as local_helper
            from pkg.star import *
            import pkg.mod as mod
            """
        ).lstrip()
    )

    syntax = extract_syntax(tmp_path)
    imports = [
        import_fact
        for import_fact in syntax.imports
        if import_fact.file_id == "file:pkg/example.py"
    ]

    assert any(
        import_fact.kind is ImportKind.FROM_IMPORT
        and import_fact.module_name == ".local"
        and import_fact.imported_name == "helper"
        and import_fact.alias == "local_helper"
        and import_fact.is_relative
        for import_fact in imports
    )
    assert any(
        import_fact.kind is ImportKind.STAR_IMPORT
        and import_fact.module_name == "pkg.star"
        and import_fact.imported_name == "*"
        for import_fact in imports
    )
    assert any(
        import_fact.kind is ImportKind.IMPORT
        and import_fact.module_name == "pkg.mod"
        and import_fact.alias == "mod"
        for import_fact in imports
    )


def test_extract_syntax_retains_metaclass_keyword_surface(
    tmp_path: Path,
) -> None:
    """Class ``metaclass=...`` syntax stays explicit instead of being dropped."""
    example_py = tmp_path / "example.py"
    example_py.write_text(
        textwrap.dedent(
            """
            class Base:
                pass

            class Example(Base, metaclass=Meta):
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )

    syntax = extract_syntax(tmp_path)
    example_definition = next(
        definition
        for definition in syntax.definitions
        if definition.qualified_name == "example.Example"
    )
    base_expressions = [
        base_expression
        for base_expression in syntax.base_expressions
        if base_expression.owner_definition_id == example_definition.definition_id
    ]
    metaclass_keywords = [
        metaclass_keyword
        for metaclass_keyword in syntax.metaclass_keywords
        if metaclass_keyword.owner_definition_id == example_definition.definition_id
    ]

    assert [
        base_expression.expression_text for base_expression in base_expressions
    ] == ["Base"]
    assert len(metaclass_keywords) == 1
    assert metaclass_keywords[0].keyword_text == "metaclass=Meta"
    assert metaclass_keywords[0].site.file_path == "example.py"
    assert metaclass_keywords[0].site.snippet == "metaclass=Meta"


def test_extract_syntax_preserves_declared_base_expression_order_for_resolver_contract(
    tmp_path: Path,
) -> None:
    """Base-expression facts stay ordered for resolver ancestry indexing."""
    example_py = tmp_path / "example.py"
    example_py.write_text(
        textwrap.dedent(
            """
            class ZBase:
                pass

            class ABase:
                pass

            class MBase:
                pass

            class Example(ZBase, ABase, MBase, metaclass=Meta):
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )

    syntax = extract_syntax(tmp_path)
    example_definition = next(
        definition
        for definition in syntax.definitions
        if definition.qualified_name == "example.Example"
    )
    base_expressions = [
        base_expression.expression_text
        for base_expression in syntax.base_expressions
        if base_expression.owner_definition_id == example_definition.definition_id
    ]

    assert base_expressions == ["ZBase", "ABase", "MBase"]


def test_extract_syntax_preserves_nested_import_scope_ownership(
    tmp_path: Path,
) -> None:
    """Import facts retain the lexical scope that owns the binding."""
    example_py = tmp_path / "example.py"
    example_py.write_text(
        textwrap.dedent(
            """
            class Example:
                import pkg.inner as class_mod

                def method(self) -> None:
                    import pkg.local as local_mod
            """
        ).lstrip()
    )

    syntax = extract_syntax(tmp_path)
    definitions = {
        definition.qualified_name: definition
        for definition in syntax.definitions
        if definition.file_id == "file:example.py"
    }
    example_definition = definitions["example.Example"]
    method_definition = definitions["example.Example.method"]

    class_import = next(
        import_fact
        for import_fact in syntax.imports
        if import_fact.alias == "class_mod"
    )
    method_import = next(
        import_fact
        for import_fact in syntax.imports
        if import_fact.alias == "local_mod"
    )

    assert class_import.scope_id == example_definition.definition_id
    assert method_import.scope_id == method_definition.definition_id


def test_extract_syntax_surfaces_parse_failures_explicitly(tmp_path: Path) -> None:
    """Syntax-invalid files emit an explicit parse-failure diagnostic."""
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken(:\n    pass\n")

    syntax = extract_syntax_file(bad_file, tmp_path)
    file_id = "file:bad.py"

    assert file_id in syntax.source_files
    assert len(syntax.diagnostics) == 1

    diagnostic = syntax.diagnostics[0]
    assert diagnostic.file_id == file_id
    assert diagnostic.code is SyntaxDiagnosticCode.PARSE_ERROR
    assert diagnostic.site.file_path == "bad.py"
    assert diagnostic.site.span.start_line == 1
    assert diagnostic.site.span.end_line == 1
    assert diagnostic.site.snippet == "def broken(:\n"
    assert diagnostic.message

    bad_file_definitions = [
        definition for definition in syntax.definitions if definition.file_id == file_id
    ]
    assert [definition.kind for definition in bad_file_definitions] == [
        DefinitionKind.MODULE
    ]


def test_extract_syntax_uses_full_file_span_for_trailing_newline(
    tmp_path: Path,
) -> None:
    """Module spans and snippets cover the full real file contents."""
    module_file = tmp_path / "sample.py"
    source_text = "VALUE = 1\nprint(VALUE)\n"
    module_file.write_text(source_text)

    syntax = extract_syntax_file(module_file, tmp_path)
    module_definition = next(
        definition
        for definition in syntax.definitions
        if definition.file_id == "file:sample.py"
        and definition.kind is DefinitionKind.MODULE
    )

    assert module_definition.site.span == SourceSpan(
        start_line=1,
        start_column=0,
        end_line=2,
        end_column=len("print(VALUE)\n"),
    )
    assert module_definition.site.snippet == source_text


def test_extract_syntax_emits_parameter_facts_for_supported_parameter_kinds(
    tmp_path: Path,
) -> None:
    """Syntax extraction preserves parameter kinds, order, defaults, and sites."""
    example_py = tmp_path / "example.py"
    example_py.write_text(
        textwrap.dedent(
            """
            class Example:
                def method(self, value: int) -> int:
                    return value

                @classmethod
                def build(cls, seed: int = 1) -> "Example":
                    return cls()

            async def run(first, /, second: int = 2, *items: str, flag, """
            """mode: str = "fast", **extras: object) -> None:
                return None
            """
        ).lstrip()
    )

    syntax = extract_syntax(tmp_path)
    definitions = {
        definition.qualified_name: definition
        for definition in syntax.definitions
        if definition.file_id == "file:example.py"
    }

    method_definition = definitions["example.Example.method"]
    build_definition = definitions["example.Example.build"]
    run_definition = definitions["example.run"]

    parameters_by_owner = {}
    for parameter in syntax.parameters:
        parameters_by_owner.setdefault(parameter.owner_definition_id, []).append(
            parameter
        )

    method_parameters = parameters_by_owner[method_definition.definition_id]
    build_parameters = parameters_by_owner[build_definition.definition_id]
    run_parameters = parameters_by_owner[run_definition.definition_id]

    assert [
        (parameter.name, parameter.kind, parameter.ordinal, parameter.annotation_text)
        for parameter in method_parameters
    ] == [
        ("self", ParameterKind.POSITIONAL_OR_KEYWORD, 0, None),
        ("value", ParameterKind.POSITIONAL_OR_KEYWORD, 1, "int"),
    ]
    assert [parameter.site.snippet for parameter in method_parameters] == [
        "self",
        "value",
    ]

    assert [
        (
            parameter.name,
            parameter.kind,
            parameter.ordinal,
            parameter.has_default,
            parameter.default_value_text,
        )
        for parameter in build_parameters
    ] == [
        ("cls", ParameterKind.POSITIONAL_OR_KEYWORD, 0, False, None),
        ("seed", ParameterKind.POSITIONAL_OR_KEYWORD, 1, True, "1"),
    ]
    assert [parameter.site.snippet for parameter in build_parameters] == [
        "cls",
        "seed",
    ]

    assert [
        (
            parameter.name,
            parameter.kind,
            parameter.ordinal,
            parameter.annotation_text,
            parameter.has_default,
            parameter.default_value_text,
        )
        for parameter in run_parameters
    ] == [
        ("first", ParameterKind.POSITIONAL_ONLY, 0, None, False, None),
        ("second", ParameterKind.POSITIONAL_OR_KEYWORD, 1, "int", True, "2"),
        ("items", ParameterKind.VARARG, 2, "str", False, None),
        ("flag", ParameterKind.KEYWORD_ONLY, 3, None, False, None),
        ("mode", ParameterKind.KEYWORD_ONLY, 4, "str", True, "'fast'"),
        ("extras", ParameterKind.KWARGS, 5, "object", False, None),
    ]

    first_parameter = run_parameters[0]
    vararg_parameter = run_parameters[2]
    kwargs_parameter = run_parameters[5]

    assert first_parameter.site.file_path == "example.py"
    assert first_parameter.site.span.start_line == 9
    assert first_parameter.site.span.end_line == 9
    assert first_parameter.site.snippet == "first"
    assert (
        first_parameter.site.span.end_column - first_parameter.site.span.start_column
        == 5
    )

    assert vararg_parameter.site.snippet == "items"
    assert vararg_parameter.site.span.start_line == 9
    assert kwargs_parameter.site.snippet == "extras"
    assert kwargs_parameter.site.span.start_line == 9


# ---------------------------------------------------------------------------
# Single-file tests
# ---------------------------------------------------------------------------


def test_parse_single_file_extracts_functions() -> None:
    """Parse a file with functions, verify FUNCTION nodes with correct metadata."""
    graph = parse_file(MODELS_PY, FIXTURES)
    funcs = {nid: n for nid, n in graph.nodes.items() if n.kind == SymbolKind.FUNCTION}
    assert "mypackage/models.py::check_length" in funcs
    assert "mypackage/models.py::validate_name" in funcs

    vn = funcs["mypackage/models.py::validate_name"]
    assert vn.name == "validate_name"
    assert vn.kind == SymbolKind.FUNCTION
    assert vn.file_path == "mypackage/models.py"
    assert vn.start_line > 0
    assert vn.end_line >= vn.start_line


def test_parse_single_file_extracts_classes_and_methods() -> None:
    """Verify CLASS and METHOD nodes, METHOD parent_id points to CLASS."""
    graph = parse_file(MODELS_PY, FIXTURES)

    assert "mypackage/models.py::User" in graph.nodes
    user_cls = graph.nodes["mypackage/models.py::User"]
    assert user_cls.kind == SymbolKind.CLASS

    init_id = "mypackage/models.py::User.__init__"
    display_id = "mypackage/models.py::User.display_name"
    assert init_id in graph.nodes
    assert display_id in graph.nodes

    init_method = graph.nodes[init_id]
    assert init_method.kind == SymbolKind.METHOD
    assert init_method.parent_id == "mypackage/models.py::User"

    display_method = graph.nodes[display_id]
    assert display_method.kind == SymbolKind.METHOD
    assert display_method.parent_id == "mypackage/models.py::User"


def test_parse_single_file_extracts_constants() -> None:
    """Verify UPPER_SNAKE assignments become CONSTANT nodes."""
    graph = parse_file(MODELS_PY, FIXTURES)
    constants = {
        nid: n for nid, n in graph.nodes.items() if n.kind == SymbolKind.CONSTANT
    }
    assert "mypackage/models.py::MAX_NAME_LENGTH" in constants
    assert "mypackage/models.py::DEFAULT_ROLE" in constants

    max_len = constants["mypackage/models.py::MAX_NAME_LENGTH"]
    assert max_len.name == "MAX_NAME_LENGTH"
    assert max_len.file_path == "mypackage/models.py"


def test_parse_single_file_extracts_imports() -> None:
    """Verify import statements become IMPORT nodes."""
    graph = parse_file(MODELS_PY, FIXTURES)
    imports = {nid: n for nid, n in graph.nodes.items() if n.kind == SymbolKind.IMPORT}
    assert len(imports) >= 1
    # models.py has "import os" on line 3.
    import_node = imports.get("mypackage/models.py::import:3")
    assert import_node is not None
    assert import_node.name == "os"


def test_parse_file_creates_file_node() -> None:
    """Verify FILE node exists with correct metadata."""
    graph = parse_file(MODELS_PY, FIXTURES)
    file_id = "file:mypackage/models.py"
    assert file_id in graph.nodes

    file_node = graph.nodes[file_id]
    assert file_node.kind == SymbolKind.FILE
    assert file_node.name == "models"
    assert file_node.file_path == "mypackage/models.py"
    assert file_node.start_line == 1
    assert file_node.end_line > 1


def test_defines_edges() -> None:
    """Verify DEFINES edges from FILE to top-level symbols, CLASS to methods."""
    graph = parse_file(MODELS_PY, FIXTURES)
    defines = [e for e in graph.edges if e.kind == EdgeKind.DEFINES]

    file_id = "file:mypackage/models.py"
    # FILE -> top-level symbols.
    file_defines = {e.target_id for e in defines if e.source_id == file_id}
    assert "mypackage/models.py::User" in file_defines
    assert "mypackage/models.py::validate_name" in file_defines
    assert "mypackage/models.py::MAX_NAME_LENGTH" in file_defines
    assert "mypackage/models.py::check_length" in file_defines

    # CLASS -> methods.
    class_id = "mypackage/models.py::User"
    class_defines = {e.target_id for e in defines if e.source_id == class_id}
    assert "mypackage/models.py::User.__init__" in class_defines
    assert "mypackage/models.py::User.display_name" in class_defines


def test_calls_edges() -> None:
    """Verify CALLS edges when one function calls another."""
    graph = parse_file(MODELS_PY, FIXTURES)
    calls = [e for e in graph.edges if e.kind == EdgeKind.CALLS]

    # validate_name calls check_length.
    caller_target_pairs = {(e.source_id, e.target_id) for e in calls}
    assert (
        "mypackage/models.py::validate_name",
        "mypackage/models.py::check_length",
    ) in caller_target_pairs


def test_calls_edges_include_same_class_self_attribute_calls(tmp_path: Path) -> None:
    """Method calls on self should resolve to same-class METHOD targets."""
    worker_file = tmp_path / "worker.py"
    worker_file.write_text(
        textwrap.dedent(
            """
            class Worker:
                def run(self) -> int:
                    return self.helper()

                def helper(self) -> int:
                    return 7
            """
        ).lstrip()
    )

    graph = parse_file(worker_file, tmp_path)
    caller_target_pairs = {
        (edge.source_id, edge.target_id)
        for edge in graph.edges
        if edge.kind == EdgeKind.CALLS
    }

    assert ("worker.py::Worker.run", "worker.py::Worker.helper") in caller_target_pairs


def test_imports_edges() -> None:
    """Verify IMPORTS edges from import nodes."""
    graph = parse_repository(FIXTURES)
    imports_edges = [e for e in graph.edges if e.kind == EdgeKind.IMPORTS]

    # utils.py imports from mypackage.models -- should resolve.
    sources = {e.source_id for e in imports_edges}
    assert "mypackage/utils.py::import:3" in sources

    # Check that the target is the models file or a symbol in it.
    utils_import_targets = {
        e.target_id
        for e in imports_edges
        if e.source_id == "mypackage/utils.py::import:3"
    }
    assert "file:mypackage/models.py" in utils_import_targets


# ---------------------------------------------------------------------------
# Repository-level tests
# ---------------------------------------------------------------------------


def test_parse_repository_creates_module_nodes() -> None:
    """Verify MODULE nodes for packages with __init__.py."""
    graph = parse_repository(FIXTURES)
    modules = {nid: n for nid, n in graph.nodes.items() if n.kind == SymbolKind.MODULE}
    assert "module:mypackage" in modules
    mod = modules["module:mypackage"]
    assert mod.name == "mypackage"
    assert mod.file_path == "mypackage"
    assert mod.start_line == 0
    assert mod.end_line == 0


def test_parse_repository_cross_file_resolution() -> None:
    """Verify edges between symbols in different files."""
    graph = parse_repository(FIXTURES)
    imports_edges = [e for e in graph.edges if e.kind == EdgeKind.IMPORTS]

    # main.py imports from mypackage.models -- should have IMPORTS edge
    # to the models file or User symbol.
    main_import_targets: set[str] = set()
    for e in imports_edges:
        if e.source_id.startswith("main.py::import:"):
            main_import_targets.add(e.target_id)

    assert "file:mypackage/models.py" in main_import_targets or any(
        t.startswith("mypackage/models.py::") for t in main_import_targets
    )


def test_nested_class_ids_preserve_full_enclosing_path(tmp_path: Path) -> None:
    """Nested class and method IDs should include the full enclosing class path."""
    nested_file = tmp_path / "nested.py"
    nested_file.write_text(
        textwrap.dedent(
            """
            class OuterA:
                class Inner:
                    def ping(self) -> None:
                        pass

            class OuterB:
                class Inner:
                    def ping(self) -> None:
                        pass
            """
        ).lstrip()
    )

    graph = parse_file(nested_file, tmp_path)

    assert "nested.py::OuterA.Inner" in graph.nodes
    assert "nested.py::OuterA.Inner.ping" in graph.nodes
    assert "nested.py::OuterB.Inner" in graph.nodes
    assert "nested.py::OuterB.Inner.ping" in graph.nodes
    assert "nested.py::Inner" not in graph.nodes
    assert "nested.py::Inner.ping" not in graph.nodes

    outer_a_inner = graph.nodes["nested.py::OuterA.Inner"]
    outer_b_inner = graph.nodes["nested.py::OuterB.Inner"]
    assert outer_a_inner.parent_id == "nested.py::OuterA"
    assert outer_b_inner.parent_id == "nested.py::OuterB"
    assert graph.nodes["nested.py::OuterA.Inner.ping"].parent_id == outer_a_inner.id
    assert graph.nodes["nested.py::OuterB.Inner.ping"].parent_id == outer_b_inner.id


def test_parse_repository_resolves_from_imported_submodule_file(
    tmp_path: Path,
) -> None:
    """Absolute submodule imports should resolve to the submodule file."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "sub.py").write_text("VALUE = 1\n")
    (tmp_path / "consumer.py").write_text("from pkg import sub\n")

    graph = parse_repository(tmp_path)
    import_targets = {
        edge.target_id
        for edge in graph.edges
        if edge.kind == EdgeKind.IMPORTS and edge.source_id == "consumer.py::import:1"
    }

    assert "file:pkg/sub.py" in import_targets
    assert "file:pkg/__init__.py" not in import_targets


def test_parse_repository_resolves_multiple_absolute_import_modules(
    tmp_path: Path,
) -> None:
    """Comma-separated absolute imports should resolve each imported module."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "a.py").write_text("A = 1\n")
    (pkg / "b.py").write_text("B = 2\n")
    (tmp_path / "consumer.py").write_text("import pkg.a, pkg.b\n")

    graph = parse_repository(tmp_path)
    import_targets = {
        edge.target_id
        for edge in graph.edges
        if edge.kind == EdgeKind.IMPORTS and edge.source_id == "consumer.py::import:1"
    }

    assert import_targets == {"file:pkg/a.py", "file:pkg/b.py"}


def test_decorated_definitions_include_decorator_lines_in_spans(
    tmp_path: Path,
) -> None:
    """Decorator lines should be part of the recorded symbol span."""
    decorated_file = tmp_path / "decorated.py"
    decorated_file.write_text(
        textwrap.dedent(
            """
            @wrap
            @other(1)
            def decorated() -> None:
                pass

            class Box:
                @classmethod
                def make(cls) -> "Box":
                    return cls()
            """
        ).lstrip()
    )

    graph = parse_file(decorated_file, tmp_path)

    assert graph.nodes["decorated.py::decorated"].start_line == 1
    assert graph.nodes["decorated.py::decorated"].end_line == 4
    assert graph.nodes["decorated.py::Box.make"].start_line == 7
    assert graph.nodes["decorated.py::Box.make"].end_line == 9


# ---------------------------------------------------------------------------
# Consistency and edge-case tests
# ---------------------------------------------------------------------------


def test_parent_id_consistency() -> None:
    """All non-FILE/MODULE nodes have parent_id set and pointing to existing nodes."""
    graph = parse_repository(FIXTURES)
    for node_id, node in graph.nodes.items():
        if node.kind not in (SymbolKind.FILE, SymbolKind.MODULE):
            assert node.parent_id is not None, (
                f"Node {node_id} ({node.kind}) has no parent_id"
            )
        if node.parent_id is not None:
            assert node.parent_id in graph.nodes, (
                f"Node {node_id} parent_id={node.parent_id} not in graph"
            )


def test_node_id_uniqueness() -> None:
    """All node IDs in the graph are unique."""
    graph = parse_repository(FIXTURES)
    # dict keys are unique by definition, but verify count matches.
    ids = list(graph.nodes.keys())
    assert len(ids) == len(set(ids))


def test_empty_file(tmp_path: Path) -> None:
    """Parser handles an empty .py file without crashing."""
    empty_file = tmp_path / "empty.py"
    empty_file.write_text("")
    graph = parse_file(empty_file, tmp_path)
    assert "file:empty.py" in graph.nodes
    file_node = graph.nodes["file:empty.py"]
    assert file_node.kind == SymbolKind.FILE


def test_syntax_error_file(tmp_path: Path) -> None:
    """Parser handles a file with syntax errors gracefully (does not crash)."""
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def foo(:\n    pass\n")
    graph = parse_file(bad_file, tmp_path)
    # Should not crash. May produce partial results or just a FILE node.
    assert "file:bad.py" in graph.nodes

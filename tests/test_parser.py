"""Comprehensive tests for the tree-sitter-based symbol graph parser."""

from __future__ import annotations

from pathlib import Path

from context_ir.parser import parse_file, parse_repository
from context_ir.types import EdgeKind, SymbolKind

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repo"
MODELS_PY = FIXTURES / "mypackage" / "models.py"
UTILS_PY = FIXTURES / "mypackage" / "utils.py"
MAIN_PY = FIXTURES / "main.py"


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

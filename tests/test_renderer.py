"""Comprehensive tests for the view renderer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_ir.parser import parse_repository
from context_ir.renderer import render
from context_ir.types import SymbolGraph, SymbolKind, SymbolNode, ViewTier

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repo"


@pytest.fixture()
def graph() -> SymbolGraph:
    """Parse the full fixture repository into a symbol graph."""
    return parse_repository(FIXTURES)


# ---------------------------------------------------------------------------
# OMIT tier
# ---------------------------------------------------------------------------


def test_omit_returns_reference_id(graph: SymbolGraph) -> None:
    """OMIT tier for a FUNCTION node returns content with the node's ID."""
    view = render("mypackage/models.py::validate_name", ViewTier.OMIT, graph, FIXTURES)
    assert view.tier == ViewTier.OMIT
    assert view.unit_id == "mypackage/models.py::validate_name"
    assert "mypackage/models.py::validate_name" in view.content
    assert view.content.startswith("[ref:")
    assert view.token_cost > 0


# ---------------------------------------------------------------------------
# SUMMARY tier
# ---------------------------------------------------------------------------


def test_summary_function(graph: SymbolGraph) -> None:
    """SUMMARY for a FUNCTION includes the signature and docstring first line."""
    view = render(
        "mypackage/models.py::validate_name", ViewTier.SUMMARY, graph, FIXTURES
    )
    assert view.tier == ViewTier.SUMMARY
    assert "def validate_name" in view.content
    assert "name: str" in view.content
    assert "bool" in view.content
    assert "Check whether a name is valid" in view.content
    assert " -- " in view.content


def test_summary_class(graph: SymbolGraph) -> None:
    """SUMMARY for a CLASS includes class name and method count."""
    view = render("mypackage/models.py::User", ViewTier.SUMMARY, graph, FIXTURES)
    assert view.tier == ViewTier.SUMMARY
    assert "class User" in view.content
    assert "2 methods" in view.content
    assert "A user in the system" in view.content


def test_summary_constant(graph: SymbolGraph) -> None:
    """SUMMARY for a CONSTANT includes the assignment."""
    view = render(
        "mypackage/models.py::MAX_NAME_LENGTH", ViewTier.SUMMARY, graph, FIXTURES
    )
    assert view.tier == ViewTier.SUMMARY
    assert "MAX_NAME_LENGTH" in view.content
    assert "128" in view.content


def test_summary_file(graph: SymbolGraph) -> None:
    """SUMMARY for a FILE includes filename and symbol count."""
    view = render("file:mypackage/models.py", ViewTier.SUMMARY, graph, FIXTURES)
    assert view.tier == ViewTier.SUMMARY
    assert "models.py" in view.content
    assert "1 class" in view.content
    assert "2 functions" in view.content
    assert "constant" in view.content


# ---------------------------------------------------------------------------
# STUB tier
# ---------------------------------------------------------------------------


def test_stub_function(graph: SymbolGraph) -> None:
    """STUB for a FUNCTION has signature with ... body, no implementation."""
    view = render("mypackage/models.py::validate_name", ViewTier.STUB, graph, FIXTURES)
    assert view.tier == ViewTier.STUB
    assert "def validate_name" in view.content
    assert "..." in view.content
    # Should NOT contain implementation details
    assert "check_length" not in view.content
    assert "strip" not in view.content


def test_stub_class(graph: SymbolGraph) -> None:
    """STUB for a CLASS has class line + method signatures with ... bodies."""
    view = render("mypackage/models.py::User", ViewTier.STUB, graph, FIXTURES)
    assert view.tier == ViewTier.STUB
    assert "class User:" in view.content
    assert "def __init__" in view.content
    assert "def display_name" in view.content
    assert "..." in view.content
    # Should NOT contain method implementations
    assert "self.name = name" not in view.content


def test_stub_method(graph: SymbolGraph) -> None:
    """STUB for a METHOD has signature with ... body."""
    view = render(
        "mypackage/models.py::User.display_name", ViewTier.STUB, graph, FIXTURES
    )
    assert view.tier == ViewTier.STUB
    assert "def display_name" in view.content
    assert "..." in view.content
    assert "self.name" not in view.content


# ---------------------------------------------------------------------------
# FULL tier
# ---------------------------------------------------------------------------


def test_full_function(graph: SymbolGraph) -> None:
    """FULL for a FUNCTION matches the source lines between start_line and end_line."""
    view = render("mypackage/models.py::validate_name", ViewTier.FULL, graph, FIXTURES)
    assert view.tier == ViewTier.FULL
    assert "def validate_name" in view.content
    assert "check_length" in view.content
    assert "name.strip()" in view.content
    # Verify it matches the actual source
    node = graph.nodes["mypackage/models.py::validate_name"]
    source_file = FIXTURES / node.file_path
    lines = source_file.read_text().splitlines(keepends=True)
    expected = "".join(lines[node.start_line - 1 : node.end_line])
    assert view.content == expected


def test_full_file(graph: SymbolGraph) -> None:
    """FULL for a FILE returns the entire file content."""
    view = render("file:mypackage/models.py", ViewTier.FULL, graph, FIXTURES)
    assert view.tier == ViewTier.FULL
    expected = (FIXTURES / "mypackage" / "models.py").read_text()
    assert view.content == expected


# ---------------------------------------------------------------------------
# SLICE tier
# ---------------------------------------------------------------------------


def test_slice_includes_called_function_stubs(graph: SymbolGraph) -> None:
    """SLICE for a function that calls another includes the callee's stub."""
    view = render("mypackage/models.py::validate_name", ViewTier.SLICE, graph, FIXTURES)
    assert view.tier == ViewTier.SLICE
    # validate_name calls check_length -- should have its stub
    assert "# Referenced signatures" in view.content
    assert "def check_length" in view.content
    # Full source should also be present
    assert "# Source" in view.content
    assert "def validate_name" in view.content
    assert "name.strip()" in view.content


def test_slice_includes_referenced_constants(graph: SymbolGraph) -> None:
    """SLICE for a function that uses a constant includes the constant."""
    view = render("mypackage/models.py::check_length", ViewTier.SLICE, graph, FIXTURES)
    assert view.tier == ViewTier.SLICE
    assert "# Constants" in view.content
    assert "MAX_NAME_LENGTH" in view.content
    assert "128" in view.content


def test_slice_includes_relevant_imports(graph: SymbolGraph) -> None:
    """SLICE for a function includes the imports its body depends on."""
    view = render("mypackage/utils.py::format_name", ViewTier.SLICE, graph, FIXTURES)
    assert view.tier == ViewTier.SLICE
    assert "# Imports" in view.content
    assert "from mypackage.models import" in view.content


def test_slice_omits_unrelated_symbols(graph: SymbolGraph) -> None:
    """SLICE does NOT include symbols the function doesn't reference."""
    view = render("mypackage/models.py::validate_name", ViewTier.SLICE, graph, FIXTURES)
    # validate_name does not reference User, DEFAULT_ROLE, or the os import
    assert "DEFAULT_ROLE" not in view.content
    assert "class User" not in view.content
    assert "import os" not in view.content


# ---------------------------------------------------------------------------
# Token cost properties
# ---------------------------------------------------------------------------


def test_token_cost_ordering(graph: SymbolGraph) -> None:
    """For the same symbol, OMIT < SUMMARY < STUB < FULL in token cost."""
    # Use the User class where the ordering naturally holds:
    # OMIT is a short ref, SUMMARY is one line, STUB has method sigs,
    # FULL has the entire class body.
    node_id = "mypackage/models.py::User"
    omit = render(node_id, ViewTier.OMIT, graph, FIXTURES)
    summary = render(node_id, ViewTier.SUMMARY, graph, FIXTURES)
    stub = render(node_id, ViewTier.STUB, graph, FIXTURES)
    full = render(node_id, ViewTier.FULL, graph, FIXTURES)
    assert omit.token_cost < summary.token_cost
    assert summary.token_cost < stub.token_cost
    assert stub.token_cost < full.token_cost


def test_token_cost_positive(graph: SymbolGraph) -> None:
    """All tiers produce positive token_cost."""
    node_id = "mypackage/models.py::validate_name"
    for tier in ViewTier:
        view = render(node_id, tier, graph, FIXTURES)
        assert view.token_cost > 0, f"Tier {tier} produced non-positive cost"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_unknown_node_id_raises(graph: SymbolGraph) -> None:
    """Render with a nonexistent node_id raises KeyError."""
    with pytest.raises(KeyError):
        render("nonexistent::symbol", ViewTier.FULL, graph, FIXTURES)


def test_missing_source_file(graph: SymbolGraph) -> None:
    """Render handles a node whose source file doesn't exist on disk."""
    fake_node = SymbolNode(
        id="ghost/missing.py::phantom",
        name="phantom",
        kind=SymbolKind.FUNCTION,
        file_path="ghost/missing.py",
        start_line=1,
        end_line=5,
    )
    graph.nodes[fake_node.id] = fake_node

    view = render(fake_node.id, ViewTier.FULL, graph, FIXTURES)
    assert "source unavailable" in view.content
    assert view.token_cost > 0

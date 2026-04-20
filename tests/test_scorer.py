"""Comprehensive tests for the scoring engine."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

import context_ir.scorer as scorer_module
from context_ir.parser import parse_repository
from context_ir.scorer import _cosine_similarity, score_graph
from context_ir.types import (
    Edge,
    EdgeKind,
    EditSupportScores,
    SymbolGraph,
    SymbolKind,
    SymbolNode,
)

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repo"


# ---------------------------------------------------------------------------
# Fake embedder for deterministic tests
# ---------------------------------------------------------------------------


def _constant_embed(texts: list[str]) -> list[list[float]]:
    """Returns identical vectors so embeddings contribute zero signal."""
    return [[0.5] * 64 for _ in texts]


def _cached_default_model_or_skip() -> object:
    """Return the cached default embedding model or skip offline-only runs."""
    from sentence_transformers import SentenceTransformer

    try:
        return SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except OSError as error:
        pytest.skip(
            "default embedding integration requires a locally cached "
            f"all-MiniLM-L6-v2 model: {error}"
        )


# ---------------------------------------------------------------------------
# Lexical feature tests
# ---------------------------------------------------------------------------


def test_name_match_boosts_p_edit() -> None:
    """Query containing a symbol's exact name gives it higher p_edit."""
    graph = parse_repository(FIXTURES)
    scores = score_graph("validate_name", graph, FIXTURES, embed_fn=_constant_embed)
    assert (
        scores["mypackage/models.py::validate_name"].p_edit
        > scores["mypackage/models.py::User.display_name"].p_edit
    )


def test_path_match_boosts_p_edit() -> None:
    """Query containing a file path gives symbols in that file higher p_edit."""
    graph = parse_repository(FIXTURES)
    scores = score_graph("models.py", graph, FIXTURES, embed_fn=_constant_embed)
    # check_length is in models.py, format_name is in utils.py
    assert (
        scores["mypackage/models.py::check_length"].p_edit
        > scores["mypackage/utils.py::format_name"].p_edit
    )


def test_content_match_boosts_score() -> None:
    """Query terms in a symbol's source body boost that symbol's score."""
    graph = parse_repository(FIXTURES)
    # "Unknown" appears in format_name's source but not in check_length's
    scores = score_graph("Unknown", graph, FIXTURES, embed_fn=_constant_embed)
    assert (
        scores["mypackage/utils.py::format_name"].p_edit
        > scores["mypackage/models.py::check_length"].p_edit
    )


# ---------------------------------------------------------------------------
# Structural prior tests
# ---------------------------------------------------------------------------


def test_structural_prior_test_file() -> None:
    """Symbols in test files get a p_support boost."""
    graph = SymbolGraph()
    # Regular file with a function
    graph.nodes["file:module/core.py"] = SymbolNode(
        id="file:module/core.py",
        name="core",
        kind=SymbolKind.FILE,
        file_path="module/core.py",
        start_line=1,
        end_line=10,
    )
    graph.nodes["module/core.py::process"] = SymbolNode(
        id="module/core.py::process",
        name="process",
        kind=SymbolKind.FUNCTION,
        file_path="module/core.py",
        start_line=1,
        end_line=5,
        parent_id="file:module/core.py",
    )
    graph.edges.append(
        Edge(
            source_id="file:module/core.py",
            target_id="module/core.py::process",
            kind=EdgeKind.DEFINES,
        )
    )
    # Test file with a function
    graph.nodes["file:tests/test_core.py"] = SymbolNode(
        id="file:tests/test_core.py",
        name="test_core",
        kind=SymbolKind.FILE,
        file_path="tests/test_core.py",
        start_line=1,
        end_line=10,
    )
    graph.nodes["tests/test_core.py::test_process"] = SymbolNode(
        id="tests/test_core.py::test_process",
        name="test_process",
        kind=SymbolKind.FUNCTION,
        file_path="tests/test_core.py",
        start_line=1,
        end_line=5,
        parent_id="file:tests/test_core.py",
    )
    graph.edges.append(
        Edge(
            source_id="file:tests/test_core.py",
            target_id="tests/test_core.py::test_process",
            kind=EdgeKind.DEFINES,
        )
    )

    with tempfile.TemporaryDirectory() as tmp:
        scores = score_graph("generic task", graph, Path(tmp), embed_fn=_constant_embed)

    assert (
        scores["tests/test_core.py::test_process"].p_support
        > scores["module/core.py::process"].p_support
    )


# ---------------------------------------------------------------------------
# Graph propagation tests
# ---------------------------------------------------------------------------


def test_graph_propagation_calls() -> None:
    """Called function gets p_support boost from caller with high p_edit."""
    graph = parse_repository(FIXTURES)
    # validate_name calls check_length (intra-file CALLS edge)
    scores = score_graph("validate_name", graph, FIXTURES, embed_fn=_constant_embed)
    # check_length (called by validate_name) should have higher p_support
    # than display_name (not called by validate_name)
    assert (
        scores["mypackage/models.py::check_length"].p_support
        > scores["mypackage/models.py::User.display_name"].p_support
    )


def test_graph_propagation_imports() -> None:
    """Imported targets get p_support boost from high-scoring import nodes."""
    graph = parse_repository(FIXTURES)
    # "mypackage.utils" matches the import node in main.py. Through
    # IMPORTS edges, greet_user (an imported symbol) gets a p_support boost.
    scores = score_graph("mypackage.utils", graph, FIXTURES, embed_fn=_constant_embed)
    # greet_user is a target of the IMPORTS edge from the matching import.
    # GREETING_PREFIX is not a target of any IMPORTS edge.
    assert (
        scores["mypackage/utils.py::greet_user"].p_support
        > scores["mypackage/utils.py::GREETING_PREFIX"].p_support
    )


# ---------------------------------------------------------------------------
# Range and completeness tests
# ---------------------------------------------------------------------------


def test_scores_in_range() -> None:
    """All p_edit and p_support values are in [0.0, 1.0]."""
    graph = parse_repository(FIXTURES)
    scores = score_graph("validate_name", graph, FIXTURES, embed_fn=_constant_embed)
    for node_id, s in scores.items():
        assert 0.0 <= s.p_edit <= 1.0, f"{node_id} p_edit out of range: {s.p_edit}"
        assert 0.0 <= s.p_support <= 1.0, (
            f"{node_id} p_support out of range: {s.p_support}"
        )


def test_all_nodes_scored() -> None:
    """Every node in the graph has an entry in the returned dict."""
    graph = parse_repository(FIXTURES)
    scores = score_graph("test query", graph, FIXTURES, embed_fn=_constant_embed)
    assert len(scores) == len(graph.nodes)
    for node_id in graph.nodes:
        assert node_id in scores, f"Missing score for {node_id}"


def test_empty_query_returns_scores() -> None:
    """Empty query returns scores for all nodes without crashing."""
    graph = parse_repository(FIXTURES)
    scores = score_graph("", graph, FIXTURES, embed_fn=_constant_embed)
    assert len(scores) == len(graph.nodes)
    for s in scores.values():
        assert isinstance(s, EditSupportScores)


# ---------------------------------------------------------------------------
# Score relationship tests
# ---------------------------------------------------------------------------


def test_p_edit_higher_for_direct_match() -> None:
    """A symbol whose name appears in the query has higher p_edit than p_support."""
    graph = parse_repository(FIXTURES)
    # display_name has no incoming CALLS/IMPORTS edges, so propagation
    # does not inflate its p_support beyond the initial combined score.
    scores = score_graph("display_name", graph, FIXTURES, embed_fn=_constant_embed)
    s = scores["mypackage/models.py::User.display_name"]
    assert s.p_edit > s.p_support


# ---------------------------------------------------------------------------
# Embedding function tests
# ---------------------------------------------------------------------------


def test_embed_fn_is_called() -> None:
    """Custom embed_fn is called during scoring."""
    graph = parse_repository(FIXTURES)
    calls: list[list[str]] = []

    def tracking_embed(texts: list[str]) -> list[list[float]]:
        calls.append(texts)
        return [[0.5] * 64 for _ in texts]

    score_graph("test query", graph, FIXTURES, embed_fn=tracking_embed)
    assert len(calls) > 0
    # First text should be the query, rest are symbol profiles
    assert calls[0][0] == "test query"


@pytest.mark.slow
def test_default_embed_integration() -> None:
    """Real sentence-transformers model produces valid scores."""
    graph = parse_repository(FIXTURES)
    cached_model = _cached_default_model_or_skip()
    previous_model = scorer_module._model
    scorer_module._model = cached_model
    try:
        scores = score_graph("fix the validate_name function", graph, FIXTURES)
    finally:
        scorer_module._model = previous_model
    assert len(scores) == len(graph.nodes)
    for s in scores.values():
        assert 0.0 <= s.p_edit <= 1.0
        assert 0.0 <= s.p_support <= 1.0


# ---------------------------------------------------------------------------
# Container and helper tests
# ---------------------------------------------------------------------------


def test_container_node_scored() -> None:
    """FILE and MODULE nodes have scores in the result dict."""
    graph = parse_repository(FIXTURES)
    scores = score_graph("test query", graph, FIXTURES, embed_fn=_constant_embed)
    for node_id, node in graph.nodes.items():
        if node.kind in (SymbolKind.FILE, SymbolKind.MODULE):
            assert node_id in scores, f"Missing score for container {node_id}"
            assert isinstance(scores[node_id], EditSupportScores)


def test_cosine_similarity_helper() -> None:
    """Cosine similarity: identical=1.0, orthogonal=0.0, zero=0.0."""
    # Identical vectors
    assert _cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert _cosine_similarity([0.5, 0.5], [0.5, 0.5]) == pytest.approx(1.0)

    # Orthogonal vectors
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    # Zero vector
    assert _cosine_similarity([0.0, 0.0], [1.0, 0.0]) == pytest.approx(0.0)
    assert _cosine_similarity([1.0, 0.0], [0.0, 0.0]) == pytest.approx(0.0)

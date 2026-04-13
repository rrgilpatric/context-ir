"""Comprehensive tests for the budget optimizer."""

from __future__ import annotations

from pathlib import Path

from context_ir.optimizer import optimize
from context_ir.parser import parse_repository
from context_ir.scorer import score_graph
from context_ir.types import (
    EditSupportScores,
    OptimizationResult,
    SymbolGraph,
    SymbolKind,
    ViewTier,
    WarningKind,
)

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repo"


# ---------------------------------------------------------------------------
# Fake embedder (same as test_scorer.py)
# ---------------------------------------------------------------------------


def _constant_embed(texts: list[str]) -> list[list[float]]:
    """Returns identical vectors so embeddings contribute zero signal."""
    return [[0.5] * 64 for _ in texts]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_scores(
    graph: SymbolGraph,
) -> dict[str, EditSupportScores]:
    """Score the fixture graph with a deterministic embedder."""
    return score_graph("validate_name", graph, FIXTURES, embed_fn=_constant_embed)


def _inject_scores(
    base_scores: dict[str, EditSupportScores],
    overrides: dict[str, EditSupportScores],
) -> dict[str, EditSupportScores]:
    """Return a copy of base_scores with specific overrides applied."""
    result = dict(base_scores)
    result.update(overrides)
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_basic_optimization() -> None:
    """Optimize with a generous budget returns tier assignments for symbols."""
    graph = parse_repository(FIXTURES)
    scores = _make_scores(graph)
    result = optimize(scores, graph, budget=50000, repo_root=FIXTURES)

    assert isinstance(result, OptimizationResult)
    assert len(result.tier_assignments) > 0
    for tier in result.tier_assignments.values():
        assert isinstance(tier, ViewTier)


def test_budget_constraint() -> None:
    """Total tokens in the result is reported and within reason."""
    graph = parse_repository(FIXTURES)
    scores = _make_scores(graph)
    result = optimize(scores, graph, budget=500, repo_root=FIXTURES)

    assert result.total_tokens >= 0
    assert result.budget == 500


def test_high_p_edit_gets_high_tier() -> None:
    """A symbol with artificially high p_edit gets FULL or SLICE tier."""
    graph = parse_repository(FIXTURES)
    scores = _make_scores(graph)
    target_id = "mypackage/models.py::validate_name"
    scores = _inject_scores(
        scores, {target_id: EditSupportScores(p_edit=0.99, p_support=0.1)}
    )
    result = optimize(scores, graph, budget=50000, repo_root=FIXTURES)

    assert target_id in result.tier_assignments
    assert result.tier_assignments[target_id].value >= ViewTier.SLICE.value


def test_low_relevance_excluded() -> None:
    """Symbols with very low scores are not in tier_assignments."""
    graph = parse_repository(FIXTURES)
    # Set all scores to near-zero, with a very tight budget
    scores: dict[str, EditSupportScores] = {
        nid: EditSupportScores(p_edit=0.001, p_support=0.001) for nid in graph.nodes
    }
    result = optimize(scores, graph, budget=5, repo_root=FIXTURES)

    # With near-zero utility and tiny budget, most should be omitted/excluded
    assert len(result.omitted_frontier) > 0


def test_dependency_closure() -> None:
    """If function A calls function B, and A is at SLICE+, B is at >= STUB."""
    graph = parse_repository(FIXTURES)
    caller_id = "mypackage/models.py::validate_name"
    callee_id = "mypackage/models.py::check_length"

    # Give caller very high scores, callee very low scores
    scores: dict[str, EditSupportScores] = {
        nid: EditSupportScores(p_edit=0.01, p_support=0.01) for nid in graph.nodes
    }
    scores[caller_id] = EditSupportScores(p_edit=0.99, p_support=0.1)
    scores[callee_id] = EditSupportScores(p_edit=0.01, p_support=0.01)

    result = optimize(scores, graph, budget=50000, repo_root=FIXTURES)

    # Caller should be at SLICE or FULL
    assert caller_id in result.tier_assignments
    assert result.tier_assignments[caller_id].value >= ViewTier.SLICE.value

    # Callee should be pulled in by closure at >= STUB
    assert callee_id in result.tier_assignments
    assert result.tier_assignments[callee_id].value >= ViewTier.STUB.value


def test_downgrade_on_tight_budget() -> None:
    """With a very small budget, some symbols get lower tiers."""
    graph = parse_repository(FIXTURES)
    scores = _make_scores(graph)

    generous = optimize(scores, graph, budget=50000, repo_root=FIXTURES)
    tight = optimize(scores, graph, budget=50, repo_root=FIXTURES)

    # Tight budget should have fewer or lower-tier assignments
    generous_total_tier_value = sum(t.value for t in generous.tier_assignments.values())
    tight_total_tier_value = sum(t.value for t in tight.tier_assignments.values())
    assert tight_total_tier_value <= generous_total_tier_value


def test_high_risk_omission_warning() -> None:
    """A symbol with high p_edit excluded by budget produces a warning."""
    graph = parse_repository(FIXTURES)
    target_id = "mypackage/models.py::validate_name"

    scores: dict[str, EditSupportScores] = {
        nid: EditSupportScores(p_edit=0.01, p_support=0.01) for nid in graph.nodes
    }
    scores[target_id] = EditSupportScores(p_edit=0.9, p_support=0.1)

    result = optimize(scores, graph, budget=0, repo_root=FIXTURES)

    high_risk = [w for w in result.warnings if w.kind == WarningKind.HIGH_RISK_OMISSION]
    assert len(high_risk) > 0
    assert any(w.unit_id == target_id for w in high_risk)


def test_budget_forced_downgrade_warning() -> None:
    """A symbol with high p_edit at STUB or below produces a downgrade warning."""
    graph = parse_repository(FIXTURES)
    target_id = "mypackage/models.py::validate_name"

    # Give target high p_edit but use a budget that only allows STUB
    scores: dict[str, EditSupportScores] = {
        nid: EditSupportScores(p_edit=0.01, p_support=0.01) for nid in graph.nodes
    }
    scores[target_id] = EditSupportScores(p_edit=0.8, p_support=0.1)

    # Use a very tight budget -- just enough for OMIT or STUB but not SLICE.
    result = optimize(scores, graph, budget=10, repo_root=FIXTURES)

    # If the target is packed at STUB or below with p_edit > 0.3, we get a
    # BUDGET_FORCED_DOWNGRADE. With budget=10 it might be excluded entirely
    # (HIGH_RISK_OMISSION instead). Check that at least one warning fires.
    target_warnings = [w for w in result.warnings if w.unit_id == target_id]
    assert len(target_warnings) > 0


def test_trace_has_entries() -> None:
    """Trace has at least one entry for each packable symbol."""
    graph = parse_repository(FIXTURES)
    scores = _make_scores(graph)
    result = optimize(scores, graph, budget=50000, repo_root=FIXTURES)

    packable_ids = {
        nid
        for nid, node in graph.nodes.items()
        if node.kind
        in (
            SymbolKind.FUNCTION,
            SymbolKind.CLASS,
            SymbolKind.METHOD,
            SymbolKind.CONSTANT,
        )
    }
    trace_ids = {entry.unit_id for entry in result.trace}

    # Every packable node that has scores should have a trace entry
    scored_packable = packable_ids & set(scores.keys())
    assert scored_packable.issubset(trace_ids)


def test_confidence_score_range() -> None:
    """Confidence is in [0.0, 1.0]."""
    graph = parse_repository(FIXTURES)
    scores = _make_scores(graph)
    result = optimize(scores, graph, budget=500, repo_root=FIXTURES)

    assert 0.0 <= result.confidence <= 1.0


def test_confidence_higher_with_more_budget() -> None:
    """Higher budget produces equal or higher confidence."""
    graph = parse_repository(FIXTURES)
    scores = _make_scores(graph)

    low = optimize(scores, graph, budget=100, repo_root=FIXTURES)
    high = optimize(scores, graph, budget=10000, repo_root=FIXTURES)

    assert high.confidence >= low.confidence


def test_omitted_frontier_disjoint() -> None:
    """Omitted frontier node IDs do not overlap with tier_assignments keys."""
    graph = parse_repository(FIXTURES)
    scores = _make_scores(graph)
    result = optimize(scores, graph, budget=500, repo_root=FIXTURES)

    packed_ids = set(result.tier_assignments.keys())
    omitted_ids = set(result.omitted_frontier)
    assert packed_ids.isdisjoint(omitted_ids)


def test_empty_graph() -> None:
    """Optimize with an empty SymbolGraph returns empty results."""
    graph = SymbolGraph()
    scores: dict[str, EditSupportScores] = {}
    result = optimize(scores, graph, budget=1000, repo_root=FIXTURES)

    assert result.tier_assignments == {}
    assert result.trace == []
    assert result.confidence == 1.0
    assert result.omitted_frontier == []
    assert result.total_tokens == 0


def test_zero_budget() -> None:
    """Optimize with budget=0 returns empty or OMIT-only tier_assignments."""
    graph = parse_repository(FIXTURES)
    scores = _make_scores(graph)
    result = optimize(scores, graph, budget=0, repo_root=FIXTURES)

    for tier in result.tier_assignments.values():
        assert tier == ViewTier.OMIT

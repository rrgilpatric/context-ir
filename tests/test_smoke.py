"""Smoke test: verify core types are importable and constructible."""

from context_ir.types import (
    CompileResult,
    CompileTraceEntry,
    CompileWarning,
    DiagnosticResult,
    DowngradeReason,
    Edge,
    EdgeKind,
    EditSupportScores,
    MissEvidence,
    MissKind,
    RecompileResult,
    SymbolGraph,
    SymbolKind,
    SymbolNode,
    UnitView,
    ViewTier,
    WarningKind,
)


def test_symbol_graph_construction() -> None:
    """Symbol nodes, edges, and graph can be constructed."""
    node = SymbolNode(
        id="fn_1",
        name="main",
        kind=SymbolKind.FUNCTION,
        file_path="src/main.py",
        start_line=1,
        end_line=10,
    )
    assert node.name == "main"
    assert node.parent_id is None

    node_with_parent = SymbolNode(
        id="method_1",
        name="run",
        kind=SymbolKind.METHOD,
        file_path="src/main.py",
        start_line=5,
        end_line=8,
        parent_id="class_1",
    )
    assert node_with_parent.parent_id == "class_1"

    edge = Edge(source_id="fn_1", target_id="fn_2", kind=EdgeKind.CALLS)
    assert edge.kind == EdgeKind.CALLS

    graph = SymbolGraph(nodes={"fn_1": node}, edges=[edge])
    assert len(graph.nodes) == 1
    assert len(graph.edges) == 1


def test_view_tier_ordering() -> None:
    """View tiers have the expected integer ordering."""
    assert ViewTier.OMIT.value < ViewTier.SUMMARY.value
    assert ViewTier.SUMMARY.value < ViewTier.STUB.value
    assert ViewTier.STUB.value < ViewTier.SLICE.value
    assert ViewTier.SLICE.value < ViewTier.FULL.value


def test_unit_view_construction() -> None:
    """UnitView can be constructed at any tier."""
    view = UnitView(
        unit_id="fn_1",
        tier=ViewTier.FULL,
        content="def main(): ...",
        token_cost=10,
    )
    assert view.tier == ViewTier.FULL
    assert view.token_cost == 10


def test_scoring() -> None:
    """EditSupportScores holds dual scores."""
    scores = EditSupportScores(p_edit=0.8, p_support=0.3)
    assert scores.p_edit == 0.8
    assert scores.p_support == 0.3


def test_compile_trace_entry() -> None:
    """CompileTraceEntry with and without downgrade reason."""
    entry = CompileTraceEntry(
        unit_id="fn_1",
        edit_score=0.8,
        support_score=0.3,
        chosen_tier=ViewTier.FULL,
        marginal_utility=0.5,
        token_cost=10,
    )
    assert entry.downgrade_reason is None

    downgraded = CompileTraceEntry(
        unit_id="fn_2",
        edit_score=0.2,
        support_score=0.1,
        chosen_tier=ViewTier.STUB,
        marginal_utility=0.05,
        token_cost=3,
        downgrade_reason=DowngradeReason.BUDGET_PRESSURE,
    )
    assert downgraded.downgrade_reason == DowngradeReason.BUDGET_PRESSURE


def test_compile_result() -> None:
    """CompileResult holds all compilation outputs."""
    trace_entry = CompileTraceEntry(
        unit_id="fn_1",
        edit_score=0.8,
        support_score=0.3,
        chosen_tier=ViewTier.FULL,
        marginal_utility=0.5,
        token_cost=10,
    )
    warning = CompileWarning(
        kind=WarningKind.HIGH_RISK_OMISSION,
        unit_id="fn_2",
        message="High-risk omission detected",
        confidence=0.9,
    )
    result = CompileResult(
        document="compiled output",
        trace=[trace_entry],
        warnings=[warning],
        omitted_frontier=["fn_3"],
        confidence=0.85,
        total_tokens=100,
        budget=200,
    )
    assert result.confidence == 0.85
    assert result.total_tokens <= result.budget


def test_miss_evidence_and_diagnostics() -> None:
    """MissEvidence and DiagnosticResult can be constructed."""
    miss = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence="symbol foo not found",
        source="solver",
    )
    assert miss.kind == MissKind.ABSENT_SYMBOL

    diag = DiagnosticResult(
        missed_units=["fn_3"],
        reason="Symbol was outside initial scope",
        recommended_expansions=["fn_3", "fn_4"],
    )
    assert len(diag.recommended_expansions) == 2


def test_recompile_result() -> None:
    """RecompileResult extends CompileResult with recompilation fields."""
    trace_entry = CompileTraceEntry(
        unit_id="fn_1",
        edit_score=0.8,
        support_score=0.3,
        chosen_tier=ViewTier.FULL,
        marginal_utility=0.5,
        token_cost=10,
    )
    recompile = RecompileResult(
        document="recompiled output",
        trace=[trace_entry],
        warnings=[],
        omitted_frontier=[],
        confidence=0.9,
        total_tokens=120,
        budget=200,
        previous_trace=[trace_entry],
        new_units_added=["fn_3"],
        budget_delta=20,
    )
    assert recompile.budget_delta == 20
    assert len(recompile.new_units_added) == 1
    assert isinstance(recompile, CompileResult)


def test_all_enum_values_accessible() -> None:
    """All enum types have the expected members."""
    assert len(SymbolKind) == 7
    assert len(EdgeKind) == 4
    assert len(ViewTier) == 5
    assert len(DowngradeReason) == 4
    assert len(WarningKind) == 4
    assert len(MissKind) == 3

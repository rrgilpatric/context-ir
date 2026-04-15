"""Unit and integration tests for the diagnose and recompile contracts."""

from __future__ import annotations

import inspect
from pathlib import Path

from context_ir.compiler import compile
from context_ir.diagnostics import diagnose, recompile
from context_ir.parser import parse_repository
from context_ir.types import (
    CompileResult,
    CompileTraceEntry,
    DiagnosticResult,
    MissEvidence,
    MissKind,
    RecompileResult,
    SymbolKind,
    ViewTier,
)

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repo"


# ---------------------------------------------------------------------------
# Fake embedder (same as test_compiler.py)
# ---------------------------------------------------------------------------


def _constant_embed(texts: list[str]) -> list[list[float]]:
    """Returns identical vectors so embeddings contribute zero signal."""
    return [[0.5] * 64 for _ in texts]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _compile_tight() -> tuple[CompileResult, int]:
    """Compile with a tight budget likely to exclude some symbols.

    Returns the result and the budget used.
    """
    budget = 50
    result = compile(
        query="validate_name",
        repo_root=FIXTURES,
        budget=budget,
        embed_fn=_constant_embed,
    )
    return result, budget


# ---------------------------------------------------------------------------
# diagnose tests
# ---------------------------------------------------------------------------


def test_diagnose_absent_symbol() -> None:
    """ABSENT_SYMBOL evidence with 'validate_name' finds the node."""
    graph = parse_repository(FIXTURES)
    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence="validate_name",
        source="test",
    )
    # Build a trace where validate_name is NOT packed
    trace: list[CompileTraceEntry] = []
    result = diagnose(evidence, graph, trace)

    assert isinstance(result, DiagnosticResult)
    assert any("validate_name" in uid for uid in result.missed_units)


def test_diagnose_absent_symbol_not_found() -> None:
    """ABSENT_SYMBOL with a non-existent name returns empty missed_units."""
    graph = parse_repository(FIXTURES)
    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence="this_symbol_does_not_exist_anywhere",
        source="test",
    )
    trace: list[CompileTraceEntry] = []
    result = diagnose(evidence, graph, trace)

    assert isinstance(result, DiagnosticResult)
    assert result.missed_units == []


def test_diagnose_out_of_pack_trace() -> None:
    """OUT_OF_PACK_TRACE with a file path reference finds nodes from that file."""
    graph = parse_repository(FIXTURES)
    evidence = MissEvidence(
        kind=MissKind.OUT_OF_PACK_TRACE,
        evidence="File 'models.py', line 25, in validate_name",
        source="test",
    )
    trace: list[CompileTraceEntry] = []
    result = diagnose(evidence, graph, trace)

    assert isinstance(result, DiagnosticResult)
    assert len(result.missed_units) > 0
    # Should find nodes from models.py
    has_models_node = any("models.py" in uid for uid in result.missed_units)
    assert has_models_node


def test_diagnose_edit_to_omitted() -> None:
    """EDIT_TO_OMITTED with a file path finds all packable nodes in that file."""
    graph = parse_repository(FIXTURES)
    evidence = MissEvidence(
        kind=MissKind.EDIT_TO_OMITTED,
        evidence="mypackage/models.py",
        source="test",
    )
    trace: list[CompileTraceEntry] = []
    result = diagnose(evidence, graph, trace)

    assert isinstance(result, DiagnosticResult)
    assert len(result.missed_units) > 0
    # All missed units should be from models.py
    for uid in result.missed_units:
        assert "models.py" in uid


def test_diagnose_recommended_expansions_include_dependencies() -> None:
    """recommended_expansions includes missed units plus their CALLS targets."""
    graph = parse_repository(FIXTURES)
    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence="validate_name",
        source="test",
    )
    trace: list[CompileTraceEntry] = []
    result = diagnose(evidence, graph, trace)

    # validate_name CALLS check_length, so recommended_expansions
    # should include both validate_name and check_length
    assert len(result.recommended_expansions) > len(result.missed_units)
    has_check_length = any(
        "check_length" in uid for uid in result.recommended_expansions
    )
    assert has_check_length


def test_diagnose_reason_nonempty() -> None:
    """reason string is non-empty for all miss kinds."""
    graph = parse_repository(FIXTURES)
    trace: list[CompileTraceEntry] = []

    for kind, evidence_str in [
        (MissKind.ABSENT_SYMBOL, "validate_name"),
        (MissKind.OUT_OF_PACK_TRACE, "File 'models.py', line 25"),
        (MissKind.EDIT_TO_OMITTED, "mypackage/models.py"),
    ]:
        evidence = MissEvidence(kind=kind, evidence=evidence_str, source="test")
        result = diagnose(evidence, graph, trace)
        assert len(result.reason) > 0, f"Empty reason for {kind}"


# ---------------------------------------------------------------------------
# recompile tests
# ---------------------------------------------------------------------------


def test_recompile_returns_recompile_result() -> None:
    """recompile returns a RecompileResult that extends CompileResult."""
    tight_result, _budget = _compile_tight()
    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence="validate_name",
        source="test",
    )
    result = recompile(
        tight_result,
        evidence,
        5000,
        embed_fn=_constant_embed,
    )

    assert isinstance(result, RecompileResult)
    # RecompileResult extends CompileResult
    assert isinstance(result, CompileResult)
    assert isinstance(result.document, str)
    assert isinstance(result.trace, list)
    assert isinstance(result.warnings, list)
    assert isinstance(result.omitted_frontier, list)
    assert isinstance(result.confidence, float)
    assert isinstance(result.total_tokens, int)
    assert isinstance(result.budget, int)
    # RecompileResult carries compile_context for chaining
    assert result.compile_context is not None


def test_recompile_includes_missed_symbol() -> None:
    """Recompile with additional budget includes a previously missed symbol."""
    tight_result, _budget = _compile_tight()

    # Find a symbol that was omitted in the tight compile
    packed_ids = {
        e.unit_id
        for e in tight_result.trace
        if e.chosen_tier.value > ViewTier.OMIT.value
    }

    # Pick a symbol from the fixture that might be missing
    graph = parse_repository(FIXTURES)
    omitted_packable = [
        nid
        for nid, node in graph.nodes.items()
        if nid not in packed_ids
        and node.kind.value in ("function", "class", "method", "constant")
    ]

    if not omitted_packable:
        # If everything fits in the tight budget, skip
        return

    target_id = omitted_packable[0]
    target_name = graph.nodes[target_id].name

    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence=target_name,
        source="test",
    )
    result = recompile(
        tight_result,
        evidence,
        10_000,
        embed_fn=_constant_embed,
    )

    # With a generous delta_budget, the missed symbol should be included
    recompile_packed = {
        e.unit_id for e in result.trace if e.chosen_tier.value > ViewTier.OMIT.value
    }
    assert target_id in recompile_packed


def test_recompile_new_units_added() -> None:
    """new_units_added contains previously missed symbol IDs."""
    tight_result, _budget = _compile_tight()
    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence="validate_name",
        source="test",
    )
    result = recompile(
        tight_result,
        evidence,
        10_000,
        embed_fn=_constant_embed,
    )

    assert isinstance(result.new_units_added, list)
    # With a much larger budget, there should be new units
    previous_packed = {
        e.unit_id
        for e in tight_result.trace
        if e.chosen_tier.value > ViewTier.OMIT.value
    }
    for uid in result.new_units_added:
        assert uid not in previous_packed


def test_recompile_previous_trace_preserved() -> None:
    """previous_trace in the result matches the input."""
    tight_result, _budget = _compile_tight()
    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence="validate_name",
        source="test",
    )
    result = recompile(
        tight_result,
        evidence,
        5000,
        embed_fn=_constant_embed,
    )

    assert result.previous_trace is tight_result.trace


def test_recompile_budget_delta() -> None:
    """budget_delta in the result matches the input delta_budget."""
    tight_result, _budget = _compile_tight()
    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence="validate_name",
        source="test",
    )
    delta = 3000
    result = recompile(
        tight_result,
        evidence,
        delta,
        embed_fn=_constant_embed,
    )

    assert result.budget_delta == delta


def test_recompile_expanded_budget() -> None:
    """result.budget equals original_budget + delta_budget."""
    tight_result, budget = _compile_tight()
    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence="validate_name",
        source="test",
    )
    delta = 7000
    result = recompile(
        tight_result,
        evidence,
        delta,
        embed_fn=_constant_embed,
    )

    assert result.budget == budget + delta


# ---------------------------------------------------------------------------
# Regression tests: contract shape and sufficiency
# ---------------------------------------------------------------------------


def test_recompile_signature_has_three_required_positional_params() -> None:
    """recompile has exactly 3 required positional parameters."""
    sig = inspect.signature(recompile)
    required_positional = [
        name
        for name, param in sig.parameters.items()
        if param.default is inspect.Parameter.empty
        and param.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    assert required_positional == [
        "previous_result",
        "miss_evidence",
        "delta_budget",
    ]


def test_diagnose_present_but_too_shallow_callable() -> None:
    """A callable present at SUMMARY is detected as missed (needs SLICE+)."""
    graph = parse_repository(FIXTURES)

    # Find a function node in the fixture
    fn_id: str | None = None
    for nid, node in graph.nodes.items():
        if node.kind == SymbolKind.FUNCTION:
            fn_id = nid
            break
    assert fn_id is not None

    # Build a trace where the function is present at SUMMARY (insufficient)
    trace = [
        CompileTraceEntry(
            unit_id=fn_id,
            edit_score=0.5,
            support_score=0.3,
            chosen_tier=ViewTier.SUMMARY,
            marginal_utility=0.1,
            token_cost=5,
        )
    ]

    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence=graph.nodes[fn_id].name,
        source="test",
    )
    result = diagnose(evidence, graph, trace)

    # Should be detected as a miss despite being in the trace at SUMMARY
    assert fn_id in result.missed_units


def test_diagnose_callable_at_slice_is_sufficient() -> None:
    """A callable present at SLICE is NOT detected as missed."""
    graph = parse_repository(FIXTURES)

    fn_id: str | None = None
    for nid, node in graph.nodes.items():
        if node.kind == SymbolKind.FUNCTION:
            fn_id = nid
            break
    assert fn_id is not None

    trace = [
        CompileTraceEntry(
            unit_id=fn_id,
            edit_score=0.8,
            support_score=0.3,
            chosen_tier=ViewTier.SLICE,
            marginal_utility=0.5,
            token_cost=50,
        )
    ]

    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence=graph.nodes[fn_id].name,
        source="test",
    )
    result = diagnose(evidence, graph, trace)

    assert fn_id not in result.missed_units


def test_diagnose_constant_at_summary_is_sufficient() -> None:
    """A constant present at SUMMARY is NOT detected as missed."""
    graph = parse_repository(FIXTURES)

    const_id: str | None = None
    for nid, node in graph.nodes.items():
        if node.kind == SymbolKind.CONSTANT:
            const_id = nid
            break

    if const_id is None:
        return  # no constants in fixture, skip

    trace = [
        CompileTraceEntry(
            unit_id=const_id,
            edit_score=0.3,
            support_score=0.5,
            chosen_tier=ViewTier.SUMMARY,
            marginal_utility=0.1,
            token_cost=3,
        )
    ]

    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence=graph.nodes[const_id].name,
        source="test",
    )
    result = diagnose(evidence, graph, trace)

    assert const_id not in result.missed_units


def test_recompile_upgrades_too_shallow_symbol() -> None:
    """recompile upgrades a symbol present at insufficient tier."""
    tight_result, _budget = _compile_tight()

    # Find a function that ended up at SUMMARY or STUB (too shallow)
    shallow_id: str | None = None
    graph = parse_repository(FIXTURES)
    for entry in tight_result.trace:
        if entry.chosen_tier.value < ViewTier.SLICE.value:
            node = graph.nodes.get(entry.unit_id)
            if node is not None and node.kind == SymbolKind.FUNCTION:
                shallow_id = entry.unit_id
                break

    if shallow_id is None:
        # If no function is packed below SLICE, skip
        return

    evidence = MissEvidence(
        kind=MissKind.ABSENT_SYMBOL,
        evidence=graph.nodes[shallow_id].name,
        source="test",
    )
    result = recompile(
        tight_result,
        evidence,
        10_000,
        embed_fn=_constant_embed,
    )

    # After recompile with generous budget, the symbol should be at SLICE+
    recompile_tiers = {e.unit_id: e.chosen_tier for e in result.trace}
    assert shallow_id in recompile_tiers
    assert recompile_tiers[shallow_id].value >= ViewTier.SLICE.value

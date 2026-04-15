"""Diagnose and recompile contracts for adaptive context compilation.

diagnose identifies what symbols were missed in a prior compile pass
and recommends expansions. recompile wraps the compile pipeline with
score boosts for missed symbols, producing an updated document under
an expanded budget.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from context_ir.compiler import _assemble_document
from context_ir.optimizer import optimize
from context_ir.parser import parse_repository
from context_ir.renderer import render
from context_ir.scorer import score_graph
from context_ir.types import (
    CompileContext,
    CompileResult,
    CompileTraceEntry,
    DiagnosticResult,
    EdgeKind,
    MissEvidence,
    MissKind,
    RecompileResult,
    SymbolGraph,
    SymbolKind,
    UnitView,
    ViewTier,
)

# ---------------------------------------------------------------------------
# Packable symbol kinds (same filter the optimizer uses)
# ---------------------------------------------------------------------------

_PACKABLE_KINDS = frozenset(
    {SymbolKind.FUNCTION, SymbolKind.CLASS, SymbolKind.METHOD, SymbolKind.CONSTANT}
)

# ---------------------------------------------------------------------------
# Tier sufficiency thresholds
# ---------------------------------------------------------------------------

# Minimum tier for a symbol to be considered "sufficiently represented"
# in the previous compile pass. Callable/class symbols need SLICE or
# better (they are edit-locus candidates). Constants are sufficiently
# represented at SUMMARY or better.
_SUFFICIENT_TIER: dict[SymbolKind, ViewTier] = {
    SymbolKind.FUNCTION: ViewTier.SLICE,
    SymbolKind.CLASS: ViewTier.SLICE,
    SymbolKind.METHOD: ViewTier.SLICE,
    SymbolKind.CONSTANT: ViewTier.SUMMARY,
}


def _is_sufficiently_represented(
    unit_id: str,
    graph: SymbolGraph,
    trace_map: dict[str, CompileTraceEntry],
) -> bool:
    """Check whether a unit is represented at a sufficient tier.

    Callable/class edit-locus misses require SLICE or better.
    Constants count as sufficient at SUMMARY or better.
    """
    entry = trace_map.get(unit_id)
    if entry is None or entry.chosen_tier == ViewTier.OMIT:
        return False
    node = graph.nodes.get(unit_id)
    if node is None:
        return False
    min_tier = _SUFFICIENT_TIER.get(node.kind, ViewTier.SUMMARY)
    return bool(entry.chosen_tier.value >= min_tier.value)


# ---------------------------------------------------------------------------
# Evidence parsing helpers
# ---------------------------------------------------------------------------

# Matches patterns like: File 'models.py', line 25, in validate_name
_TRACE_FILE_RE = re.compile(r"File\s+'([^']+)'")
_TRACE_FUNC_RE = re.compile(r",\s+in\s+(\w+)")
# Matches bare .py paths
_BARE_PY_PATH_RE = re.compile(r"[\w./\\]+\.py")


def _parse_absent_symbol(
    evidence: str,
    graph: SymbolGraph,
) -> list[str]:
    """Find graph nodes matching an absent symbol name or dotted path."""
    evidence = evidence.strip()
    candidates: list[str] = []

    # 1. Exact node ID match
    if evidence in graph.nodes:
        node = graph.nodes[evidence]
        if node.kind in _PACKABLE_KINDS:
            return [evidence]

    # 2. Exact name match
    for nid, node in graph.nodes.items():
        if node.name == evidence and node.kind in _PACKABLE_KINDS:
            candidates.append(nid)
    if candidates:
        return candidates

    # 3. Dotted path match: convert dots to path separators
    if "." in evidence:
        parts = evidence.rsplit(".", 1)
        if len(parts) == 2:
            file_part = parts[0].replace(".", "/") + ".py"
            name_part = parts[1]
            for nid, node in graph.nodes.items():
                if (
                    node.file_path.endswith(file_part)
                    and node.name == name_part
                    and node.kind in _PACKABLE_KINDS
                ):
                    candidates.append(nid)
    if candidates:
        return candidates

    # 4. Substring match on node.name
    for nid, node in graph.nodes.items():
        if evidence in node.name and node.kind in _PACKABLE_KINDS:
            candidates.append(nid)

    return candidates


def _parse_out_of_pack_trace(
    evidence: str,
    graph: SymbolGraph,
) -> list[str]:
    """Extract file paths and function names from a stack trace fragment."""
    candidates: list[str] = []
    seen: set[str] = set()

    # Extract file paths from File '...' patterns
    file_paths = _TRACE_FILE_RE.findall(evidence)
    # Extract function names from "in <name>" patterns
    func_names = _TRACE_FUNC_RE.findall(evidence)

    # Also try bare .py paths
    bare_paths = _BARE_PY_PATH_RE.findall(evidence)
    file_paths.extend(bare_paths)

    # Match extracted paths against graph nodes
    for fp in file_paths:
        for nid, node in graph.nodes.items():
            if nid in seen:
                continue
            if node.kind not in _PACKABLE_KINDS:
                continue
            if node.file_path.endswith(fp) or fp.endswith(node.file_path):
                seen.add(nid)
                candidates.append(nid)

    # Match function names against graph nodes
    for fname in func_names:
        for nid, node in graph.nodes.items():
            if nid in seen:
                continue
            if node.kind not in _PACKABLE_KINDS:
                continue
            if node.name == fname:
                seen.add(nid)
                candidates.append(nid)

    return candidates


def _parse_edit_to_omitted(
    evidence: str,
    graph: SymbolGraph,
) -> list[str]:
    """Find all packable graph nodes in the given file path."""
    evidence = evidence.strip()
    candidates: list[str] = []

    for nid, node in graph.nodes.items():
        if node.kind not in _PACKABLE_KINDS:
            continue
        if node.file_path == evidence or node.file_path.endswith(evidence):
            candidates.append(nid)

    return candidates


# ---------------------------------------------------------------------------
# One-hop dependency expansion
# ---------------------------------------------------------------------------


def _expand_dependencies(
    unit_ids: list[str],
    graph: SymbolGraph,
) -> list[str]:
    """Return unit_ids plus their one-hop CALLS/IMPORTS targets in the graph."""
    expanded: list[str] = list(unit_ids)
    seen: set[str] = set(unit_ids)

    for uid in unit_ids:
        for edge in graph.edges:
            if edge.source_id != uid:
                continue
            if edge.kind not in (EdgeKind.CALLS, EdgeKind.IMPORTS):
                continue
            target = edge.target_id
            if target in seen:
                continue
            if target in graph.nodes and graph.nodes[target].kind in _PACKABLE_KINDS:
                seen.add(target)
                expanded.append(target)

    return expanded


# ---------------------------------------------------------------------------
# Reason builder
# ---------------------------------------------------------------------------


def _build_reason(
    missed_units: list[str],
    graph: SymbolGraph,
    previous_trace: list[CompileTraceEntry],
    miss_kind: MissKind,
) -> str:
    """Build a human-readable reason string for missed symbols."""
    if not missed_units:
        return "No matching symbols found in the graph."

    packed_ids = {e.unit_id for e in previous_trace if e.token_cost > 0}
    omitted_ids = {e.unit_id for e in previous_trace if e.token_cost == 0}
    trace_ids = {e.unit_id for e in previous_trace}

    parts: list[str] = []
    for uid in missed_units:
        node = graph.nodes.get(uid)
        label = node.name if node else uid

        if uid in packed_ids:
            # Was in the pack but apparently insufficient
            parts.append(f"Symbol '{label}' was included but at an insufficient tier.")
        elif uid in omitted_ids:
            parts.append(f"Symbol '{label}' was omitted due to budget pressure.")
        elif uid not in trace_ids:
            if miss_kind == MissKind.EDIT_TO_OMITTED:
                file_path = node.file_path if node else uid
                parts.append(f"File '{file_path}' was not represented in the pack.")
            else:
                parts.append(
                    f"Symbol '{label}' was not scored highly enough for inclusion."
                )

    return " ".join(parts) if parts else f"Missed {len(missed_units)} symbol(s)."


# ---------------------------------------------------------------------------
# Public API: diagnose
# ---------------------------------------------------------------------------


def diagnose(
    miss_evidence: MissEvidence,
    graph: SymbolGraph,
    previous_trace: list[CompileTraceEntry],
) -> DiagnosticResult:
    """Identify what was missed and recommend expansions.

    Analyzes the miss evidence against the symbol graph to find which
    units were missed, explains why, and recommends which symbols to
    expand in a recompile pass.
    """
    # Step 1: Parse evidence based on miss kind
    if miss_evidence.kind == MissKind.ABSENT_SYMBOL:
        candidate_ids = _parse_absent_symbol(miss_evidence.evidence, graph)
    elif miss_evidence.kind == MissKind.OUT_OF_PACK_TRACE:
        candidate_ids = _parse_out_of_pack_trace(miss_evidence.evidence, graph)
    elif miss_evidence.kind == MissKind.EDIT_TO_OMITTED:
        candidate_ids = _parse_edit_to_omitted(miss_evidence.evidence, graph)
    else:  # pragma: no cover
        candidate_ids = []

    # Step 2: Cross-reference with previous trace --
    # filter out candidates already sufficiently represented.
    # "Sufficiently represented" depends on symbol kind:
    # callables/classes need SLICE+, constants need SUMMARY+.
    trace_map = {e.unit_id: e for e in previous_trace}
    missed_units = [
        cid
        for cid in candidate_ids
        if not _is_sufficiently_represented(cid, graph, trace_map)
    ]

    # Step 3: Build recommended expansions (missed + one-hop deps)
    recommended_expansions = _expand_dependencies(missed_units, graph)

    # Step 4: Build reason string
    reason = _build_reason(missed_units, graph, previous_trace, miss_evidence.kind)

    return DiagnosticResult(
        missed_units=missed_units,
        reason=reason,
        recommended_expansions=recommended_expansions,
    )


# ---------------------------------------------------------------------------
# Public API: recompile
# ---------------------------------------------------------------------------


def recompile(
    previous_result: CompileResult,
    miss_evidence: MissEvidence,
    delta_budget: int,
    *,
    embed_fn: Callable[[list[str]], list[list[float]]] | None = None,
    graph: SymbolGraph | None = None,
) -> RecompileResult:
    """Targeted recompilation incorporating missed symbols.

    Consumes a prior CompileResult (which carries CompileContext with
    the query and repo_root needed for re-scoring), diagnoses the miss,
    boosts scores for missed units, expands the budget by delta_budget,
    and re-runs the compile pipeline.

    Parameters
    ----------
    previous_result:
        The CompileResult from the prior compile or recompile pass.
        Must carry a non-None compile_context.
    miss_evidence:
        Evidence describing what the prior pass missed.
    delta_budget:
        Additional token budget to add on top of the prior budget.
    embed_fn:
        Optional custom embedding function for testing.
    graph:
        Optional pre-parsed SymbolGraph to skip re-parsing.
    """
    ctx = previous_result.compile_context
    if ctx is None:
        msg = (
            "previous_result.compile_context is None; "
            "recompile requires a CompileResult produced by compile()"
        )
        raise ValueError(msg)

    query = ctx.query
    repo_root = ctx.repo_root
    previous_trace = previous_result.trace
    original_budget = previous_result.budget

    # Step 1: Parse graph if not provided
    if graph is None:
        graph = parse_repository(repo_root)

    # Step 2: Diagnose
    diagnostic = diagnose(miss_evidence, graph, previous_trace)

    # Step 3: Score graph
    scores = score_graph(query, graph, repo_root, embed_fn)

    # Step 4: Boost scores for missed units and recommended expansions
    missed_set = set(diagnostic.missed_units)
    recommended_set = set(diagnostic.recommended_expansions)

    for uid in missed_set:
        if uid in scores:
            scores[uid] = scores[uid].__class__(
                p_edit=max(scores[uid].p_edit, 1.0),
                p_support=scores[uid].p_support,
            )

    for uid in recommended_set - missed_set:
        if uid in scores:
            scores[uid] = scores[uid].__class__(
                p_edit=scores[uid].p_edit,
                p_support=max(scores[uid].p_support, 0.8),
            )

    # Step 5: Compute new budget
    new_budget = original_budget + delta_budget

    # Step 6: Optimize with boosted scores and expanded budget
    opt = optimize(scores, graph, new_budget, repo_root)

    # Step 7: Render each assigned symbol at its tier
    views: list[UnitView] = []
    for node_id, tier in opt.tier_assignments.items():
        view = render(node_id, tier, graph, repo_root)
        views.append(view)

    # Step 8: Assemble document
    document = _assemble_document(
        views=views,
        graph=graph,
        tier_assignments=opt.tier_assignments,
        query=query,
        total_tokens=opt.total_tokens,
        budget=new_budget,
        confidence=opt.confidence,
        omitted_frontier=opt.omitted_frontier,
    )

    # Step 9: Determine new units added
    previous_packed = {
        e.unit_id for e in previous_trace if e.chosen_tier.value > ViewTier.OMIT.value
    }
    new_units_added = [
        uid
        for uid in opt.tier_assignments
        if uid not in previous_packed
        and opt.tier_assignments[uid].value > ViewTier.OMIT.value
    ]

    return RecompileResult(
        document=document,
        trace=opt.trace,
        warnings=opt.warnings,
        omitted_frontier=opt.omitted_frontier,
        confidence=opt.confidence,
        total_tokens=opt.total_tokens,
        budget=new_budget,
        compile_context=CompileContext(query=query, repo_root=repo_root),
        previous_trace=previous_trace,
        new_units_added=new_units_added,
        budget_delta=delta_budget,
    )

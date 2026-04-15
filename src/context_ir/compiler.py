"""Compile contract: end-to-end context document compilation.

Orchestrates parser, scorer, optimizer, and renderer into a single
call. Given a query, a repo path, and a token budget, returns a
CompileResult with a formatted document, compile trace, warnings,
omitted frontier, and confidence score.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from context_ir.optimizer import optimize
from context_ir.parser import parse_repository
from context_ir.renderer import render
from context_ir.scorer import score_graph
from context_ir.types import (
    CompileContext,
    CompileResult,
    SymbolGraph,
    UnitView,
    ViewTier,
)

# ---------------------------------------------------------------------------
# Tier label mapping for document headers
# ---------------------------------------------------------------------------

_TIER_LABEL: dict[ViewTier, str] = {
    ViewTier.FULL: "FULL",
    ViewTier.SLICE: "SLICE",
    ViewTier.STUB: "STUB",
    ViewTier.SUMMARY: "SUMMARY",
    ViewTier.OMIT: "OMIT",
}


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------


def _assemble_document(
    views: list[UnitView],
    graph: SymbolGraph,
    tier_assignments: dict[str, ViewTier],
    query: str,
    total_tokens: int,
    budget: int,
    confidence: float,
    omitted_frontier: list[str],
) -> str:
    """Format rendered views into the compiled context document.

    Groups symbols by file, orders files alphabetically, orders symbols
    within each file by start_line. Appends an omitted section if any
    symbols were omitted.
    """
    truncated_query = query[:200]
    packed_count = sum(1 for t in tier_assignments.values() if t != ViewTier.OMIT)
    omitted_count = len(omitted_frontier) + sum(
        1 for t in tier_assignments.values() if t == ViewTier.OMIT
    )

    lines: list[str] = [
        "# Compiled Context",
        f"# Query: {truncated_query}",
        f"# Budget: {total_tokens}/{budget} tokens | Confidence: {confidence:.2f}",
        f"# Symbols: {packed_count} included, {omitted_count} omitted",
    ]

    # Build a lookup from unit_id to UnitView
    view_map: dict[str, UnitView] = {v.unit_id: v for v in views}

    # Group by file_path, ordered alphabetically
    file_groups: dict[str, list[str]] = {}
    for node_id in tier_assignments:
        node = graph.nodes[node_id]
        fp = node.file_path
        if fp not in file_groups:
            file_groups[fp] = []
        file_groups[fp].append(node_id)

    for fp in sorted(file_groups):
        lines.append("")
        lines.append(f"## {fp}")

        # Sort symbols within file by start_line
        node_ids = file_groups[fp]
        node_ids.sort(key=lambda nid: graph.nodes[nid].start_line)

        for nid in node_ids:
            node = graph.nodes[nid]
            tier = tier_assignments[nid]
            label = _TIER_LABEL[tier]
            view = view_map[nid]
            lines.append("")
            lines.append(f"### {node.name} [{label}]")
            lines.append(view.content)

    # Omitted section
    if omitted_frontier:
        lines.append("")
        lines.append(f"## Omitted ({len(omitted_frontier)})")
        for nid in omitted_frontier:
            lines.append(f"# {nid}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compile(
    query: str,
    repo_root: Path,
    budget: int,
    embed_fn: Callable[[list[str]], list[list[float]]] | None = None,
    graph: SymbolGraph | None = None,
) -> CompileResult:
    """Compile a context document for the given query within a token budget.

    Orchestrates the full pipeline: parse -> score -> optimize -> render -> assemble.

    If graph is None, parses the repository from repo_root.
    If graph is provided, skips parsing and uses the given graph.

    If embed_fn is None, uses sentence-transformers (all-MiniLM-L6-v2)
    with lazy model loading. Pass a custom embed_fn for testing or
    alternative backends.
    """
    # Step 1: Parse (if graph not provided)
    if graph is None:
        graph = parse_repository(repo_root)

    # Step 2: Score
    scores = score_graph(query, graph, repo_root, embed_fn)

    # Step 3: Optimize
    opt = optimize(scores, graph, budget, repo_root)

    # Step 4: Render each assigned symbol at its tier
    views: list[UnitView] = []
    for node_id, tier in opt.tier_assignments.items():
        view = render(node_id, tier, graph, repo_root)
        views.append(view)

    # Step 5: Assemble document
    document = _assemble_document(
        views=views,
        graph=graph,
        tier_assignments=opt.tier_assignments,
        query=query,
        total_tokens=opt.total_tokens,
        budget=budget,
        confidence=opt.confidence,
        omitted_frontier=opt.omitted_frontier,
    )

    return CompileResult(
        document=document,
        trace=opt.trace,
        warnings=opt.warnings,
        omitted_frontier=opt.omitted_frontier,
        confidence=opt.confidence,
        total_tokens=opt.total_tokens,
        budget=budget,
        compile_context=CompileContext(query=query, repo_root=repo_root),
    )

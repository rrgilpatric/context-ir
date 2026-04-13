"""Budget optimizer for context IR.

Decides which symbols to include and at what ViewTier given a token
budget. Uses greedy selection by marginal utility per token with
dependency closure. Produces a compile trace, warnings, omitted
frontier, and confidence score.
"""

from __future__ import annotations

from pathlib import Path

from context_ir.renderer import render
from context_ir.types import (
    CompileTraceEntry,
    CompileWarning,
    DowngradeReason,
    EdgeKind,
    EditSupportScores,
    OptimizationResult,
    SymbolGraph,
    SymbolKind,
    ViewTier,
    WarningKind,
)

# ---------------------------------------------------------------------------
# Tier value tables (tunable later via eval, Slice 9)
# ---------------------------------------------------------------------------

TIER_EDIT_VALUE: dict[ViewTier, float] = {
    ViewTier.OMIT: 0.0,
    ViewTier.SUMMARY: 0.1,
    ViewTier.STUB: 0.3,
    ViewTier.SLICE: 0.9,
    ViewTier.FULL: 1.0,
}

TIER_SUPPORT_VALUE: dict[ViewTier, float] = {
    ViewTier.OMIT: 0.1,
    ViewTier.SUMMARY: 0.5,
    ViewTier.STUB: 0.8,
    ViewTier.SLICE: 0.25,
    ViewTier.FULL: 0.3,
}

# Ordered list of tiers from lowest to highest for step generation.
_TIER_ORDER: list[ViewTier] = [
    ViewTier.OMIT,
    ViewTier.SUMMARY,
    ViewTier.STUB,
    ViewTier.SLICE,
    ViewTier.FULL,
]

# Packable symbol kinds (excludes FILE, MODULE, IMPORT).
_PACKABLE_KINDS: frozenset[SymbolKind] = frozenset(
    {SymbolKind.FUNCTION, SymbolKind.CLASS, SymbolKind.METHOD, SymbolKind.CONSTANT}
)


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


class _UpgradeStep:
    """A candidate step: upgrading a node from one tier to the next."""

    __slots__ = (
        "node_id",
        "tier_from",
        "tier_to",
        "marginal_utility",
        "token_delta",
        "efficiency",
    )

    def __init__(
        self,
        node_id: str,
        tier_from: ViewTier | None,
        tier_to: ViewTier,
        marginal_utility: float,
        token_delta: int,
    ) -> None:
        self.node_id = node_id
        self.tier_from = tier_from
        self.tier_to = tier_to
        self.marginal_utility = marginal_utility
        self.token_delta = token_delta
        self.efficiency = marginal_utility / max(1, token_delta)


# ---------------------------------------------------------------------------
# Utility computation
# ---------------------------------------------------------------------------


def _utility(p_edit: float, p_support: float, tier: ViewTier) -> float:
    """Compute the utility of a symbol at a given tier."""
    return p_edit * TIER_EDIT_VALUE[tier] + p_support * TIER_SUPPORT_VALUE[tier]


# ---------------------------------------------------------------------------
# Pre-computation: tier costs and upgrade steps
# ---------------------------------------------------------------------------


def _compute_tier_costs(
    packable_ids: list[str],
    graph: SymbolGraph,
    repo_root: Path,
) -> dict[str, dict[ViewTier, int]]:
    """Render each packable node at all tiers and record token costs."""
    costs: dict[str, dict[ViewTier, int]] = {}
    for node_id in packable_ids:
        node_costs: dict[ViewTier, int] = {}
        for tier in _TIER_ORDER:
            view = render(node_id, tier, graph, repo_root)
            node_costs[tier] = view.token_cost
        costs[node_id] = node_costs
    return costs


def _build_upgrade_steps(
    packable_ids: list[str],
    scores: dict[str, EditSupportScores],
    costs: dict[str, dict[ViewTier, int]],
) -> list[_UpgradeStep]:
    """Build all upgrade steps for every packable node.

    Steps go from excluded -> OMIT -> SUMMARY -> STUB -> SLICE -> FULL.
    The first step (excluded -> OMIT) uses utility=0, cost=0 as baseline.
    """
    steps: list[_UpgradeStep] = []

    for node_id in packable_ids:
        s = scores[node_id]
        node_costs = costs[node_id]

        # First step: excluded -> OMIT (baseline utility=0, cost=0)
        u_omit = _utility(s.p_edit, s.p_support, ViewTier.OMIT)
        c_omit = node_costs[ViewTier.OMIT]
        steps.append(
            _UpgradeStep(
                node_id=node_id,
                tier_from=None,  # None means "excluded"
                tier_to=ViewTier.OMIT,
                marginal_utility=u_omit,
                token_delta=c_omit,
            )
        )

        # Subsequent steps: each consecutive tier pair
        for i in range(len(_TIER_ORDER) - 1):
            tier_from = _TIER_ORDER[i]
            tier_to = _TIER_ORDER[i + 1]
            u_from = _utility(s.p_edit, s.p_support, tier_from)
            u_to = _utility(s.p_edit, s.p_support, tier_to)
            c_from = node_costs[tier_from]
            c_to = node_costs[tier_to]
            steps.append(
                _UpgradeStep(
                    node_id=node_id,
                    tier_from=tier_from,
                    tier_to=tier_to,
                    marginal_utility=u_to - u_from,
                    token_delta=c_to - c_from,
                )
            )

    return steps


# ---------------------------------------------------------------------------
# Greedy selection
# ---------------------------------------------------------------------------


def _greedy_select(
    steps: list[_UpgradeStep],
    budget: int,
) -> dict[str, ViewTier]:
    """Select symbols and tiers greedily by efficiency.

    Iterates the sorted step list multiple times because a high-efficiency
    upgrade step (e.g. STUB->SLICE) may be sorted before its prerequisite
    (excluded->OMIT). Each pass applies all newly eligible steps. Stops
    when a full pass applies nothing.

    Returns a dict mapping node_id to the assigned ViewTier for nodes
    that are included in the pack. Nodes not in the returned dict are
    excluded.
    """
    # Sort by efficiency descending, break ties by marginal_utility descending
    steps.sort(key=lambda s: (-s.efficiency, -s.marginal_utility))

    # Track current tier per node: None means excluded
    current_tier: dict[str, ViewTier | None] = {}
    remaining = budget
    assignments: dict[str, ViewTier] = {}

    # Iterate until no progress (at most len(_TIER_ORDER) passes)
    changed = True
    while changed:
        changed = False
        for step in steps:
            if step.marginal_utility <= 0:
                break

            node_current = current_tier.get(step.node_id)

            # Check that the step's from-tier matches the node's current state
            if step.tier_from is None:
                if node_current is not None:
                    continue
            else:
                if node_current != step.tier_from:
                    continue

            if step.token_delta > remaining:
                continue

            # Apply the step
            current_tier[step.node_id] = step.tier_to
            assignments[step.node_id] = step.tier_to
            remaining -= step.token_delta
            changed = True

    return assignments


# ---------------------------------------------------------------------------
# Dependency closure
# ---------------------------------------------------------------------------


def _apply_dependency_closure(
    assignments: dict[str, ViewTier],
    graph: SymbolGraph,
    costs: dict[str, dict[ViewTier, int]],
) -> tuple[dict[str, ViewTier], set[str]]:
    """Ensure dependencies of selected symbols are in the pack.

    For each selected symbol at STUB or above, find CALLS edge targets.
    If a target is packable and not in the pack (or below STUB), add or
    upgrade it to STUB.

    Returns the updated assignments and a set of node IDs added by closure.
    """
    closure_additions: set[str] = set()

    # Collect all CALLS edges indexed by source
    calls_by_source: dict[str, list[str]] = {}
    for edge in graph.edges:
        if edge.kind == EdgeKind.CALLS:
            if edge.source_id not in calls_by_source:
                calls_by_source[edge.source_id] = []
            calls_by_source[edge.source_id].append(edge.target_id)

    for node_id, tier in list(assignments.items()):
        if tier.value < ViewTier.STUB.value:
            continue
        targets = calls_by_source.get(node_id, [])
        for target_id in targets:
            # Only add packable nodes
            if target_id not in costs:
                continue
            current = assignments.get(target_id)
            if current is None or current.value < ViewTier.STUB.value:
                assignments[target_id] = ViewTier.STUB
                closure_additions.add(target_id)

    return assignments, closure_additions


# ---------------------------------------------------------------------------
# Optimal tier computation (for downgrade reason)
# ---------------------------------------------------------------------------


def _compute_optimal_tiers(
    packable_ids: list[str],
    scores: dict[str, EditSupportScores],
) -> dict[str, ViewTier]:
    """Compute the optimal tier for each node (unconstrained by budget).

    The optimal tier is the one with the highest utility.
    """
    optimal: dict[str, ViewTier] = {}
    for node_id in packable_ids:
        s = scores[node_id]
        best_tier = ViewTier.OMIT
        best_utility = _utility(s.p_edit, s.p_support, ViewTier.OMIT)
        for tier in _TIER_ORDER[1:]:
            u = _utility(s.p_edit, s.p_support, tier)
            if u > best_utility:
                best_utility = u
                best_tier = tier
        optimal[node_id] = best_tier
    return optimal


# ---------------------------------------------------------------------------
# Warning generation
# ---------------------------------------------------------------------------


def _generate_warnings(
    assignments: dict[str, ViewTier],
    scores: dict[str, EditSupportScores],
    packable_ids: list[str],
    graph: SymbolGraph,
    costs: dict[str, dict[ViewTier, int]],
) -> list[CompileWarning]:
    """Generate warnings for high-risk omissions and budget-forced downgrades."""
    warnings: list[CompileWarning] = []
    packed_ids = set(assignments.keys())

    for node_id in packable_ids:
        s = scores[node_id]
        node = graph.nodes[node_id]

        # HIGH_RISK_OMISSION: packable symbol with p_edit > 0.5, not packed
        if node_id not in packed_ids and s.p_edit > 0.5:
            warnings.append(
                CompileWarning(
                    kind=WarningKind.HIGH_RISK_OMISSION,
                    unit_id=node_id,
                    message=f"High-risk omission: {node.name} (p_edit={s.p_edit:.2f})",
                    confidence=s.p_edit,
                )
            )

        # BUDGET_FORCED_DOWNGRADE: packed at STUB or below with p_edit > 0.3
        if node_id in packed_ids and s.p_edit > 0.3:
            tier = assignments[node_id]
            if tier.value <= ViewTier.STUB.value:
                warnings.append(
                    CompileWarning(
                        kind=WarningKind.BUDGET_FORCED_DOWNGRADE,
                        unit_id=node_id,
                        message=(
                            f"Budget-forced downgrade: {node.name} at {tier.name} "
                            f"(p_edit={s.p_edit:.2f})"
                        ),
                        confidence=s.p_edit,
                    )
                )

    # UNRESOLVED_SYMBOL_FRONTIER: targets of CALLS/IMPORTS edges from packed
    # symbols that are not in the pack and are not packable (IMPORT/FILE/MODULE)
    frontier_ids: set[str] = set()
    for edge in graph.edges:
        if edge.kind not in (EdgeKind.CALLS, EdgeKind.IMPORTS):
            continue
        if edge.source_id not in packed_ids:
            continue
        if edge.target_id in packed_ids:
            continue
        target = graph.nodes.get(edge.target_id)
        if target is None:
            continue
        # Only flag non-packable targets (IMPORT/FILE/MODULE kind)
        if target.kind not in _PACKABLE_KINDS:
            frontier_ids.add(edge.target_id)

    for target_id in sorted(frontier_ids):
        target = graph.nodes[target_id]
        warnings.append(
            CompileWarning(
                kind=WarningKind.UNRESOLVED_SYMBOL_FRONTIER,
                unit_id=target_id,
                message=f"Unresolved frontier: {target.name}",
                confidence=0.0,
            )
        )

    return warnings


# ---------------------------------------------------------------------------
# Trace generation
# ---------------------------------------------------------------------------


def _generate_trace(
    assignments: dict[str, ViewTier],
    scores: dict[str, EditSupportScores],
    packable_ids: list[str],
    costs: dict[str, dict[ViewTier, int]],
    optimal_tiers: dict[str, ViewTier],
    closure_additions: set[str],
) -> list[CompileTraceEntry]:
    """Generate a compile trace entry for each packable symbol."""
    trace: list[CompileTraceEntry] = []

    for node_id in packable_ids:
        s = scores[node_id]
        assigned = assignments.get(node_id)
        optimal = optimal_tiers[node_id]

        if assigned is not None:
            chosen_tier = assigned
            mu = _utility(s.p_edit, s.p_support, assigned)
            tc = costs[node_id][assigned]
        else:
            # Excluded: report as OMIT tier with zero cost
            chosen_tier = ViewTier.OMIT
            mu = 0.0
            tc = 0

        # Determine downgrade reason
        downgrade: DowngradeReason | None = None
        if node_id in closure_additions:
            downgrade = DowngradeReason.DEPENDENCY_ONLY
        elif assigned is None:
            # Excluded -- why?
            if s.p_edit < 0.1 and s.p_support < 0.1:
                downgrade = DowngradeReason.LOW_RELEVANCE
            else:
                downgrade = DowngradeReason.BUDGET_PRESSURE
        elif assigned.value < optimal.value:
            downgrade = DowngradeReason.BUDGET_PRESSURE

        trace.append(
            CompileTraceEntry(
                unit_id=node_id,
                edit_score=s.p_edit,
                support_score=s.p_support,
                chosen_tier=chosen_tier,
                marginal_utility=mu,
                token_cost=tc,
                downgrade_reason=downgrade,
            )
        )

    return trace


# ---------------------------------------------------------------------------
# Confidence score
# ---------------------------------------------------------------------------


def _compute_confidence(
    assignments: dict[str, ViewTier],
    scores: dict[str, EditSupportScores],
    packable_ids: list[str],
) -> float:
    """Compute confidence as ratio of achieved utility to max possible.

    Confidence of 1.0 means every symbol is at its best tier.
    If there are no packable symbols, confidence is 1.0.
    """
    if not packable_ids:
        return 1.0

    total_max = 0.0
    total_achieved = 0.0

    for node_id in packable_ids:
        s = scores[node_id]
        max_u = max(_utility(s.p_edit, s.p_support, t) for t in _TIER_ORDER)
        total_max += max_u

        assigned = assignments.get(node_id)
        if assigned is not None:
            total_achieved += _utility(s.p_edit, s.p_support, assigned)

    if total_max == 0.0:
        return 1.0

    return total_achieved / total_max


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def optimize(
    scores: dict[str, EditSupportScores],
    graph: SymbolGraph,
    budget: int,
    repo_root: Path,
) -> OptimizationResult:
    """Pack symbols into a token budget using greedy marginal utility.

    Selects which symbols to include and at what ViewTier, enforces
    dependency closure, generates a compile trace with per-unit decisions,
    and produces warnings for high-risk omissions and budget-forced
    downgrades.

    Only packs symbol-level nodes (FUNCTION, CLASS, METHOD, CONSTANT).
    FILE, MODULE, and IMPORT nodes are excluded from packing -- imports
    are already included in SLICE-tier renders, and file/module context
    is the compiler's responsibility.
    """
    # Filter to packable nodes
    packable_ids = [
        nid
        for nid, node in graph.nodes.items()
        if node.kind in _PACKABLE_KINDS and nid in scores
    ]

    # Pre-compute tier costs
    costs = _compute_tier_costs(packable_ids, graph, repo_root)

    # Build upgrade steps
    steps = _build_upgrade_steps(packable_ids, scores, costs)

    # Greedy selection
    assignments = _greedy_select(steps, budget)

    # Dependency closure (one-hop, may exceed budget)
    assignments, closure_additions = _apply_dependency_closure(
        assignments, graph, costs
    )

    # Compute total tokens
    total_tokens = sum(costs[nid][tier] for nid, tier in assignments.items())

    # Compute optimal tiers (for downgrade detection)
    optimal_tiers = _compute_optimal_tiers(packable_ids, scores)

    # Generate trace
    trace = _generate_trace(
        assignments, scores, packable_ids, costs, optimal_tiers, closure_additions
    )

    # Generate warnings
    warnings = _generate_warnings(assignments, scores, packable_ids, graph, costs)

    # Omitted frontier: packable symbols not in the pack
    omitted_frontier = [nid for nid in packable_ids if nid not in assignments]

    # Confidence score
    confidence = _compute_confidence(assignments, scores, packable_ids)

    return OptimizationResult(
        tier_assignments=assignments,
        trace=trace,
        warnings=warnings,
        omitted_frontier=omitted_frontier,
        confidence=confidence,
        total_tokens=total_tokens,
        budget=budget,
    )

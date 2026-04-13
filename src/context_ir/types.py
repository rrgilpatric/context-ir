"""Core type definitions for Context IR.

These types define the contracts the entire system builds on:
symbol graphs, view tiers, scoring, compilation traces, diagnostics,
and recompilation results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------------
# Symbol graph
# ---------------------------------------------------------------------------


class SymbolKind(Enum):
    """Kind of symbol node in the codebase graph."""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    CONSTANT = "constant"
    IMPORT = "import"
    FILE = "file"
    MODULE = "module"


class EdgeKind(Enum):
    """Kind of relationship between symbol nodes."""

    CALLS = "calls"
    IMPORTS = "imports"
    DEFINES = "defines"
    REFERENCES = "references"


@dataclass
class SymbolNode:
    """A symbol-level node in the codebase graph."""

    id: str
    name: str
    kind: SymbolKind
    file_path: str
    start_line: int
    end_line: int
    parent_id: str | None = None


@dataclass
class Edge:
    """A directed relationship between two symbol nodes."""

    source_id: str
    target_id: str
    kind: EdgeKind


@dataclass
class SymbolGraph:
    """The full symbol graph for a codebase or subset."""

    nodes: dict[str, SymbolNode] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)


# ---------------------------------------------------------------------------
# View representation
# ---------------------------------------------------------------------------


class ViewTier(Enum):
    """Representation density tier for a symbol unit.

    Ordered from least to most information:
    1. OMIT -- reference ID only
    2. SUMMARY -- one-line structural summary
    3. STUB -- interface stub (signature + type info)
    4. SLICE -- dependency-preserving source slice
    5. FULL -- full source
    """

    OMIT = 1
    SUMMARY = 2
    STUB = 3
    SLICE = 4
    FULL = 5


@dataclass
class UnitView:
    """A rendered view of a symbol unit at a chosen tier."""

    unit_id: str
    tier: ViewTier
    content: str
    token_cost: int


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@dataclass
class EditSupportScores:
    """Dual relevance scores for a symbol unit.

    p_edit: probability this unit is part of the edit locus.
    p_support: probability this unit is supporting context for an edit elsewhere.
    """

    p_edit: float
    p_support: float


# ---------------------------------------------------------------------------
# Compilation trace
# ---------------------------------------------------------------------------


class DowngradeReason(Enum):
    """Why a unit was rendered at a lower tier than its score would suggest."""

    BUDGET_PRESSURE = "budget_pressure"
    LOW_RELEVANCE = "low_relevance"
    REDUNDANT = "redundant"
    DEPENDENCY_ONLY = "dependency_only"


@dataclass
class CompileTraceEntry:
    """Per-unit record of the compilation decision."""

    unit_id: str
    edit_score: float
    support_score: float
    chosen_tier: ViewTier
    marginal_utility: float
    token_cost: int
    downgrade_reason: DowngradeReason | None = None


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------


class WarningKind(Enum):
    """Category of compiler warning."""

    HIGH_RISK_OMISSION = "high_risk_omission"
    BUDGET_FORCED_DOWNGRADE = "budget_forced_downgrade"
    LOW_CONFIDENCE_CLUSTER = "low_confidence_cluster"
    UNRESOLVED_SYMBOL_FRONTIER = "unresolved_symbol_frontier"


@dataclass
class CompileWarning:
    """A warning emitted during compilation."""

    kind: WarningKind
    unit_id: str
    message: str
    confidence: float


# ---------------------------------------------------------------------------
# Compile result
# ---------------------------------------------------------------------------


@dataclass
class CompileResult:
    """Output of compile(query, repo, budget)."""

    document: str
    trace: list[CompileTraceEntry]
    warnings: list[CompileWarning]
    omitted_frontier: list[str]
    confidence: float
    total_tokens: int
    budget: int


# ---------------------------------------------------------------------------
# Optimization result
# ---------------------------------------------------------------------------


@dataclass
class OptimizationResult:
    """Output of the budget optimizer.

    Contains the packing decision (which symbols at which tiers),
    the compile trace, warnings, and metadata for the compiler to
    assemble into a CompileResult.
    """

    tier_assignments: dict[str, ViewTier]
    trace: list[CompileTraceEntry]
    warnings: list[CompileWarning]
    omitted_frontier: list[str]
    confidence: float
    total_tokens: int
    budget: int


# ---------------------------------------------------------------------------
# Miss detection and recompilation
# ---------------------------------------------------------------------------


class MissKind(Enum):
    """What triggered a miss detection."""

    ABSENT_SYMBOL = "absent_symbol"
    OUT_OF_PACK_TRACE = "out_of_pack_trace"
    EDIT_TO_OMITTED = "edit_to_omitted"


@dataclass
class MissEvidence:
    """Evidence that the compiled document missed something."""

    kind: MissKind
    evidence: str
    source: str


@dataclass
class DiagnosticResult:
    """Output of diagnose(miss_evidence)."""

    missed_units: list[str]
    reason: str
    recommended_expansions: list[str]


@dataclass
class RecompileResult(CompileResult):
    """Output of recompile(previous_trace, new_evidence, delta_budget).

    Extends CompileResult with recompilation-specific fields.
    """

    previous_trace: list[CompileTraceEntry] = field(default_factory=list)
    new_units_added: list[str] = field(default_factory=list)
    budget_delta: int = 0

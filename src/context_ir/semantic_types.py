"""Semantic contract types for the semantic-first baseline.

This module freezes the durable syntax and semantic data model that later
parser, binder, resolver, renderer, ranking, optimizer, compiler, and
diagnostic slices build on. It intentionally defines contracts only and does
not fabricate semantic analysis results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ProofStatus(Enum):
    """Whether a reported fact is proven, unknown, or unsupported."""

    PROVEN = "proven"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"


class DefinitionKind(Enum):
    """Supported syntax-level definition forms."""

    MODULE = "module"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    CLASS = "class"
    METHOD = "method"


class ImportKind(Enum):
    """Syntax-level import forms recognized by the baseline contracts."""

    IMPORT = "import"
    FROM_IMPORT = "from_import"
    STAR_IMPORT = "star_import"


class ParameterKind(Enum):
    """Syntax-level parameter forms preserved for later binding."""

    POSITIONAL_ONLY = "positional_only"
    POSITIONAL_OR_KEYWORD = "positional_or_keyword"
    VARARG = "vararg"
    KEYWORD_ONLY = "keyword_only"
    KWARGS = "kwargs"


class SupportedDecorator(Enum):
    """Decorator facts that the initial semantic baseline models explicitly."""

    DATACLASS = "dataclass"


class DecoratorSupport(Enum):
    """Whether a decorator is explicitly supported, opaque, or unsupported."""

    SUPPORTED = "supported"
    OPAQUE = "opaque"
    UNSUPPORTED = "unsupported"


class BindingKind(Enum):
    """How a name becomes bound in a lexical scope."""

    DEFINITION = "definition"
    IMPORT = "import"
    PARAMETER = "parameter"
    ASSIGNMENT = "assignment"
    CLASS_ATTRIBUTE = "class_attribute"


class ImportTargetKind(Enum):
    """Kinds of object-model targets that an import binding can prove."""

    MODULE = "module"
    DEFINITION = "definition"
    EXTERNAL = "external"


class ResolvedSymbolKind(Enum):
    """Semantic symbol kinds exposed by the resolver layer."""

    MODULE = "module"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    CLASS = "class"
    METHOD = "method"
    IMPORTED_NAME = "imported_name"
    PARAMETER = "parameter"
    LOCAL = "local"
    ATTRIBUTE = "attribute"


class ReferenceContext(Enum):
    """How a resolved or unresolved reference is used."""

    LOAD = "load"
    STORE = "store"
    CALL = "call"
    ATTRIBUTE_ACCESS = "attribute_access"
    BASE_CLASS = "base_class"
    DECORATOR = "decorator"


class SemanticDependencyKind(Enum):
    """Kinds of semantically proven dependencies."""

    IMPORT = "import"
    CALL = "call"
    ATTRIBUTE = "attribute"
    INHERITANCE = "inheritance"
    DECORATOR = "decorator"


class DependencyProofKind(Enum):
    """Proof origin for a semantically proven dependency."""

    IMPORT_RESOLUTION = "import_resolution"
    CALL_RESOLUTION = "call_resolution"
    ATTRIBUTE_RESOLUTION = "attribute_resolution"
    BASE_CLASS_RESOLUTION = "base_class_resolution"
    DECORATOR_RESOLUTION = "decorator_resolution"


class UnresolvedReasonCode(Enum):
    """Stable reasons for unknown or unsupported semantic frontier items."""

    UNRESOLVED_NAME = "unresolved_name"
    UNRESOLVED_ATTRIBUTE = "unresolved_attribute"
    DYNAMIC_IMPORT = "dynamic_import"
    STAR_IMPORT = "star_import"
    ALIAS_CHAIN = "alias_chain"
    OPAQUE_DECORATOR = "opaque_decorator"
    UNSUPPORTED_DECORATOR = "unsupported_decorator"
    UNSUPPORTED_BASE_EXPRESSION = "unsupported_base_expression"
    UNSUPPORTED_CALL_TARGET = "unsupported_call_target"
    METACLASS_BEHAVIOR = "metaclass_behavior"
    RUNTIME_MUTATION = "runtime_mutation"
    EXEC_OR_EVAL = "exec_or_eval"


class DiagnosticSeverity(Enum):
    """Severity levels for semantic diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SyntaxDiagnosticCode(Enum):
    """Stable syntax-layer diagnostics emitted during syntax extraction."""

    PARSE_ERROR = "parse_error"


class SelectionBasis(Enum):
    """Downstream selection basis separate from semantic proof."""

    PINNED_OBLIGATION = "pinned_obligation"
    PROVEN_DEPENDENCY = "proven_dependency"
    HEURISTIC_CANDIDATE = "heuristic_candidate"
    UNRESOLVED_FRONTIER_ESCALATION = "unresolved_frontier_escalation"


class SemanticOptimizationWarningCode(Enum):
    """Minimal warning codes for semantic-first optimization and compilation."""

    BUDGET_PRESSURE = "budget_pressure"
    OMITTED_DIRECT_CANDIDATE = "omitted_direct_candidate"
    OMITTED_UNCERTAINTY = "omitted_uncertainty"


class SemanticMissKind(Enum):
    """Evidence kinds supported by the semantic-first diagnose/recompile layer."""

    ABSENT_SYMBOL = "absent_symbol"
    OUT_OF_PACK_TRACE = "out_of_pack_trace"
    EDIT_TO_OMITTED_PATH = "edit_to_omitted_path"


@dataclass(frozen=True)
class SourceSpan:
    """Normalized span for a source-backed fact."""

    start_line: int
    start_column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class SourceSite:
    """Stable source location with identifier and optional local snippet."""

    site_id: str
    file_path: str
    span: SourceSpan
    snippet: str | None = None

    def __post_init__(self) -> None:
        """Reject empty site identifiers."""
        if not self.site_id:
            raise ValueError("site_id must be non-empty")


@dataclass(frozen=True)
class SupportedSubsetBoundary:
    """Explicit first supported-subset boundary for semantic analysis."""

    subset_name: str = "python-static-core-v1"
    python_file_suffixes: tuple[str, ...] = (".py",)
    supported_definition_kinds: tuple[DefinitionKind, ...] = (
        DefinitionKind.MODULE,
        DefinitionKind.FUNCTION,
        DefinitionKind.ASYNC_FUNCTION,
        DefinitionKind.CLASS,
        DefinitionKind.METHOD,
    )
    supported_import_kinds: tuple[ImportKind, ...] = (
        ImportKind.IMPORT,
        ImportKind.FROM_IMPORT,
    )
    supported_decorators: tuple[SupportedDecorator, ...] = (
        SupportedDecorator.DATACLASS,
    )
    supported_reference_contexts: tuple[ReferenceContext, ...] = (
        ReferenceContext.LOAD,
        ReferenceContext.STORE,
        ReferenceContext.CALL,
        ReferenceContext.ATTRIBUTE_ACCESS,
        ReferenceContext.BASE_CLASS,
        ReferenceContext.DECORATOR,
    )
    unknown_without_proof: tuple[UnresolvedReasonCode, ...] = (
        UnresolvedReasonCode.DYNAMIC_IMPORT,
        UnresolvedReasonCode.STAR_IMPORT,
        UnresolvedReasonCode.ALIAS_CHAIN,
        UnresolvedReasonCode.OPAQUE_DECORATOR,
        UnresolvedReasonCode.UNSUPPORTED_DECORATOR,
        UnresolvedReasonCode.UNSUPPORTED_BASE_EXPRESSION,
        UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET,
        UnresolvedReasonCode.METACLASS_BEHAVIOR,
        UnresolvedReasonCode.RUNTIME_MUTATION,
        UnresolvedReasonCode.EXEC_OR_EVAL,
    )


@dataclass(frozen=True)
class SourceFileFact:
    """Syntax-level source inventory entry for one repository file."""

    file_id: str
    path: str
    module_name: str


@dataclass(frozen=True)
class SyntaxDiagnostic:
    """Syntax-layer diagnostic for a file that could not yield trustworthy facts."""

    diagnostic_id: str
    file_id: str
    site: SourceSite
    code: SyntaxDiagnosticCode
    message: str

    def __post_init__(self) -> None:
        """Reject empty identifiers and messages for syntax diagnostics."""
        if not self.diagnostic_id:
            raise ValueError("diagnostic_id must be non-empty")
        if not self.file_id:
            raise ValueError("file_id must be non-empty")
        if not self.message:
            raise ValueError("message must be non-empty")


@dataclass(frozen=True)
class RawDefinitionFact:
    """Unbound syntax fact for a raw definition node."""

    definition_id: str
    kind: DefinitionKind
    name: str
    qualified_name: str
    file_id: str
    site: SourceSite
    parent_definition_id: str | None = None


@dataclass(frozen=True)
class ParameterFact:
    """Syntax fact for one declared parameter on a function-like definition."""

    parameter_id: str
    owner_definition_id: str
    name: str
    kind: ParameterKind
    ordinal: int
    site: SourceSite
    annotation_text: str | None = None
    has_default: bool = False
    default_value_text: str | None = None

    def __post_init__(self) -> None:
        """Reject incomplete or inconsistent parameter syntax facts."""
        if not self.parameter_id:
            raise ValueError("parameter_id must be non-empty")
        if not self.owner_definition_id:
            raise ValueError("owner_definition_id must be non-empty")
        if not self.name:
            raise ValueError("name must be non-empty")
        if self.ordinal < 0:
            raise ValueError("ordinal must be >= 0")
        if not self.has_default and self.default_value_text is not None:
            raise ValueError(
                "default_value_text requires has_default=True on ParameterFact"
            )


@dataclass(frozen=True)
class ImportFact:
    """Syntax fact for an import statement before semantic resolution."""

    import_id: str
    file_id: str
    scope_id: str
    site: SourceSite
    kind: ImportKind
    module_name: str
    imported_name: str | None = None
    alias: str | None = None
    is_relative: bool = False


@dataclass(frozen=True)
class DecoratorFact:
    """Syntax fact for a decorator attached to a definition."""

    decorator_id: str
    owner_definition_id: str
    site: SourceSite
    expression_text: str
    support: DecoratorSupport
    supported_decorator: SupportedDecorator | None = None
    resolved_qualified_name: str | None = None

    def __post_init__(self) -> None:
        """Keep supported decorators explicit and opaque decorators unmodeled."""
        if (
            self.support is DecoratorSupport.SUPPORTED
            and self.supported_decorator is None
        ):
            raise ValueError("supported decorators must name the supported_decorator")
        if (
            self.support is not DecoratorSupport.SUPPORTED
            and self.supported_decorator is not None
        ):
            raise ValueError("non-supported decorators may not set supported_decorator")


@dataclass(frozen=True)
class BaseExpressionFact:
    """Syntax fact for a class base expression."""

    base_expression_id: str
    owner_definition_id: str
    site: SourceSite
    expression_text: str


@dataclass(frozen=True)
class AssignmentFact:
    """Syntax fact for an assignment statement inside a scope."""

    assignment_id: str
    scope_id: str
    site: SourceSite
    target_text: str
    value_text: str | None = None
    annotation_text: str | None = None


@dataclass(frozen=True)
class CallSiteFact:
    """Syntax fact for a call expression site."""

    call_site_id: str
    enclosing_scope_id: str
    site: SourceSite
    callee_text: str
    argument_count: int


@dataclass(frozen=True)
class AttributeSiteFact:
    """Syntax fact for an attribute access site."""

    attribute_site_id: str
    enclosing_scope_id: str
    site: SourceSite
    base_text: str
    attribute_name: str
    context: ReferenceContext = ReferenceContext.ATTRIBUTE_ACCESS


@dataclass
class SyntaxProgram:
    """Syntax facts collected for the semantic-first baseline."""

    repo_root: Path
    supported_subset: SupportedSubsetBoundary = field(
        default_factory=SupportedSubsetBoundary
    )
    source_files: dict[str, SourceFileFact] = field(default_factory=dict)
    diagnostics: list[SyntaxDiagnostic] = field(default_factory=list)
    definitions: list[RawDefinitionFact] = field(default_factory=list)
    parameters: list[ParameterFact] = field(default_factory=list)
    imports: list[ImportFact] = field(default_factory=list)
    decorators: list[DecoratorFact] = field(default_factory=list)
    base_expressions: list[BaseExpressionFact] = field(default_factory=list)
    assignments: list[AssignmentFact] = field(default_factory=list)
    call_sites: list[CallSiteFact] = field(default_factory=list)
    attribute_sites: list[AttributeSiteFact] = field(default_factory=list)


@dataclass(frozen=True)
class ResolvedSymbol:
    """Concrete symbol identity proven by semantic analysis."""

    symbol_id: str
    kind: ResolvedSymbolKind
    qualified_name: str
    file_id: str
    definition_site: SourceSite
    defining_scope_id: str
    supported_decorators: tuple[SupportedDecorator, ...] = ()


@dataclass(frozen=True)
class BindingFact:
    """Name binding fact produced by the binder layer."""

    binding_id: str
    scope_id: str
    name: str
    binding_kind: BindingKind
    symbol_id: str
    site: SourceSite


@dataclass(frozen=True)
class ResolvedImport:
    """Proven import target recorded by the resolver object model."""

    import_id: str
    binding_symbol_id: str
    bound_name: str
    scope_id: str
    site: SourceSite
    target_kind: ImportTargetKind
    target_qualified_name: str
    target_symbol_id: str | None = None
    proof_status: ProofStatus = ProofStatus.PROVEN

    def __post_init__(self) -> None:
        """Keep import targets explicit and concrete where possible."""
        if not self.import_id:
            raise ValueError("import_id must be non-empty")
        if not self.binding_symbol_id:
            raise ValueError("binding_symbol_id must be non-empty")
        if not self.bound_name:
            raise ValueError("bound_name must be non-empty")
        if not self.scope_id:
            raise ValueError("scope_id must be non-empty")
        if not self.target_qualified_name:
            raise ValueError("target_qualified_name must be non-empty")
        if self.target_kind is ImportTargetKind.EXTERNAL:
            if self.target_symbol_id is not None:
                raise ValueError("external import targets may not set target_symbol_id")
        elif self.target_symbol_id is None:
            raise ValueError(
                "repository module and definition targets require target_symbol_id"
            )
        if self.proof_status is not ProofStatus.PROVEN:
            raise ValueError("resolved imports must have proof_status=PROVEN")


@dataclass(frozen=True)
class DataclassModel:
    """Proven narrow object-model fact for a supported ``@dataclass`` class."""

    model_id: str
    class_symbol_id: str
    decorator_reference_id: str
    decorator_site: SourceSite
    decorator_target_qualified_name: str = "dataclasses.dataclass"
    proof_status: ProofStatus = ProofStatus.PROVEN

    def __post_init__(self) -> None:
        """Require concrete proof for supported dataclass models."""
        if not self.model_id:
            raise ValueError("model_id must be non-empty")
        if not self.class_symbol_id:
            raise ValueError("class_symbol_id must be non-empty")
        if not self.decorator_reference_id:
            raise ValueError("decorator_reference_id must be non-empty")
        if not self.decorator_target_qualified_name:
            raise ValueError("decorator_target_qualified_name must be non-empty")
        if self.proof_status is not ProofStatus.PROVEN:
            raise ValueError("dataclass models must have proof_status=PROVEN")


@dataclass(frozen=True)
class DataclassField:
    """Proven dataclass field fact for one annotated simple class attribute."""

    field_id: str
    class_symbol_id: str
    field_symbol_id: str
    name: str
    site: SourceSite
    annotation_text: str
    has_default: bool = False
    default_value_text: str | None = None
    proof_status: ProofStatus = ProofStatus.PROVEN

    def __post_init__(self) -> None:
        """Keep dataclass field facts narrow and source-backed."""
        if not self.field_id:
            raise ValueError("field_id must be non-empty")
        if not self.class_symbol_id:
            raise ValueError("class_symbol_id must be non-empty")
        if not self.field_symbol_id:
            raise ValueError("field_symbol_id must be non-empty")
        if not self.name:
            raise ValueError("name must be non-empty")
        if not self.annotation_text:
            raise ValueError("annotation_text must be non-empty")
        if not self.has_default and self.default_value_text is not None:
            raise ValueError("default_value_text requires has_default=True")
        if self.proof_status is not ProofStatus.PROVEN:
            raise ValueError("dataclass fields must have proof_status=PROVEN")


@dataclass(frozen=True)
class ResolvedReference:
    """Reference proven to resolve to a concrete symbol identity."""

    reference_id: str
    site: SourceSite
    name: str
    context: ReferenceContext
    resolved_symbol_id: str
    enclosing_scope_id: str
    proof_status: ProofStatus = ProofStatus.PROVEN

    def __post_init__(self) -> None:
        """Keep resolved references separate from frontier items."""
        if self.proof_status is not ProofStatus.PROVEN:
            raise ValueError("resolved references must have proof_status=PROVEN")


@dataclass(frozen=True)
class SemanticDependency:
    """A semantically proven dependency between concrete resolved symbols."""

    dependency_id: str
    source_symbol_id: str
    target_symbol_id: str
    kind: SemanticDependencyKind
    proof_kind: DependencyProofKind
    evidence_site_id: str | None = None
    evidence_reference_id: str | None = None
    proof_status: ProofStatus = ProofStatus.PROVEN

    def __post_init__(self) -> None:
        """Keep semantic dependencies concrete and explicitly proven."""
        if not self.source_symbol_id or not self.target_symbol_id:
            raise ValueError(
                "semantic dependencies require concrete source and target symbols"
            )
        if self.proof_status is not ProofStatus.PROVEN:
            raise ValueError("semantic dependencies must have proof_status=PROVEN")


@dataclass(frozen=True)
class UnresolvedAccess:
    """Unknown semantic frontier item that still carries source context."""

    access_id: str
    site: SourceSite
    access_text: str
    context: ReferenceContext
    enclosing_scope_id: str
    reason_code: UnresolvedReasonCode
    detail: str | None = None
    proof_status: ProofStatus = ProofStatus.UNKNOWN

    def __post_init__(self) -> None:
        """Keep unresolved frontier items distinct from proven facts."""
        if self.proof_status is not ProofStatus.UNKNOWN:
            raise ValueError("unresolved accesses must have proof_status=UNKNOWN")


@dataclass(frozen=True)
class UnsupportedConstruct:
    """Unsupported syntax or semantic construct surfaced explicitly in analysis."""

    construct_id: str
    site: SourceSite
    construct_text: str
    reason_code: UnresolvedReasonCode
    detail: str | None = None
    enclosing_scope_id: str | None = None
    proof_status: ProofStatus = ProofStatus.UNSUPPORTED

    def __post_init__(self) -> None:
        """Keep unsupported constructs distinct from unknown frontier items."""
        if self.proof_status is not ProofStatus.UNSUPPORTED:
            raise ValueError(
                "unsupported constructs must have proof_status=UNSUPPORTED"
            )


@dataclass(frozen=True)
class ResolverDiagnostic:
    """Diagnostic emitted while deriving semantic facts or frontier items."""

    diagnostic_id: str
    site: SourceSite
    severity: DiagnosticSeverity
    reason_code: UnresolvedReasonCode
    message: str
    related_symbol_id: str | None = None


@dataclass(frozen=True)
class SelectionDirective:
    """Downstream selection input kept separate from semantic proof types."""

    directive_id: str
    basis: SelectionBasis
    symbol_id: str | None = None
    frontier_item_id: str | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        """Require the correct target for each selection basis."""
        if self.basis is SelectionBasis.UNRESOLVED_FRONTIER_ESCALATION:
            if self.frontier_item_id is None:
                raise ValueError("frontier escalations require frontier_item_id")
            return
        if self.symbol_id is None:
            raise ValueError("non-frontier selection directives require symbol_id")


@dataclass(frozen=True)
class SemanticSelectionRecord:
    """Traceable selection record for one compiled semantic unit."""

    unit_id: str
    detail: str
    token_count: int
    basis: SelectionBasis
    reason: str
    edit_score: float
    support_score: float

    def __post_init__(self) -> None:
        """Keep selected detail, cost, and scores concrete and bounded."""
        if not self.unit_id:
            raise ValueError("unit_id must be non-empty")
        if self.detail not in {"identity", "summary", "source"}:
            raise ValueError("detail must be identity, summary, or source")
        if self.token_count < 0:
            raise ValueError("token_count must be >= 0")
        if not self.reason:
            raise ValueError("reason must be non-empty")
        if not 0.0 <= self.edit_score <= 1.0:
            raise ValueError("edit_score must be within [0.0, 1.0]")
        if not 0.0 <= self.support_score <= 1.0:
            raise ValueError("support_score must be within [0.0, 1.0]")


@dataclass(frozen=True)
class SemanticOptimizationWarning:
    """Truthful warning emitted during semantic-first optimization."""

    code: SemanticOptimizationWarningCode
    message: str
    unit_id: str | None = None

    def __post_init__(self) -> None:
        """Reject empty warning messages."""
        if not self.message:
            raise ValueError("message must be non-empty")


@dataclass(frozen=True)
class SemanticOptimizationResult:
    """Budget-feasible selection result over semantic units."""

    selections: tuple[SemanticSelectionRecord, ...]
    omitted_unit_ids: tuple[str, ...]
    warnings: tuple[SemanticOptimizationWarning, ...]
    total_tokens: int
    budget: int
    confidence: float

    def __post_init__(self) -> None:
        """Keep optimization results bounded and internally consistent."""
        if self.total_tokens < 0:
            raise ValueError("total_tokens must be >= 0")
        if self.budget < 0:
            raise ValueError("budget must be >= 0")
        if self.total_tokens > self.budget:
            raise ValueError("total_tokens may not exceed budget")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within [0.0, 1.0]")

        selected_ids = [record.unit_id for record in self.selections]
        if len(selected_ids) != len(set(selected_ids)):
            raise ValueError("selection records must have unique unit_id values")
        if set(selected_ids) & set(self.omitted_unit_ids):
            raise ValueError("selected and omitted unit IDs must be disjoint")


@dataclass(frozen=True)
class SemanticCompileContext:
    """Minimal durable compile context required for semantic recompilation."""

    query: str


@dataclass(frozen=True)
class SemanticCompileResult:
    """Compiled semantic context artifact kept separate from ``SemanticProgram``."""

    document: str
    optimization: SemanticOptimizationResult
    omitted_unit_ids: tuple[str, ...]
    total_tokens: int
    budget: int
    confidence: float
    compile_context: SemanticCompileContext | None = None

    def __post_init__(self) -> None:
        """Keep compile outputs bounded and aligned with optimization trace."""
        if not self.document:
            raise ValueError("document must be non-empty")
        if self.total_tokens < 0:
            raise ValueError("total_tokens must be >= 0")
        if self.budget < 0:
            raise ValueError("budget must be >= 0")
        if self.total_tokens > self.budget:
            raise ValueError("SemanticCompileResult.total_tokens may not exceed budget")
        if self.omitted_unit_ids != self.optimization.omitted_unit_ids:
            raise ValueError(
                "SemanticCompileResult.omitted_unit_ids must match optimization"
            )
        if self.total_tokens < self.optimization.total_tokens:
            raise ValueError(
                "SemanticCompileResult.total_tokens must cover optimization tokens"
            )
        if self.budget != self.optimization.budget:
            raise ValueError("SemanticCompileResult.budget must match optimization")
        if self.confidence != self.optimization.confidence:
            raise ValueError("SemanticCompileResult.confidence must match optimization")


@dataclass(frozen=True)
class SemanticMissEvidence:
    """Concrete evidence describing how a prior semantic compile missed context."""

    kind: SemanticMissKind
    evidence: str
    source: str | None = None

    def __post_init__(self) -> None:
        """Reject empty miss evidence payloads."""
        if not self.evidence:
            raise ValueError("evidence must be non-empty")


@dataclass(frozen=True)
class SemanticDiagnosticResult:
    """Conservative diagnosis of grounded semantic miss evidence."""

    grounded_unit_ids: tuple[str, ...]
    omitted_unit_ids: tuple[str, ...]
    too_shallow_unit_ids: tuple[str, ...]
    sufficiently_represented_unit_ids: tuple[str, ...]
    recommended_expansions: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        """Keep grounded classifications disjoint and reasoned."""
        if not self.reason:
            raise ValueError("reason must be non-empty")

        grounded = set(self.grounded_unit_ids)
        omitted = set(self.omitted_unit_ids)
        too_shallow = set(self.too_shallow_unit_ids)
        sufficient = set(self.sufficiently_represented_unit_ids)
        if len(self.grounded_unit_ids) != len(grounded):
            raise ValueError("grounded_unit_ids must be unique")
        if len(self.recommended_expansions) != len(set(self.recommended_expansions)):
            raise ValueError("recommended_expansions must be unique")
        if omitted & too_shallow:
            raise ValueError("omitted and too_shallow unit IDs must be disjoint")
        if omitted & sufficient:
            raise ValueError("omitted and sufficient unit IDs must be disjoint")
        if too_shallow & sufficient:
            raise ValueError("too_shallow and sufficient unit IDs must be disjoint")
        classified = omitted | too_shallow | sufficient
        if classified != grounded:
            raise ValueError(
                "grounded_unit_ids must equal the union of classified unit IDs"
            )


@dataclass(frozen=True)
class SemanticRecompileResult:
    """Result of re-running semantic compilation after a diagnosis pass."""

    compile_result: SemanticCompileResult
    diagnostic: SemanticDiagnosticResult
    budget_delta: int
    newly_selected_unit_ids: tuple[str, ...]
    upgraded_unit_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Keep change accounting bounded and disjoint."""
        if self.budget_delta < 0:
            raise ValueError("budget_delta must be >= 0")
        if len(self.newly_selected_unit_ids) != len(set(self.newly_selected_unit_ids)):
            raise ValueError("newly_selected_unit_ids must be unique")
        if len(self.upgraded_unit_ids) != len(set(self.upgraded_unit_ids)):
            raise ValueError("upgraded_unit_ids must be unique")
        if set(self.newly_selected_unit_ids) & set(self.upgraded_unit_ids):
            raise ValueError(
                "newly_selected_unit_ids and upgraded_unit_ids must be disjoint"
            )


@dataclass
class SemanticProgram:
    """Durable semantic product of repository analysis."""

    repo_root: Path
    syntax: SyntaxProgram
    supported_subset: SupportedSubsetBoundary = field(
        default_factory=SupportedSubsetBoundary
    )
    resolved_symbols: dict[str, ResolvedSymbol] = field(default_factory=dict)
    bindings: list[BindingFact] = field(default_factory=list)
    resolved_imports: list[ResolvedImport] = field(default_factory=list)
    dataclass_models: list[DataclassModel] = field(default_factory=list)
    dataclass_fields: list[DataclassField] = field(default_factory=list)
    resolved_references: list[ResolvedReference] = field(default_factory=list)
    proven_dependencies: list[SemanticDependency] = field(default_factory=list)
    unresolved_frontier: list[UnresolvedAccess] = field(default_factory=list)
    unsupported_constructs: list[UnsupportedConstruct] = field(default_factory=list)
    diagnostics: list[ResolverDiagnostic] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Keep the bundled syntax program aligned with the semantic root."""
        if self.syntax.repo_root != self.repo_root:
            raise ValueError(
                "SemanticProgram.repo_root must match SyntaxProgram.repo_root"
            )
        if self.syntax.supported_subset != self.supported_subset:
            raise ValueError(
                "SemanticProgram.supported_subset must match "
                "SyntaxProgram.supported_subset"
            )


def analyze_repository(repo_root: Path | str) -> SemanticProgram:
    """Analyze a repository with the accepted semantic-first pipeline."""
    from context_ir.analyzer import analyze_repository as _analyze_repository

    return _analyze_repository(repo_root)


__all__ = [
    "AssignmentFact",
    "AttributeSiteFact",
    "BaseExpressionFact",
    "BindingFact",
    "BindingKind",
    "CallSiteFact",
    "DataclassField",
    "DataclassModel",
    "DecoratorFact",
    "DecoratorSupport",
    "DefinitionKind",
    "DependencyProofKind",
    "DiagnosticSeverity",
    "ImportFact",
    "ImportKind",
    "ImportTargetKind",
    "ParameterFact",
    "ParameterKind",
    "ProofStatus",
    "RawDefinitionFact",
    "ReferenceContext",
    "ResolvedImport",
    "ResolvedReference",
    "ResolvedSymbol",
    "ResolvedSymbolKind",
    "ResolverDiagnostic",
    "SelectionBasis",
    "SelectionDirective",
    "SemanticCompileContext",
    "SemanticCompileResult",
    "SemanticDependency",
    "SemanticDiagnosticResult",
    "SemanticDependencyKind",
    "SemanticMissEvidence",
    "SemanticMissKind",
    "SemanticOptimizationResult",
    "SemanticOptimizationWarning",
    "SemanticOptimizationWarningCode",
    "SemanticProgram",
    "SemanticRecompileResult",
    "SemanticSelectionRecord",
    "SourceFileFact",
    "SourceSite",
    "SourceSpan",
    "SupportedDecorator",
    "SupportedSubsetBoundary",
    "SyntaxDiagnostic",
    "SyntaxDiagnosticCode",
    "SyntaxProgram",
    "UnresolvedAccess",
    "UnresolvedReasonCode",
    "UnsupportedConstruct",
    "analyze_repository",
]

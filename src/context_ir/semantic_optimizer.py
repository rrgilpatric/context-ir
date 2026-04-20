"""Semantic-first budget optimizer over renderable semantic units."""

from __future__ import annotations

from dataclasses import dataclass

from context_ir.semantic_renderer import (
    RenderDetail,
    RenderedUnit,
    RenderedUnitKind,
    render_semantic_unit,
)
from context_ir.semantic_scorer import SemanticScoringResult, SemanticUnitScore
from context_ir.semantic_types import (
    CapabilityTier,
    DownstreamVisibility,
    EvidenceOriginKind,
    ReplayStatus,
    SelectionBasis,
    SemanticOptimizationResult,
    SemanticOptimizationWarning,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticProvenanceRecord,
    SemanticSelectionRecord,
    SemanticSubjectKind,
    SemanticUnitTraceSummary,
    SourceSite,
)

_DETAIL_ORDER: tuple[RenderDetail, ...] = (
    RenderDetail.IDENTITY,
    RenderDetail.SUMMARY,
    RenderDetail.SOURCE,
)
_DETAIL_RANK: dict[RenderDetail, int] = {
    detail: index for index, detail in enumerate(_DETAIL_ORDER)
}
_EDIT_VALUE: dict[RenderDetail, float] = {
    RenderDetail.IDENTITY: 0.20,
    RenderDetail.SUMMARY: 0.60,
    RenderDetail.SOURCE: 1.00,
}
_SUPPORT_VALUE: dict[RenderDetail, float] = {
    RenderDetail.IDENTITY: 0.35,
    RenderDetail.SUMMARY: 0.85,
    RenderDetail.SOURCE: 0.55,
}
_MIN_RELEVANCE = 0.05
_DIRECT_SOURCE_THRESHOLD = 0.30
_DIRECT_SUMMARY_THRESHOLD = 0.20
_SUPPORT_SUMMARY_THRESHOLD = 0.24
_SOURCE_PROMOTION_SLACK = 8
_SUPPORT_DETAIL_PROMOTION_SLACK = 2
_FOCUS_SOURCE_SUPPORT_THRESHOLD = 0.26
_STRONG_DIRECT_WARNING_THRESHOLD = 0.50
_UNCERTAINTY_WARNING_THRESHOLD = 0.30


@dataclass(frozen=True)
class _SemanticCandidate:
    """One renderable semantic unit with its score and exact render costs."""

    unit_id: str
    kind: RenderedUnitKind
    provenance: SourceSite
    file_scope_id: str | None
    score: SemanticUnitScore
    renders: dict[RenderDetail, RenderedUnit]
    incoming_dependency_sources: tuple[str, ...]
    outgoing_dependency_targets: tuple[str, ...]
    enclosing_scope_id: str | None
    trace_summary: SemanticUnitTraceSummary


_PRIMARY_TRACE_DEFAULTS: dict[
    SemanticSubjectKind, tuple[CapabilityTier, EvidenceOriginKind, ReplayStatus]
] = {
    SemanticSubjectKind.SYMBOL: (
        CapabilityTier.STATICALLY_PROVED,
        EvidenceOriginKind.STATIC_DERIVATION_RULE,
        ReplayStatus.DETERMINISTIC_STATIC,
    ),
    SemanticSubjectKind.DEPENDENCY: (
        CapabilityTier.STATICALLY_PROVED,
        EvidenceOriginKind.STATIC_DERIVATION_RULE,
        ReplayStatus.DETERMINISTIC_STATIC,
    ),
    SemanticSubjectKind.FRONTIER_ITEM: (
        CapabilityTier.HEURISTIC_FRONTIER,
        EvidenceOriginKind.HEURISTIC_RULE,
        ReplayStatus.NON_PROOF_HEURISTIC,
    ),
    SemanticSubjectKind.UNSUPPORTED_FINDING: (
        CapabilityTier.UNSUPPORTED_OPAQUE,
        EvidenceOriginKind.UNSUPPORTED_REASON_CODE,
        ReplayStatus.OPAQUE_BOUNDARY,
    ),
}
_SUBJECT_KIND_BY_RENDERED_UNIT: dict[RenderedUnitKind, SemanticSubjectKind] = {
    RenderedUnitKind.PROVEN_SYMBOL: SemanticSubjectKind.SYMBOL,
    RenderedUnitKind.UNRESOLVED_FRONTIER: SemanticSubjectKind.FRONTIER_ITEM,
    RenderedUnitKind.UNSUPPORTED_CONSTRUCT: SemanticSubjectKind.UNSUPPORTED_FINDING,
}


def optimize_semantic_units(
    program: SemanticProgram,
    scoring: SemanticScoringResult,
    budget: int,
) -> SemanticOptimizationResult:
    """Select budget-feasible semantic units without mutating ``program``."""
    if budget < 0:
        raise ValueError("budget must be >= 0")

    candidates = _build_candidates(program, scoring)
    if not candidates:
        return SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=budget,
            confidence=1.0,
        )

    ordered_candidates = sorted(candidates, key=_candidate_sort_key)
    candidate_by_id = {candidate.unit_id: candidate for candidate in ordered_candidates}
    selections: list[SemanticSelectionRecord] = []
    omitted_unit_ids: list[str] = []
    remaining_budget = budget
    current_focus_id: str | None = None
    current_focus_support_count = 0
    current_focus_has_uncertainty_surface = False
    current_focus_inherited_uncertainty_surface = False
    pending_focus_id: str | None = None
    focus_unit_ids: set[str] = set()
    suppressed_uncertainty_unit_ids: set[str] = set()

    pending_candidates = list(ordered_candidates)
    while pending_candidates:
        current_focus_file_scope_id = (
            candidate_by_id[current_focus_id].file_scope_id
            if current_focus_id is not None
            else None
        )
        pending_candidates.sort(
            key=lambda candidate: _candidate_sort_key(
                candidate,
                current_focus_id=current_focus_id,
                current_focus_file_scope_id=current_focus_file_scope_id,
                current_focus_has_support=current_focus_support_count > 0,
                current_focus_has_uncertainty_surface=(
                    current_focus_has_uncertainty_surface
                ),
            )
        )
        candidate = pending_candidates.pop(0)
        chosen_detail = _choose_detail(
            candidate,
            remaining_budget,
            current_focus_id=current_focus_id,
            current_focus_file_scope_id=current_focus_file_scope_id,
            current_focus_inherited_uncertainty_surface=(
                current_focus_inherited_uncertainty_surface
            ),
        )
        if chosen_detail is None:
            omitted_unit_ids.append(candidate.unit_id)
            if _is_policy_suppressed_uncertainty_candidate(
                candidate,
                current_focus_id=current_focus_id,
                current_focus_file_scope_id=current_focus_file_scope_id,
                current_focus_inherited_uncertainty_surface=(
                    current_focus_inherited_uncertainty_surface
                ),
            ):
                suppressed_uncertainty_unit_ids.add(candidate.unit_id)
            if (
                pending_focus_id is not None
                and current_focus_id is not None
                and _is_uncertainty_for_focus(
                    candidate,
                    focus_unit_id=current_focus_id,
                    focus_file_scope_id=current_focus_file_scope_id,
                )
            ):
                current_focus_id = pending_focus_id
                focus_unit_ids.add(current_focus_id)
                pending_focus_id = None
                current_focus_support_count = 0
                current_focus_inherited_uncertainty_surface = False
            continue

        rendered = candidate.renders[chosen_detail]
        preferred_detail = _preferred_detail(candidate)
        selections.append(
            _selection_record(
                candidate=candidate,
                chosen_detail=chosen_detail,
                preferred_detail=preferred_detail,
                program=program,
                scoring=scoring,
            )
        )
        remaining_budget -= rendered.token_count
        if _is_focus_selection(candidate, chosen_detail):
            if current_focus_id is None:
                current_focus_id = candidate.unit_id
                focus_unit_ids.add(current_focus_id)
                current_focus_support_count = 0
                current_focus_has_uncertainty_surface = False
                current_focus_inherited_uncertainty_surface = False
                pending_focus_id = None
                continue
            if _is_direct_caller_of_focus(
                candidate,
                focus_unit_id=current_focus_id,
            ):
                if _focus_has_uncertainty_candidate(
                    current_focus_id,
                    current_focus_file_scope_id,
                    pending_candidates,
                ):
                    pending_focus_id = candidate.unit_id
                    continue
                current_focus_id = candidate.unit_id
                focus_unit_ids.add(current_focus_id)
                current_focus_support_count = 0
                current_focus_has_uncertainty_surface = False
                current_focus_inherited_uncertainty_surface = False
                pending_focus_id = None
                continue
        if current_focus_id is not None and _is_uncertainty_for_focus(
            candidate,
            focus_unit_id=current_focus_id,
            focus_file_scope_id=current_focus_file_scope_id,
        ):
            current_focus_has_uncertainty_surface = True
            if pending_focus_id is not None:
                current_focus_id = pending_focus_id
                focus_unit_ids.add(current_focus_id)
                pending_focus_id = None
                current_focus_support_count = 0
                current_focus_inherited_uncertainty_surface = True
                continue
        if current_focus_id is not None and _is_support_for_focus(
            candidate,
            focus_unit_id=current_focus_id,
        ):
            current_focus_support_count += 1

    selections.sort(
        key=lambda record: _candidate_sort_key(candidate_by_id[record.unit_id])
    )
    omitted_unit_ids.sort(
        key=lambda unit_id: _candidate_sort_key(candidate_by_id[unit_id])
    )

    warnings = tuple(
        _build_warnings(
            candidates=ordered_candidates,
            selections=tuple(selections),
            omitted_unit_ids=tuple(omitted_unit_ids),
            focus_unit_ids=frozenset(focus_unit_ids),
            suppressed_uncertainty_unit_ids=frozenset(suppressed_uncertainty_unit_ids),
            program=program,
        )
    )
    total_tokens = sum(record.token_count for record in selections)
    confidence = _confidence(
        candidates=ordered_candidates,
        selections=tuple(selections),
    )
    return SemanticOptimizationResult(
        selections=tuple(selections),
        omitted_unit_ids=tuple(omitted_unit_ids),
        warnings=warnings,
        total_tokens=total_tokens,
        budget=budget,
        confidence=confidence,
    )


def _build_candidates(
    program: SemanticProgram,
    scoring: SemanticScoringResult,
) -> list[_SemanticCandidate]:
    """Materialize every renderable semantic unit with exact render costs."""
    renderable_unit_ids = _renderable_unit_ids(program)
    expected_unit_ids = set(renderable_unit_ids)
    scoring_unit_ids = set(scoring.scores)
    if scoring_unit_ids != expected_unit_ids:
        raise ValueError("scoring.scores must cover exactly the renderable unit IDs")

    incoming_dependency_sources = _incoming_dependency_sources(program)
    outgoing_dependency_targets = _outgoing_dependency_targets(program)
    enclosing_scope_ids = _enclosing_scope_ids(program)
    file_scope_ids = _file_scope_ids(program)
    trace_summaries = _trace_summaries_by_subject(program)
    candidates: list[_SemanticCandidate] = []

    for unit_id in renderable_unit_ids:
        identity = render_semantic_unit(program, unit_id, RenderDetail.IDENTITY)
        summary = render_semantic_unit(program, unit_id, RenderDetail.SUMMARY)
        source = render_semantic_unit(program, unit_id, RenderDetail.SOURCE)
        subject_kind = _SUBJECT_KIND_BY_RENDERED_UNIT[identity.kind]
        renders = {
            RenderDetail.IDENTITY: identity,
            RenderDetail.SUMMARY: summary,
            RenderDetail.SOURCE: source,
        }
        candidates.append(
            _SemanticCandidate(
                unit_id=unit_id,
                kind=identity.kind,
                provenance=identity.provenance,
                file_scope_id=file_scope_ids.get(identity.provenance.file_path),
                score=scoring.scores[unit_id],
                renders=renders,
                incoming_dependency_sources=incoming_dependency_sources.get(
                    unit_id, ()
                ),
                outgoing_dependency_targets=outgoing_dependency_targets.get(
                    unit_id, ()
                ),
                enclosing_scope_id=enclosing_scope_ids.get(unit_id),
                trace_summary=trace_summaries[(subject_kind, unit_id)],
            )
        )

    return candidates


def _trace_summaries_by_subject(
    program: SemanticProgram,
) -> dict[tuple[SemanticSubjectKind, str], SemanticUnitTraceSummary]:
    """Build deterministic compile-visible trace summaries for renderable units."""
    records_by_subject: dict[
        tuple[SemanticSubjectKind, str], list[SemanticProvenanceRecord]
    ] = {}
    for record in program.provenance_records:
        if DownstreamVisibility.COMPILE not in record.downstream_visibility:
            continue
        records_by_subject.setdefault(
            (record.subject_kind, record.subject_id), []
        ).append(record)

    summaries: dict[tuple[SemanticSubjectKind, str], SemanticUnitTraceSummary] = {}
    subject_keys = [
        *(
            (SemanticSubjectKind.SYMBOL, symbol_id)
            for symbol_id in program.resolved_symbols
        ),
        *(
            (SemanticSubjectKind.FRONTIER_ITEM, access.access_id)
            for access in program.unresolved_frontier
        ),
        *(
            (SemanticSubjectKind.UNSUPPORTED_FINDING, construct.construct_id)
            for construct in program.unsupported_constructs
        ),
    ]
    for subject_kind, subject_id in subject_keys:
        key = (subject_kind, subject_id)
        summaries[key] = _trace_summary_for_subject(
            subject_kind=subject_kind,
            subject_id=subject_id,
            records=records_by_subject.get(key, ()),
        )
    return summaries


def _trace_summary_for_subject(
    *,
    subject_kind: SemanticSubjectKind,
    subject_id: str,
    records: list[SemanticProvenanceRecord] | tuple[SemanticProvenanceRecord, ...],
) -> SemanticUnitTraceSummary:
    """Summarize primary subject truth plus additive runtime-backed support."""
    ordered_records = tuple(sorted(records, key=lambda record: record.record_id))
    primary_record = next(
        (
            record
            for record in ordered_records
            if record.capability_tier is not CapabilityTier.RUNTIME_BACKED
        ),
        None,
    )
    if primary_record is None:
        (
            primary_capability_tier,
            primary_evidence_origin,
            primary_replay_status,
        ) = _PRIMARY_TRACE_DEFAULTS[subject_kind]
    else:
        primary_capability_tier = primary_record.capability_tier
        primary_evidence_origin = primary_record.evidence_origin
        primary_replay_status = primary_record.replay_status

    return SemanticUnitTraceSummary(
        subject_id=subject_id,
        subject_kind=subject_kind,
        primary_capability_tier=primary_capability_tier,
        primary_evidence_origin=primary_evidence_origin,
        primary_replay_status=primary_replay_status,
        attached_runtime_provenance_record_ids=tuple(
            record.record_id
            for record in ordered_records
            if record.capability_tier is CapabilityTier.RUNTIME_BACKED
        ),
    )


def _renderable_unit_ids(program: SemanticProgram) -> list[str]:
    """Return every semantic unit ID that the accepted renderer can represent."""
    return sorted(
        [
            *program.resolved_symbols.keys(),
            *(access.access_id for access in program.unresolved_frontier),
            *(construct.construct_id for construct in program.unsupported_constructs),
        ]
    )


def _incoming_dependency_sources(
    program: SemanticProgram,
) -> dict[str, tuple[str, ...]]:
    """Index concrete dependency sources by dependency target."""
    sources_by_target: dict[str, set[str]] = {}
    for dependency in program.proven_dependencies:
        sources_by_target.setdefault(dependency.target_symbol_id, set()).add(
            dependency.source_symbol_id
        )
    return {
        unit_id: tuple(sorted(source_ids))
        for unit_id, source_ids in sources_by_target.items()
    }


def _file_scope_ids(program: SemanticProgram) -> dict[str, str]:
    """Return the module-scope symbol ID for each source file."""
    return {
        symbol.definition_site.file_path: unit_id
        for unit_id, symbol in program.resolved_symbols.items()
        if symbol.kind.value == "module"
    }


def _enclosing_scope_ids(program: SemanticProgram) -> dict[str, str | None]:
    """Return enclosing-scope IDs for uncertainty surfaces."""
    result: dict[str, str | None] = {}
    for access in program.unresolved_frontier:
        result[access.access_id] = access.enclosing_scope_id
    for construct in program.unsupported_constructs:
        result[construct.construct_id] = construct.enclosing_scope_id
    return result


def _outgoing_dependency_targets(
    program: SemanticProgram,
) -> dict[str, tuple[str, ...]]:
    """Index direct dependency targets by concrete source symbol."""
    targets_by_source: dict[str, set[str]] = {}
    for dependency in program.proven_dependencies:
        targets_by_source.setdefault(dependency.source_symbol_id, set()).add(
            dependency.target_symbol_id
        )
    return {
        unit_id: tuple(sorted(target_ids))
        for unit_id, target_ids in targets_by_source.items()
    }


def _candidate_sort_key(
    candidate: _SemanticCandidate,
    *,
    current_focus_id: str | None = None,
    current_focus_file_scope_id: str | None = None,
    current_focus_has_support: bool = False,
    current_focus_has_uncertainty_surface: bool = False,
) -> tuple[float, float, float, float, int, str, int, int, str]:
    """Sort by strongest relevance first, then stable source order."""
    if current_focus_id is not None:
        pack_score = _support_pack_score(candidate)
        scope_priority = _scope_priority(
            candidate,
            current_focus_id=current_focus_id,
            current_focus_file_scope_id=current_focus_file_scope_id,
            current_focus_has_support=current_focus_has_support,
            current_focus_has_uncertainty_surface=(
                current_focus_has_uncertainty_surface
            ),
        )
        proven_priority = 0 if candidate.kind is RenderedUnitKind.PROVEN_SYMBOL else 1
        span = candidate.provenance.span
        return (
            float(scope_priority),
            -_focus_relevance_score(
                candidate,
                current_focus_id=current_focus_id,
                current_focus_has_support=current_focus_has_support,
            ),
            -pack_score,
            -candidate.score.p_edit,
            proven_priority,
            candidate.provenance.file_path,
            span.start_line,
            span.start_column,
            candidate.unit_id,
        )

    strongest_relevance = max(candidate.score.p_edit, candidate.score.p_support)
    proven_priority = 0 if candidate.kind is RenderedUnitKind.PROVEN_SYMBOL else 1
    span = candidate.provenance.span
    return (
        -strongest_relevance,
        -candidate.score.p_edit,
        -candidate.score.p_support,
        0.0,
        proven_priority,
        candidate.provenance.file_path,
        span.start_line,
        span.start_column,
        candidate.unit_id,
    )


def _scope_priority(
    candidate: _SemanticCandidate,
    *,
    current_focus_id: str,
    current_focus_file_scope_id: str | None,
    current_focus_has_support: bool,
    current_focus_has_uncertainty_surface: bool,
) -> int:
    """Prefer direct callers, then one honest uncertainty, then support packing."""
    if _is_direct_caller_of_focus(candidate, focus_unit_id=current_focus_id):
        return 0
    if _is_uncertainty_for_focus(
        candidate,
        focus_unit_id=current_focus_id,
        focus_file_scope_id=current_focus_file_scope_id,
    ):
        if current_focus_has_uncertainty_surface:
            return 3
        return 1
    if _is_support_for_focus(candidate, focus_unit_id=current_focus_id):
        if current_focus_has_uncertainty_surface:
            return 2 if current_focus_has_support else 1
        if current_focus_has_support:
            return 3
        return 2
    return 4


def _support_pack_score(candidate: _SemanticCandidate) -> float:
    """Score pack efficiency after the direct edit anchor is secured."""
    preferred_detail = _preferred_detail(candidate)
    if preferred_detail is None:
        return 0.0

    preferred_tokens = candidate.renders[preferred_detail].token_count
    return candidate.score.p_support / max(1, preferred_tokens)


def _focus_relevance_score(
    candidate: _SemanticCandidate,
    *,
    current_focus_id: str,
    current_focus_has_support: bool,
) -> float:
    """Prefer the strongest first support before switching to pack efficiency."""
    strongest_relevance = max(candidate.score.p_edit, candidate.score.p_support)
    if _is_direct_caller_of_focus(candidate, focus_unit_id=current_focus_id):
        return strongest_relevance
    if not current_focus_has_support and _is_support_for_focus(
        candidate, focus_unit_id=current_focus_id
    ):
        return strongest_relevance
    return 0.0


def _is_focus_selection(
    candidate: _SemanticCandidate,
    chosen_detail: RenderDetail,
) -> bool:
    """Return whether ``candidate`` should guide later support packing."""
    return (
        candidate.kind is RenderedUnitKind.PROVEN_SYMBOL
        and chosen_detail is not RenderDetail.IDENTITY
        and candidate.score.p_edit >= _DIRECT_SUMMARY_THRESHOLD
        and candidate.score.p_edit >= candidate.score.p_support
    )


def _is_direct_caller_of_focus(
    candidate: _SemanticCandidate,
    *,
    focus_unit_id: str,
) -> bool:
    """Return whether ``candidate`` is a direct caller of ``focus_unit_id``."""
    return (
        candidate.kind is RenderedUnitKind.PROVEN_SYMBOL
        and focus_unit_id in candidate.outgoing_dependency_targets
        and candidate.score.p_edit >= _DIRECT_SUMMARY_THRESHOLD
    )


def _is_support_for_focus(
    candidate: _SemanticCandidate,
    *,
    focus_unit_id: str,
) -> bool:
    """Return whether ``candidate`` supports ``focus_unit_id`` with repo evidence."""
    return (
        candidate.kind is RenderedUnitKind.PROVEN_SYMBOL
        and focus_unit_id in candidate.incoming_dependency_sources
    )


def _is_uncertainty_for_focus(
    candidate: _SemanticCandidate,
    *,
    focus_unit_id: str,
    focus_file_scope_id: str | None = None,
) -> bool:
    """Return whether ``candidate`` is the honest uncertainty surface for ``focus``."""
    return candidate.kind is not RenderedUnitKind.PROVEN_SYMBOL and (
        candidate.enclosing_scope_id == focus_unit_id
        or _is_file_scope_uncertainty_for_focus(
            candidate,
            focus_file_scope_id=focus_file_scope_id,
        )
    )


def _focus_has_uncertainty_candidate(
    focus_unit_id: str,
    focus_file_scope_id: str | None,
    candidates: list[_SemanticCandidate],
) -> bool:
    """Return whether ``focus_unit_id`` still has a relevant uncertainty candidate."""
    return any(
        _is_uncertainty_for_focus(
            candidate,
            focus_unit_id=focus_unit_id,
            focus_file_scope_id=focus_file_scope_id,
        )
        and _uncertainty_preferred_detail(
            candidate,
            focus_file_scope_id=focus_file_scope_id,
        )
        is not None
        for candidate in candidates
    )


def _choose_detail(
    candidate: _SemanticCandidate,
    remaining_budget: int,
    *,
    current_focus_id: str | None = None,
    current_focus_file_scope_id: str | None = None,
    current_focus_inherited_uncertainty_surface: bool = False,
) -> RenderDetail | None:
    """Pick the richest affordable detail for ``candidate``."""
    if _is_policy_suppressed_uncertainty_candidate(
        candidate,
        current_focus_id=current_focus_id,
        current_focus_file_scope_id=current_focus_file_scope_id,
        current_focus_inherited_uncertainty_surface=(
            current_focus_inherited_uncertainty_surface
        ),
    ) or _is_policy_suppressed_standalone_proven_candidate(
        candidate,
        current_focus_id=current_focus_id,
    ):
        return None

    preferred_detail = _uncertainty_preferred_detail(
        candidate,
        focus_file_scope_id=current_focus_file_scope_id,
    )
    if preferred_detail is None:
        return None

    detail_chain = _detail_chain(candidate, preferred_detail)
    if _should_promote_direct_support_to_source(
        candidate,
        current_focus_id=current_focus_id,
    ):
        detail_chain = (RenderDetail.SOURCE, *detail_chain)
    for detail in detail_chain:
        if candidate.renders[detail].token_count <= remaining_budget:
            return detail
    return None


def _preferred_detail(candidate: _SemanticCandidate) -> RenderDetail | None:
    """Return the richest honest target detail for ``candidate``."""
    p_edit = candidate.score.p_edit
    p_support = candidate.score.p_support

    if p_edit < _MIN_RELEVANCE and p_support < _MIN_RELEVANCE:
        return None

    if candidate.kind is RenderedUnitKind.PROVEN_SYMBOL:
        if p_edit >= _DIRECT_SOURCE_THRESHOLD:
            return RenderDetail.SOURCE
        if (
            p_edit >= _DIRECT_SUMMARY_THRESHOLD
            or p_support >= _SUPPORT_SUMMARY_THRESHOLD
        ):
            return RenderDetail.SUMMARY
        return RenderDetail.IDENTITY

    if p_edit >= _DIRECT_SOURCE_THRESHOLD + 0.10:
        return RenderDetail.SOURCE
    if p_edit >= _DIRECT_SUMMARY_THRESHOLD:
        return RenderDetail.SUMMARY
    if p_support >= _MIN_RELEVANCE:
        return RenderDetail.IDENTITY
    if p_edit >= _MIN_RELEVANCE:
        return RenderDetail.SUMMARY
    return RenderDetail.IDENTITY


def _uncertainty_preferred_detail(
    candidate: _SemanticCandidate,
    *,
    focus_file_scope_id: str | None,
) -> RenderDetail | None:
    """Allow same-file module uncertainty to surface under an active focus."""
    preferred_detail = _preferred_detail(candidate)
    if preferred_detail is not None:
        return preferred_detail
    if _is_file_scope_uncertainty_for_focus(
        candidate,
        focus_file_scope_id=focus_file_scope_id,
    ):
        return RenderDetail.IDENTITY
    return None


def _is_file_scope_uncertainty_for_focus(
    candidate: _SemanticCandidate,
    *,
    focus_file_scope_id: str | None,
) -> bool:
    """Return whether ``candidate`` is module-scope uncertainty in the focus file."""
    return (
        focus_file_scope_id is not None
        and candidate.file_scope_id == focus_file_scope_id
        and candidate.enclosing_scope_id == focus_file_scope_id
    )


def _is_policy_suppressed_uncertainty_candidate(
    candidate: _SemanticCandidate,
    *,
    current_focus_id: str | None,
    current_focus_file_scope_id: str | None,
    current_focus_inherited_uncertainty_surface: bool,
) -> bool:
    """Return whether surplus uncertainty should stay out of the pack."""
    if candidate.kind is RenderedUnitKind.PROVEN_SYMBOL or current_focus_id is None:
        return False
    if not _is_uncertainty_for_focus(
        candidate,
        focus_unit_id=current_focus_id,
        focus_file_scope_id=current_focus_file_scope_id,
    ):
        return True
    return (
        current_focus_inherited_uncertainty_surface
        and candidate.kind is RenderedUnitKind.UNRESOLVED_FRONTIER
    )


def _is_policy_suppressed_standalone_proven_candidate(
    candidate: _SemanticCandidate,
    *,
    current_focus_id: str | None,
) -> bool:
    """Return whether a weak non-support symbol is leftover focus-exterior noise."""
    if current_focus_id is None or candidate.kind is not RenderedUnitKind.PROVEN_SYMBOL:
        return False
    if _is_direct_caller_of_focus(candidate, focus_unit_id=current_focus_id):
        return False
    if _is_support_for_focus(candidate, focus_unit_id=current_focus_id):
        return False
    return max(candidate.score.p_edit, candidate.score.p_support) < (
        _DIRECT_SUMMARY_THRESHOLD
    )


def _detail_chain(
    candidate: _SemanticCandidate,
    preferred_detail: RenderDetail,
) -> tuple[RenderDetail, ...]:
    """Return the ordered fallback chain for a preferred detail."""
    if preferred_detail is RenderDetail.SOURCE:
        return (
            RenderDetail.SOURCE,
            RenderDetail.SUMMARY,
            RenderDetail.IDENTITY,
        )

    promoted_detail = _promoted_detail_for_pack_efficiency(
        candidate,
        preferred_detail,
    )
    if promoted_detail is RenderDetail.SOURCE:
        if preferred_detail is RenderDetail.SUMMARY:
            return (
                RenderDetail.SOURCE,
                RenderDetail.SUMMARY,
                RenderDetail.IDENTITY,
            )
        return (
            RenderDetail.SOURCE,
            RenderDetail.IDENTITY,
        )
    if promoted_detail is RenderDetail.SUMMARY:
        return (
            RenderDetail.SUMMARY,
            RenderDetail.IDENTITY,
        )

    if preferred_detail is RenderDetail.SUMMARY:
        if (
            max(candidate.score.p_edit, candidate.score.p_support)
            >= _DIRECT_SUMMARY_THRESHOLD
            and candidate.renders[RenderDetail.SOURCE].token_count
            <= candidate.renders[RenderDetail.SUMMARY].token_count
        ):
            return (
                RenderDetail.SOURCE,
                RenderDetail.SUMMARY,
                RenderDetail.IDENTITY,
            )
        if (
            candidate.renders[RenderDetail.SOURCE].token_count
            <= candidate.renders[RenderDetail.SUMMARY].token_count
        ):
            return (RenderDetail.SUMMARY, RenderDetail.IDENTITY)
        if (
            candidate.score.p_support >= _DIRECT_SUMMARY_THRESHOLD
            and candidate.renders[RenderDetail.SOURCE].token_count
            <= candidate.renders[RenderDetail.SUMMARY].token_count
            + _SUPPORT_DETAIL_PROMOTION_SLACK
        ):
            return (
                RenderDetail.SOURCE,
                RenderDetail.SUMMARY,
                RenderDetail.IDENTITY,
            )
        if (
            candidate.score.p_edit >= _DIRECT_SUMMARY_THRESHOLD
            and candidate.renders[RenderDetail.SOURCE].token_count
            <= candidate.renders[RenderDetail.SUMMARY].token_count
            + _SOURCE_PROMOTION_SLACK
        ):
            return (
                RenderDetail.SOURCE,
                RenderDetail.SUMMARY,
                RenderDetail.IDENTITY,
            )
        return (RenderDetail.SUMMARY, RenderDetail.IDENTITY)
    return (RenderDetail.IDENTITY,)


def _promoted_detail_for_pack_efficiency(
    candidate: _SemanticCandidate,
    preferred_detail: RenderDetail,
) -> RenderDetail | None:
    """Promote to richer detail when it costs no more and the signal is material."""
    strongest_relevance = max(candidate.score.p_edit, candidate.score.p_support)
    if strongest_relevance < _DIRECT_SUMMARY_THRESHOLD:
        return None

    preferred_tokens = candidate.renders[preferred_detail].token_count
    if (
        candidate.kind is RenderedUnitKind.PROVEN_SYMBOL
        and candidate.renders[RenderDetail.SOURCE].token_count <= preferred_tokens
    ):
        return RenderDetail.SOURCE
    if (
        preferred_detail is RenderDetail.IDENTITY
        and candidate.renders[RenderDetail.SUMMARY].token_count <= preferred_tokens
    ):
        return RenderDetail.SUMMARY
    if (
        preferred_detail is RenderDetail.IDENTITY
        and candidate.kind is RenderedUnitKind.PROVEN_SYMBOL
        and candidate.score.p_support >= _DIRECT_SUMMARY_THRESHOLD
    ):
        source_tokens = candidate.renders[RenderDetail.SOURCE].token_count
        summary_tokens = candidate.renders[RenderDetail.SUMMARY].token_count
        if (
            source_tokens <= preferred_tokens + _SUPPORT_DETAIL_PROMOTION_SLACK
            and source_tokens <= summary_tokens
        ):
            return RenderDetail.SOURCE
        if summary_tokens <= preferred_tokens + _SUPPORT_DETAIL_PROMOTION_SLACK:
            return RenderDetail.SUMMARY
    return None


def _should_promote_direct_support_to_source(
    candidate: _SemanticCandidate,
    *,
    current_focus_id: str | None,
) -> bool:
    """Prefer source for strong direct supports under the active focus."""
    if current_focus_id is None:
        return False
    if not _is_support_for_focus(candidate, focus_unit_id=current_focus_id):
        return False
    if candidate.kind is not RenderedUnitKind.PROVEN_SYMBOL:
        return False
    return (
        candidate.score.p_edit >= _DIRECT_SUMMARY_THRESHOLD
        or candidate.score.p_support >= _FOCUS_SOURCE_SUPPORT_THRESHOLD
    )


def _selection_record(
    *,
    candidate: _SemanticCandidate,
    chosen_detail: RenderDetail,
    preferred_detail: RenderDetail | None,
    program: SemanticProgram,
    scoring: SemanticScoringResult,
) -> SemanticSelectionRecord:
    """Create the trace record for one selected unit."""
    basis = _selection_basis(candidate, scoring)
    reason = _selection_reason(
        candidate=candidate,
        chosen_detail=chosen_detail,
        preferred_detail=preferred_detail,
        basis=basis,
        program=program,
        scoring=scoring,
    )
    return SemanticSelectionRecord(
        unit_id=candidate.unit_id,
        detail=chosen_detail.value,
        token_count=candidate.renders[chosen_detail].token_count,
        basis=basis,
        reason=reason,
        edit_score=candidate.score.p_edit,
        support_score=candidate.score.p_support,
        trace_summary=candidate.trace_summary,
    )


def _selection_basis(
    candidate: _SemanticCandidate,
    scoring: SemanticScoringResult,
) -> SelectionBasis:
    """Classify why ``candidate`` was selected."""
    if candidate.kind is RenderedUnitKind.UNRESOLVED_FRONTIER:
        return SelectionBasis.UNRESOLVED_FRONTIER_ESCALATION
    if (
        candidate.incoming_dependency_sources
        and _strongest_dependency_source(candidate, scoring) is not None
        and candidate.score.p_support > candidate.score.p_edit
    ):
        return SelectionBasis.PROVEN_DEPENDENCY
    return SelectionBasis.HEURISTIC_CANDIDATE


def _selection_reason(
    *,
    candidate: _SemanticCandidate,
    chosen_detail: RenderDetail,
    preferred_detail: RenderDetail | None,
    basis: SelectionBasis,
    program: SemanticProgram,
    scoring: SemanticScoringResult,
) -> str:
    """Describe the honest selection reason for later diagnose/recompile work."""
    base_reason: str
    score_summary = (
        f"p_edit={candidate.score.p_edit:.2f}, "
        f"p_support={candidate.score.p_support:.2f}"
    )

    if basis is SelectionBasis.PROVEN_DEPENDENCY:
        source_id = _strongest_dependency_source(candidate, scoring)
        source_name = _display_name(source_id, program) if source_id is not None else ""
        base_reason = (
            f"selected as repository-backed support for {source_name} ({score_summary})"
        )
    elif candidate.kind is RenderedUnitKind.UNRESOLVED_FRONTIER:
        scope_name = _display_name(candidate.enclosing_scope_id, program)
        if candidate.score.p_edit >= candidate.score.p_support:
            base_reason = (
                f"selected to surface directly relevant unresolved uncertainty "
                f"({score_summary})"
            )
        elif scope_name is not None:
            base_reason = (
                f"selected to keep unresolved uncertainty visible around {scope_name} "
                f"({score_summary})"
            )
        else:
            base_reason = (
                f"selected to keep unresolved uncertainty visible ({score_summary})"
            )
    elif candidate.kind is RenderedUnitKind.UNSUPPORTED_CONSTRUCT:
        scope_name = _display_name(candidate.enclosing_scope_id, program)
        if candidate.score.p_edit >= candidate.score.p_support:
            base_reason = (
                f"selected to surface directly relevant unsupported behavior "
                f"({score_summary})"
            )
        elif scope_name is not None:
            base_reason = (
                f"selected to keep unsupported behavior visible around {scope_name} "
                f"({score_summary})"
            )
        else:
            base_reason = (
                f"selected to keep unsupported behavior visible ({score_summary})"
            )
    else:
        base_reason = f"selected for direct semantic relevance ({score_summary})"

    if preferred_detail is not None and chosen_detail is not preferred_detail:
        if _detail_richer_than(left=chosen_detail, right=preferred_detail):
            chosen_tokens = candidate.renders[chosen_detail].token_count
            preferred_tokens = candidate.renders[preferred_detail].token_count
            if chosen_tokens <= preferred_tokens:
                return (
                    f"{base_reason}; promoted to {chosen_detail.value} because it "
                    f"cost no more than {preferred_detail.value}"
                )
            return (
                f"{base_reason}; promoted to {chosen_detail.value} because the richer "
                f"view stayed within pack slack (+{chosen_tokens - preferred_tokens} "
                f"tokens over {preferred_detail.value})"
            )
        return (
            f"{base_reason}; downgraded to {chosen_detail.value} under budget pressure"
        )
    return base_reason


def _display_name(unit_id: str | None, program: SemanticProgram) -> str | None:
    """Return a stable human-readable name for ``unit_id`` if it is known."""
    if unit_id is None:
        return None
    symbol = program.resolved_symbols.get(unit_id)
    if symbol is not None:
        return symbol.qualified_name
    return unit_id


def _strongest_dependency_source(
    candidate: _SemanticCandidate,
    scoring: SemanticScoringResult,
) -> str | None:
    """Return the strongest directly relevant dependency source for ``candidate``."""
    strongest_source_id: str | None = None
    strongest_edit = 0.0
    for source_id in candidate.incoming_dependency_sources:
        score = scoring.scores.get(source_id)
        if score is None or score.p_edit <= strongest_edit:
            continue
        strongest_source_id = source_id
        strongest_edit = score.p_edit
    return strongest_source_id


def _build_warnings(
    *,
    candidates: tuple[_SemanticCandidate, ...] | list[_SemanticCandidate],
    selections: tuple[SemanticSelectionRecord, ...],
    omitted_unit_ids: tuple[str, ...],
    focus_unit_ids: frozenset[str],
    suppressed_uncertainty_unit_ids: frozenset[str],
    program: SemanticProgram,
) -> list[SemanticOptimizationWarning]:
    """Emit truthful, minimal warnings about budget tradeoffs."""
    candidate_by_id = {candidate.unit_id: candidate for candidate in candidates}
    omitted_unit_id_set = set(omitted_unit_ids)
    warnings: list[SemanticOptimizationWarning] = []

    for selection in selections:
        candidate = candidate_by_id[selection.unit_id]
        preferred_detail = _preferred_detail(candidate)
        if preferred_detail is not None and _detail_richer_than(
            left=preferred_detail,
            right=_detail_from_record(selection),
        ):
            warnings.append(
                SemanticOptimizationWarning(
                    code=SemanticOptimizationWarningCode.BUDGET_PRESSURE,
                    unit_id=selection.unit_id,
                    message=(
                        f"{selection.unit_id} was downgraded from "
                        f"{preferred_detail.value} to {selection.detail} under budget "
                        "pressure"
                    ),
                    trace_summary=candidate.trace_summary,
                )
            )
            continue

        omitted_support_ids = [
            target_id
            for target_id in _dependency_targets_for(selection.unit_id, program)
            if target_id in omitted_unit_id_set
        ]
        if omitted_support_ids:
            warnings.append(
                SemanticOptimizationWarning(
                    code=SemanticOptimizationWarningCode.BUDGET_PRESSURE,
                    unit_id=selection.unit_id,
                    message=(
                        f"{selection.unit_id} was selected without repository-backed "
                        f"support units under budget pressure: "
                        f"{', '.join(sorted(omitted_support_ids))}"
                    ),
                    trace_summary=candidate.trace_summary,
                )
            )

    for unit_id in omitted_unit_ids:
        candidate = candidate_by_id[unit_id]
        if candidate.score.p_edit >= _STRONG_DIRECT_WARNING_THRESHOLD:
            warnings.append(
                SemanticOptimizationWarning(
                    code=SemanticOptimizationWarningCode.OMITTED_DIRECT_CANDIDATE,
                    unit_id=unit_id,
                    message=(
                        f"{unit_id} was omitted despite strong direct relevance "
                        f"(p_edit={candidate.score.p_edit:.2f})"
                    ),
                    trace_summary=candidate.trace_summary,
                )
            )
            continue

        if unit_id in suppressed_uncertainty_unit_ids:
            continue

        if candidate.kind is not RenderedUnitKind.PROVEN_SYMBOL and (
            max(candidate.score.p_edit, candidate.score.p_support)
            >= _UNCERTAINTY_WARNING_THRESHOLD
            or candidate.enclosing_scope_id in focus_unit_ids
        ):
            warnings.append(
                SemanticOptimizationWarning(
                    code=SemanticOptimizationWarningCode.OMITTED_UNCERTAINTY,
                    unit_id=unit_id,
                    message=(
                        f"{unit_id} was omitted even though it carried relevant "
                        "uncertainty under the current budget"
                    ),
                    trace_summary=candidate.trace_summary,
                )
            )

    return warnings


def _dependency_targets_for(
    unit_id: str,
    program: SemanticProgram,
) -> tuple[str, ...]:
    """Return proven dependency targets for one selected symbol."""
    target_ids = [
        dependency.target_symbol_id
        for dependency in program.proven_dependencies
        if dependency.source_symbol_id == unit_id
    ]
    return tuple(sorted(target_ids))


def _detail_from_record(record: SemanticSelectionRecord) -> RenderDetail:
    """Convert a recorded detail value back into ``RenderDetail``."""
    return RenderDetail(record.detail)


def _detail_richer_than(*, left: RenderDetail, right: RenderDetail) -> bool:
    """Return whether ``left`` represents a richer detail than ``right``."""
    return _DETAIL_RANK[left] > _DETAIL_RANK[right]


def _confidence(
    *,
    candidates: tuple[_SemanticCandidate, ...] | list[_SemanticCandidate],
    selections: tuple[SemanticSelectionRecord, ...],
) -> float:
    """Return deterministic confidence from achieved versus ideal utility."""
    if not candidates:
        return 1.0

    selected_detail_by_unit_id = {
        selection.unit_id: RenderDetail(selection.detail) for selection in selections
    }
    achieved_utility = 0.0
    ideal_utility = 0.0

    for candidate in candidates:
        chosen_detail = selected_detail_by_unit_id.get(candidate.unit_id)
        if chosen_detail is not None:
            achieved_utility += _utility(candidate, chosen_detail)
        ideal_utility += max(
            (_utility(candidate, detail) for detail in _DETAIL_ORDER), default=0.0
        )

    if ideal_utility == 0.0:
        return 0.0
    confidence = achieved_utility / ideal_utility
    if confidence < 0.0:
        return 0.0
    if confidence > 1.0:
        return 1.0
    return confidence


def _utility(candidate: _SemanticCandidate, detail: RenderDetail) -> float:
    """Return detail utility from semantic edit/support scores."""
    edit_value = _EDIT_VALUE[detail]
    support_value = _SUPPORT_VALUE[detail]
    if (
        candidate.kind is not RenderedUnitKind.PROVEN_SYMBOL
        and detail is RenderDetail.SOURCE
    ):
        edit_value *= 0.85
        support_value *= 0.90
    return (
        candidate.score.p_edit * edit_value + candidate.score.p_support * support_value
    )


__all__ = ["optimize_semantic_units"]

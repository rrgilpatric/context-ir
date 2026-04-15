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
    SelectionBasis,
    SemanticOptimizationResult,
    SemanticOptimizationWarning,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticSelectionRecord,
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
_DIRECT_SOURCE_THRESHOLD = 0.55
_DIRECT_SUMMARY_THRESHOLD = 0.20
_SUPPORT_SUMMARY_THRESHOLD = 0.40
_STRONG_DIRECT_WARNING_THRESHOLD = 0.50
_UNCERTAINTY_WARNING_THRESHOLD = 0.30


@dataclass(frozen=True)
class _SemanticCandidate:
    """One renderable semantic unit with its score and exact render costs."""

    unit_id: str
    kind: RenderedUnitKind
    provenance: SourceSite
    score: SemanticUnitScore
    renders: dict[RenderDetail, RenderedUnit]
    incoming_dependency_sources: tuple[str, ...]
    enclosing_scope_id: str | None


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

    for candidate in ordered_candidates:
        chosen_detail = _choose_detail(candidate, remaining_budget)
        if chosen_detail is None:
            omitted_unit_ids.append(candidate.unit_id)
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
    enclosing_scope_ids = _enclosing_scope_ids(program)
    candidates: list[_SemanticCandidate] = []

    for unit_id in renderable_unit_ids:
        identity = render_semantic_unit(program, unit_id, RenderDetail.IDENTITY)
        summary = render_semantic_unit(program, unit_id, RenderDetail.SUMMARY)
        source = render_semantic_unit(program, unit_id, RenderDetail.SOURCE)
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
                score=scoring.scores[unit_id],
                renders=renders,
                incoming_dependency_sources=incoming_dependency_sources.get(
                    unit_id, ()
                ),
                enclosing_scope_id=enclosing_scope_ids.get(unit_id),
            )
        )

    return candidates


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


def _enclosing_scope_ids(program: SemanticProgram) -> dict[str, str | None]:
    """Return enclosing-scope IDs for uncertainty surfaces."""
    result: dict[str, str | None] = {}
    for access in program.unresolved_frontier:
        result[access.access_id] = access.enclosing_scope_id
    for construct in program.unsupported_constructs:
        result[construct.construct_id] = construct.enclosing_scope_id
    return result


def _candidate_sort_key(
    candidate: _SemanticCandidate,
) -> tuple[float, float, float, int, str, int, int, str]:
    """Sort by directness first, then support, then stable source order."""
    direct_priority = (
        0
        if candidate.score.p_edit >= max(candidate.score.p_support, _MIN_RELEVANCE)
        else 1
    )
    proven_priority = 0 if candidate.kind is RenderedUnitKind.PROVEN_SYMBOL else 1
    span = candidate.provenance.span
    return (
        direct_priority,
        -candidate.score.p_edit,
        -candidate.score.p_support,
        proven_priority,
        candidate.provenance.file_path,
        span.start_line,
        span.start_column,
        candidate.unit_id,
    )


def _choose_detail(
    candidate: _SemanticCandidate,
    remaining_budget: int,
) -> RenderDetail | None:
    """Pick the richest affordable detail for ``candidate``."""
    preferred_detail = _preferred_detail(candidate)
    if preferred_detail is None:
        return None

    detail_chain = _detail_chain(preferred_detail)
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
    if p_edit >= _MIN_RELEVANCE or p_support >= _MIN_RELEVANCE:
        return RenderDetail.SUMMARY
    return RenderDetail.IDENTITY


def _detail_chain(preferred_detail: RenderDetail) -> tuple[RenderDetail, ...]:
    """Return the ordered fallback chain for a preferred detail."""
    if preferred_detail is RenderDetail.SOURCE:
        return (
            RenderDetail.SOURCE,
            RenderDetail.SUMMARY,
            RenderDetail.IDENTITY,
        )
    if preferred_detail is RenderDetail.SUMMARY:
        return (RenderDetail.SUMMARY, RenderDetail.IDENTITY)
    return (RenderDetail.IDENTITY,)


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
                )
            )
            continue

        if (
            candidate.kind is not RenderedUnitKind.PROVEN_SYMBOL
            and max(candidate.score.p_edit, candidate.score.p_support)
            >= _UNCERTAINTY_WARNING_THRESHOLD
        ):
            warnings.append(
                SemanticOptimizationWarning(
                    code=SemanticOptimizationWarningCode.OMITTED_UNCERTAINTY,
                    unit_id=unit_id,
                    message=(
                        f"{unit_id} was omitted even though it carried relevant "
                        "uncertainty under the current budget"
                    ),
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

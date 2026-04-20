"""Semantic-first diagnose and recompile helpers."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from context_ir.semantic_compiler import compile_semantic_context
from context_ir.semantic_renderer import RenderDetail
from context_ir.semantic_scorer import (
    SemanticScoringResult,
    SemanticUnitScore,
    score_semantic_units,
)
from context_ir.semantic_types import (
    CapabilityTier,
    ResolvedSymbol,
    SemanticCompileResult,
    SemanticDiagnosticBoundary,
    SemanticDiagnosticBoundaryKind,
    SemanticDiagnosticResult,
    SemanticDiagnosticUnitStatus,
    SemanticMissEvidence,
    SemanticMissKind,
    SemanticOptimizationWarning,
    SemanticProgram,
    SemanticRecompileResult,
    SemanticSelectionRecord,
    SemanticUnitTraceSummary,
    UnresolvedAccess,
    UnsupportedConstruct,
)

EmbeddingFunction = Callable[[list[str]], list[list[float]]]

_TRACE_FILE_RE = re.compile(r"File\s+[\"']([^\"']+)[\"']")
_TRACE_FUNCTION_RE = re.compile(r",\s+in\s+([A-Za-z_][A-Za-z0-9_]*)")
_PYTHON_PATH_RE = re.compile(r"[A-Za-z0-9_./\\-]+\.py")
_WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:/")
_DETAIL_RANK: dict[str, int] = {
    RenderDetail.IDENTITY.value: 0,
    RenderDetail.SUMMARY.value: 1,
    RenderDetail.SOURCE.value: 2,
}
_DIRECT_MISS_EDIT_BOOST = 0.95
_DIRECT_MISS_SUPPORT_FLOOR = 0.60
_BOUNDARY_SURFACE_EDIT_BOOST = 0.12
_BOUNDARY_SURFACE_SUPPORT_FLOOR = 0.25
_ATTACHED_RUNTIME_BOUNDARY_EDIT_BOOST = 0.25
_ATTACHED_RUNTIME_BOUNDARY_SUPPORT_FLOOR = 0.45
_EXPANSION_SUPPORT_BOOST = 0.65


class _UnitCategory(Enum):
    """Kinds of semantic units the diagnose layer can ground to."""

    PROVEN_SYMBOL = "proven_symbol"
    UNRESOLVED_FRONTIER = "unresolved_frontier"
    UNSUPPORTED_CONSTRUCT = "unsupported_construct"


@dataclass(frozen=True)
class _UnitRecord:
    """Lookup surface for one accepted semantic unit."""

    unit_id: str
    category: _UnitCategory
    file_path: str
    qualified_name: str | None = None
    simple_name: str | None = None
    surface_text: str | None = None


def diagnose_semantic_miss(
    previous_result: SemanticCompileResult,
    miss_evidence: SemanticMissEvidence,
    program: SemanticProgram,
) -> SemanticDiagnosticResult:
    """Diagnose a prior semantic compile miss without mutating any inputs."""
    unit_records = _unit_records(program)
    grounded_unit_ids = _ground_miss_evidence(
        miss_evidence=miss_evidence,
        unit_records=unit_records,
    )
    if not grounded_unit_ids:
        return SemanticDiagnosticResult(
            grounded_unit_ids=(),
            omitted_unit_ids=(),
            too_shallow_unit_ids=(),
            sufficiently_represented_unit_ids=(),
            recommended_expansions=(),
            reason="Could not ground the evidence to accepted semantic unit IDs.",
        )

    previous_detail_by_unit_id = {
        selection.unit_id: selection.detail
        for selection in previous_result.optimization.selections
    }
    trace_summary_by_unit_id = _trace_summary_by_unit_id(previous_result)
    boundary_classifications = tuple(
        _diagnostic_boundary(
            unit_id=unit_id,
            previous_detail=previous_detail_by_unit_id.get(unit_id),
            unit_record=unit_records[unit_id],
            trace_summary=trace_summary_by_unit_id.get(unit_id),
        )
        for unit_id in grounded_unit_ids
    )
    omitted_unit_ids = tuple(
        boundary.unit_id
        for boundary in boundary_classifications
        if boundary.status is SemanticDiagnosticUnitStatus.OMITTED
    )
    too_shallow_unit_ids = tuple(
        boundary.unit_id
        for boundary in boundary_classifications
        if boundary.status is SemanticDiagnosticUnitStatus.TOO_SHALLOW
    )
    sufficiently_represented_unit_ids = tuple(
        boundary.unit_id
        for boundary in boundary_classifications
        if boundary.status is SemanticDiagnosticUnitStatus.SUFFICIENTLY_REPRESENTED
    )

    recommended_expansions = _recommended_expansions(
        boundary_classifications=boundary_classifications,
        program=program,
        unit_records=unit_records,
    )
    return SemanticDiagnosticResult(
        grounded_unit_ids=grounded_unit_ids,
        omitted_unit_ids=omitted_unit_ids,
        too_shallow_unit_ids=too_shallow_unit_ids,
        sufficiently_represented_unit_ids=sufficiently_represented_unit_ids,
        recommended_expansions=recommended_expansions,
        reason=_diagnostic_reason(
            grounded_unit_ids=grounded_unit_ids,
            boundary_classifications=boundary_classifications,
        ),
        boundary_classifications=boundary_classifications,
    )


def recompile_semantic_context(
    previous_result: SemanticCompileResult,
    miss_evidence: SemanticMissEvidence,
    delta_budget: int,
    program: SemanticProgram,
    *,
    embed_fn: EmbeddingFunction | None = None,
) -> SemanticRecompileResult:
    """Recompile semantic context under an expanded budget after diagnosis."""
    if delta_budget < 0:
        raise ValueError("delta_budget must be >= 0")
    if previous_result.compile_context is None:
        raise ValueError(
            "previous_result.compile_context is required for semantic recompilation"
        )

    diagnostic = diagnose_semantic_miss(previous_result, miss_evidence, program)
    base_scoring = score_semantic_units(
        program,
        previous_result.compile_context.query,
        embed_fn=embed_fn,
    )
    boosted_scoring = _boost_scoring(base_scoring, diagnostic)
    compile_result = compile_semantic_context(
        program,
        previous_result.compile_context.query,
        previous_result.budget + delta_budget,
        scoring=boosted_scoring,
    )

    previous_detail_by_unit_id = {
        selection.unit_id: selection.detail
        for selection in previous_result.optimization.selections
    }
    current_detail_by_unit_id = {
        selection.unit_id: selection.detail
        for selection in compile_result.optimization.selections
    }
    newly_selected_unit_ids = tuple(
        sorted(set(current_detail_by_unit_id) - set(previous_detail_by_unit_id))
    )
    upgraded_unit_ids = tuple(
        sorted(
            unit_id
            for unit_id, current_detail in current_detail_by_unit_id.items()
            if unit_id in previous_detail_by_unit_id
            and _detail_rank(current_detail)
            > _detail_rank(previous_detail_by_unit_id[unit_id])
        )
    )
    return SemanticRecompileResult(
        compile_result=compile_result,
        diagnostic=diagnostic,
        budget_delta=delta_budget,
        newly_selected_unit_ids=newly_selected_unit_ids,
        upgraded_unit_ids=upgraded_unit_ids,
    )


def _unit_records(program: SemanticProgram) -> dict[str, _UnitRecord]:
    """Build grounding surfaces for every accepted semantic unit ID."""
    records: dict[str, _UnitRecord] = {}

    for unit_id, symbol in program.resolved_symbols.items():
        records[unit_id] = _record_for_symbol(unit_id, symbol)

    for access in program.unresolved_frontier:
        records[access.access_id] = _record_for_unresolved(access)

    for construct in program.unsupported_constructs:
        records[construct.construct_id] = _record_for_unsupported(construct)

    return records


def _record_for_symbol(unit_id: str, symbol: ResolvedSymbol) -> _UnitRecord:
    """Return the grounding record for one proven symbol."""
    simple_name = symbol.qualified_name.rsplit(".", maxsplit=1)[-1]
    return _UnitRecord(
        unit_id=unit_id,
        category=_UnitCategory.PROVEN_SYMBOL,
        file_path=symbol.definition_site.file_path,
        qualified_name=symbol.qualified_name,
        simple_name=simple_name,
    )


def _record_for_unresolved(access: UnresolvedAccess) -> _UnitRecord:
    """Return the grounding record for one unresolved frontier item."""
    return _UnitRecord(
        unit_id=access.access_id,
        category=_UnitCategory.UNRESOLVED_FRONTIER,
        file_path=access.site.file_path,
        surface_text=access.access_text,
    )


def _record_for_unsupported(construct: UnsupportedConstruct) -> _UnitRecord:
    """Return the grounding record for one unsupported construct."""
    return _UnitRecord(
        unit_id=construct.construct_id,
        category=_UnitCategory.UNSUPPORTED_CONSTRUCT,
        file_path=construct.site.file_path,
        surface_text=construct.construct_text,
    )


def _ground_miss_evidence(
    *,
    miss_evidence: SemanticMissEvidence,
    unit_records: dict[str, _UnitRecord],
) -> tuple[str, ...]:
    """Ground miss evidence conservatively to accepted semantic unit IDs."""
    if miss_evidence.kind is SemanticMissKind.ABSENT_SYMBOL:
        return _ground_absent_symbol(miss_evidence.evidence, unit_records)
    if miss_evidence.kind is SemanticMissKind.OUT_OF_PACK_TRACE:
        return _ground_out_of_pack_trace(miss_evidence.evidence, unit_records)
    return _ground_path_edit(miss_evidence.evidence, unit_records)


def _ground_absent_symbol(
    evidence: str,
    unit_records: dict[str, _UnitRecord],
) -> tuple[str, ...]:
    """Ground absent-symbol evidence by exact semantic identifiers or names."""
    text = evidence.strip()
    grounded: list[str] = []

    if text in unit_records:
        grounded.append(text)

    for record in unit_records.values():
        if record.qualified_name == text:
            grounded.append(record.unit_id)
        if (
            record.category is _UnitCategory.PROVEN_SYMBOL
            and record.simple_name == text
        ):
            grounded.append(record.unit_id)
        if record.surface_text == text:
            grounded.append(record.unit_id)

    return _dedupe_preserve_order(grounded)


def _ground_out_of_pack_trace(
    evidence: str,
    unit_records: dict[str, _UnitRecord],
) -> tuple[str, ...]:
    """Ground stack-trace evidence by concrete file and function surfaces."""
    file_snippets = _trace_file_snippets(evidence)
    function_names = tuple(_TRACE_FUNCTION_RE.findall(evidence))
    file_matches: list[str] = []
    for file_snippet in file_snippets:
        file_matches.extend(_ground_path_snippet(file_snippet, unit_records))
    function_matches: list[str] = []
    for function_name in function_names:
        function_matches.extend(_ground_absent_symbol(function_name, unit_records))

    grounded_file_matches = _dedupe_preserve_order(file_matches)
    grounded_function_matches = _dedupe_preserve_order(function_matches)
    if file_snippets and function_names:
        function_match_set = set(grounded_function_matches)
        intersection = tuple(
            unit_id
            for unit_id in grounded_file_matches
            if unit_id in function_match_set
        )
        return intersection
    if function_names:
        return grounded_function_matches
    return grounded_file_matches


def _ground_path_edit(
    evidence: str,
    unit_records: dict[str, _UnitRecord],
) -> tuple[str, ...]:
    """Ground file/path edit evidence to units defined at matching paths."""
    return _ground_path_snippet(evidence, unit_records)


def _ground_path_snippet(
    snippet: str,
    unit_records: dict[str, _UnitRecord],
) -> tuple[str, ...]:
    """Ground a file/path snippet to matching semantic units."""
    normalized_snippet = _normalize_path_text(snippet)
    if not _is_path_shaped(normalized_snippet):
        return ()

    matches = [
        record.unit_id
        for record in unit_records.values()
        if _path_matches(record.file_path, normalized_snippet)
    ]
    return _dedupe_preserve_order(matches)


def _trace_file_snippets(evidence: str) -> tuple[str, ...]:
    """Extract concrete file/path snippets from a stack trace fragment."""
    snippets = [*_TRACE_FILE_RE.findall(evidence), *_PYTHON_PATH_RE.findall(evidence)]
    return _dedupe_preserve_order(snippets)


def _path_matches(file_path: str, normalized_snippet: str) -> bool:
    """Return whether ``normalized_snippet`` is directly supported by ``file_path``."""
    normalized_path = _normalize_path_text(file_path)
    if not normalized_path:
        return False
    if normalized_path == normalized_snippet:
        return True
    if _is_segment_suffix(normalized_path, normalized_snippet):
        return True
    if _is_absolute_path(normalized_snippet):
        return _is_segment_suffix(normalized_snippet, normalized_path)
    return False


def _normalize_path_text(value: str) -> str:
    """Normalize path-like evidence for direct string comparison."""
    normalized = value.strip().replace("\\", "/")
    normalized = re.sub(r"/+", "/", normalized)
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/")


def _is_path_shaped(normalized_snippet: str) -> bool:
    """Return whether ``normalized_snippet`` is concrete enough for path grounding."""
    if not normalized_snippet:
        return False
    segments = [segment for segment in normalized_snippet.split("/") if segment]
    if not segments:
        return False
    return segments[-1].endswith(".py")


def _is_segment_suffix(candidate: str, suffix: str) -> bool:
    """Return whether ``candidate`` matches ``suffix`` on a path boundary."""
    return candidate == suffix or candidate.endswith("/" + suffix)


def _is_absolute_path(normalized_path: str) -> bool:
    """Return whether ``normalized_path`` looks like an absolute filesystem path."""
    return normalized_path.startswith("/") or bool(
        _WINDOWS_ABSOLUTE_PATH_RE.match(normalized_path)
    )


def _trace_summary_by_unit_id(
    previous_result: SemanticCompileResult,
) -> dict[str, SemanticUnitTraceSummary]:
    """Return the best available trace summary for each prior unit."""
    summaries: dict[str, SemanticUnitTraceSummary] = {}
    summaries.update(_warning_trace_summaries(previous_result.optimization.warnings))
    summaries.update(
        _selection_trace_summaries(previous_result.optimization.selections)
    )
    return summaries


def _selection_trace_summaries(
    selections: tuple[SemanticSelectionRecord, ...],
) -> dict[str, SemanticUnitTraceSummary]:
    """Index selection trace summaries by unit ID."""
    return {
        selection.unit_id: selection.trace_summary
        for selection in selections
        if selection.trace_summary is not None
    }


def _warning_trace_summaries(
    warnings: tuple[SemanticOptimizationWarning, ...],
) -> dict[str, SemanticUnitTraceSummary]:
    """Index warning trace summaries by unit ID."""
    return {
        warning.unit_id: warning.trace_summary
        for warning in warnings
        if warning.unit_id is not None and warning.trace_summary is not None
    }


def _diagnostic_boundary(
    *,
    unit_id: str,
    previous_detail: str | None,
    unit_record: _UnitRecord,
    trace_summary: SemanticUnitTraceSummary | None,
) -> SemanticDiagnosticBoundary:
    """Classify one grounded unit by tier boundary and surfaced depth."""
    primary_capability_tier = _primary_capability_tier(
        unit_record=unit_record,
        trace_summary=trace_summary,
    )
    has_attached_runtime_provenance = (
        trace_summary.has_attached_runtime_provenance
        if trace_summary is not None
        else False
    )
    boundary_kind = _boundary_kind(
        primary_capability_tier=primary_capability_tier,
        has_attached_runtime_provenance=has_attached_runtime_provenance,
    )
    if previous_detail is None:
        status = SemanticDiagnosticUnitStatus.OMITTED
    elif _detail_rank(previous_detail) < _required_detail_rank(boundary_kind):
        status = SemanticDiagnosticUnitStatus.TOO_SHALLOW
    else:
        status = SemanticDiagnosticUnitStatus.SUFFICIENTLY_REPRESENTED
    return SemanticDiagnosticBoundary(
        unit_id=unit_id,
        status=status,
        boundary_kind=boundary_kind,
        primary_capability_tier=primary_capability_tier,
        has_attached_runtime_provenance=has_attached_runtime_provenance,
        trace_summary=trace_summary,
    )


def _primary_capability_tier(
    *,
    unit_record: _UnitRecord,
    trace_summary: SemanticUnitTraceSummary | None,
) -> CapabilityTier:
    """Return the accepted primary capability tier for one diagnostic unit."""
    if trace_summary is not None:
        return trace_summary.primary_capability_tier
    if unit_record.category is _UnitCategory.PROVEN_SYMBOL:
        return CapabilityTier.STATICALLY_PROVED
    if unit_record.category is _UnitCategory.UNRESOLVED_FRONTIER:
        return CapabilityTier.HEURISTIC_FRONTIER
    return CapabilityTier.UNSUPPORTED_OPAQUE


def _boundary_kind(
    *,
    primary_capability_tier: CapabilityTier,
    has_attached_runtime_provenance: bool,
) -> SemanticDiagnosticBoundaryKind:
    """Return the typed boundary kind for one grounded diagnostic unit."""
    if primary_capability_tier is CapabilityTier.STATICALLY_PROVED:
        return SemanticDiagnosticBoundaryKind.STATICALLY_PROVED
    if primary_capability_tier is CapabilityTier.HEURISTIC_FRONTIER:
        return (
            SemanticDiagnosticBoundaryKind.HEURISTIC_FRONTIER_WITH_ATTACHED_RUNTIME_SUPPORT
            if has_attached_runtime_provenance
            else (
                SemanticDiagnosticBoundaryKind.HEURISTIC_FRONTIER_MISSING_RUNTIME_SUPPORT
            )
        )
    if primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE:
        return (
            SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
            if has_attached_runtime_provenance
            else (
                SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
            )
        )
    raise ValueError(
        "diagnostic boundary classification requires a non-runtime primary tier"
    )


def _required_detail_rank(boundary_kind: SemanticDiagnosticBoundaryKind) -> int:
    """Return the minimum surfaced detail that counts as sufficient."""
    if boundary_kind is SemanticDiagnosticBoundaryKind.STATICALLY_PROVED:
        return _detail_rank(RenderDetail.SOURCE.value)
    if boundary_kind in {
        SemanticDiagnosticBoundaryKind.HEURISTIC_FRONTIER_WITH_ATTACHED_RUNTIME_SUPPORT,
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT,
    }:
        return _detail_rank(RenderDetail.SUMMARY.value)
    return _detail_rank(RenderDetail.IDENTITY.value)


def _detail_rank(detail: str) -> int:
    """Return the stable richness rank for a rendered detail string."""
    return _DETAIL_RANK[detail]


def _recommended_expansions(
    *,
    boundary_classifications: tuple[SemanticDiagnosticBoundary, ...],
    program: SemanticProgram,
    unit_records: dict[str, _UnitRecord],
) -> tuple[str, ...]:
    """Return narrowly justified expansion targets from accepted semantic facts."""
    expansions: list[str] = []
    for boundary in boundary_classifications:
        if boundary.status is SemanticDiagnosticUnitStatus.SUFFICIENTLY_REPRESENTED:
            continue
        expansions.append(boundary.unit_id)
        if boundary.primary_capability_tier is not CapabilityTier.STATICALLY_PROVED:
            continue
        record = unit_records[boundary.unit_id]
        if record.category is not _UnitCategory.PROVEN_SYMBOL:
            continue
        for dependency in program.proven_dependencies:
            if dependency.source_symbol_id != boundary.unit_id:
                continue
            if dependency.target_symbol_id not in program.resolved_symbols:
                continue
            expansions.append(dependency.target_symbol_id)
    return _dedupe_preserve_order(expansions)


def _diagnostic_reason(
    *,
    grounded_unit_ids: tuple[str, ...],
    boundary_classifications: tuple[SemanticDiagnosticBoundary, ...],
) -> str:
    """Build a conservative explanation of why the miss happened."""
    segments = [f"Grounded {len(grounded_unit_ids)} semantic unit(s)."]
    segments.extend(
        _reason_segments_for_status(
            boundary_classifications,
            status=SemanticDiagnosticUnitStatus.OMITTED,
        )
    )
    segments.extend(
        _reason_segments_for_status(
            boundary_classifications,
            status=SemanticDiagnosticUnitStatus.TOO_SHALLOW,
        )
    )
    segments.extend(
        _reason_segments_for_status(
            boundary_classifications,
            status=SemanticDiagnosticUnitStatus.SUFFICIENTLY_REPRESENTED,
        )
    )
    return " ".join(segments)


def _reason_segments_for_status(
    boundary_classifications: tuple[SemanticDiagnosticBoundary, ...],
    *,
    status: SemanticDiagnosticUnitStatus,
) -> list[str]:
    """Build grouped reason segments for one diagnostic status bucket."""
    counts = {
        boundary_kind: sum(
            1
            for boundary in boundary_classifications
            if boundary.status is status and boundary.boundary_kind is boundary_kind
        )
        for boundary_kind in SemanticDiagnosticBoundaryKind
    }
    static_proved = counts[SemanticDiagnosticBoundaryKind.STATICALLY_PROVED]
    frontier_missing_runtime = counts[
        SemanticDiagnosticBoundaryKind.HEURISTIC_FRONTIER_MISSING_RUNTIME_SUPPORT
    ]
    frontier_with_runtime = counts[
        SemanticDiagnosticBoundaryKind.HEURISTIC_FRONTIER_WITH_ATTACHED_RUNTIME_SUPPORT
    ]
    unsupported_missing_runtime = counts[
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_MISSING_RUNTIME_SUPPORT
    ]
    unsupported_with_runtime = counts[
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    ]
    segments: list[str] = []
    if status is SemanticDiagnosticUnitStatus.OMITTED:
        if static_proved:
            segments.append(
                f"{static_proved} "
                "statically proved unit(s) were omitted due to budget pressure."
            )
        if frontier_missing_runtime:
            segments.append(
                f"{frontier_missing_runtime} "
                "heuristic frontier unit(s) were omitted; they remain non-proof "
                "boundary work without attached runtime-backed support."
            )
        if frontier_with_runtime:
            segments.append(
                f"{frontier_with_runtime} "
                "heuristic frontier unit(s) with attached runtime-backed "
                "provenance were omitted."
            )
        if unsupported_missing_runtime:
            segments.append(
                f"{unsupported_missing_runtime} "
                "unsupported/opaque unit(s) were omitted; they remain boundary "
                "work without attached runtime-backed support."
            )
        if unsupported_with_runtime:
            segments.append(
                f"{unsupported_with_runtime} "
                "unsupported/opaque unit(s) with attached runtime-backed "
                "provenance were omitted."
            )
        return segments

    if status is SemanticDiagnosticUnitStatus.TOO_SHALLOW:
        if static_proved:
            segments.append(
                f"{static_proved} "
                "statically proved unit(s) were present but too shallow."
            )
        if frontier_with_runtime:
            segments.append(
                f"{frontier_with_runtime} "
                "heuristic frontier unit(s) carried attached runtime-backed "
                "provenance but were still too shallow."
            )
        if unsupported_with_runtime:
            segments.append(
                f"{unsupported_with_runtime} "
                "unsupported/opaque unit(s) carried attached runtime-backed "
                "provenance but were still too shallow."
            )
        return segments

    if static_proved:
        segments.append(
            f"{static_proved} "
            "statically proved unit(s) were already sufficiently represented."
        )
    if frontier_missing_runtime:
        segments.append(
            f"{frontier_missing_runtime} "
            "heuristic frontier unit(s) were already surfaced as non-proof "
            "boundary work without attached runtime-backed support."
        )
    if frontier_with_runtime:
        segments.append(
            f"{frontier_with_runtime} "
            "heuristic frontier unit(s) were already surfaced with attached "
            "runtime-backed provenance."
        )
    if unsupported_missing_runtime:
        segments.append(
            f"{unsupported_missing_runtime} "
            "unsupported/opaque unit(s) were already surfaced as boundary work "
            "without attached runtime-backed support."
        )
    if unsupported_with_runtime:
        segments.append(
            f"{unsupported_with_runtime} "
            "unsupported/opaque unit(s) were already surfaced with attached "
            "runtime-backed provenance."
        )
    return segments


def _boost_scoring(
    scoring: SemanticScoringResult,
    diagnostic: SemanticDiagnosticResult,
) -> SemanticScoringResult:
    """Apply conservative miss-driven boosts without fabricating grounded evidence."""
    boosted_scores = {
        unit_id: SemanticUnitScore(
            unit_id=score.unit_id,
            p_edit=score.p_edit,
            p_support=score.p_support,
        )
        for unit_id, score in scoring.scores.items()
    }
    if diagnostic.boundary_classifications:
        sufficient_status = SemanticDiagnosticUnitStatus.SUFFICIENTLY_REPRESENTED
        actionable_unit_ids = {
            boundary.unit_id
            for boundary in diagnostic.boundary_classifications
            if boundary.status is not sufficient_status
        }
        for boundary in diagnostic.boundary_classifications:
            if boundary.status is sufficient_status:
                continue
            score = boosted_scores.get(boundary.unit_id)
            if score is None:
                continue
            if boundary.primary_capability_tier is CapabilityTier.STATICALLY_PROVED:
                boosted_scores[boundary.unit_id] = SemanticUnitScore(
                    unit_id=score.unit_id,
                    p_edit=max(score.p_edit, _DIRECT_MISS_EDIT_BOOST),
                    p_support=max(score.p_support, _DIRECT_MISS_SUPPORT_FLOOR),
                )
                continue
            edit_floor = (
                _ATTACHED_RUNTIME_BOUNDARY_EDIT_BOOST
                if boundary.has_attached_runtime_provenance
                else _BOUNDARY_SURFACE_EDIT_BOOST
            )
            support_floor = (
                _ATTACHED_RUNTIME_BOUNDARY_SUPPORT_FLOOR
                if boundary.has_attached_runtime_provenance
                else _BOUNDARY_SURFACE_SUPPORT_FLOOR
            )
            boosted_scores[boundary.unit_id] = SemanticUnitScore(
                unit_id=score.unit_id,
                p_edit=max(score.p_edit, edit_floor),
                p_support=max(score.p_support, support_floor),
            )
    else:
        actionable_unit_ids = set(diagnostic.omitted_unit_ids) | set(
            diagnostic.too_shallow_unit_ids
        )
        for unit_id in actionable_unit_ids:
            score = boosted_scores.get(unit_id)
            if score is None:
                continue
            boosted_scores[unit_id] = SemanticUnitScore(
                unit_id=score.unit_id,
                p_edit=max(score.p_edit, _DIRECT_MISS_EDIT_BOOST),
                p_support=max(score.p_support, _DIRECT_MISS_SUPPORT_FLOOR),
            )

    for unit_id in diagnostic.recommended_expansions:
        if unit_id in actionable_unit_ids:
            continue
        score = boosted_scores.get(unit_id)
        if score is None:
            continue
        boosted_scores[unit_id] = SemanticUnitScore(
            unit_id=score.unit_id,
            p_edit=score.p_edit,
            p_support=_merge_support(score.p_support, _EXPANSION_SUPPORT_BOOST),
        )

    return SemanticScoringResult(query=scoring.query, scores=boosted_scores)


def _merge_support(current_support: float, boost: float) -> float:
    """Combine support evidence with saturation at one."""
    return min(1.0, current_support + boost * (1.0 - current_support))


def _dedupe_preserve_order(values: list[str]) -> tuple[str, ...]:
    """Return unique values while keeping first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


__all__ = [
    "diagnose_semantic_miss",
    "recompile_semantic_context",
]

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
    ResolvedSymbol,
    SemanticCompileResult,
    SemanticDiagnosticResult,
    SemanticMissEvidence,
    SemanticMissKind,
    SemanticProgram,
    SemanticRecompileResult,
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
    omitted_unit_ids: list[str] = []
    too_shallow_unit_ids: list[str] = []
    sufficiently_represented_unit_ids: list[str] = []
    for unit_id in grounded_unit_ids:
        previous_detail = previous_detail_by_unit_id.get(unit_id)
        if previous_detail is None:
            omitted_unit_ids.append(unit_id)
            continue
        if _detail_rank(previous_detail) < _required_detail_rank(unit_records[unit_id]):
            too_shallow_unit_ids.append(unit_id)
            continue
        sufficiently_represented_unit_ids.append(unit_id)

    recommended_expansions = _recommended_expansions(
        actionable_unit_ids=[*omitted_unit_ids, *too_shallow_unit_ids],
        program=program,
        unit_records=unit_records,
    )
    return SemanticDiagnosticResult(
        grounded_unit_ids=grounded_unit_ids,
        omitted_unit_ids=tuple(omitted_unit_ids),
        too_shallow_unit_ids=tuple(too_shallow_unit_ids),
        sufficiently_represented_unit_ids=tuple(sufficiently_represented_unit_ids),
        recommended_expansions=recommended_expansions,
        reason=_diagnostic_reason(
            grounded_unit_ids=grounded_unit_ids,
            omitted_unit_ids=tuple(omitted_unit_ids),
            too_shallow_unit_ids=tuple(too_shallow_unit_ids),
            sufficiently_represented_unit_ids=tuple(sufficiently_represented_unit_ids),
            unit_records=unit_records,
        ),
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


def _required_detail_rank(record: _UnitRecord) -> int:
    """Return the minimum detail rank that counts as sufficient."""
    if record.category is _UnitCategory.PROVEN_SYMBOL:
        return _detail_rank(RenderDetail.SOURCE.value)
    return _detail_rank(RenderDetail.SUMMARY.value)


def _detail_rank(detail: str) -> int:
    """Return the stable richness rank for a rendered detail string."""
    return _DETAIL_RANK[detail]


def _recommended_expansions(
    *,
    actionable_unit_ids: list[str],
    program: SemanticProgram,
    unit_records: dict[str, _UnitRecord],
) -> tuple[str, ...]:
    """Return narrowly justified expansion targets from accepted semantic facts."""
    expansions: list[str] = list(actionable_unit_ids)
    for unit_id in actionable_unit_ids:
        record = unit_records[unit_id]
        if record.category is not _UnitCategory.PROVEN_SYMBOL:
            continue
        for dependency in program.proven_dependencies:
            if dependency.source_symbol_id != unit_id:
                continue
            if dependency.target_symbol_id not in program.resolved_symbols:
                continue
            expansions.append(dependency.target_symbol_id)
    return _dedupe_preserve_order(expansions)


def _diagnostic_reason(
    *,
    grounded_unit_ids: tuple[str, ...],
    omitted_unit_ids: tuple[str, ...],
    too_shallow_unit_ids: tuple[str, ...],
    sufficiently_represented_unit_ids: tuple[str, ...],
    unit_records: dict[str, _UnitRecord],
) -> str:
    """Build a conservative explanation of why the miss happened."""
    segments = [f"Grounded {len(grounded_unit_ids)} semantic unit(s)."]
    if omitted_unit_ids:
        uncertainty_omissions = sum(
            1
            for unit_id in omitted_unit_ids
            if unit_records[unit_id].category is not _UnitCategory.PROVEN_SYMBOL
        )
        proven_omissions = len(omitted_unit_ids) - uncertainty_omissions
        if proven_omissions:
            segments.append(
                f"{proven_omissions} grounded unit(s) were omitted due to "
                "budget pressure."
            )
        if uncertainty_omissions:
            segments.append(
                f"{uncertainty_omissions} unresolved or unsupported unit(s) "
                "were not surfaced."
            )
    if too_shallow_unit_ids:
        segments.append(
            f"{len(too_shallow_unit_ids)} grounded unit(s) were present but "
            "too shallow."
        )
    if sufficiently_represented_unit_ids:
        segments.append(
            f"{len(sufficiently_represented_unit_ids)} grounded unit(s) were "
            "already sufficiently represented."
        )
    return " ".join(segments)


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

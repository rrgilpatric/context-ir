"""Semantic-first compile orchestration over scored semantic units."""

from __future__ import annotations

from collections.abc import Callable

from context_ir.semantic_optimizer import optimize_semantic_units
from context_ir.semantic_renderer import (
    RenderDetail,
    RenderedUnit,
    render_semantic_unit,
)
from context_ir.semantic_scorer import SemanticScoringResult, score_semantic_units
from context_ir.semantic_types import (
    SemanticCompileContext,
    SemanticCompileResult,
    SemanticOptimizationResult,
    SemanticOptimizationWarning,
    SemanticProgram,
    SemanticSelectionRecord,
)

EmbeddingFunction = Callable[[list[str]], list[list[float]]]


def compile_semantic_context(
    program: SemanticProgram,
    query: str,
    budget: int,
    *,
    scoring: SemanticScoringResult | None = None,
    embed_fn: EmbeddingFunction | None = None,
) -> SemanticCompileResult:
    """Compile a truthful semantic context artifact within ``budget``."""
    if budget < 0:
        raise ValueError("budget must be >= 0")
    if scoring is not None and scoring.query != query:
        raise ValueError("scoring.query must match compile_semantic_context(query=...)")

    active_scoring = scoring
    if active_scoring is None:
        active_scoring = score_semantic_units(program, query, embed_fn=embed_fn)

    optimization, rendered_units, document = _compile_budget_honest_artifact(
        program=program,
        scoring=active_scoring,
        query=query,
        budget=budget,
    )
    total_tokens = _estimate_document_tokens(document)
    return SemanticCompileResult(
        document=document,
        optimization=optimization,
        omitted_unit_ids=optimization.omitted_unit_ids,
        total_tokens=total_tokens,
        budget=budget,
        confidence=optimization.confidence,
        compile_context=SemanticCompileContext(query=query),
    )


def _compile_budget_honest_artifact(
    *,
    program: SemanticProgram,
    scoring: SemanticScoringResult,
    query: str,
    budget: int,
) -> tuple[SemanticOptimizationResult, dict[str, RenderedUnit], str]:
    """Reserve document-assembly overhead before returning a compiled artifact."""
    max_unit_budget = _initial_unit_budget(query=query, scoring=scoring, budget=budget)
    best_fit: tuple[SemanticOptimizationResult, dict[str, RenderedUnit], str] | None = (
        None
    )
    low = 0
    high = max_unit_budget

    while low <= high:
        unit_budget = (low + high) // 2
        raw_optimization = optimize_semantic_units(program, scoring, unit_budget)
        optimization = _with_compile_budget(raw_optimization, budget)
        rendered_units = _render_selected_units(program, optimization)
        document = _assemble_document(
            query=query,
            optimization=optimization,
            rendered_units=rendered_units,
        )
        document_tokens = _estimate_document_tokens(document)
        if document_tokens <= budget:
            best_fit = (optimization, rendered_units, document)
            low = unit_budget + 1
            continue
        high = unit_budget - 1

    if best_fit is not None:
        return best_fit
    raise ValueError("budget is too small for the compiled document envelope")


def _initial_unit_budget(
    *,
    query: str,
    scoring: SemanticScoringResult,
    budget: int,
) -> int:
    """Reserve the minimum compile envelope before selecting semantic units."""
    empty_optimization = SemanticOptimizationResult(
        selections=(),
        omitted_unit_ids=tuple(sorted(scoring.scores)),
        warnings=(),
        total_tokens=0,
        budget=budget,
        confidence=0.0,
    )
    empty_document = _assemble_document(
        query=query,
        optimization=empty_optimization,
        rendered_units={},
    )
    return max(0, budget - _estimate_document_tokens(empty_document))


def _with_compile_budget(
    optimization: SemanticOptimizationResult,
    budget: int,
) -> SemanticOptimizationResult:
    """Return ``optimization`` normalized to the caller-visible compile budget."""
    if optimization.budget == budget:
        return optimization
    return SemanticOptimizationResult(
        selections=optimization.selections,
        omitted_unit_ids=optimization.omitted_unit_ids,
        warnings=_copy_warnings(optimization.warnings),
        total_tokens=optimization.total_tokens,
        budget=budget,
        confidence=optimization.confidence,
    )


def _copy_warnings(
    warnings: tuple[SemanticOptimizationWarning, ...],
) -> tuple[SemanticOptimizationWarning, ...]:
    """Return a stable copy of optimization warnings."""
    return tuple(
        SemanticOptimizationWarning(
            code=warning.code,
            message=warning.message,
            unit_id=warning.unit_id,
            trace_summary=warning.trace_summary,
        )
        for warning in warnings
    )


def _render_selected_units(
    program: SemanticProgram,
    optimization: SemanticOptimizationResult,
) -> dict[str, RenderedUnit]:
    """Render every selected unit at its chosen detail."""
    rendered_units: dict[str, RenderedUnit] = {}
    for selection in optimization.selections:
        rendered_units[selection.unit_id] = render_semantic_unit(
            program,
            selection.unit_id,
            RenderDetail(selection.detail),
        )
    return rendered_units


def _assemble_document(
    *,
    query: str,
    optimization: SemanticOptimizationResult,
    rendered_units: dict[str, RenderedUnit],
) -> str:
    """Assemble the selected semantic units into a stable compiled document."""
    del query
    lines = ["# Context"]

    grouped_records = _group_records_by_file(optimization.selections, rendered_units)
    for file_index, (file_path, records) in enumerate(grouped_records):
        lines.append(file_path)
        for record_index, (_selection, rendered) in enumerate(records):
            if record_index > 0:
                lines.append("")
            lines.append(rendered.content)
        if file_index < len(grouped_records) - 1:
            lines.append("")

    return "\n".join(lines)


def _group_records_by_file(
    selections: tuple[SemanticSelectionRecord, ...],
    rendered_units: dict[str, RenderedUnit],
) -> list[tuple[str, list[tuple[SemanticSelectionRecord, RenderedUnit]]]]:
    """Group selected units by file in stable source order."""
    grouped: dict[str, list[tuple[SemanticSelectionRecord, RenderedUnit]]] = {}
    for selection in selections:
        rendered = rendered_units[selection.unit_id]
        grouped.setdefault(rendered.provenance.file_path, []).append(
            (selection, rendered)
        )

    ordered_groups: list[
        tuple[str, list[tuple[SemanticSelectionRecord, RenderedUnit]]]
    ] = []
    for file_path in sorted(grouped):
        records = grouped[file_path]
        records.sort(
            key=lambda item: (
                item[1].provenance.span.start_line,
                item[1].provenance.span.start_column,
                item[0].unit_id,
            )
        )
        ordered_groups.append((file_path, records))
    return ordered_groups


def _estimate_document_tokens(document: str) -> int:
    """Return the compile-level token estimate for the assembled document."""
    return max(1, (len(document) + 3) // 4)


__all__ = ["compile_semantic_context"]

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
    unit_budget = budget
    while True:
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
            return optimization, rendered_units, document
        if not raw_optimization.selections:
            raise ValueError("budget is too small for the compiled document envelope")

        assembly_overhead = document_tokens - raw_optimization.total_tokens
        unit_budget = max(0, budget - assembly_overhead)


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
    lines = [
        "# Semantic Context",
        f"query: {query or '<empty>'}",
        f"selected_unit_tokens: {optimization.total_tokens}/{optimization.budget}",
        f"confidence: {optimization.confidence:.2f}",
        f"selected_units: {len(optimization.selections)}",
        f"omitted_units: {len(optimization.omitted_unit_ids)}",
    ]
    if optimization.warnings:
        lines.append(f"warnings: {len(optimization.warnings)}")

    grouped_records = _group_records_by_file(optimization.selections, rendered_units)
    for file_path, records in grouped_records:
        lines.extend(("", f"## {file_path}"))
        for selection, rendered in records:
            lines.extend(
                (
                    "",
                    (
                        f"[{selection.detail}] {selection.unit_id} | "
                        f"{selection.basis.value}"
                    ),
                    rendered.content,
                )
            )

    if optimization.omitted_unit_ids:
        lines.extend(
            ("", "## Omitted", _omitted_surface(optimization.omitted_unit_ids))
        )

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


def _omitted_surface(omitted_unit_ids: tuple[str, ...]) -> str:
    """Return a concise omitted-unit surface for the compiled document."""
    preview = ", ".join(omitted_unit_ids[:5])
    if len(omitted_unit_ids) <= 5:
        return f"unit_ids: {preview}"
    remaining = len(omitted_unit_ids) - 5
    return f"unit_ids: {preview}, ... (+{remaining} more)"


def _estimate_document_tokens(document: str) -> int:
    """Return the compile-level token estimate for the assembled document."""
    return max(1, (len(document) + 3) // 4)


__all__ = ["compile_semantic_context"]

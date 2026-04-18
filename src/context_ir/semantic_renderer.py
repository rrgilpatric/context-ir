"""Semantic-first rendering for proven units and uncertainty surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from context_ir.semantic_types import (
    DataclassField,
    DataclassModel,
    ProofStatus,
    ResolvedSymbol,
    SemanticProgram,
    SourceSite,
    SourceSpan,
    UnresolvedAccess,
    UnsupportedConstruct,
)


class RenderDetail(Enum):
    """Minimal render-density baseline for semantic-first rendering."""

    IDENTITY = "identity"
    SUMMARY = "summary"
    SOURCE = "source"


class RenderedUnitKind(Enum):
    """Kinds of semantic units the renderer can truthfully represent."""

    PROVEN_SYMBOL = "proven_symbol"
    UNRESOLVED_FRONTIER = "unresolved_frontier"
    UNSUPPORTED_CONSTRUCT = "unsupported_construct"


@dataclass(frozen=True)
class RenderedUnit:
    """Rendered semantic unit with explicit provenance and token accounting."""

    unit_id: str
    detail: RenderDetail
    kind: RenderedUnitKind
    proof_status: ProofStatus
    provenance: SourceSite
    content: str
    token_count: int


@dataclass(frozen=True)
class _DataclassFacts:
    """Dataclass facts attached to one class symbol, if any."""

    model: DataclassModel | None
    fields: tuple[DataclassField, ...]


def render_semantic_unit(
    program: SemanticProgram,
    unit_id: str,
    detail: RenderDetail,
) -> RenderedUnit:
    """Render one semantic unit or frontier item from ``program``."""
    symbol = program.resolved_symbols.get(unit_id)
    if symbol is not None:
        content = _render_symbol(program=program, symbol=symbol, detail=detail)
        return RenderedUnit(
            unit_id=unit_id,
            detail=detail,
            kind=RenderedUnitKind.PROVEN_SYMBOL,
            proof_status=ProofStatus.PROVEN,
            provenance=symbol.definition_site,
            content=content,
            token_count=_estimate_tokens(content),
        )

    unresolved_access = _unresolved_by_id(program).get(unit_id)
    if unresolved_access is not None:
        content = _render_unresolved(unresolved_access, detail)
        return RenderedUnit(
            unit_id=unit_id,
            detail=detail,
            kind=RenderedUnitKind.UNRESOLVED_FRONTIER,
            proof_status=unresolved_access.proof_status,
            provenance=unresolved_access.site,
            content=content,
            token_count=_estimate_tokens(content),
        )

    unsupported_construct = _unsupported_by_id(program).get(unit_id)
    if unsupported_construct is not None:
        content = _render_unsupported(unsupported_construct, detail)
        return RenderedUnit(
            unit_id=unit_id,
            detail=detail,
            kind=RenderedUnitKind.UNSUPPORTED_CONSTRUCT,
            proof_status=unsupported_construct.proof_status,
            provenance=unsupported_construct.site,
            content=content,
            token_count=_estimate_tokens(content),
        )

    raise KeyError(unit_id)


def _render_symbol(
    *,
    program: SemanticProgram,
    symbol: ResolvedSymbol,
    detail: RenderDetail,
) -> str:
    """Render one proven semantic symbol at ``detail``."""
    dataclass_facts = _dataclass_facts_for_symbol(program, symbol.symbol_id)

    if detail is RenderDetail.IDENTITY:
        return _join_lines(
            (
                "proven symbol",
                f"kind: {symbol.kind.value}",
                f"qualified_name: {symbol.qualified_name}",
                f"unit_id: {symbol.symbol_id}",
                f"file: {symbol.definition_site.file_path}",
                f"span: {_format_span(symbol.definition_site.span)}",
                f"proof_status: {ProofStatus.PROVEN.value}",
            )
        )

    if detail is RenderDetail.SUMMARY:
        lines = [
            (
                f"proven summary: {symbol.kind.value} {symbol.qualified_name} @ "
                f"{_format_site(symbol.definition_site)}"
            )
        ]
        if symbol.supported_decorators:
            lines.append(
                "decorators: "
                + ",".join(decorator.value for decorator in symbol.supported_decorators)
            )
        if dataclass_facts.model is not None:
            lines.append(
                "dataclass: " + dataclass_facts.model.decorator_target_qualified_name
            )
        if dataclass_facts.fields:
            lines.append(
                "fields: "
                + "; ".join(
                    _format_dataclass_field(field) for field in dataclass_facts.fields
                )
            )
        return _join_lines(lines)

    source_text = _read_source_span(
        repo_root=program.repo_root,
        site=symbol.definition_site,
    )
    if source_text is not None:
        return source_text
    return _join_lines(
        (
            "proven symbol source unavailable",
            f"kind: {symbol.kind.value}",
            f"qualified_name: {symbol.qualified_name}",
            f"unit_id: {symbol.symbol_id}",
            f"file: {symbol.definition_site.file_path}",
            f"span: {_format_span(symbol.definition_site.span)}",
            "reason: exact source span could not be read from disk",
        )
    )


def _render_unresolved(access: UnresolvedAccess, detail: RenderDetail) -> str:
    """Render one unresolved frontier item without overclaiming proof."""
    if detail is RenderDetail.IDENTITY:
        return (
            f"unresolved: {access.access_text} @ {_format_identity_site(access.site)}"
        )

    lines = [
        "unresolved frontier item",
        f"unit_id: {access.access_id}",
        f"proof_status: {access.proof_status.value}",
        f"reason_code: {access.reason_code.value}",
        f"context: {access.context.value}",
        f"file: {access.site.file_path}",
        f"span: {_format_span(access.site.span)}",
        f"text: {access.access_text}",
    ]
    if access.detail is not None:
        lines.append(f"detail: {access.detail}")
    if detail is RenderDetail.SOURCE:
        snippet = access.site.snippet
        if snippet is not None:
            lines.extend(("source_snippet:", snippet))
        else:
            lines.append("source_unavailable: no local snippet recorded")
    return _join_lines(lines)


def _render_unsupported(
    construct: UnsupportedConstruct,
    detail: RenderDetail,
) -> str:
    """Render one unsupported construct without inventing missing context."""
    if detail is RenderDetail.IDENTITY:
        return _join_lines(
            (
                "unsupported construct",
                f"unit_id: {construct.construct_id}",
                f"text: {construct.construct_text}",
                f"kind: {RenderedUnitKind.UNSUPPORTED_CONSTRUCT.value}",
                f"file: {construct.site.file_path}",
                f"span: {_format_span(construct.site.span)}",
            )
        )

    lines = [
        "unsupported construct",
        f"unit_id: {construct.construct_id}",
        f"proof_status: {construct.proof_status.value}",
        f"reason_code: {construct.reason_code.value}",
        "context: unavailable",
        f"file: {construct.site.file_path}",
        f"span: {_format_span(construct.site.span)}",
        f"text: {construct.construct_text}",
    ]
    if construct.enclosing_scope_id is not None:
        lines.append(f"enclosing_scope_id: {construct.enclosing_scope_id}")
    if construct.detail is not None:
        lines.append(f"detail: {construct.detail}")
    if detail is RenderDetail.SOURCE:
        snippet = construct.site.snippet
        if snippet is not None:
            lines.extend(("source_snippet:", snippet))
        else:
            lines.append("source_unavailable: no local snippet recorded")
    return _join_lines(lines)


def _dataclass_facts_for_symbol(
    program: SemanticProgram,
    symbol_id: str,
) -> _DataclassFacts:
    """Return proven dataclass facts for ``symbol_id``."""
    model = next(
        (
            dataclass_model
            for dataclass_model in program.dataclass_models
            if dataclass_model.class_symbol_id == symbol_id
        ),
        None,
    )
    fields = tuple(
        sorted(
            (
                dataclass_field
                for dataclass_field in program.dataclass_fields
                if dataclass_field.class_symbol_id == symbol_id
            ),
            key=lambda field: (
                field.site.span.start_line,
                field.site.span.start_column,
                field.site.span.end_line,
                field.site.span.end_column,
                field.name,
            ),
        )
    )
    return _DataclassFacts(model=model, fields=fields)


def _format_dataclass_field(field: DataclassField) -> str:
    """Return one concise dataclass-field summary."""
    if field.has_default and field.default_value_text is not None:
        return f"{field.name}: {field.annotation_text} = {field.default_value_text}"
    return f"{field.name}: {field.annotation_text}"


def _unresolved_by_id(program: SemanticProgram) -> dict[str, UnresolvedAccess]:
    """Index unresolved frontier items by stable ID."""
    return {access.access_id: access for access in program.unresolved_frontier}


def _unsupported_by_id(program: SemanticProgram) -> dict[str, UnsupportedConstruct]:
    """Index unsupported constructs by stable ID."""
    return {
        construct.construct_id: construct
        for construct in program.unsupported_constructs
    }


def _format_span(span: SourceSpan) -> str:
    """Return a compact human-readable span string."""
    return f"{span.start_line}:{span.start_column}-{span.end_line}:{span.end_column}"


def _format_site(site: SourceSite) -> str:
    """Return a stable site marker with the full source span."""
    return f"{site.file_path}:{_format_span(site.span)}"


def _format_identity_site(site: SourceSite) -> str:
    """Return a concise site marker for identity-only uncertainty surfaces."""
    span = site.span
    return f"{site.file_path}:{span.start_line}:{span.start_column}"


def _join_lines(lines: list[str] | tuple[str, ...]) -> str:
    """Return newline-joined text without dropping intentional blank lines."""
    return "\n".join(lines)


def _read_source_span(*, repo_root: Path, site: SourceSite) -> str | None:
    """Return the exact on-disk text for ``site.span`` or ``None``."""
    source_path = repo_root / site.file_path
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except OSError:
        return None
    return _slice_source_text(source_text, site.span)


def _slice_source_text(source_text: str, span: SourceSpan) -> str | None:
    """Return the exact source text covered by ``span``."""
    if span.start_line < 1 or span.end_line < span.start_line:
        return None

    lines = source_text.splitlines(keepends=True)
    if not lines:
        return None
    if span.end_line > len(lines):
        return None

    if span.start_line == span.end_line:
        line = lines[span.start_line - 1]
        if span.start_column < 0 or span.end_column > len(line):
            return None
        snippet = line[span.start_column : span.end_column]
        return snippet or None

    segment = lines[span.start_line - 1 : span.end_line]
    if not segment:
        return None
    if span.start_column < 0 or span.start_column > len(segment[0]):
        return None
    if span.end_column < 0 or span.end_column > len(segment[-1]):
        return None

    segment[0] = segment[0][span.start_column :]
    segment[-1] = segment[-1][: span.end_column]
    snippet = "".join(segment)
    return snippet or None


def _estimate_tokens(text: str) -> int:
    """Return a simple positive token estimate for ``text``."""
    return max(1, (len(text) + 3) // 4)


__all__ = [
    "RenderDetail",
    "RenderedUnit",
    "RenderedUnitKind",
    "render_semantic_unit",
]

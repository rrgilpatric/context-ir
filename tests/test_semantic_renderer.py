"""Semantic-first renderer tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_renderer import (
    RenderDetail,
    RenderedUnitKind,
    render_semantic_unit,
)
from context_ir.semantic_types import SemanticProgram, SourceSite, SourceSpan


def _semantic_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted lower layers through dependency/frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _definition_id_for(program: SemanticProgram, qualified_name: str) -> str:
    """Return the unique definition ID for ``qualified_name``."""
    return next(
        definition.definition_id
        for definition in program.syntax.definitions
        if definition.qualified_name == qualified_name
    )


def _unresolved_id_for(program: SemanticProgram, access_text: str) -> str:
    """Return the unresolved frontier ID for ``access_text``."""
    return next(
        access.access_id
        for access in program.unresolved_frontier
        if access.access_text == access_text
    )


def _unsupported_id_for(program: SemanticProgram, construct_text: str) -> str:
    """Return the unsupported-construct ID for ``construct_text``."""
    return next(
        construct.construct_id
        for construct in program.unsupported_constructs
        if construct.construct_text == construct_text
    )


def _source_text_for_site(repo_root: Path, site: SourceSite) -> str | None:
    """Return exact on-disk text for ``site.span``."""
    source_path = repo_root / site.file_path
    source_text = source_path.read_text(encoding="utf-8")
    return _slice_source_text(source_text, site.span)


def _slice_source_text(source_text: str, span: SourceSpan) -> str | None:
    """Return the exact slice of ``source_text`` covered by ``span``."""
    lines = source_text.splitlines(keepends=True)
    if not lines:
        return None

    if span.start_line == span.end_line:
        line = lines[span.start_line - 1]
        snippet = line[span.start_column : span.end_column]
        return snippet or None

    segment = lines[span.start_line - 1 : span.end_line]
    segment[0] = segment[0][span.start_column :]
    segment[-1] = segment[-1][: span.end_column]
    snippet = "".join(segment)
    return snippet or None


def test_render_semantic_unit_renders_proven_symbol_across_detail_levels(
    tmp_path: Path,
) -> None:
    """Proven symbols render identity, summary, and exact source faithfully."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "models.py").write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass

            @dataclass
            class User:
                name: str
                age: int = 0
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    user_symbol_id = _definition_id_for(program, "pkg.models.User")
    user_symbol = program.resolved_symbols[user_symbol_id]

    identity = render_semantic_unit(program, user_symbol_id, RenderDetail.IDENTITY)
    summary = render_semantic_unit(program, user_symbol_id, RenderDetail.SUMMARY)
    source = render_semantic_unit(program, user_symbol_id, RenderDetail.SOURCE)

    assert identity.kind is RenderedUnitKind.PROVEN_SYMBOL
    assert identity.provenance == user_symbol.definition_site
    assert "kind: class" in identity.content
    assert "qualified_name: pkg.models.User" in identity.content
    assert f"unit_id: {user_symbol_id}" in identity.content

    assert "supported_decorators: dataclass" in summary.content
    assert "dataclass_support: dataclasses.dataclass" in summary.content
    assert "dataclass_fields: name: str; age: int = 0" in summary.content
    assert "file: pkg/models.py" in summary.content
    assert "proof_status: proven" in summary.content

    assert source.kind is RenderedUnitKind.PROVEN_SYMBOL
    assert source.content == _source_text_for_site(
        tmp_path, user_symbol.definition_site
    )
    assert source.token_count > 0


def test_render_semantic_unit_renders_unresolved_frontier_with_explicit_uncertainty(
    tmp_path: Path,
) -> None:
    """Unresolved frontier items keep reason codes, context, and site snippets."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run() -> None:
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    unresolved_id = _unresolved_id_for(program, "missing_call")
    unresolved = next(
        access
        for access in program.unresolved_frontier
        if access.access_id == unresolved_id
    )

    identity = render_semantic_unit(program, unresolved_id, RenderDetail.IDENTITY)
    summary = render_semantic_unit(program, unresolved_id, RenderDetail.SUMMARY)
    source = render_semantic_unit(program, unresolved_id, RenderDetail.SOURCE)

    assert identity.kind is RenderedUnitKind.UNRESOLVED_FRONTIER
    assert identity.provenance == unresolved.site
    assert "text: missing_call" in identity.content
    assert "kind: unresolved_frontier" in identity.content

    assert "proof_status: unknown" in summary.content
    assert "reason_code: unresolved_name" in summary.content
    assert "context: call" in summary.content
    assert "text: missing_call" in summary.content

    assert "proof_status: unknown" in source.content
    assert "reason_code: unresolved_name" in source.content
    assert "context: call" in source.content
    assert "source_snippet:" in source.content
    assert "missing_call()" in source.content
    assert source.token_count > 0


def test_render_semantic_unit_renders_unsupported_construct_with_truthful_fallbacks(
    tmp_path: Path,
) -> None:
    """Unsupported constructs stay explicit and use local site snippets when present."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        "from pkg.helpers import *\n",
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    unsupported_id = _unsupported_id_for(program, "from pkg.helpers import *")
    construct = next(
        item
        for item in program.unsupported_constructs
        if item.construct_id == unsupported_id
    )

    identity = render_semantic_unit(program, unsupported_id, RenderDetail.IDENTITY)
    summary = render_semantic_unit(program, unsupported_id, RenderDetail.SUMMARY)
    source = render_semantic_unit(program, unsupported_id, RenderDetail.SOURCE)

    assert identity.kind is RenderedUnitKind.UNSUPPORTED_CONSTRUCT
    assert identity.provenance == construct.site
    assert "text: from pkg.helpers import *" in identity.content
    assert "kind: unsupported_construct" in identity.content

    assert "proof_status: unsupported" in summary.content
    assert "reason_code: star_import" in summary.content
    assert "context: unavailable" in summary.content
    assert "text: from pkg.helpers import *" in summary.content

    assert "proof_status: unsupported" in source.content
    assert "reason_code: star_import" in source.content
    assert "source_snippet:" in source.content
    assert "from pkg.helpers import *" in source.content
    assert source.token_count > 0


def test_render_semantic_unit_raises_key_error_for_unknown_unit(
    tmp_path: Path,
) -> None:
    """Unknown unit IDs fail loudly."""
    (tmp_path / "main.py").write_text(
        "def run() -> None:\n    return None\n",
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)

    with pytest.raises(KeyError):
        render_semantic_unit(program, "missing:unit", RenderDetail.IDENTITY)


def test_render_semantic_unit_does_not_mutate_lower_layer_outputs(
    tmp_path: Path,
) -> None:
    """Rendering leaves the accepted semantic substrate unchanged."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "models.py").write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass

            @dataclass
            class User:
                name: str
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.models import *

            def run() -> None:
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    symbol_id = _definition_id_for(program, "pkg.models.User")
    unresolved_id = _unresolved_id_for(program, "missing_call")
    unsupported_id = _unsupported_id_for(program, "from pkg.models import *")

    resolved_symbols_before = dict(program.resolved_symbols)
    proven_dependencies_before = list(program.proven_dependencies)
    unresolved_before = list(program.unresolved_frontier)
    unsupported_before = list(program.unsupported_constructs)
    diagnostics_before = list(program.diagnostics)

    render_semantic_unit(program, symbol_id, RenderDetail.SUMMARY)
    render_semantic_unit(program, unresolved_id, RenderDetail.SOURCE)
    render_semantic_unit(program, unsupported_id, RenderDetail.SOURCE)

    assert program.resolved_symbols == resolved_symbols_before
    assert program.proven_dependencies == proven_dependencies_before
    assert program.unresolved_frontier == unresolved_before
    assert program.unsupported_constructs == unsupported_before
    assert program.diagnostics == diagnostics_before

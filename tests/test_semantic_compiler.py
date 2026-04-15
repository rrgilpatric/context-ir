"""Semantic-first compiler tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_compiler import compile_semantic_context
from context_ir.semantic_scorer import score_semantic_units
from context_ir.semantic_types import SemanticCompileResult, SemanticProgram


def _semantic_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted lower layers through dependency/frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _estimate_tokens(text: str) -> int:
    """Mirror compile-level token estimation for assembled documents."""
    return max(1, (len(text) + 3) // 4)


def test_compile_semantic_context_returns_separate_result_without_mutation(
    tmp_path: Path,
) -> None:
    """Compilation does not mutate the semantic substrate or scoring result."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.helpers import helper

            def run() -> None:
                helper()
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    scoring = score_semantic_units(program, "run missing_call")
    resolved_symbols_before = dict(program.resolved_symbols)
    bindings_before = list(program.bindings)
    resolved_imports_before = list(program.resolved_imports)
    dataclass_models_before = list(program.dataclass_models)
    dataclass_fields_before = list(program.dataclass_fields)
    resolved_references_before = list(program.resolved_references)
    dependencies_before = list(program.proven_dependencies)
    unresolved_before = list(program.unresolved_frontier)
    unsupported_before = list(program.unsupported_constructs)
    diagnostics_before = list(program.diagnostics)
    scores_before = dict(scoring.scores)

    result = compile_semantic_context(
        program,
        "run missing_call",
        budget=200,
        scoring=scoring,
    )

    assert isinstance(result, SemanticCompileResult)
    assert program.resolved_symbols == resolved_symbols_before
    assert program.bindings == bindings_before
    assert program.resolved_imports == resolved_imports_before
    assert program.dataclass_models == dataclass_models_before
    assert program.dataclass_fields == dataclass_fields_before
    assert program.resolved_references == resolved_references_before
    assert program.proven_dependencies == dependencies_before
    assert program.unresolved_frontier == unresolved_before
    assert program.unsupported_constructs == unsupported_before
    assert program.diagnostics == diagnostics_before
    assert dict(scoring.scores) == scores_before


def test_compile_semantic_context_renders_proven_and_uncertain_units_truthfully(
    tmp_path: Path,
) -> None:
    """Compiled output preserves provenance and uncertainty without overclaiming."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def unrelated() -> None:
                return None
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.helpers import *
            from pkg.helpers import helper

            def run() -> None:
                helper()
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    result = compile_semantic_context(
        program,
        "run missing_call from pkg.helpers import *",
        budget=300,
    )

    assert result.document.startswith("# Semantic Context")
    assert "query: run missing_call from pkg.helpers import *" in result.document
    assert "## main.py" in result.document
    assert "## pkg/helpers.py" in result.document
    assert "proof_status: proven" in result.document
    assert "kind: unresolved_frontier" in result.document
    assert "proof_status: unsupported" in result.document
    assert "## Omitted" in result.document
    assert len(result.omitted_unit_ids) > 0
    assert result.total_tokens == _estimate_tokens(result.document)
    assert result.total_tokens <= result.budget
    assert 0.0 <= result.confidence <= 1.0


def test_compile_semantic_context_uses_supplied_scoring_when_available(
    tmp_path: Path,
) -> None:
    """The compiler reuses caller-supplied scoring instead of requiring re-scoring."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def run() -> None:
                helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    scoring = score_semantic_units(program, "run")

    result = compile_semantic_context(program, "run", budget=120, scoring=scoring)

    assert result.optimization.budget == 120
    assert result.total_tokens == _estimate_tokens(result.document)
    assert result.total_tokens >= result.optimization.total_tokens
    assert result.confidence == result.optimization.confidence


def test_compile_semantic_context_is_conservative_for_empty_query(
    tmp_path: Path,
) -> None:
    """An empty query yields a bounded document with no selected semantic units."""
    (tmp_path / "main.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    result = compile_semantic_context(program, "", budget=100)

    assert "query: <empty>" in result.document
    assert "selected_units: 0" in result.document
    assert result.optimization.selections == ()
    assert result.total_tokens == _estimate_tokens(result.document)
    assert result.total_tokens <= result.budget
    assert result.confidence == 0.0


def test_compile_semantic_context_accounts_for_document_assembly_overhead(
    tmp_path: Path,
) -> None:
    """Compile totals reflect the emitted document, not just selected-unit costs."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def run() -> None:
                helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    result = compile_semantic_context(program, "run", budget=120)

    assert result.total_tokens == _estimate_tokens(result.document)
    assert result.total_tokens > result.optimization.total_tokens
    assert result.total_tokens <= result.budget


def test_compile_semantic_context_reserves_budget_for_document_overhead(
    tmp_path: Path,
) -> None:
    """A formerly under-reported case now trims selection until the document fits."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def run() -> None:
                helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    roomier_result = compile_semantic_context(program, "run", budget=120)
    tight_result = compile_semantic_context(program, "run", budget=80)

    assert tight_result.total_tokens == _estimate_tokens(tight_result.document)
    assert tight_result.total_tokens <= 80
    assert (
        tight_result.optimization.total_tokens
        < roomier_result.optimization.total_tokens
    )


def test_compile_semantic_context_rejects_impossible_document_budget(
    tmp_path: Path,
) -> None:
    """Compilation fails loudly when even the envelope cannot fit the budget."""
    (tmp_path / "main.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)

    with pytest.raises(
        ValueError,
        match="budget is too small for the compiled document envelope",
    ):
        compile_semantic_context(program, "", budget=10)

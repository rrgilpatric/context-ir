"""Semantic-first optimizer tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_optimizer import optimize_semantic_units
from context_ir.semantic_renderer import RenderDetail, render_semantic_unit
from context_ir.semantic_scorer import score_semantic_units
from context_ir.semantic_types import (
    SelectionBasis,
    SemanticOptimizationResult,
    SemanticProgram,
    SemanticSelectionRecord,
)


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


def _renderable_unit_ids(program: SemanticProgram) -> set[str]:
    """Return every renderable semantic unit ID."""
    return {
        *program.resolved_symbols.keys(),
        *(access.access_id for access in program.unresolved_frontier),
        *(construct.construct_id for construct in program.unsupported_constructs),
    }


def _selection_by_unit_id(
    result: SemanticOptimizationResult,
) -> dict[str, SemanticSelectionRecord]:
    """Index selected units by stable unit ID."""
    return {selection.unit_id: selection for selection in result.selections}


def test_optimize_semantic_units_returns_separate_result_without_mutation(
    tmp_path: Path,
) -> None:
    """Optimization stays separate from the accepted semantic substrate."""
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

    result = optimize_semantic_units(program, scoring, budget=200)

    assert isinstance(result, SemanticOptimizationResult)
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


def test_optimize_semantic_units_prefers_richer_detail_for_direct_relevance(
    tmp_path: Path,
) -> None:
    """Directly relevant units get richer detail than dependency-only support."""
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
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    scoring = score_semantic_units(program, "run")
    run_id = _definition_id_for(program, "main.run")
    helper_id = _definition_id_for(program, "pkg.helpers.helper")
    run_source = render_semantic_unit(program, run_id, RenderDetail.SOURCE)
    helper_identity = render_semantic_unit(program, helper_id, RenderDetail.IDENTITY)
    helper_summary = render_semantic_unit(program, helper_id, RenderDetail.SUMMARY)
    budget = run_source.token_count + helper_identity.token_count

    result = optimize_semantic_units(program, scoring, budget=budget)
    selections = _selection_by_unit_id(result)

    assert selections[run_id].detail == RenderDetail.SOURCE.value
    assert helper_id in selections
    assert selections[helper_id].detail == RenderDetail.IDENTITY.value
    assert helper_identity.token_count < helper_summary.token_count


def test_optimize_semantic_units_uses_rendered_token_costs_and_stays_within_budget(
    tmp_path: Path,
) -> None:
    """Selection costs come from the actual accepted renderer outputs."""
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
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    scoring = score_semantic_units(program, "run")
    result = optimize_semantic_units(program, scoring, budget=40)

    expected_total = 0
    for selection in result.selections:
        rendered = render_semantic_unit(
            program,
            selection.unit_id,
            RenderDetail(selection.detail),
        )
        assert selection.token_count == rendered.token_count
        expected_total += rendered.token_count

    assert result.total_tokens == expected_total
    assert result.total_tokens <= result.budget


def test_optimize_semantic_units_selects_dependency_support_with_proven_basis(
    tmp_path: Path,
) -> None:
    """Repository-backed dependency support can justify inclusion."""
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
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    scoring = score_semantic_units(program, "run")
    helper_id = _definition_id_for(program, "pkg.helpers.helper")

    result = optimize_semantic_units(program, scoring, budget=200)
    selections = _selection_by_unit_id(result)

    assert helper_id in selections
    assert selections[helper_id].basis is SelectionBasis.PROVEN_DEPENDENCY
    assert selections[helper_id].support_score > selections[helper_id].edit_score


def test_optimize_semantic_units_is_conservative_for_empty_query(
    tmp_path: Path,
) -> None:
    """Empty-query optimization stays bounded and omits everything."""
    (tmp_path / "main.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    scoring = score_semantic_units(program, "")
    result = optimize_semantic_units(program, scoring, budget=100)

    assert result.selections == ()
    assert set(result.omitted_unit_ids) == _renderable_unit_ids(program)
    assert result.total_tokens == 0
    assert result.confidence == 0.0
    assert result.warnings == ()

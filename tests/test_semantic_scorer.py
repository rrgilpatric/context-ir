"""Semantic-first scorer tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_scorer import score_semantic_units
from context_ir.semantic_types import SemanticProgram


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


def test_score_semantic_units_returns_complete_separate_result_without_mutation(
    tmp_path: Path,
) -> None:
    """Scoring returns a separate result over every renderable unit."""
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

    result = score_semantic_units(program, "")

    expected_unit_ids = {
        *program.resolved_symbols.keys(),
        *(access.access_id for access in program.unresolved_frontier),
        *(construct.construct_id for construct in program.unsupported_constructs),
    }
    assert set(result.scores) == expected_unit_ids
    assert result.scores is not program.resolved_symbols
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


def test_score_semantic_units_prefers_direct_symbol_matches_for_edit_likelihood(
    tmp_path: Path,
) -> None:
    """Direct symbol matches outrank unrelated symbols on ``p_edit``."""
    (tmp_path / "main.py").write_text(
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

    program = _semantic_program(tmp_path)
    helper_id = _definition_id_for(program, "main.helper")
    unrelated_id = _definition_id_for(program, "main.unrelated")

    result = score_semantic_units(program, "helper")

    assert result.scores[helper_id].p_edit > result.scores[unrelated_id].p_edit
    assert result.scores[helper_id].p_edit > 0.5


def test_score_semantic_units_scores_direct_unresolved_matches(
    tmp_path: Path,
) -> None:
    """Frontier items can be directly relevant from their own text surface."""
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

    result = score_semantic_units(program, "missing call")

    assert result.scores[unresolved_id].p_edit > 0.5
    assert result.scores[unresolved_id].p_edit > result.scores[unresolved_id].p_support


def test_score_semantic_units_scores_unsupported_constructs_without_proof_claims(
    tmp_path: Path,
) -> None:
    """Unsupported constructs remain rankable without becoming proven facts."""
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

    result = score_semantic_units(program, "from pkg.helpers import *")

    assert unsupported_id in result.scores
    assert result.scores[unsupported_id].p_edit > 0.5


def test_score_semantic_units_propagates_support_over_proven_dependencies(
    tmp_path: Path,
) -> None:
    """Relevant source symbols raise support on repository-backed dependency targets."""
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
    run_id = _definition_id_for(program, "main.run")
    helper_id = _definition_id_for(program, "pkg.helpers.helper")

    result = score_semantic_units(program, "run")

    assert result.scores[run_id].p_edit > 0.5
    assert result.scores[helper_id].p_support > 0.0
    assert result.scores[helper_id].p_support > result.scores[helper_id].p_edit


def test_score_semantic_units_uses_relevant_scope_support_for_uncertainty_items(
    tmp_path: Path,
) -> None:
    """Relevant scopes can raise support on unresolved and unsupported items."""
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
            import pkg.helpers

            def run() -> None:
                missing_call()
                pkg.helpers.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    run_id = _definition_id_for(program, "main.run")
    unresolved_id = _unresolved_id_for(program, "missing_call")
    unsupported_id = _unsupported_id_for(program, "pkg.helpers.helper")

    result = score_semantic_units(program, "run")

    assert result.scores[run_id].p_edit > 0.5
    assert result.scores[unresolved_id].p_support > 0.0
    assert result.scores[unresolved_id].p_support > result.scores[unresolved_id].p_edit
    assert result.scores[unsupported_id].p_support > 0.0
    assert (
        result.scores[unsupported_id].p_support > result.scores[unsupported_id].p_edit
    )


def test_score_semantic_units_returns_bounded_defaults_for_empty_query(
    tmp_path: Path,
) -> None:
    """Empty queries still return a complete, conservative score map."""
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

    result = score_semantic_units(program, "")

    expected_unit_ids = {
        *program.resolved_symbols.keys(),
        *(access.access_id for access in program.unresolved_frontier),
        *(construct.construct_id for construct in program.unsupported_constructs),
    }
    assert set(result.scores) == expected_unit_ids
    assert all(score.p_edit == 0.0 for score in result.scores.values())
    assert all(score.p_support == 0.0 for score in result.scores.values())


def test_score_semantic_units_keeps_all_scores_within_probability_bounds(
    tmp_path: Path,
) -> None:
    """Direct and propagated signals remain within closed probability bounds."""
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
            import pkg.helpers
            from pkg.helpers import helper

            def run() -> None:
                helper()
                missing_call()
                pkg.helpers.helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)

    result = score_semantic_units(program, "run helper missing")

    assert all(0.0 <= score.p_edit <= 1.0 for score in result.scores.values())
    assert all(0.0 <= score.p_support <= 1.0 for score in result.scores.values())


def test_score_semantic_units_supports_optional_embedding_injection(
    tmp_path: Path,
) -> None:
    """Injected embeddings can contribute semantic similarity without downloads."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def alpha() -> None:
                return None

            def beta() -> None:
                return None
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    alpha_id = _definition_id_for(program, "main.alpha")
    beta_id = _definition_id_for(program, "main.beta")

    def embed_fn(texts: list[str]) -> list[list[float]]:
        """Return deterministic toy embeddings for scorer injection tests."""
        vectors: list[list[float]] = []
        for text in texts:
            if text == "semantic intent" or "alpha" in text:
                vectors.append([1.0, 0.0])
            else:
                vectors.append([0.0, 1.0])
        return vectors

    result = score_semantic_units(program, "semantic intent", embed_fn=embed_fn)

    assert result.scores[alpha_id].p_edit > result.scores[beta_id].p_edit
    assert result.scores[alpha_id].p_support > result.scores[beta_id].p_support

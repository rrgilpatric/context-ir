"""Semantic-first diagnose and recompile tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_compiler import compile_semantic_context
from context_ir.semantic_diagnostics import (
    diagnose_semantic_miss,
    recompile_semantic_context,
)
from context_ir.semantic_renderer import RenderDetail
from context_ir.semantic_types import (
    SemanticDiagnosticResult,
    SemanticMissEvidence,
    SemanticMissKind,
    SemanticProgram,
    SemanticRecompileResult,
)


def _semantic_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted semantic pipeline through dependency/frontier derivation."""
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


def _frontier_id_for(program: SemanticProgram, access_text: str) -> str:
    """Return the unresolved frontier ID for ``access_text``."""
    return next(
        access.access_id
        for access in program.unresolved_frontier
        if access.access_text == access_text
    )


def _write_sample_program(tmp_path: Path) -> None:
    """Write a minimal semantic fixture with a dependency and unresolved call."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def extra() -> None:
                return None

            def run() -> None:
                helper()
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_nested_path_program(tmp_path: Path) -> None:
    """Write a semantic fixture with a nested module for path grounding tests."""
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "worker.py").write_text(
        textwrap.dedent(
            """
            def perform() -> None:
                return None
            """
        ).lstrip(),
        encoding="utf-8",
    )


def test_compile_semantic_context_populates_compile_context(tmp_path: Path) -> None:
    """Semantic compile results carry the durable query needed for recompile."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)

    result = compile_semantic_context(program, "run", budget=160)

    assert result.compile_context is not None
    assert result.compile_context.query == "run"


def test_diagnose_semantic_miss_returns_separate_result_without_mutation(
    tmp_path: Path,
) -> None:
    """Diagnosis returns a separate result and does not mutate its inputs."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "run", budget=160)
    resolved_symbols_before = dict(program.resolved_symbols)
    dependencies_before = list(program.proven_dependencies)
    unresolved_before = list(program.unresolved_frontier)
    unsupported_before = list(program.unsupported_constructs)
    diagnostics_before = list(program.diagnostics)
    previous_optimization = previous_result.optimization
    previous_document = previous_result.document
    previous_context = previous_result.compile_context

    result = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="missing_call",
            source="test",
        ),
        program,
    )

    assert isinstance(result, SemanticDiagnosticResult)
    assert program.resolved_symbols == resolved_symbols_before
    assert program.proven_dependencies == dependencies_before
    assert program.unresolved_frontier == unresolved_before
    assert program.unsupported_constructs == unsupported_before
    assert program.diagnostics == diagnostics_before
    assert previous_result.optimization == previous_optimization
    assert previous_result.document == previous_document
    assert previous_result.compile_context == previous_context


def test_diagnose_semantic_miss_grounds_absent_symbols_by_supported_names(
    tmp_path: Path,
) -> None:
    """Absent-symbol evidence grounds by exact unit ID, qualified name, and name."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "run", budget=220)
    helper_id = _definition_id_for(program, "main.helper")

    by_unit_id = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence=helper_id,
        ),
        program,
    )
    by_qualified_name = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="main.helper",
        ),
        program,
    )
    by_simple_name = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="helper",
        ),
        program,
    )

    assert helper_id in by_unit_id.grounded_unit_ids
    assert helper_id in by_qualified_name.grounded_unit_ids
    assert helper_id in by_simple_name.grounded_unit_ids


def test_diagnose_semantic_miss_returns_no_grounding_for_inconsistent_trace_clues(
    tmp_path: Path,
) -> None:
    """Conflicting trace file/function clues do not ground unrelated units."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "run", budget=160)

    result = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.OUT_OF_PACK_TRACE,
            evidence="File 'other.py', line 1, in run",
        ),
        program,
    )

    assert result.grounded_unit_ids == ()
    assert result.omitted_unit_ids == ()
    assert result.too_shallow_unit_ids == ()
    assert result.sufficiently_represented_unit_ids == ()
    assert result.recommended_expansions == ()
    assert "Could not ground" in result.reason


def test_diagnose_semantic_miss_keeps_consistent_trace_grounding(
    tmp_path: Path,
) -> None:
    """Consistent trace file/function clues still ground to the real unit."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "run", budget=160)
    run_id = _definition_id_for(program, "main.run")

    result = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.OUT_OF_PACK_TRACE,
            evidence="File 'main.py', line 8, in run",
        ),
        program,
    )

    assert result.grounded_unit_ids == (run_id,)


def test_diagnose_semantic_miss_supports_exact_and_suffix_path_grounding(
    tmp_path: Path,
) -> None:
    """Path grounding accepts exact and suffix path matches that stay path-shaped."""
    _write_nested_path_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "perform", budget=160)
    perform_id = _definition_id_for(program, "pkg.worker.perform")

    exact_result = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.EDIT_TO_OMITTED_PATH,
            evidence="pkg/worker.py",
        ),
        program,
    )
    suffix_result = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.EDIT_TO_OMITTED_PATH,
            evidence="worker.py",
        ),
        program,
    )

    assert perform_id in exact_result.grounded_unit_ids
    assert perform_id in suffix_result.grounded_unit_ids


def test_diagnose_semantic_miss_rejects_arbitrary_substring_path_evidence(
    tmp_path: Path,
) -> None:
    """Path grounding rejects non-path-shaped substrings."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "run", budget=160)

    result = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.EDIT_TO_OMITTED_PATH,
            evidence="ain",
        ),
        program,
    )

    assert result.grounded_unit_ids == ()
    assert result.recommended_expansions == ()
    assert "Could not ground" in result.reason


def test_diagnose_semantic_miss_distinguishes_omitted_too_shallow_and_sufficient(
    tmp_path: Path,
) -> None:
    """Diagnosis distinguishes omitted units, shallow units, and surfaced ones."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    tight_result = compile_semantic_context(program, "run", budget=160)
    helper_id = _definition_id_for(program, "main.helper")
    extra_id = _definition_id_for(program, "main.extra")
    missing_call_id = _frontier_id_for(program, "missing_call")
    helper_selection = next(
        selection
        for selection in tight_result.optimization.selections
        if selection.unit_id == helper_id
    )
    surfaced_result = compile_semantic_context(program, "run", budget=220)

    helper_diagnostic = diagnose_semantic_miss(
        tight_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="helper",
        ),
        program,
    )
    extra_diagnostic = diagnose_semantic_miss(
        tight_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="extra",
        ),
        program,
    )
    missing_call_diagnostic = diagnose_semantic_miss(
        tight_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="missing_call",
        ),
        program,
    )
    surfaced_diagnostic = diagnose_semantic_miss(
        surfaced_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="missing_call",
        ),
        program,
    )

    assert helper_selection.detail == RenderDetail.IDENTITY.value
    assert helper_diagnostic.too_shallow_unit_ids == (helper_id,)
    assert "too shallow" in helper_diagnostic.reason
    assert extra_diagnostic.omitted_unit_ids == (extra_id,)
    assert "omitted due to budget pressure" in extra_diagnostic.reason
    assert missing_call_diagnostic.omitted_unit_ids == (missing_call_id,)
    assert "not surfaced" in missing_call_diagnostic.reason
    assert surfaced_diagnostic.sufficiently_represented_unit_ids == (missing_call_id,)
    assert "already sufficiently represented" in surfaced_diagnostic.reason


def test_diagnose_semantic_miss_recommends_grounded_units_and_dependencies(
    tmp_path: Path,
) -> None:
    """Recommended expansions include grounded misses and one-hop dependencies."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "", budget=100)
    run_id = _definition_id_for(program, "main.run")
    helper_id = _definition_id_for(program, "main.helper")

    result = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="main.run",
        ),
        program,
    )

    assert result.omitted_unit_ids == (run_id,)
    assert run_id in result.recommended_expansions
    assert helper_id in result.recommended_expansions


def test_diagnose_semantic_miss_returns_honest_result_for_ungrounded_evidence(
    tmp_path: Path,
) -> None:
    """Ungrounded evidence does not fabricate grounded misses or expansions."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "run", budget=160)

    result = diagnose_semantic_miss(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="does_not_exist_anywhere",
        ),
        program,
    )

    assert result.grounded_unit_ids == ()
    assert result.omitted_unit_ids == ()
    assert result.too_shallow_unit_ids == ()
    assert result.recommended_expansions == ()
    assert "Could not ground" in result.reason


def test_recompile_semantic_context_returns_separate_result_without_mutation(
    tmp_path: Path,
) -> None:
    """Recompile returns a separate result and leaves inputs unchanged."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "", budget=100)
    resolved_symbols_before = dict(program.resolved_symbols)
    dependencies_before = list(program.proven_dependencies)
    unresolved_before = list(program.unresolved_frontier)
    unsupported_before = list(program.unsupported_constructs)
    diagnostics_before = list(program.diagnostics)
    previous_optimization = previous_result.optimization
    previous_document = previous_result.document
    previous_context = previous_result.compile_context

    result = recompile_semantic_context(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="main.run",
        ),
        delta_budget=140,
        program=program,
    )

    assert isinstance(result, SemanticRecompileResult)
    assert program.resolved_symbols == resolved_symbols_before
    assert program.proven_dependencies == dependencies_before
    assert program.unresolved_frontier == unresolved_before
    assert program.unsupported_constructs == unsupported_before
    assert program.diagnostics == diagnostics_before
    assert previous_result.optimization == previous_optimization
    assert previous_result.document == previous_document
    assert previous_result.compile_context == previous_context


def test_recompile_semantic_context_adds_newly_selected_units_within_budget(
    tmp_path: Path,
) -> None:
    """Recompile can add newly selected units under the expanded budget."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "", budget=100)
    run_id = _definition_id_for(program, "main.run")
    helper_id = _definition_id_for(program, "main.helper")

    result = recompile_semantic_context(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="main.run",
        ),
        delta_budget=140,
        program=program,
    )

    assert run_id in result.newly_selected_unit_ids
    assert helper_id in result.compile_result.optimization.omitted_unit_ids or (
        helper_id
        in {
            selection.unit_id
            for selection in result.compile_result.optimization.selections
        }
    )
    assert result.compile_result.budget == 240
    assert result.compile_result.total_tokens <= result.compile_result.budget


def test_recompile_semantic_context_can_upgrade_selected_units_to_richer_detail(
    tmp_path: Path,
) -> None:
    """Recompile can upgrade a grounded unit from shallow detail to richer detail."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "run", budget=160)
    helper_id = _definition_id_for(program, "main.helper")
    previous_detail = next(
        selection.detail
        for selection in previous_result.optimization.selections
        if selection.unit_id == helper_id
    )

    result = recompile_semantic_context(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.ABSENT_SYMBOL,
            evidence="helper",
        ),
        delta_budget=80,
        program=program,
    )
    upgraded_detail = next(
        selection.detail
        for selection in result.compile_result.optimization.selections
        if selection.unit_id == helper_id
    )

    assert previous_detail == RenderDetail.IDENTITY.value
    assert helper_id in result.upgraded_unit_ids
    assert upgraded_detail == RenderDetail.SOURCE.value
    assert result.compile_result.total_tokens <= result.compile_result.budget


def test_recompile_semantic_context_keeps_ungrounded_trace_evidence_honest(
    tmp_path: Path,
) -> None:
    """Contradictory trace evidence does not fabricate grounded recompile changes."""
    _write_sample_program(tmp_path)
    program = _semantic_program(tmp_path)
    previous_result = compile_semantic_context(program, "", budget=100)

    result = recompile_semantic_context(
        previous_result,
        SemanticMissEvidence(
            kind=SemanticMissKind.OUT_OF_PACK_TRACE,
            evidence="File 'other.py', line 1, in run",
        ),
        delta_budget=120,
        program=program,
    )

    assert result.diagnostic.grounded_unit_ids == ()
    assert result.diagnostic.recommended_expansions == ()
    assert result.newly_selected_unit_ids == ()
    assert result.upgraded_unit_ids == ()
    assert result.compile_result.optimization.selections == ()
    assert "Could not ground" in result.diagnostic.reason

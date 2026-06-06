"""Semantic-first scorer tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

import context_ir.semantic_renderer as semantic_renderer
import context_ir.semantic_scorer as semantic_scorer
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_scorer import score_semantic_units
from context_ir.semantic_types import (
    CapabilityTier,
    SemanticEvalRuntimeEvidence,
    SemanticEvalRuntimeEvidenceField,
    SemanticProgram,
    SourceSite,
    SourceSpan,
    SyntaxProgram,
    UnresolvedAccess,
    UnresolvedReasonCode,
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


def _semantic_eval_evidence_program(tmp_path: Path) -> SemanticProgram:
    """Return a minimal program with one compact eval runtime evidence unit."""
    return SemanticProgram(
        repo_root=tmp_path,
        syntax=SyntaxProgram(repo_root=tmp_path),
        eval_runtime_evidence=[
            SemanticEvalRuntimeEvidence(
                unit_id="eval_evidence:oracle_signal_hasattr_probe:hasattr:main.py:2:11",
                evidence_id="oracle_signal_hasattr_probe:hasattr:main.py:2:11",
                runtime_family="hasattr",
                fixture_id="oracle_signal_hasattr_probe",
                task_ids=("oracle_signal_hasattr_probe",),
                run_spec_ids=("oracle_signal_hasattr_probe_matrix",),
                artifact_path=(
                    "evals/fixtures/oracle_signal_hasattr_probe/"
                    "eval_runtime_observations.json"
                ),
                site=SourceSite(
                    site_id="site:eval-evidence:hasattr",
                    file_path="evals/fixtures/oracle_signal_hasattr_probe/main.py",
                    span=SourceSpan(
                        start_line=2,
                        start_column=11,
                        end_line=2,
                        end_column=29,
                    ),
                    snippet="hasattr(obj, name)",
                ),
                construct_text="hasattr(obj, name)",
                reason_code=UnresolvedReasonCode.REFLECTIVE_BUILTIN,
                primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
                expect_attached_runtime_provenance=True,
                normalized_payload=(
                    SemanticEvalRuntimeEvidenceField(
                        key="attribute_present",
                        value="true",
                    ),
                ),
                durable_payload_reference=(
                    "artifact://hasattr/int-bit-length-observation.json"
                ),
            )
        ],
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
    assert all(score.p_edit == 0.0 for score in result.scores.values())
    assert all(score.p_support == 0.0 for score in result.scores.values())
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


def test_score_semantic_units_boosts_snake_case_exact_identifier_edit_anchor(
    tmp_path: Path,
) -> None:
    """A leading-underscore symbol mention becomes a strong direct edit anchor."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def _selected_unit_metadata() -> str:
                return "target"

            def selected_unit_metadata_support() -> str:
                return "selected unit metadata support"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    target_id = _definition_id_for(program, "main._selected_unit_metadata")
    support_id = _definition_id_for(program, "main.selected_unit_metadata_support")

    result = score_semantic_units(
        program,
        (
            "Fix _selected_unit_metadata while keeping selected unit metadata "
            "support aligned"
        ),
    )

    assert result.scores[target_id].p_edit >= 0.85
    assert result.scores[target_id].p_edit > result.scores[support_id].p_edit
    assert result.scores[target_id].p_edit > result.scores[target_id].p_support


def test_score_semantic_units_does_not_exact_anchor_unqualified_probe_names(
    tmp_path: Path,
) -> None:
    """Unqualified non-leading snake_case query names do not get exact floors."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def probe_directory() -> str:
                return "directory"

            def probe_namespace() -> str:
                return "namespace"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    directory_id = _definition_id_for(program, "main.probe_directory")
    namespace_id = _definition_id_for(program, "main.probe_namespace")

    directory_result = score_semantic_units(program, "probe_directory")
    namespace_result = score_semantic_units(program, "probe_namespace")

    assert directory_result.scores[directory_id].p_edit < 0.85
    assert namespace_result.scores[namespace_id].p_edit < 0.85


def test_score_semantic_units_boosts_literal_implementation_surface_mentions(
    tmp_path: Path,
) -> None:
    """Literal snake-case implementation names get a direct but sub-exact floor."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def discover_runtime_contract() -> str:
                return "contract"

            def saturated_helper_support() -> str:
                return "helper"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)
    target_id = _definition_id_for(program, "main.discover_runtime_contract")
    helper_id = _definition_id_for(program, "main.saturated_helper_support")

    result = score_semantic_units(
        program,
        "Fix discover_runtime_contract without changing helper support",
    )

    assert result.scores[target_id].p_edit >= 0.30
    assert result.scores[target_id].p_edit < 0.85
    assert result.scores[target_id].p_edit > result.scores[helper_id].p_edit


def test_score_semantic_units_keeps_short_snake_mentions_below_output_flow(
    tmp_path: Path,
) -> None:
    """Short snake-case mentions do not swamp the broader output-flow target."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def probe_namespace(obj: object) -> dict[str, object]:
                return vars(obj)

            def render_probe_digest() -> str:
                try:
                    probe_namespace(1)
                except TypeError:
                    status = "raised_type_error"
                else:
                    status = "returned_namespace"
                return f"probe_digest:{status}"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)
    probe_id = _definition_id_for(program, "main.probe_namespace")
    renderer_id = _definition_id_for(program, "main.render_probe_digest")
    unsupported_id = _unsupported_id_for(program, "vars(obj)")

    result = score_semantic_units(
        program,
        "Fix probe_namespace unsupported vars(obj) raised TypeError "
        "and keep digest output aligned",
    )

    assert result.scores[renderer_id].p_edit > result.scores[probe_id].p_edit
    assert result.scores[unsupported_id].p_support < 0.24


def test_score_semantic_units_boosts_exact_output_surface_emitters(
    tmp_path: Path,
) -> None:
    """Functions emitting exact key/value surfaces become direct edit anchors."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def render_contract_surface() -> str:
                return "runtime=additive"

            class RuntimeEvidenceField:
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)
    renderer_id = _definition_id_for(program, "main.render_contract_surface")
    field_id = _definition_id_for(program, "main.RuntimeEvidenceField")

    result = score_semantic_units(
        program,
        "Fix renderer so evidence renders runtime=additive",
    )

    assert result.scores[renderer_id].p_edit >= 0.30
    assert result.scores[renderer_id].p_edit > result.scores[field_id].p_edit


def test_score_semantic_units_prefers_semantic_renderer_surface_when_named(
    tmp_path: Path,
) -> None:
    """Semantic renderer prose lifts renderer surfaces over sibling emitters."""
    package_dir = tmp_path / "src" / "context_ir"
    package_dir.mkdir(parents=True)
    (package_dir / "semantic_renderer.py").write_text(
        textwrap.dedent(
            """
            def _render_contract_surface() -> str:
                return "runtime=additive"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (package_dir / "eval_evidence.py").write_text(
        textwrap.dedent(
            """
            def render_contract_surface() -> str:
                return "runtime=additive"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)
    renderer_id = _definition_id_for(
        program,
        "src.context_ir.semantic_renderer._render_contract_surface",
    )
    sibling_id = _definition_id_for(
        program,
        "src.context_ir.eval_evidence.render_contract_surface",
    )

    result = score_semantic_units(
        program,
        "Fix semantic renderer so evidence renders runtime=additive",
    )

    assert result.scores[renderer_id].p_edit >= 0.40
    assert result.scores[renderer_id].p_edit > result.scores[sibling_id].p_edit


def test_score_semantic_units_boosts_fully_named_class_contract_surfaces(
    tmp_path: Path,
) -> None:
    """A class whose contract-name terms are all queried gets a direct floor."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class SemanticEvalRuntimeEvidence:
                pass

            class SemanticEvalRuntimeEvidenceField:
                pass

            class EvalRuntimeEvidence:
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)
    contract_id = _definition_id_for(program, "main.SemanticEvalRuntimeEvidence")
    non_semantic_id = _definition_id_for(program, "main.EvalRuntimeEvidence")

    result = score_semantic_units(
        program,
        "Fix semantic eval runtime evidence contract",
    )

    assert result.scores[contract_id].p_edit >= 0.30
    assert result.scores[contract_id].p_edit > result.scores[non_semantic_id].p_edit


def test_score_semantic_units_preserves_qualified_exact_identifier_anchors(
    tmp_path: Path,
) -> None:
    """A qualified symbol mention still becomes a strong direct edit anchor."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def probe_directory() -> str:
                return "directory"

            def probe_namespace() -> str:
                return "namespace"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    directory_id = _definition_id_for(program, "main.probe_directory")
    namespace_id = _definition_id_for(program, "main.probe_namespace")

    directory_result = score_semantic_units(program, "main.probe_directory")
    namespace_result = score_semantic_units(program, "main.probe_namespace")

    assert directory_result.scores[directory_id].p_edit >= 0.85
    assert namespace_result.scores[namespace_id].p_edit >= 0.85


def test_score_semantic_units_does_not_anchor_single_titlecase_command_words(
    tmp_path: Path,
) -> None:
    """A Titlecase prose command does not become an exact identifier anchor."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def Fix() -> str:
                return "prose command"

            def _selected_unit_metadata() -> str:
                return "target"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    command_id = _definition_id_for(program, "main.Fix")
    target_id = _definition_id_for(program, "main._selected_unit_metadata")

    result = score_semantic_units(program, "Fix _selected_unit_metadata")

    assert result.scores[target_id].p_edit >= 0.85
    assert result.scores[command_id].p_edit < 0.85
    assert result.scores[target_id].p_edit > result.scores[command_id].p_edit


def test_score_semantic_units_scores_eval_runtime_evidence_as_support(
    tmp_path: Path,
) -> None:
    """Compact eval evidence becomes a searchable internal support unit."""
    program = _semantic_eval_evidence_program(tmp_path)
    evidence_id = program.eval_runtime_evidence[0].unit_id

    result = score_semantic_units(
        program,
        "unsupported hasattr runtime provenance attribute_present",
    )

    assert set(result.scores) == {evidence_id}
    assert result.scores[evidence_id].p_support >= 0.20
    assert result.scores[evidence_id].p_support > result.scores[evidence_id].p_edit


def test_score_semantic_units_preserves_digit_and_camel_exact_identifier_anchors(
    tmp_path: Path,
) -> None:
    """Digit-bearing and multi-part Pascal/Camel names still get exact floors."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def parser2() -> str:
                return "digit"

            class EvalSelectedUnit:
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    parser_id = _definition_id_for(program, "main.parser2")
    eval_selected_id = _definition_id_for(program, "main.EvalSelectedUnit")

    digit_result = score_semantic_units(program, "parser2")
    camel_result = score_semantic_units(program, "EvalSelectedUnit")

    assert digit_result.scores[parser_id].p_edit >= 0.85
    assert camel_result.scores[eval_selected_id].p_edit >= 0.85


def test_score_semantic_units_exact_identifier_anchor_requires_whole_symbol_name(
    tmp_path: Path,
) -> None:
    """The raw identifier anchor does not fire for adjacent symbol names."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def _selected_unit_metadata() -> str:
                return "target"

            def _selected_unit_metadata_extra() -> str:
                return "extra"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    target_id = _definition_id_for(program, "main._selected_unit_metadata")
    extra_id = _definition_id_for(program, "main._selected_unit_metadata_extra")

    exact_result = score_semantic_units(program, "Fix _selected_unit_metadata")
    partial_result = score_semantic_units(program, "Fix selected_unit_metadata")

    assert exact_result.scores[target_id].p_edit >= 0.85
    assert exact_result.scores[target_id].p_edit > exact_result.scores[extra_id].p_edit
    assert exact_result.scores[extra_id].p_edit < 0.85
    assert (
        partial_result.scores[target_id].p_edit < exact_result.scores[target_id].p_edit
    )


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
                pkg.helpers.helper.extra()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    run_id = _definition_id_for(program, "main.run")
    unresolved_id = _unresolved_id_for(program, "missing_call")
    unsupported_id = _unsupported_id_for(program, "pkg.helpers.helper.extra")

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


def test_score_semantic_units_uses_scope_body_signal_for_behavioral_queries(
    tmp_path: Path,
) -> None:
    """Behavioral queries can rank the owning function above its helpers."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "planner.py").write_text(
        textwrap.dedent(
            """
            def build_execution_plan(query: str) -> list[str]:
                return [query, "draft execution plan", "confirm preview"]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "presenter.py").write_text(
        textwrap.dedent(
            """
            def render_patch_preview(plan: list[str]) -> str:
                return "patch preview: " + " | ".join(plan)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.planner import build_execution_plan
            from pkg.presenter import render_patch_preview

            def run_signal_smoke(query: str) -> str:
                plan = build_execution_plan(query)
                preview = render_patch_preview(plan)
                record_missing_step(plan)
                return preview
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    run_id = _definition_id_for(program, "main.run_signal_smoke")
    planner_id = _definition_id_for(program, "pkg.planner.build_execution_plan")
    presenter_id = _definition_id_for(program, "pkg.presenter.render_patch_preview")

    result = score_semantic_units(
        program,
        "Fix missing step while keeping execution plan preview aligned",
    )

    assert result.scores[run_id].p_edit > 0.40
    assert result.scores[run_id].p_edit > result.scores[planner_id].p_edit
    assert result.scores[planner_id].p_edit > result.scores[presenter_id].p_edit


def test_score_semantic_units_reuses_render_session_for_candidate_profiles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scoring builds renderer lookup indexes once while profiling candidates."""
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

            def run() -> None:
                helper()
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    run_id = _definition_id_for(program, "main.run")
    unresolved_id = _unresolved_id_for(program, "missing_call")
    unsupported_id = _unsupported_id_for(program, "from pkg.helpers import *")
    original_build_context = semantic_renderer._build_render_context
    original_unresolved_by_id = semantic_renderer._unresolved_by_id
    original_render_with_context = semantic_renderer._render_semantic_unit_with_context
    build_context_calls = 0
    unresolved_index_builds = 0
    render_calls: dict[tuple[str, semantic_renderer.RenderDetail], int] = {}

    def counting_build_context(
        program_arg: SemanticProgram,
    ) -> semantic_renderer._SemanticRenderContext:
        nonlocal build_context_calls
        build_context_calls += 1
        return original_build_context(program_arg)

    def counting_unresolved_by_id(
        program_arg: SemanticProgram,
    ) -> dict[str, UnresolvedAccess]:
        nonlocal unresolved_index_builds
        unresolved_index_builds += 1
        return original_unresolved_by_id(program_arg)

    def counting_render_with_context(
        *,
        program: SemanticProgram,
        unit_id: str,
        detail: semantic_renderer.RenderDetail,
        context: semantic_renderer._SemanticRenderContext,
        source_file_cache: dict[
            Path, semantic_renderer._SourceFileMaterialization | None
        ],
    ) -> semantic_renderer.RenderedUnit:
        cache_key = (unit_id, detail)
        render_calls[cache_key] = render_calls.get(cache_key, 0) + 1
        return original_render_with_context(
            program=program,
            unit_id=unit_id,
            detail=detail,
            context=context,
            source_file_cache=source_file_cache,
        )

    monkeypatch.setattr(
        semantic_renderer,
        "_build_render_context",
        counting_build_context,
    )
    monkeypatch.setattr(
        semantic_renderer,
        "_unresolved_by_id",
        counting_unresolved_by_id,
    )
    monkeypatch.setattr(
        semantic_renderer,
        "_render_semantic_unit_with_context",
        counting_render_with_context,
    )

    score_semantic_units(program, "fix missing call while keeping helper")

    assert build_context_calls == 1
    assert unresolved_index_builds == 1
    assert render_calls[(run_id, semantic_renderer.RenderDetail.SUMMARY)] == 1
    assert render_calls[(run_id, semantic_renderer.RenderDetail.SOURCE)] == 1
    assert render_calls[(unresolved_id, semantic_renderer.RenderDetail.SUMMARY)] == 1
    assert render_calls[(unsupported_id, semantic_renderer.RenderDetail.SUMMARY)] == 1


def test_score_semantic_units_reuses_lexical_cache_within_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scoring reuses lexical terms but does not retain them across requests."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def run() -> None:
                helper()
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    query = "fix main.run while keeping helper"
    original_extract_terms = semantic_scorer._extract_terms
    extract_calls_by_text: dict[str, int] = {}

    def counting_extract_terms(text: str) -> tuple[str, ...]:
        extract_calls_by_text[text] = extract_calls_by_text.get(text, 0) + 1
        return original_extract_terms(text)

    monkeypatch.setattr(
        semantic_scorer,
        "_extract_terms",
        counting_extract_terms,
    )

    score_semantic_units(program, query)

    assert extract_calls_by_text[query] == 1
    assert extract_calls_by_text["main.run"] == 1
    assert extract_calls_by_text["main.py"] == 1

    score_semantic_units(program, query)

    assert extract_calls_by_text[query] == 2
    assert extract_calls_by_text["main.run"] == 2
    assert extract_calls_by_text["main.py"] == 2


def test_lexical_relevance_composes_searchable_parts_without_joined_extraction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lexical scoring reuses part terms without extracting the joined surface."""
    searchable_parts = (
        "main.run",
        "main.py",
        "summary MissingCallSupport repeated main.run",
    )
    candidate = semantic_scorer._CandidateProfile(
        unit_id="def:main.py:main.run",
        kind=semantic_renderer.RenderedUnitKind.PROVEN_SYMBOL,
        primary_text="main.run",
        file_path="main.py",
        scope_id=None,
        symbol_kind=None,
        searchable_parts=searchable_parts,
        body_text=None,
    )
    original_extract_terms = semantic_scorer._extract_terms
    expected_searchable_terms = original_extract_terms(candidate.searchable_text)
    extract_calls_by_text: dict[str, int] = {}

    def counting_extract_terms(text: str) -> tuple[str, ...]:
        extract_calls_by_text[text] = extract_calls_by_text.get(text, 0) + 1
        return original_extract_terms(text)

    monkeypatch.setattr(
        semantic_scorer,
        "_extract_terms",
        counting_extract_terms,
    )

    lexical_cache = semantic_scorer._LexicalCache()
    query = "fix missing call support in main.run"
    query_terms = lexical_cache.terms(query)
    normalized_query = lexical_cache.normalized(query)
    extract_calls_by_text.clear()

    lexical_score = semantic_scorer._lexical_relevance(
        candidate=candidate,
        query_terms=query_terms,
        normalized_query=normalized_query,
        lexical_cache=lexical_cache,
    )

    assert lexical_score > 0.0
    assert candidate.searchable_text not in extract_calls_by_text
    assert lexical_cache.terms_for_parts(searchable_parts) == expected_searchable_terms
    assert lexical_cache.normalized_parts(searchable_parts) == " ".join(
        expected_searchable_terms
    )
    assert extract_calls_by_text == {
        "main.run": 1,
        "main.py": 1,
        "summary MissingCallSupport repeated main.run": 1,
    }


def test_lexical_relevance_fast_paths_summary_content_without_semantic_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Summary content is fragmented while preserving joined-searchable terms."""
    summary_content = (
        "proven summary: function main.run @ main.py:1:0-2:0\n"
        "fields: ownerAlias: str = owner_alias\n"
        "decorators: cached_property"
    )
    searchable_parts = ("main.run", "main.py", summary_content)
    lexical_searchable_parts = (
        semantic_scorer._SearchablePart("main.run"),
        semantic_scorer._SearchablePart("main.py"),
        semantic_scorer._SearchablePart(
            text=summary_content,
            term_fragments=semantic_scorer._summary_content_term_fragments(
                summary_content
            ),
        ),
    )
    candidate = semantic_scorer._CandidateProfile(
        unit_id="def:main.py:main.run",
        kind=semantic_renderer.RenderedUnitKind.PROVEN_SYMBOL,
        primary_text="main.run",
        file_path="main.py",
        scope_id=None,
        symbol_kind=None,
        searchable_parts=searchable_parts,
        body_text=None,
        lexical_searchable_parts=lexical_searchable_parts,
    )
    original_extract_terms = semantic_scorer._extract_terms
    expected_searchable_terms = original_extract_terms(candidate.searchable_text)
    expected_summary_terms = original_extract_terms(summary_content)
    extract_calls_by_text: dict[str, int] = {}

    def counting_extract_terms(text: str) -> tuple[str, ...]:
        extract_calls_by_text[text] = extract_calls_by_text.get(text, 0) + 1
        return original_extract_terms(text)

    monkeypatch.setattr(
        semantic_scorer,
        "_extract_terms",
        counting_extract_terms,
    )

    lexical_cache = semantic_scorer._LexicalCache()
    query = "fix owner alias on main.run cached property"
    query_terms = lexical_cache.terms(query)
    normalized_query = lexical_cache.normalized(query)
    extract_calls_by_text.clear()

    lexical_score = semantic_scorer._lexical_relevance(
        candidate=candidate,
        query_terms=query_terms,
        normalized_query=normalized_query,
        lexical_cache=lexical_cache,
    )

    assert lexical_score > 0.0
    assert candidate.searchable_text == "\n".join(searchable_parts)
    assert summary_content not in extract_calls_by_text
    assert candidate.searchable_text not in extract_calls_by_text
    assert (
        lexical_cache.terms_for_searchable_parts(candidate.lexical_searchable_parts)
        == expected_searchable_terms
    )
    assert (
        lexical_cache.terms_for_searchable_parts((lexical_searchable_parts[-1],))
        == expected_summary_terms
    )
    assert lexical_cache.normalized_searchable_parts(
        candidate.lexical_searchable_parts
    ) == " ".join(expected_searchable_terms)


def test_score_semantic_units_calibrates_tests_for_implementation_intent(
    tmp_path: Path,
) -> None:
    """Implementation queries keep behavior tests as support, not first edit anchors."""
    source_dir = tmp_path / "src" / "context_ir"
    source_dir.mkdir(parents=True)
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (source_dir / "runtime_observation_recompile.py").write_text(
        textwrap.dedent(
            """
            def apply_default_local_python_subprocess_for_diagnostic_and_recompile(
                source: str,
            ) -> str:
                probe_result = "runtime probe results attach additive provenance"
                boundary = "unsupported EXEC_OR_EVAL units"
                exec(source)
                return f"{probe_result} to {boundary} without promoting primary truth"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (tests_dir / "test_runtime_observation_recompile.py").write_text(
        textwrap.dedent(
            """
            def test_default_local_python_subprocess_recompile_observes_exec() -> None:
                observed = (
                    "default local Python subprocess recompile runtime probe results "
                    "attach additive provenance unsupported EXEC_OR_EVAL primary truth"
                )
                assert "exec" in observed
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    source_id = _definition_id_for(
        program,
        (
            "src.context_ir.runtime_observation_recompile."
            "apply_default_local_python_subprocess_for_diagnostic_and_recompile"
        ),
    )
    test_id = _definition_id_for(
        program,
        (
            "tests.test_runtime_observation_recompile."
            "test_default_local_python_subprocess_recompile_observes_exec"
        ),
    )

    implementation_result = score_semantic_units(
        program,
        (
            "Fix default local Python subprocess recompile so exec(source) runtime "
            "probe results attach additive provenance to unsupported EXEC_OR_EVAL "
            "units without promoting primary truth"
        ),
    )
    explicit_test_result = score_semantic_units(
        program,
        (
            "Update tests/test_runtime_observation_recompile.py coverage for default "
            "local Python subprocess recompile"
        ),
    )

    assert implementation_result.scores[source_id].p_edit > (
        implementation_result.scores[test_id].p_edit
    )
    assert implementation_result.scores[test_id].p_edit <= 0.19
    assert implementation_result.scores[test_id].p_support > 0.0
    assert explicit_test_result.scores[test_id].p_edit > (
        implementation_result.scores[test_id].p_edit
    )
    assert explicit_test_result.scores[test_id].p_edit >= 0.30


def test_score_semantic_units_boosts_runtime_probe_result_flow_surfaces(
    tmp_path: Path,
) -> None:
    """Exec/eval runtime-proof queries lift admission bridges and result contracts."""
    source_dir = tmp_path / "src" / "example_package"
    source_dir.mkdir(parents=True)
    (source_dir / "runtime_probe_bridge.py").write_text(
        textwrap.dedent(
            """
            def _attach_observed_result_provenance(
                result: object,
            ) -> str:
                return "attach additive runtime provenance"

            def _unrelated_admission_helper(value: object) -> object:
                return value
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (source_dir / "runtime_probe_contracts.py").write_text(
        textwrap.dedent(
            """
            class ObservedResultContract:
                pass

            class RuntimeProbeTimeout:
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    admission_id = _definition_id_for(
        program,
        ("src.example_package.runtime_probe_bridge._attach_observed_result_provenance"),
    )
    unrelated_id = _definition_id_for(
        program,
        "src.example_package.runtime_probe_bridge._unrelated_admission_helper",
    )
    result_contract_id = _definition_id_for(
        program,
        "src.example_package.runtime_probe_contracts.ObservedResultContract",
    )
    timeout_id = _definition_id_for(
        program,
        "src.example_package.runtime_probe_contracts.RuntimeProbeTimeout",
    )

    result = score_semantic_units(
        program,
        (
            "Fix exec/eval runtime probe results so admission converts observed "
            "results into additive provenance while keeping unsupported primary truth"
        ),
    )

    assert result.scores[admission_id].p_edit >= 0.36
    assert result.scores[result_contract_id].p_edit >= 0.34
    assert result.scores[admission_id].p_edit > result.scores[unrelated_id].p_edit
    assert result.scores[result_contract_id].p_edit > result.scores[timeout_id].p_edit

    contract_result = score_semantic_units(
        program,
        "Fix runtime probe result contract for observed results",
    )

    assert contract_result.scores[result_contract_id].p_edit >= 0.34
    assert contract_result.scores[result_contract_id].p_edit > (
        contract_result.scores[timeout_id].p_edit
    )


def test_score_semantic_units_reapplies_test_cap_after_orchestration_signal(
    tmp_path: Path,
) -> None:
    """Implementation test candidates stay capped after orchestration edit boosts."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "collector.py").write_text(
        textwrap.dedent(
            """
            def collect_signal_rows(query: str) -> list[str]:
                cleaned_query = query.strip() or "signal digest"
                return [
                    f"assignment signal for {cleaned_query}",
                    "priority labels stay deterministic",
                    "digest note stays visible",
                ]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "digest.py").write_text(
        textwrap.dedent(
            """
            def render_assignment_digest(rows: list[str], labels: list[str]) -> str:
                row_text = " / ".join(rows)
                label_text = ", ".join(labels)
                return f"assignment digest: {row_text} [{label_text}]"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "labels.py").write_text(
        textwrap.dedent(
            """
            def build_priority_labels(rows: list[str]) -> list[str]:
                return [f"priority:{index + 1}" for index, _ in enumerate(rows)]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_signal_smoke.py").write_text(
        textwrap.dedent(
            """
            from pkg.collector import collect_signal_rows
            from pkg.digest import render_assignment_digest
            from pkg.labels import build_priority_labels

            def test_run_signal_smoke() -> None:
                rows = collect_signal_rows("assignment")
                labels = build_priority_labels(rows)
                digest = render_assignment_digest(rows, labels)
                assert "assignment" in digest
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    test_id = _definition_id_for(
        program,
        "tests.test_signal_smoke.test_run_signal_smoke",
    )
    dependency_target_ids = {
        _definition_id_for(program, "pkg.collector.collect_signal_rows"),
        _definition_id_for(program, "pkg.digest.render_assignment_digest"),
        _definition_id_for(program, "pkg.labels.build_priority_labels"),
    }
    direct_targets = {
        dependency.target_symbol_id
        for dependency in program.proven_dependencies
        if dependency.source_symbol_id == test_id
    }

    result = score_semantic_units(
        program,
        (
            "Fix missing assignment note while keeping signal digest and priority "
            "labels aligned"
        ),
    )
    relevant_dependency_targets = {
        target_id
        for target_id in dependency_target_ids
        if max(
            result.scores[target_id].p_edit,
            result.scores[target_id].p_support,
        )
        >= 0.15
    }

    assert dependency_target_ids <= direct_targets
    assert len(relevant_dependency_targets) >= 2
    assert result.scores[test_id].p_edit == 0.19
    assert result.scores[test_id].p_support > 0.0


def test_score_semantic_units_boosts_orchestrating_symbol_across_relevant_dependencies(
    tmp_path: Path,
) -> None:
    """Multi-step coordination can outrank the shallowest single helper surface."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "collector.py").write_text(
        textwrap.dedent(
            """
            def collect_signal_rows(query: str) -> list[str]:
                cleaned_query = query.strip() or "signal digest"
                return [
                    f"assignment signal for {cleaned_query}",
                    "priority labels stay deterministic",
                    "digest note stays visible",
                ]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "digest.py").write_text(
        textwrap.dedent(
            """
            def render_assignment_digest(rows: list[str], labels: list[str]) -> str:
                row_text = " / ".join(rows)
                label_text = ", ".join(labels)
                return f"assignment digest: {row_text} [{label_text}]"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "labels.py").write_text(
        textwrap.dedent(
            """
            def build_priority_labels(rows: list[str]) -> list[str]:
                return [f"priority:{index + 1}" for index, _ in enumerate(rows)]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.collector import collect_signal_rows
            from pkg.digest import render_assignment_digest
            from pkg.labels import build_priority_labels

            def run_signal_smoke_b(query: str) -> str:
                rows = collect_signal_rows(query)
                labels = build_priority_labels(rows)
                digest = render_assignment_digest(rows, labels)
                gap_registry.record_assignment_note(digest)
                return digest
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    run_id = _definition_id_for(program, "main.run_signal_smoke_b")
    collector_id = _definition_id_for(program, "pkg.collector.collect_signal_rows")
    digest_id = _definition_id_for(program, "pkg.digest.render_assignment_digest")
    labels_id = _definition_id_for(program, "pkg.labels.build_priority_labels")

    result = score_semantic_units(
        program,
        (
            "Fix missing assignment note while keeping signal digest and priority "
            "labels aligned"
        ),
    )

    assert result.scores[run_id].p_edit > 0.36
    assert result.scores[run_id].p_edit > result.scores[collector_id].p_edit
    assert result.scores[digest_id].p_edit > 0.20
    assert result.scores[labels_id].p_edit > 0.15


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

"""Semantic-first scorer tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

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

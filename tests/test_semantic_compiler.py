"""Semantic-first compiler tests."""

from __future__ import annotations

import textwrap
from dataclasses import replace
from pathlib import Path

import pytest

import context_ir.semantic_compiler as semantic_compiler
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_compiler import compile_semantic_context
from context_ir.semantic_renderer import RenderDetail
from context_ir.semantic_scorer import (
    SemanticScoringResult,
    SemanticUnitScore,
    score_semantic_units,
)
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
    RepositorySnapshotBasis,
    RuntimeAttachmentLink,
    SelectionBasis,
    SemanticCompileResult,
    SemanticOptimizationResult,
    SemanticOptimizationWarning,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticProvenanceRecord,
    SemanticSelectionRecord,
    SemanticSubjectKind,
    SemanticUnitTraceSummary,
    SourceSite,
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


def _estimate_tokens(text: str) -> int:
    """Mirror compile-level token estimation for assembled documents."""
    return max(1, (len(text) + 3) // 4)


def _runtime_backed_record(
    *,
    record_id: str,
    subject_kind: SemanticSubjectKind,
    subject_id: str,
    site: SourceSite,
) -> SemanticProvenanceRecord:
    """Create one admissible runtime-backed provenance record for tests."""
    return SemanticProvenanceRecord(
        record_id=record_id,
        subject_kind=subject_kind,
        subject_id=subject_id,
        capability_tier=CapabilityTier.RUNTIME_BACKED,
        evidence_origin=EvidenceOriginKind.RUNTIME_PROBE_IDENTITY,
        origin_detail="probe:test-runtime",
        replay_status=ReplayStatus.REPRODUCIBLE_RUNTIME,
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id=f"attachment:{record_id}",
                attachment_role="trace",
            ),
        ),
        subject_sites=(site,),
    )


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


def test_compile_semantic_context_carries_tier_aware_selection_traces(
    tmp_path: Path,
) -> None:
    """Compile results preserve tier-aware selection trace summaries."""
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

    base_program = _semantic_program(tmp_path)
    run_id = _definition_id_for(base_program, "main.run")
    frontier_id = next(
        access.access_id
        for access in base_program.unresolved_frontier
        if access.enclosing_scope_id == run_id
    )
    star_import_id = next(
        construct.construct_id
        for construct in base_program.unsupported_constructs
        if construct.construct_text == "from pkg.helpers import *"
    )
    program = replace(
        base_program,
        provenance_records=[
            _runtime_backed_record(
                record_id="prov:symbol:runtime:run",
                subject_kind=SemanticSubjectKind.SYMBOL,
                subject_id=run_id,
                site=base_program.resolved_symbols[run_id].definition_site,
            ),
            _runtime_backed_record(
                record_id="prov:frontier:runtime:missing",
                subject_kind=SemanticSubjectKind.FRONTIER_ITEM,
                subject_id=frontier_id,
                site=next(
                    access.site
                    for access in base_program.unresolved_frontier
                    if access.access_id == frontier_id
                ),
            ),
            _runtime_backed_record(
                record_id="prov:unsupported:runtime:star",
                subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
                subject_id=star_import_id,
                site=next(
                    construct.site
                    for construct in base_program.unsupported_constructs
                    if construct.construct_id == star_import_id
                ),
            ),
        ],
    )
    scoring = SemanticScoringResult(
        query="run missing call star import helper",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    0.70
                    if unit_id == run_id
                    else 0.46
                    if unit_id == frontier_id
                    else 0.42
                    if unit_id == star_import_id
                    else 0.08
                ),
                p_support=0.0,
            )
            for unit_id in {
                *program.resolved_symbols.keys(),
                *(access.access_id for access in program.unresolved_frontier),
                *(
                    construct.construct_id
                    for construct in program.unsupported_constructs
                ),
            }
        },
    )

    result = compile_semantic_context(
        program,
        "run missing call star import helper",
        budget=400,
        scoring=scoring,
    )
    selections = {
        selection.unit_id: selection for selection in result.optimization.selections
    }

    assert selections[run_id].trace_summary is not None
    assert selections[run_id].trace_summary == SemanticUnitTraceSummary(
        subject_id=run_id,
        subject_kind=SemanticSubjectKind.SYMBOL,
        primary_capability_tier=CapabilityTier.STATICALLY_PROVED,
        primary_evidence_origin=EvidenceOriginKind.STATIC_DERIVATION_RULE,
        primary_replay_status=ReplayStatus.DETERMINISTIC_STATIC,
        attached_runtime_provenance_record_ids=("prov:symbol:runtime:run",),
    )
    assert selections[frontier_id].trace_summary is not None
    assert selections[frontier_id].trace_summary == SemanticUnitTraceSummary(
        subject_id=frontier_id,
        subject_kind=SemanticSubjectKind.FRONTIER_ITEM,
        primary_capability_tier=CapabilityTier.HEURISTIC_FRONTIER,
        primary_evidence_origin=EvidenceOriginKind.HEURISTIC_RULE,
        primary_replay_status=ReplayStatus.NON_PROOF_HEURISTIC,
        attached_runtime_provenance_record_ids=("prov:frontier:runtime:missing",),
    )
    assert selections[star_import_id].trace_summary is not None
    assert selections[star_import_id].trace_summary == SemanticUnitTraceSummary(
        subject_id=star_import_id,
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        primary_capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
        primary_evidence_origin=EvidenceOriginKind.UNSUPPORTED_REASON_CODE,
        primary_replay_status=ReplayStatus.OPAQUE_BOUNDARY,
        attached_runtime_provenance_record_ids=("prov:unsupported:runtime:star",),
    )


def test_compile_budget_normalization_preserves_warning_trace_summary() -> None:
    """Compiler budget normalization keeps warning summaries intact."""
    trace_summary = SemanticUnitTraceSummary(
        subject_id="frontier:missing",
        subject_kind=SemanticSubjectKind.FRONTIER_ITEM,
        primary_capability_tier=CapabilityTier.HEURISTIC_FRONTIER,
        primary_evidence_origin=EvidenceOriginKind.HEURISTIC_RULE,
        primary_replay_status=ReplayStatus.NON_PROOF_HEURISTIC,
        attached_runtime_provenance_record_ids=("prov:frontier:runtime:missing",),
    )
    selection = SemanticSelectionRecord(
        unit_id="unit:selected",
        detail="identity",
        token_count=4,
        basis=SelectionBasis.HEURISTIC_CANDIDATE,
        reason="selected for query",
        edit_score=0.2,
        support_score=0.0,
    )
    warning = SemanticOptimizationWarning(
        code=SemanticOptimizationWarningCode.OMITTED_UNCERTAINTY,
        message="uncertainty omitted by budget",
        unit_id="frontier:missing",
        trace_summary=trace_summary,
    )
    optimization = SemanticOptimizationResult(
        selections=(selection,),
        omitted_unit_ids=("frontier:missing",),
        warnings=(warning,),
        total_tokens=4,
        budget=12,
        confidence=0.4,
    )

    normalized = semantic_compiler._with_compile_budget(optimization, budget=32)

    assert normalized.budget == 32
    assert normalized.warnings[0] is not warning
    assert normalized.warnings[0].trace_summary == trace_summary


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

    assert result.document.startswith("# Context")
    assert "main.py" in result.document
    assert "pkg/helpers.py" in result.document
    assert "proof_status: proven" in result.document
    assert "unresolved: missing_call @ main.py:6:4" in result.document
    assert "unsupported construct" in result.document
    assert "text: from pkg.helpers import *" in result.document
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

    assert result.document == "# Context"
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
    tight_result = compile_semantic_context(program, "run", budget=60)

    assert tight_result.total_tokens == _estimate_tokens(tight_result.document)
    assert tight_result.total_tokens <= 60
    tight_unit_ids = [
        selection.unit_id for selection in tight_result.optimization.selections
    ]
    roomier_unit_ids = [
        selection.unit_id for selection in roomier_result.optimization.selections
    ]
    tight_details = [
        selection.detail for selection in tight_result.optimization.selections
    ]
    roomier_details = [
        selection.detail for selection in roomier_result.optimization.selections
    ]

    assert tight_unit_ids == roomier_unit_ids
    assert tight_details == roomier_details


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
        compile_semantic_context(program, "", budget=2)


def test_compile_semantic_context_finds_largest_fitting_selection_under_budget(
    tmp_path: Path,
) -> None:
    """Compilation keeps the best fitting pack instead of collapsing too early."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "planner.py").write_text(
        textwrap.dedent(
            """
            def build_execution_plan(query: str) -> list[str]:
                cleaned_query = query.strip() or "signal smoke"
                return [
                    f"collect signal for {cleaned_query}",
                    "draft execution plan",
                    "confirm preview",
                ]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.planner import build_execution_plan

            def run_signal_smoke(query: str) -> list[str]:
                plan = build_execution_plan(query)
                record_missing_step(plan)
                return plan
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    run_id = next(
        definition.definition_id
        for definition in program.syntax.definitions
        if definition.qualified_name == "main.run_signal_smoke"
    )
    planner_id = next(
        definition.definition_id
        for definition in program.syntax.definitions
        if definition.qualified_name == "pkg.planner.build_execution_plan"
    )
    scoring = SemanticScoringResult(
        query="missing step execution plan",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=0.40
                if unit_id == run_id
                else 0.30
                if unit_id == planner_id
                else 0.0,
                p_support=0.0,
            )
            for unit_id in {
                *program.resolved_symbols.keys(),
                *(access.access_id for access in program.unresolved_frontier),
                *(
                    construct.construct_id
                    for construct in program.unsupported_constructs
                ),
            }
        },
    )

    result = compile_semantic_context(
        program,
        "missing step execution plan",
        budget=240,
        scoring=scoring,
    )

    assert result.total_tokens <= 240
    assert [selection.unit_id for selection in result.optimization.selections] == [
        run_id,
        planner_id,
    ]


def test_compile_semantic_context_keeps_smoke_support_units_under_budget(
    tmp_path: Path,
) -> None:
    """Compact omission reporting leaves room for the full support pack."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "planner.py").write_text(
        textwrap.dedent(
            """
            def build_execution_plan(query: str) -> list[str]:
                cleaned_query = query.strip() or "signal smoke"
                return [
                    f"collect signal for {cleaned_query}",
                    "draft execution plan",
                    "confirm preview",
                ]
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
            from pkg.presenter import *
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

    result = compile_semantic_context(
        program,
        "Fix missing step while keeping execution plan preview aligned",
        budget=240,
    )
    selections = {
        selection.unit_id: selection for selection in result.optimization.selections
    }

    assert result.total_tokens <= 240
    assert run_id in selections
    assert planner_id in selections
    assert presenter_id in selections
    assert selections[run_id].detail == RenderDetail.SOURCE.value
    assert selections[planner_id].detail == RenderDetail.SOURCE.value
    assert selections[presenter_id].detail == RenderDetail.SOURCE.value


def test_compile_semantic_context_surfaces_smoke_c_uncertainty_within_budget(
    tmp_path: Path,
) -> None:
    """Smoke_c budgets keep the frontier honest and can widen support."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "router.py").write_text(
        textwrap.dedent(
            """
            from pkg.registry import resolve_owner_alias

            def build_handoff_route(query: str) -> list[str]:
                owner_alias = resolve_owner_alias(query)
                route = [f"owner:{owner_alias}", "keep route summary aligned"]
                handoff_tracker.record_missing_note(route)
                return route
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "registry.py").write_text(
        textwrap.dedent(
            """
            def resolve_owner_alias(query: str) -> str:
                normalized_query = query.lower()
                if "owner" in normalized_query or "alias" in normalized_query:
                    return "ops-handoff"
                return "review-handoff"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "summary.py").write_text(
        textwrap.dedent(
            """
            def render_route_summary(route: list[str]) -> str:
                return "route summary: " + " -> ".join(route)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.router import build_handoff_route
            from pkg.summary import render_route_summary

            def run_signal_smoke_c(query: str) -> str:
                handoff_query = query.strip() or "missing handoff note"
                route = build_handoff_route(handoff_query)
                return render_route_summary(route)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    run_id = _definition_id_for(program, "main.run_signal_smoke_c")
    router_id = _definition_id_for(program, "pkg.router.build_handoff_route")
    registry_id = _definition_id_for(program, "pkg.registry.resolve_owner_alias")
    summary_id = _definition_id_for(program, "pkg.summary.render_route_summary")
    frontier_id = next(
        access.access_id
        for access in program.unresolved_frontier
        if access.enclosing_scope_id == router_id
    )
    query = (
        "Fix missing handoff note while keeping owner alias and route summary aligned"
    )

    tight_result = compile_semantic_context(program, query, budget=200)
    roomy_result = compile_semantic_context(program, query, budget=240)
    tight_selections = {
        selection.unit_id: selection
        for selection in tight_result.optimization.selections
    }
    roomy_unit_ids = {
        selection.unit_id for selection in roomy_result.optimization.selections
    }

    assert tight_result.total_tokens <= 200
    assert run_id in tight_selections
    assert router_id in tight_selections
    assert frontier_id in tight_selections
    assert summary_id in tight_selections
    assert registry_id in tight_selections
    assert tight_selections[run_id].detail == RenderDetail.SOURCE.value
    assert tight_selections[router_id].detail == RenderDetail.SOURCE.value
    assert tight_selections[registry_id].detail == RenderDetail.SUMMARY.value
    assert tight_selections[summary_id].detail == RenderDetail.SOURCE.value

    assert roomy_result.total_tokens <= 240
    assert run_id in roomy_unit_ids
    assert router_id in roomy_unit_ids
    assert frontier_id in roomy_unit_ids
    assert summary_id in roomy_unit_ids
    assert registry_id in roomy_unit_ids

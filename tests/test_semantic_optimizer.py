"""Semantic-first optimizer tests."""

from __future__ import annotations

import textwrap
from dataclasses import replace
from pathlib import Path

import context_ir.runtime_acquisition as runtime_acquisition
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_optimizer import optimize_semantic_units
from context_ir.semantic_renderer import RenderDetail, render_semantic_unit
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
    SemanticOptimizationResult,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticProvenanceRecord,
    SemanticSelectionRecord,
    SemanticSubjectKind,
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


def _dynamic_import_runtime_observation(
    site: SourceSite,
) -> runtime_acquisition.DynamicImportRuntimeObservation:
    """Create one admissible dynamic-import runtime observation for optimizer tests."""
    return runtime_acquisition.DynamicImportRuntimeObservation(
        site=site,
        probe_identifier="probe:dynamic-import",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id=f"attachment:{site.site_id}:trace",
                attachment_role="trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="imported_module",
                value="pkg.dynamic",
            ),
        ),
    )


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


def test_optimize_semantic_units_emits_tier_aware_trace_summaries(
    tmp_path: Path,
) -> None:
    """Selections and warnings carry typed tier/provenance summaries."""
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
            for unit_id in _renderable_unit_ids(program)
        },
    )

    roomy_result = optimize_semantic_units(program, scoring, budget=400)
    roomy_selections = _selection_by_unit_id(roomy_result)
    run_trace = roomy_selections[run_id].trace_summary
    frontier_trace = roomy_selections[frontier_id].trace_summary
    unsupported_trace = roomy_selections[star_import_id].trace_summary

    assert run_trace is not None
    assert run_trace.subject_kind is SemanticSubjectKind.SYMBOL
    assert run_trace.primary_capability_tier is CapabilityTier.STATICALLY_PROVED
    assert (
        run_trace.primary_evidence_origin is EvidenceOriginKind.STATIC_DERIVATION_RULE
    )
    assert run_trace.primary_replay_status is ReplayStatus.DETERMINISTIC_STATIC
    assert run_trace.attached_runtime_provenance_record_ids == (
        "prov:symbol:runtime:run",
    )
    assert run_trace.has_attached_runtime_provenance is True

    assert frontier_trace is not None
    assert frontier_trace.subject_kind is SemanticSubjectKind.FRONTIER_ITEM
    assert frontier_trace.primary_capability_tier is CapabilityTier.HEURISTIC_FRONTIER
    assert frontier_trace.primary_evidence_origin is EvidenceOriginKind.HEURISTIC_RULE
    assert frontier_trace.primary_replay_status is ReplayStatus.NON_PROOF_HEURISTIC
    assert frontier_trace.attached_runtime_provenance_record_ids == (
        "prov:frontier:runtime:missing",
    )

    assert unsupported_trace is not None
    assert unsupported_trace.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert (
        unsupported_trace.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    )
    assert (
        unsupported_trace.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported_trace.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported_trace.attached_runtime_provenance_record_ids == (
        "prov:unsupported:runtime:star",
    )

    tight_result = optimize_semantic_units(program, scoring, budget=0)
    warnings_by_unit_id = {
        warning.unit_id: warning for warning in tight_result.warnings if warning.unit_id
    }

    assert warnings_by_unit_id[run_id].code is (
        SemanticOptimizationWarningCode.OMITTED_DIRECT_CANDIDATE
    )
    assert warnings_by_unit_id[run_id].trace_summary == run_trace
    assert warnings_by_unit_id[frontier_id].code is (
        SemanticOptimizationWarningCode.OMITTED_UNCERTAINTY
    )
    assert warnings_by_unit_id[frontier_id].trace_summary == frontier_trace
    assert warnings_by_unit_id[star_import_id].code is (
        SemanticOptimizationWarningCode.OMITTED_UNCERTAINTY
    )
    assert warnings_by_unit_id[star_import_id].trace_summary == unsupported_trace


def test_optimize_semantic_units_keeps_importlib_dynamic_import_primary_unsupported(
    tmp_path: Path,
) -> None:
    """Attached importlib runtime support stays additive on unsupported units."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(name: str) -> None:
                importlib.import_module(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = _semantic_program(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "importlib.import_module(name)"
    )
    program = runtime_acquisition.attach_dynamic_import_runtime_provenance(
        base_program,
        [_dynamic_import_runtime_observation(construct.site)],
    )
    [record] = program.provenance_records
    scoring = SemanticScoringResult(
        query="dynamic import",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=0.95 if unit_id == construct.construct_id else 0.01,
                p_support=0.0,
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=400)
    trace = _selection_by_unit_id(result)[construct.construct_id].trace_summary

    assert trace is not None
    assert trace.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert trace.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert trace.primary_evidence_origin is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    assert trace.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert trace.attached_runtime_provenance_record_ids == (record.record_id,)
    assert trace.has_attached_runtime_provenance is True


def test_optimize_semantic_units_uses_compact_summary_and_cheaper_source_when_available(
    tmp_path: Path,
) -> None:
    """Summary compaction can still leave source as the cheapest rich detail."""
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
    helper_source = render_semantic_unit(program, helper_id, RenderDetail.SOURCE)
    budget = run_source.token_count + helper_identity.token_count

    result = optimize_semantic_units(program, scoring, budget=budget)
    selections = _selection_by_unit_id(result)

    assert selections[run_id].detail == RenderDetail.SOURCE.value
    assert helper_id in selections
    assert selections[helper_id].detail == RenderDetail.SOURCE.value
    assert helper_summary.token_count < helper_identity.token_count
    assert helper_source.token_count < helper_summary.token_count


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


def test_optimize_semantic_units_uses_source_when_it_is_cheaper_or_near_cost(
    tmp_path: Path,
) -> None:
    """Summary-level candidates may upgrade to source when the cost tradeoff is tiny."""
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

    program = _semantic_program(tmp_path)
    planner_id = _definition_id_for(program, "pkg.planner.build_execution_plan")
    presenter_id = _definition_id_for(program, "pkg.presenter.render_patch_preview")
    scoring = SemanticScoringResult(
        query="execution plan preview",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    0.30
                    if unit_id == planner_id
                    else 0.20
                    if unit_id == presenter_id
                    else 0.0
                ),
                p_support=0.30 if unit_id == presenter_id else 0.0,
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=90)
    selections = _selection_by_unit_id(result)

    assert selections[planner_id].detail == RenderDetail.SOURCE.value
    assert selections[presenter_id].detail == RenderDetail.SOURCE.value


def test_optimize_semantic_units_prefers_summary_outside_focus(
    tmp_path: Path,
) -> None:
    """Standalone support-heavy symbols stay at compact summary detail."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def render_patch_preview(plan: list[str]) -> str:
                return "patch preview: " + " | ".join(plan)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    presenter_id = _definition_id_for(program, "main.render_patch_preview")
    source = render_semantic_unit(program, presenter_id, RenderDetail.SOURCE)
    identity = render_semantic_unit(program, presenter_id, RenderDetail.IDENTITY)
    scoring = SemanticScoringResult(
        query="preview aligned",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=0.17 if unit_id == presenter_id else 0.0,
                p_support=0.25 if unit_id == presenter_id else 0.0,
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=30)
    selections = _selection_by_unit_id(result)

    assert source.token_count < identity.token_count
    assert selections[presenter_id].detail == RenderDetail.SUMMARY.value
    assert (
        result.total_tokens
        == render_semantic_unit(
            program,
            presenter_id,
            RenderDetail.SUMMARY,
        ).token_count
    )


def test_optimize_semantic_units_promotes_support_to_summary_when_summary_is_compact(
    tmp_path: Path,
) -> None:
    """Compact summaries beat identity-only support when the signal is material."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "labels.py").write_text(
        textwrap.dedent(
            """
            def build_priority_labels(rows: list[str]) -> list[str]:
                labels = [f"priority:{index + 1}" for index, _ in enumerate(rows)]
                if not labels:
                    return ["priority:none"]
                return labels
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    labels_id = _definition_id_for(program, "pkg.labels.build_priority_labels")
    identity = render_semantic_unit(program, labels_id, RenderDetail.IDENTITY)
    summary = render_semantic_unit(program, labels_id, RenderDetail.SUMMARY)
    source = render_semantic_unit(program, labels_id, RenderDetail.SOURCE)
    scoring = SemanticScoringResult(
        query="keep priority labels aligned",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=0.17 if unit_id == labels_id else 0.0,
                p_support=0.25 if unit_id == labels_id else 0.0,
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=50)
    selections = _selection_by_unit_id(result)

    assert summary.token_count < identity.token_count
    assert selections[labels_id].detail == RenderDetail.SUMMARY.value
    assert result.total_tokens == summary.token_count
    assert source.token_count > summary.token_count


def test_optimize_semantic_units_keeps_source_edit_locus_under_tight_budget(
    tmp_path: Path,
) -> None:
    """Tight budgets keep the edit locus source-backed and both helpers shallow."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "collector.py").write_text(
        textwrap.dedent(
            """
            def collect_signal_rows(query: str) -> list[str]:
                cleaned_query = query.strip() or "signal digest"
                first_row = f"assignment signal for {cleaned_query}"
                second_row = "priority labels stay deterministic"
                third_row = "digest note stays visible"
                return [first_row, second_row, third_row]
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
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.collector import collect_signal_rows
            from pkg.digest import render_assignment_digest

            def run_signal_smoke_b(query: str) -> str:
                rows = collect_signal_rows(query)
                digest = render_assignment_digest(rows, [])
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
    scoring = SemanticScoringResult(
        query=(
            "Fix missing assignment note while keeping signal digest and priority "
            "labels aligned"
        ),
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    0.38
                    if unit_id == run_id
                    else 0.37
                    if unit_id == collector_id
                    else 0.22
                    if unit_id == digest_id
                    else 0.0
                ),
                p_support=0.24 if unit_id == digest_id else 0.0,
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=113)
    selections = _selection_by_unit_id(result)

    assert selections[run_id].detail == RenderDetail.SOURCE.value
    assert selections[collector_id].detail == RenderDetail.SUMMARY.value
    assert selections[digest_id].detail == RenderDetail.SUMMARY.value


def test_optimize_semantic_units_keeps_direct_caller_uncertainty_before_support_pack(
    tmp_path: Path,
) -> None:
    """Tight smoke_c budgets surface anchor uncertainty before widening support."""
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
    main_frontier_id = next(
        access.access_id
        for access in program.unresolved_frontier
        if access.enclosing_scope_id == run_id
    )
    scoring = SemanticScoringResult(
        query=(
            "Fix missing handoff note while keeping owner alias and route summary "
            "aligned"
        ),
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    0.3240
                    if unit_id == run_id
                    else 0.5276
                    if unit_id == router_id
                    else 0.2355
                    if unit_id == registry_id
                    else 0.1771
                    if unit_id == summary_id
                    else 0.0700
                    if unit_id == frontier_id
                    else 0.0
                ),
                p_support=(
                    0.1056
                    if unit_id == run_id
                    else 0.3300
                    if unit_id == router_id
                    else 0.3311
                    if unit_id == registry_id
                    else 0.2203
                    if unit_id == summary_id
                    else 0.2318
                    if unit_id == frontier_id
                    else 0.0
                ),
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=152)
    selections = _selection_by_unit_id(result)

    assert selections[router_id].detail == RenderDetail.SOURCE.value
    assert selections[run_id].detail == RenderDetail.SOURCE.value
    assert selections[frontier_id].detail == RenderDetail.IDENTITY.value
    assert selections[summary_id].detail == RenderDetail.SOURCE.value
    assert registry_id not in selections
    assert main_frontier_id not in selections
    assert all(warning.unit_id != main_frontier_id for warning in result.warnings)


def test_optimize_semantic_units_surfaces_same_file_module_uncertainty_for_focus(
    tmp_path: Path,
) -> None:
    """Module-scope uncertainty in the focus file stays visible under tight budgets."""
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
    scoring = score_semantic_units(
        program,
        "Fix missing step while keeping execution plan preview aligned",
    )
    run_id = _definition_id_for(program, "main.run_signal_smoke")
    planner_id = _definition_id_for(program, "pkg.planner.build_execution_plan")
    presenter_id = _definition_id_for(program, "pkg.presenter.render_patch_preview")
    main_frontier_id = next(
        access.access_id
        for access in program.unresolved_frontier
        if access.enclosing_scope_id == run_id
    )
    planner_frontier_id = next(
        access.access_id
        for access in program.unresolved_frontier
        if access.enclosing_scope_id == planner_id
    )
    presenter_unsupported_id = next(
        construct.construct_id
        for construct in program.unsupported_constructs
        if construct.enclosing_scope_id == presenter_id
    )
    star_import_id = next(
        construct.construct_id
        for construct in program.unsupported_constructs
        if construct.construct_text == "from pkg.presenter import *"
    )

    result = optimize_semantic_units(program, scoring, budget=188)
    selections = _selection_by_unit_id(result)

    assert selections[run_id].detail == RenderDetail.SOURCE.value
    assert selections[planner_id].detail == RenderDetail.SOURCE.value
    assert selections[presenter_id].detail == RenderDetail.SOURCE.value
    assert selections[main_frontier_id].detail == RenderDetail.IDENTITY.value
    assert selections[star_import_id].detail == RenderDetail.IDENTITY.value
    assert planner_frontier_id not in selections
    assert presenter_unsupported_id not in selections


def test_optimize_semantic_units_skips_support_scope_uncertainty_noise(
    tmp_path: Path,
) -> None:
    """Leftover budget does not reopen support-scope uncertainty after a clean floor."""
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
    scoring = score_semantic_units(
        program,
        "Fix missing step while keeping execution plan preview aligned",
    )
    run_id = _definition_id_for(program, "main.run_signal_smoke")
    planner_id = _definition_id_for(program, "pkg.planner.build_execution_plan")
    presenter_id = _definition_id_for(program, "pkg.presenter.render_patch_preview")
    main_frontier_id = next(
        access.access_id
        for access in program.unresolved_frontier
        if access.enclosing_scope_id == run_id
    )
    planner_frontier_id = next(
        access.access_id
        for access in program.unresolved_frontier
        if access.enclosing_scope_id == planner_id
    )
    planner_import_id = next(
        unit_id
        for unit_id in _renderable_unit_ids(program)
        if unit_id.startswith("import:main.py:1:0:1:build_execution_plan:_")
    )
    presenter_unsupported_id = next(
        construct.construct_id
        for construct in program.unsupported_constructs
        if construct.enclosing_scope_id == presenter_id
    )
    star_import_id = next(
        construct.construct_id
        for construct in program.unsupported_constructs
        if construct.construct_text == "from pkg.presenter import *"
    )

    result = optimize_semantic_units(program, scoring, budget=240)
    selections = _selection_by_unit_id(result)

    assert selections[run_id].detail == RenderDetail.SOURCE.value
    assert selections[planner_id].detail == RenderDetail.SOURCE.value
    assert selections[presenter_id].detail == RenderDetail.SOURCE.value
    assert selections[main_frontier_id].detail == RenderDetail.IDENTITY.value
    assert selections[star_import_id].detail == RenderDetail.IDENTITY.value
    assert planner_frontier_id not in selections
    assert planner_import_id not in selections
    assert presenter_unsupported_id not in selections
    assert result.warnings == ()

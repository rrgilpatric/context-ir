"""Semantic-first optimizer tests."""

from __future__ import annotations

import textwrap
from dataclasses import replace
from pathlib import Path

import pytest

import context_ir.runtime_acquisition as runtime_acquisition
import context_ir.semantic_optimizer as semantic_optimizer
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_optimizer import optimize_semantic_units
from context_ir.semantic_renderer import (
    RenderDetail,
    RenderedUnit,
    render_semantic_unit,
)
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
    SemanticEvalRuntimeEvidence,
    SemanticEvalRuntimeEvidenceField,
    SemanticOptimizationResult,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticProvenanceRecord,
    SemanticSelectionRecord,
    SemanticSubjectKind,
    SourceSite,
    SourceSpan,
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


def _renderable_unit_ids(program: SemanticProgram) -> set[str]:
    """Return every renderable semantic unit ID."""
    return {
        *program.resolved_symbols.keys(),
        *(access.access_id for access in program.unresolved_frontier),
        *(construct.construct_id for construct in program.unsupported_constructs),
        *(evidence.unit_id for evidence in program.eval_runtime_evidence),
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


def _eval_hasattr_evidence() -> SemanticEvalRuntimeEvidence:
    """Return one compact eval evidence unit for optimizer tests."""
    return SemanticEvalRuntimeEvidence(
        unit_id="eval_evidence:oracle_signal_hasattr_probe:hasattr:main.py:2:11",
        evidence_id="oracle_signal_hasattr_probe:hasattr:main.py:2:11",
        runtime_family="hasattr",
        fixture_id="oracle_signal_hasattr_probe",
        task_ids=("oracle_signal_hasattr_probe",),
        run_spec_ids=("oracle_signal_hasattr_probe_matrix",),
        artifact_path=(
            "evals/fixtures/oracle_signal_hasattr_probe/eval_runtime_observations.json"
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
        durable_payload_reference="artifact://hasattr/int-bit-length-observation.json",
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


def test_optimize_semantic_units_reuses_one_render_session_per_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Candidate construction requests each render once through one session."""
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
    scoring = score_semantic_units(program, "run missing_call helper")
    expected_result = optimize_semantic_units(program, scoring, budget=200)
    original_session = semantic_optimizer._SemanticRenderSession
    session_count = 0
    render_calls: dict[tuple[str, RenderDetail], int] = {}

    class CountingRenderSession:
        """Counting proxy for the optimizer's request-scoped renderer."""

        def __init__(self, program_arg: SemanticProgram) -> None:
            nonlocal session_count
            session_count += 1
            self._delegate = original_session(program_arg)

        def render(self, unit_id: str, detail: RenderDetail) -> RenderedUnit:
            cache_key = (unit_id, detail)
            render_calls[cache_key] = render_calls.get(cache_key, 0) + 1
            return self._delegate.render(unit_id, detail)

    monkeypatch.setattr(
        semantic_optimizer,
        "_SemanticRenderSession",
        CountingRenderSession,
    )

    result = optimize_semantic_units(program, scoring, budget=200)

    expected_render_calls = {
        (unit_id, detail)
        for unit_id in _renderable_unit_ids(program)
        for detail in (
            RenderDetail.IDENTITY,
            RenderDetail.SUMMARY,
            RenderDetail.SOURCE,
        )
    }
    assert result == expected_result
    assert session_count == 1
    assert set(render_calls) == expected_render_calls
    assert all(count == 1 for count in render_calls.values())


def test_optimize_semantic_units_rejects_negative_budget_before_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Negative budgets fail before scoring coverage or candidate materialization."""
    (tmp_path / "main.py").write_text(
        "def run() -> None:\n    return None\n",
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)
    malformed_scoring = SemanticScoringResult(query="run", scores={})
    original_build_candidates = semantic_optimizer._build_candidates
    build_candidates_called = False

    def tracking_build_candidates(
        program_arg: SemanticProgram,
        scoring_arg: SemanticScoringResult,
    ) -> list[semantic_optimizer._SemanticCandidate]:
        nonlocal build_candidates_called
        build_candidates_called = True
        return original_build_candidates(program_arg, scoring_arg)

    monkeypatch.setattr(
        semantic_optimizer,
        "_build_candidates",
        tracking_build_candidates,
    )

    with pytest.raises(ValueError, match="^budget must be >= 0$"):
        optimize_semantic_units(program, malformed_scoring, budget=-1)

    assert build_candidates_called is False


def test_optimize_semantic_units_bounds_sorting_when_focus_state_is_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stable dynamic sort state does not trigger repeated full pending sorts."""
    (tmp_path / "main.py").write_text(
        "\n\n".join(
            f"def helper_{index}() -> int:\n    return {index}" for index in range(40)
        ),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    renderable_unit_ids = _renderable_unit_ids(program)
    scoring = SemanticScoringResult(
        query="low relevance smoke",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=0.04,
                p_support=0.0,
            )
            for unit_id in renderable_unit_ids
        },
    )
    expected_result = optimize_semantic_units(program, scoring, budget=500)
    original_candidate_sort_key = semantic_optimizer._candidate_sort_key
    sort_key_calls = 0

    def counting_candidate_sort_key(
        candidate: semantic_optimizer._SemanticCandidate,
        *,
        current_focus_id: str | None = None,
        current_focus_file_path: str | None = None,
        current_focus_file_scope_id: str | None = None,
        current_focus_has_support: bool = False,
        current_focus_has_uncertainty_surface: bool = False,
        current_focus_has_eval_evidence_surface: bool = False,
    ) -> tuple[float, float, float, float, float, int, str, int, int, str]:
        nonlocal sort_key_calls
        sort_key_calls += 1
        return original_candidate_sort_key(
            candidate,
            current_focus_id=current_focus_id,
            current_focus_file_path=current_focus_file_path,
            current_focus_file_scope_id=current_focus_file_scope_id,
            current_focus_has_support=current_focus_has_support,
            current_focus_has_uncertainty_surface=(
                current_focus_has_uncertainty_surface
            ),
            current_focus_has_eval_evidence_surface=(
                current_focus_has_eval_evidence_surface
            ),
        )

    monkeypatch.setattr(
        semantic_optimizer,
        "_candidate_sort_key",
        counting_candidate_sort_key,
    )

    result = optimize_semantic_units(program, scoring, budget=500)

    assert result == expected_result
    assert result.selections == ()
    assert set(result.omitted_unit_ids) == renderable_unit_ids
    assert sort_key_calls <= len(renderable_unit_ids) * 3


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


def test_optimize_semantic_units_omits_exact_dynamic_import_under_tight_budget(
    tmp_path: Path,
) -> None:
    """Tight budgets keep weak direct anchors ahead of exact uncertainty support."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / "__init__.py").write_text("", encoding="utf-8")
    (plugins_dir / "weather.py").write_text(
        textwrap.dedent(
            """
            def render_card() -> str:
                return "forecast"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from importlib import import_module

            def load_weather_plugin() -> object:
                plugin = import_module("plugins.weather")
                return plugin.render_card()

            def render_probe_digest() -> str:
                return "probe digest output aligned"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = _semantic_program(tmp_path)
    load_id = _definition_id_for(base_program, "main.load_weather_plugin")
    digest_id = _definition_id_for(base_program, "main.render_probe_digest")
    frontier_id = next(
        access.access_id
        for access in base_program.unresolved_frontier
        if access.enclosing_scope_id == load_id
    )
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == 'import_module("plugins.weather")'
    )
    program = runtime_acquisition.attach_dynamic_import_runtime_provenance(
        base_program,
        [_dynamic_import_runtime_observation(construct.site)],
    )
    scoring = SemanticScoringResult(
        query='Fix unsupported dynamic import import_module("plugins.weather") '
        "while keeping probe digest output aligned",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    0.19
                    if unit_id == load_id
                    else 0.18
                    if unit_id == digest_id
                    else 0.09
                    if unit_id == construct.construct_id
                    else 0.02
                ),
                p_support=(
                    1.0
                    if unit_id == construct.construct_id
                    else 0.08
                    if unit_id == frontier_id
                    else 0.0
                ),
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )
    budget = (
        render_semantic_unit(program, load_id, RenderDetail.IDENTITY).token_count
        + render_semantic_unit(program, digest_id, RenderDetail.IDENTITY).token_count
        + render_semantic_unit(program, frontier_id, RenderDetail.IDENTITY).token_count
    )

    result = optimize_semantic_units(program, scoring, budget=budget)
    selections = _selection_by_unit_id(result)

    assert scoring.scores[construct.construct_id].p_support >= 0.90
    assert selections[load_id].detail == RenderDetail.IDENTITY.value
    assert selections[digest_id].detail == RenderDetail.IDENTITY.value
    assert selections[frontier_id].detail == RenderDetail.IDENTITY.value
    assert construct.construct_id not in selections
    assert construct.construct_id in result.omitted_unit_ids
    assert result.total_tokens <= budget


def test_optimize_semantic_units_prefers_eval_evidence_over_frontier_spillover(
    tmp_path: Path,
) -> None:
    """Compact eval evidence and peer source context displace low-value frontier."""
    eval_providers_dir = tmp_path / "src" / "context_ir"
    eval_providers_dir.mkdir(parents=True)
    (eval_providers_dir / "eval_providers.py").write_text(
        textwrap.dedent(
            """
            class EvalSelectedUnit:
                pass

            def _selected_unit_metadata(record: object) -> EvalSelectedUnit:
                record.trace_summary
                record.unit_id
                record.detail
                return EvalSelectedUnit()
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (eval_providers_dir / "eval_summary.py").write_text(
        textwrap.dedent(
            """
            def build_eval_ledger_summary(ledger: object) -> str:
                selected_unit_runtime_outcome_counts = {}
                runtime_provenance_records_by_id = {}
                return "eval report accounting"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = _semantic_program(tmp_path)
    target_id = _definition_id_for(
        base_program,
        "src.context_ir.eval_providers._selected_unit_metadata",
    )
    summary_id = _definition_id_for(
        base_program,
        "src.context_ir.eval_summary.build_eval_ledger_summary",
    )
    frontier_id = next(
        access.access_id
        for access in base_program.unresolved_frontier
        if access.enclosing_scope_id == target_id
    )
    evidence = _eval_hasattr_evidence()
    program = replace(base_program, eval_runtime_evidence=[evidence])
    scoring = SemanticScoringResult(
        query="selected unit metadata eval report accounting hasattr runtime",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    0.90
                    if unit_id == target_id
                    else 0.30
                    if unit_id == summary_id
                    else 0.04
                ),
                p_support=(
                    0.45
                    if unit_id == evidence.unit_id
                    else 0.34
                    if unit_id == frontier_id
                    else 0.0
                ),
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )
    budget = (
        render_semantic_unit(program, target_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(program, summary_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(
            program,
            evidence.unit_id,
            RenderDetail.IDENTITY,
        ).token_count
    )

    result = optimize_semantic_units(program, scoring, budget=budget)
    selections = _selection_by_unit_id(result)

    assert target_id in selections
    assert summary_id in selections
    assert evidence.unit_id in selections
    assert frontier_id not in selections
    assert result.total_tokens <= budget


def test_optimize_semantic_units_keeps_direct_anchor_before_saturated_helper_support(
    tmp_path: Path,
) -> None:
    """Saturated helper support does not outrank a directly named edit surface."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def direct_contract_anchor() -> str:
                return "contract"

            def helper_support_hub() -> str:
                return "helper"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)
    anchor_id = _definition_id_for(program, "main.direct_contract_anchor")
    helper_id = _definition_id_for(program, "main.helper_support_hub")
    anchor_source_tokens = render_semantic_unit(
        program,
        anchor_id,
        RenderDetail.SOURCE,
    ).token_count
    scoring = SemanticScoringResult(
        query="Fix direct_contract_anchor without widening helper support",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=0.42 if unit_id == anchor_id else 0.06,
                p_support=1.0 if unit_id == helper_id else 0.0,
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=anchor_source_tokens)
    selections = _selection_by_unit_id(result)

    assert anchor_id in selections
    assert helper_id not in selections
    assert result.total_tokens <= anchor_source_tokens


def test_optimize_semantic_units_keeps_focused_contract_anchor_before_support_pack(
    tmp_path: Path,
) -> None:
    """Focused support packing still yields to a direct contract anchor."""
    package_dir = tmp_path / "src" / "context_ir"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text(
        textwrap.dedent(
            """
            \"\"\"Public package surface.

            This package root documents the public API export boundary for callers.
            The longer source span keeps the compact summary as the budget target.
            \"\"\"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (package_dir / "core.py").write_text(
        textwrap.dedent(
            """
            def direct_contract_anchor() -> str:
                return "contract"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (package_dir / "types.py").write_text(
        textwrap.dedent(
            """
            class SaturatedSupportContract:
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)
    focus_id = _definition_id_for(
        program,
        "src.context_ir.core.direct_contract_anchor",
    )
    boundary_id = _definition_id_for(program, "src.context_ir")
    support_id = _definition_id_for(
        program,
        "src.context_ir.types.SaturatedSupportContract",
    )
    budget = (
        render_semantic_unit(program, focus_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(program, boundary_id, RenderDetail.SUMMARY).token_count
    )
    scoring = SemanticScoringResult(
        query="Fix direct_contract_anchor without becoming public API",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    0.64
                    if unit_id == focus_id
                    else 0.36
                    if unit_id == boundary_id
                    else 0.21
                ),
                p_support=1.0 if unit_id == support_id else 0.0,
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=budget)
    selections = _selection_by_unit_id(result)

    assert focus_id in selections
    assert boundary_id in selections
    assert support_id not in selections
    assert result.total_tokens <= budget


def test_optimize_semantic_units_suppresses_redundant_enclosing_class_container(
    tmp_path: Path,
) -> None:
    """A selected method focus does not spend tight budget on its class container."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class SupportFormatter:
                def format_digest(self) -> str:
                    return "digest"

            class EnvelopeCompiler:
                def compile_digest(self) -> str:
                    return "compiled digest"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    program = _semantic_program(tmp_path)
    focus_id = _definition_id_for(program, "main.EnvelopeCompiler.compile_digest")
    enclosing_class_id = _definition_id_for(program, "main.EnvelopeCompiler")
    support_id = _definition_id_for(program, "main.SupportFormatter.format_digest")
    budget = render_semantic_unit(
        program,
        focus_id,
        RenderDetail.SOURCE,
    ).token_count + max(
        render_semantic_unit(
            program,
            enclosing_class_id,
            RenderDetail.SUMMARY,
        ).token_count,
        render_semantic_unit(program, support_id, RenderDetail.SUMMARY).token_count,
    )
    scoring = SemanticScoringResult(
        query="Fix compile digest while keeping formatter support visible",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    0.50
                    if unit_id == focus_id
                    else 0.38
                    if unit_id == enclosing_class_id
                    else 0.22
                    if unit_id == support_id
                    else 0.0
                ),
                p_support=0.10 if unit_id == enclosing_class_id else 0.0,
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=budget)
    selections = _selection_by_unit_id(result)

    assert focus_id in selections
    assert support_id in selections
    assert enclosing_class_id not in selections
    assert result.total_tokens <= budget


def test_optimize_semantic_units_focuses_named_child_method_before_parent_class(
    tmp_path: Path,
) -> None:
    """A direct child method anchor keeps its support and frontier under budget."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "labels.py").write_text(
        textwrap.dedent(
            """
            def build_member_label(owner_alias: str) -> str:
                return f"member:{owner_alias}"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "service.py").write_text(
        textwrap.dedent(
            """
            from pkg.labels import build_member_label

            class MemberSignalCompiler:
                def compile_member_digest(self, query: str) -> str:
                    owner_alias = self.resolve_owner_alias(query)
                    alias_chain_tracker(owner_alias)
                    return build_member_label(owner_alias)

                def resolve_owner_alias(self, query: str) -> str:
                    if "owner" in query:
                        return "owner"
                    return "member"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    parent_class_id = _definition_id_for(program, "pkg.service.MemberSignalCompiler")
    method_id = _definition_id_for(
        program,
        "pkg.service.MemberSignalCompiler.compile_member_digest",
    )
    label_id = _definition_id_for(program, "pkg.labels.build_member_label")
    alias_id = _definition_id_for(
        program,
        "pkg.service.MemberSignalCompiler.resolve_owner_alias",
    )
    frontier_id = next(
        access.access_id
        for access in program.unresolved_frontier
        if access.enclosing_scope_id == method_id
        and access.access_id.startswith("frontier:call:")
    )
    budget = (
        render_semantic_unit(program, method_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(program, label_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(program, alias_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(program, frontier_id, RenderDetail.IDENTITY).token_count
    )
    scoring = SemanticScoringResult(
        query=(
            "Fix MemberSignalCompiler.compile_member_digest while preserving "
            "alias_chain frontier"
        ),
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    0.38
                    if unit_id == parent_class_id
                    else 0.31
                    if unit_id == method_id
                    else 0.17
                    if unit_id == label_id
                    else 0.16
                    if unit_id == alias_id
                    else 0.08
                    if unit_id == frontier_id
                    else 0.0
                ),
                p_support=(
                    0.10
                    if unit_id == parent_class_id
                    else 0.11
                    if unit_id == method_id
                    else 0.21
                    if unit_id in {label_id, alias_id}
                    else 0.15
                    if unit_id == frontier_id
                    else 0.0
                ),
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )

    result = optimize_semantic_units(program, scoring, budget=budget)
    selections = _selection_by_unit_id(result)

    assert selections[method_id].detail == RenderDetail.SOURCE.value
    assert selections[label_id].detail == RenderDetail.SOURCE.value
    assert selections[alias_id].detail == RenderDetail.SOURCE.value
    assert selections[frontier_id].detail == RenderDetail.IDENTITY.value
    assert parent_class_id not in selections
    assert result.warnings == ()
    assert result.total_tokens <= budget


def test_optimize_semantic_units_keeps_full_repo_task3_exact_units(
    tmp_path: Path,
) -> None:
    """Repo-root qualified fixture names still focus the exact child method."""
    pkg = tmp_path / "evals" / "fixtures" / "oracle_signal_smoke_e" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "labels.py").write_text(
        textwrap.dedent(
            """
            def build_member_label(owner_alias: str) -> str:
                if owner_alias == "member-review":
                    return "member owner: member review"
                return "member owner: digest review"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    (pkg / "service.py").write_text(
        textwrap.dedent(
            """
            import pkg

            class MemberSignalCompiler:
                def compile_member_digest(self, query: str) -> str:
                    member_note = query or "missing member note"
                    owner_alias = self.resolve_owner_alias(member_note)
                    owner_label = pkg.labels.build_member_label(owner_alias)
                    pkg_alias = pkg
                    pkg_alias.labels.build_member_label(owner_alias)
                    return f"{owner_label} | keep member report aligned | {member_note}"

                def resolve_owner_alias(self, query: str) -> str:
                    if "owner" in query or "member" in query:
                        return "member-review"
                    return "digest-review"
            """
        ).lstrip(),
        encoding="utf-8",
    )

    program = _semantic_program(tmp_path)
    parent_class_id = _definition_id_for(
        program,
        ("evals.fixtures.oracle_signal_smoke_e.pkg.service.MemberSignalCompiler"),
    )
    method_id = _definition_id_for(
        program,
        (
            "evals.fixtures.oracle_signal_smoke_e.pkg.service."
            "MemberSignalCompiler.compile_member_digest"
        ),
    )
    label_id = _definition_id_for(
        program,
        "evals.fixtures.oracle_signal_smoke_e.pkg.labels.build_member_label",
    )
    alias_id = _definition_id_for(
        program,
        (
            "evals.fixtures.oracle_signal_smoke_e.pkg.service."
            "MemberSignalCompiler.resolve_owner_alias"
        ),
    )
    alias_uncertainty_id = next(
        construct.construct_id
        for construct in program.unsupported_constructs
        if construct.construct_text.startswith("pkg_alias.labels.build_member_label")
    )
    scoring = score_semantic_units(
        program,
        (
            "Fix transitive sole-provider self-call resolution for "
            "MemberSignalCompiler.compile_member_digest while preserving "
            "alias_chain frontier on pkg_alias.labels.build_member_label"
        ),
    )
    budget = (
        render_semantic_unit(program, method_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(program, label_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(program, alias_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(
            program,
            alias_uncertainty_id,
            RenderDetail.IDENTITY,
        ).token_count
    )

    result = optimize_semantic_units(program, scoring, budget=budget)
    selections = _selection_by_unit_id(result)

    assert scoring.scores[method_id].p_edit >= 0.85
    assert scoring.scores[label_id].p_edit >= 0.30
    assert scoring.scores[label_id].p_edit < 0.85
    assert selections[method_id].detail == RenderDetail.SOURCE.value
    assert selections[label_id].detail == RenderDetail.SOURCE.value
    assert selections[alias_id].detail == RenderDetail.SOURCE.value
    assert selections[alias_uncertainty_id].detail == RenderDetail.IDENTITY.value
    assert parent_class_id not in selections
    assert result.total_tokens <= budget


@pytest.mark.parametrize(
    ("target_file", "target_qualified_name", "target_source"),
    (
        (
            "src/context_ir/named_anchor.py",
            "src.context_ir.named_anchor.keep_named_src_anchor",
            (
                "def keep_named_src_anchor() -> str:\n"
                '    return "src anchor stays available"\n'
            ),
        ),
        (
            "tests/test_named_anchor.py",
            "tests.test_named_anchor.test_named_anchor_survives",
            (
                "def test_named_anchor_survives() -> None:\n"
                '    assert "named tests anchor"\n'
            ),
        ),
    ),
)
def test_optimize_semantic_units_keeps_named_repo_units_after_external_focus(
    tmp_path: Path,
    target_file: str,
    target_qualified_name: str,
    target_source: str,
) -> None:
    """Explicit repo-root anchors survive after a non-src focus is selected."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "driver.py").write_text(
        textwrap.dedent(
            """
            def build_external_focus() -> str:
                return "external focus selected first"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    target_path = tmp_path / target_file
    target_path.parent.mkdir(parents=True)
    (target_path.parent / "__init__.py").write_text("", encoding="utf-8")
    target_path.write_text(target_source, encoding="utf-8")

    program = _semantic_program(tmp_path)
    focus_id = _definition_id_for(program, "pkg.driver.build_external_focus")
    target_id = _definition_id_for(program, target_qualified_name)
    scoring = SemanticScoringResult(
        query=f"Fix pkg.driver.build_external_focus and {target_qualified_name}",
        scores={
            unit_id: SemanticUnitScore(
                unit_id=unit_id,
                p_edit=(
                    1.0
                    if unit_id == focus_id
                    else 0.34
                    if unit_id == target_id
                    else 0.0
                ),
                p_support=0.0,
            )
            for unit_id in _renderable_unit_ids(program)
        },
    )
    budget = (
        render_semantic_unit(program, focus_id, RenderDetail.SOURCE).token_count
        + render_semantic_unit(program, target_id, RenderDetail.SOURCE).token_count
    )

    result = optimize_semantic_units(program, scoring, budget=budget)
    selections = _selection_by_unit_id(result)

    assert tuple(selection.unit_id for selection in result.selections[:2]) == (
        focus_id,
        target_id,
    )
    assert scoring.scores[target_id].p_edit < 0.50
    assert selections[focus_id].detail == RenderDetail.SOURCE.value
    assert selections[target_id].detail == RenderDetail.SOURCE.value
    assert result.total_tokens <= budget


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

    assert tuple(selection.unit_id for selection in result.selections) == (
        router_id,
        run_id,
        frontier_id,
        summary_id,
    )
    assert result.total_tokens == 146
    assert selections[router_id].detail == RenderDetail.SOURCE.value
    assert selections[run_id].detail == RenderDetail.SOURCE.value
    assert selections[frontier_id].detail == RenderDetail.IDENTITY.value
    assert selections[summary_id].detail == RenderDetail.SOURCE.value
    assert registry_id not in selections
    assert main_frontier_id not in selections
    assert tuple(warning.code for warning in result.warnings) == (
        SemanticOptimizationWarningCode.BUDGET_PRESSURE,
    )
    assert result.warnings[0].unit_id == router_id
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

"""Deterministic per-run eval metric scoring tests."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

import context_ir
import context_ir.eval_metrics as eval_metrics
from context_ir.eval_oracles import (
    EvalOracleSetup,
    EvalOracleTask,
    FrontierOracleSelector,
    ResolvedOracleSelector,
    SymbolOracleSelector,
    UnsupportedOracleSelector,
)
from context_ir.eval_providers import (
    CONTEXT_IR_PROVIDER,
    LEXICAL_TOP_K_FILES_PROVIDER,
    PROVIDER_ALGORITHM_VERSION,
    EvalProviderConfig,
    EvalProviderMetadata,
    EvalProviderResult,
    EvalProviderWarning,
    EvalSelectedUnit,
    estimate_tokens,
)
from context_ir.semantic_types import SemanticProgram, SourceSpan, SyntaxProgram


def _write_file(repo_root: Path, relative_path: str, text: str) -> None:
    """Write one UTF-8 fixture file below ``repo_root``."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _span_for_snippet(
    source_text: str,
    snippet: str,
    *,
    occurrence: int = 1,
) -> SourceSpan:
    """Return the exact source span covering the requested snippet occurrence."""
    start = -1
    search_start = 0
    for _ in range(occurrence):
        start = source_text.index(snippet, search_start)
        search_start = start + 1
    end = start + len(snippet)
    return _span_from_offsets(source_text, start, end)


def _span_from_offsets(source_text: str, start: int, end: int) -> SourceSpan:
    """Return a source span for exact character offsets."""
    if start < 0 or end < start:
        raise ValueError("invalid offsets")
    if end > len(source_text):
        raise ValueError("offsets exceed source length")

    if not source_text:
        return SourceSpan(start_line=1, start_column=0, end_line=1, end_column=0)

    lines = source_text.splitlines(keepends=True)
    line_start = 0
    start_line: int | None = None
    start_column: int | None = None
    end_line: int | None = None
    end_column: int | None = None
    for line_number, line in enumerate(lines, start=1):
        line_end = line_start + len(line)
        if start_line is None and start <= line_end:
            start_line = line_number
            start_column = start - line_start
        if end_line is None and end <= line_end:
            end_line = line_number
            end_column = end - line_start
            break
        line_start = line_end

    if (
        start_line is None
        or start_column is None
        or end_line is None
        or end_column is None
    ):
        raise AssertionError("failed to map offsets to source span")

    return SourceSpan(
        start_line=start_line,
        start_column=start_column,
        end_line=end_line,
        end_column=end_column,
    )


def _resolved_symbol_selector(
    *,
    qualified_name: str,
    role: str,
    min_detail: str,
    unit_id: str,
    file_path: str,
    span: SourceSpan,
) -> ResolvedOracleSelector:
    """Build one resolved symbol oracle selector record."""
    return ResolvedOracleSelector(
        selector=SymbolOracleSelector(
            kind="symbol",
            qualified_name=qualified_name,
            role=role,  # type: ignore[arg-type]
            min_detail=min_detail,  # type: ignore[arg-type]
        ),
        resolution_status="resolved",
        resolved_unit_id=unit_id,
        resolved_file_path=file_path,
        resolved_span=span,
        failure_reason=None,
        candidate_count=1,
        candidate_summaries=(unit_id,),
    )


def _resolved_frontier_selector(
    *,
    file_path: str,
    access_text: str,
    min_detail: str,
    unit_id: str,
    span: SourceSpan,
) -> ResolvedOracleSelector:
    """Build one resolved frontier oracle selector record."""
    return ResolvedOracleSelector(
        selector=FrontierOracleSelector(
            kind="frontier",
            file_path=file_path,
            access_text=access_text,
            context="call",  # type: ignore[arg-type]
            reason_code="unresolved_name",  # type: ignore[arg-type]
            min_detail=min_detail,  # type: ignore[arg-type]
        ),
        resolution_status="resolved",
        resolved_unit_id=unit_id,
        resolved_file_path=file_path,
        resolved_span=span,
        failure_reason=None,
        candidate_count=1,
        candidate_summaries=(unit_id,),
    )


def _resolved_unsupported_selector(
    *,
    file_path: str,
    construct_text: str,
    min_detail: str,
    unit_id: str,
    span: SourceSpan,
) -> ResolvedOracleSelector:
    """Build one resolved unsupported oracle selector record."""
    return ResolvedOracleSelector(
        selector=UnsupportedOracleSelector(
            kind="unsupported",
            file_path=file_path,
            construct_text=construct_text,
            reason_code="star_import",  # type: ignore[arg-type]
            min_detail=min_detail,  # type: ignore[arg-type]
        ),
        resolution_status="resolved",
        resolved_unit_id=unit_id,
        resolved_file_path=file_path,
        resolved_span=span,
        failure_reason=None,
        candidate_count=1,
        candidate_summaries=(unit_id,),
    )


def _setup(
    repo_root: Path,
    *,
    resolved_selectors: tuple[ResolvedOracleSelector, ...],
    task_id: str = "task",
) -> EvalOracleSetup:
    """Build one minimal resolved oracle setup for scoring tests."""
    task = EvalOracleTask(
        task_id=task_id,
        fixture_id="fixture",
        expected_selectors=tuple(
            resolved_selector.selector for resolved_selector in resolved_selectors
        ),
    )
    syntax = SyntaxProgram(repo_root=repo_root)
    program = SemanticProgram(repo_root=repo_root, syntax=syntax)
    return EvalOracleSetup(
        task=task,
        semantic_program=program,
        resolved_selectors=resolved_selectors,
    )


def _document_for_total_tokens(total_tokens: int) -> str:
    """Return non-empty text whose estimated tokens equal ``total_tokens``."""
    if total_tokens <= 0:
        raise ValueError("total_tokens must be > 0")
    return "x" * (total_tokens * 4)


def _context_ir_result(
    *,
    task_id: str = "task",
    selected_units: tuple[EvalSelectedUnit, ...] = (),
    omitted_unit_ids: tuple[str, ...] = (),
    warning_details: tuple[EvalProviderWarning, ...] = (),
    total_tokens: int = 40,
    budget: int = 100,
) -> EvalProviderResult:
    """Build one deterministic Context IR provider result for tests."""
    document = _document_for_total_tokens(total_tokens)
    metadata = EvalProviderMetadata(
        selected_units=selected_units,
        warning_details=warning_details,
    )
    return EvalProviderResult(
        provider_name=CONTEXT_IR_PROVIDER,
        provider_algorithm_version=PROVIDER_ALGORITHM_VERSION,
        provider_config=EvalProviderConfig(),
        task_id=task_id,
        query="query",
        budget=budget,
        document=document,
        total_tokens=estimate_tokens(document),
        selected_files=(),
        omitted_candidate_files=(),
        selected_unit_ids=tuple(unit.unit_id for unit in selected_units),
        omitted_unit_ids=omitted_unit_ids,
        warnings=tuple(warning.code for warning in warning_details),
        metadata=metadata,
    )


def _baseline_result(
    *,
    selected_files: tuple[str, ...],
    task_id: str = "task",
    total_tokens: int = 40,
    budget: int = 100,
) -> EvalProviderResult:
    """Build one deterministic whole-file baseline result for tests."""
    document = _document_for_total_tokens(total_tokens)
    metadata = EvalProviderMetadata(
        candidate_files=selected_files,
        omitted_candidate_files=(),
    )
    return EvalProviderResult(
        provider_name=LEXICAL_TOP_K_FILES_PROVIDER,
        provider_algorithm_version=PROVIDER_ALGORITHM_VERSION,
        provider_config=EvalProviderConfig(max_candidates=len(selected_files)),
        task_id=task_id,
        query="query",
        budget=budget,
        document=document,
        total_tokens=estimate_tokens(document),
        selected_files=selected_files,
        omitted_candidate_files=(),
        selected_unit_ids=(),
        omitted_unit_ids=(),
        warnings=(),
        metadata=metadata,
    )


def test_context_ir_detail_ranks_drive_adequacy_and_uncertainty_is_none(
    tmp_path: Path,
) -> None:
    """Identity, summary, and source ranks control adequacy deterministically."""
    source_text = (
        "def shallow() -> None:\n"
        "    return None\n\n"
        "def support() -> None:\n"
        "    return None\n\n"
        "def needs_source() -> None:\n"
        "    return None\n"
    )
    _write_file(tmp_path, "main.py", source_text)
    shallow_span = _span_for_snippet(source_text, "def shallow() -> None:\n")
    support_span = _span_for_snippet(source_text, "def support() -> None:\n")
    source_span = _span_for_snippet(source_text, "def needs_source() -> None:\n")
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.shallow",
                role="edit",
                min_detail="identity",
                unit_id="def:main.py:main.shallow",
                file_path="main.py",
                span=shallow_span,
            ),
            _resolved_symbol_selector(
                qualified_name="main.support",
                role="support",
                min_detail="summary",
                unit_id="def:main.py:main.support",
                file_path="main.py",
                span=support_span,
            ),
            _resolved_symbol_selector(
                qualified_name="main.needs_source",
                role="edit",
                min_detail="source",
                unit_id="def:main.py:main.needs_source",
                file_path="main.py",
                span=source_span,
            ),
        ),
    )
    result = _context_ir_result(
        selected_units=(
            EvalSelectedUnit(
                unit_id="def:main.py:main.shallow",
                detail="summary",
                token_count=7,
                basis="heuristic_candidate",
            ),
            EvalSelectedUnit(
                unit_id="def:main.py:main.support",
                detail="summary",
                token_count=5,
                basis="heuristic_candidate",
            ),
            EvalSelectedUnit(
                unit_id="def:main.py:main.needs_source",
                detail="summary",
                token_count=11,
                basis="heuristic_candidate",
            ),
        ),
        total_tokens=40,
    )

    metrics = eval_metrics.score_eval_run(setup, result)

    assert metrics.edit_coverage == pytest.approx(0.5)
    assert metrics.support_coverage == pytest.approx(1.0)
    assert metrics.representation_adequacy == pytest.approx(2.0 / 3.0)
    assert metrics.uncertainty_honesty is None
    assert metrics.credited_relevant_tokens == 12
    assert metrics.total_expected_edit_selectors == 2
    assert metrics.adequate_edit_selectors == 1
    assert metrics.total_expected_support_selectors == 1
    assert metrics.adequate_support_selectors == 1
    assert metrics.represented_expected_selector_count == 3
    assert metrics.too_shallow_selector_ids == ("def:main.py:main.needs_source",)
    assert metrics.selected_matched_selector_ids == (
        "def:main.py:main.shallow",
        "def:main.py:main.support",
        "def:main.py:main.needs_source",
    )
    expected_aggregate = (
        0.35 * 0.5 + 0.25 * 1.0 + 0.15 * (2.0 / 3.0) + 0.10 * (12 / 40)
    ) / 0.85
    assert metrics.aggregate_score == pytest.approx(expected_aggregate)


def test_support_coverage_is_none_and_aggregate_renormalizes_when_support_missing(
    tmp_path: Path,
) -> None:
    """Missing support selectors drop that component and renormalize weights."""
    source_text = "def edit() -> None:\n    maybe_missing()\n"
    _write_file(tmp_path, "main.py", source_text)
    edit_span = _span_for_snippet(source_text, "def edit() -> None:\n")
    uncertainty_span = _span_for_snippet(source_text, "maybe_missing()")
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.edit",
                role="edit",
                min_detail="summary",
                unit_id="def:main.py:main.edit",
                file_path="main.py",
                span=edit_span,
            ),
            _resolved_frontier_selector(
                file_path="main.py",
                access_text="maybe_missing",
                min_detail="summary",
                unit_id="frontier:main.py:maybe_missing",
                span=uncertainty_span,
            ),
        ),
    )
    result = _context_ir_result(
        selected_units=(
            EvalSelectedUnit(
                unit_id="def:main.py:main.edit",
                detail="summary",
                token_count=6,
                basis="heuristic_candidate",
            ),
            EvalSelectedUnit(
                unit_id="frontier:main.py:maybe_missing",
                detail="summary",
                token_count=4,
                basis="unresolved_frontier_escalation",
            ),
        ),
        total_tokens=40,
    )

    metrics = eval_metrics.score_eval_run(setup, result)

    assert metrics.support_coverage is None
    assert metrics.uncertainty_honesty == pytest.approx(1.0)
    expected_aggregate = (
        0.35 * 1.0 + 0.15 * 1.0 + 0.15 * 1.0 + 0.10 * (10 / 40)
    ) / 0.75
    assert metrics.aggregate_score == pytest.approx(expected_aggregate)


def test_whole_file_baseline_source_inclusion_is_adequate_and_uses_exact_span_tokens(
    tmp_path: Path,
) -> None:
    """Whole-file baseline matches count as source-adequate and span-scoped."""
    source_text = (
        "def edit_target() -> None:\n"
        "    pass\n\n"
        "def support_target() -> None:\n"
        "    pass\n\n"
        "PADDING = 'x' * 100\n"
    )
    _write_file(tmp_path, "main.py", source_text)
    edit_span = _span_for_snippet(source_text, "def edit_target() -> None:\n")
    support_span = _span_for_snippet(source_text, "def support_target() -> None:\n")
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.edit_target",
                role="edit",
                min_detail="source",
                unit_id="def:main.py:main.edit_target",
                file_path="main.py",
                span=edit_span,
            ),
            _resolved_symbol_selector(
                qualified_name="main.support_target",
                role="support",
                min_detail="source",
                unit_id="def:main.py:main.support_target",
                file_path="main.py",
                span=support_span,
            ),
        ),
    )
    result = _baseline_result(selected_files=("main.py",), total_tokens=50)

    metrics = eval_metrics.score_eval_run(setup, result)

    expected_tokens = estimate_tokens("def edit_target() -> None:\n") + estimate_tokens(
        "def support_target() -> None:\n"
    )
    assert metrics.edit_coverage == pytest.approx(1.0)
    assert metrics.support_coverage == pytest.approx(1.0)
    assert metrics.representation_adequacy == pytest.approx(1.0)
    assert metrics.credited_relevant_tokens == expected_tokens


def test_selected_uncertainty_at_adequate_detail_gets_full_credit_and_span_tokens(
    tmp_path: Path,
) -> None:
    """Adequately selected uncertainty gets full honesty and source-span credit."""
    source_text = "def edit() -> None:\n    risky_call()\n"
    _write_file(tmp_path, "main.py", source_text)
    edit_span = _span_for_snippet(source_text, "def edit() -> None:\n")
    uncertainty_span = _span_for_snippet(source_text, "risky_call()")
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.edit",
                role="edit",
                min_detail="source",
                unit_id="def:main.py:main.edit",
                file_path="main.py",
                span=edit_span,
            ),
            _resolved_frontier_selector(
                file_path="main.py",
                access_text="risky_call",
                min_detail="source",
                unit_id="frontier:main.py:risky_call",
                span=uncertainty_span,
            ),
        ),
    )
    result = _context_ir_result(
        selected_units=(
            EvalSelectedUnit(
                unit_id="def:main.py:main.edit",
                detail="source",
                token_count=99,
                basis="heuristic_candidate",
            ),
            EvalSelectedUnit(
                unit_id="frontier:main.py:risky_call",
                detail="source",
                token_count=88,
                basis="unresolved_frontier_escalation",
            ),
        ),
        total_tokens=50,
    )

    metrics = eval_metrics.score_eval_run(setup, result)

    expected_tokens = estimate_tokens("def edit() -> None:\n") + estimate_tokens(
        "risky_call()"
    )
    assert metrics.uncertainty_honesty == pytest.approx(1.0)
    assert metrics.credited_relevant_tokens == expected_tokens


def test_selected_uncertainty_below_required_detail_gets_half_credit(
    tmp_path: Path,
) -> None:
    """Below-detail selected uncertainty gets partial honesty and no token credit."""
    source_text = "def edit() -> None:\n    risky_call()\n"
    _write_file(tmp_path, "main.py", source_text)
    edit_span = _span_for_snippet(source_text, "def edit() -> None:\n")
    uncertainty_span = _span_for_snippet(source_text, "risky_call()")
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.edit",
                role="edit",
                min_detail="summary",
                unit_id="def:main.py:main.edit",
                file_path="main.py",
                span=edit_span,
            ),
            _resolved_frontier_selector(
                file_path="main.py",
                access_text="risky_call",
                min_detail="source",
                unit_id="frontier:main.py:risky_call",
                span=uncertainty_span,
            ),
        ),
    )
    result = _context_ir_result(
        selected_units=(
            EvalSelectedUnit(
                unit_id="def:main.py:main.edit",
                detail="summary",
                token_count=6,
                basis="heuristic_candidate",
            ),
            EvalSelectedUnit(
                unit_id="frontier:main.py:risky_call",
                detail="summary",
                token_count=9,
                basis="unresolved_frontier_escalation",
            ),
        ),
        total_tokens=40,
    )

    metrics = eval_metrics.score_eval_run(setup, result)

    assert metrics.uncertainty_honesty == pytest.approx(0.5)
    assert metrics.credited_relevant_tokens == 6
    assert metrics.too_shallow_selector_ids == ("frontier:main.py:risky_call",)


def test_omitted_uncertainty_gets_quarter_credit_from_omission_alone(
    tmp_path: Path,
) -> None:
    """Omitted uncertainty gets quarter credit without a matching warning."""
    source_text = "def edit() -> None:\n    risky_call()\n"
    _write_file(tmp_path, "main.py", source_text)
    edit_span = _span_for_snippet(source_text, "def edit() -> None:\n")
    uncertainty_span = _span_for_snippet(source_text, "risky_call()")
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.edit",
                role="edit",
                min_detail="summary",
                unit_id="def:main.py:main.edit",
                file_path="main.py",
                span=edit_span,
            ),
            _resolved_frontier_selector(
                file_path="main.py",
                access_text="risky_call",
                min_detail="summary",
                unit_id="frontier:main.py:risky_call",
                span=uncertainty_span,
            ),
        ),
    )
    result = _context_ir_result(
        selected_units=(
            EvalSelectedUnit(
                unit_id="def:main.py:main.edit",
                detail="summary",
                token_count=6,
                basis="heuristic_candidate",
            ),
        ),
        omitted_unit_ids=("frontier:main.py:risky_call",),
        total_tokens=40,
    )

    metrics = eval_metrics.score_eval_run(setup, result)

    assert metrics.uncertainty_honesty == pytest.approx(0.25)
    assert metrics.omitted_expected_uncertainty_ids == ("frontier:main.py:risky_call",)


def test_omitted_uncertainty_with_matching_warning_gets_half_credit(
    tmp_path: Path,
) -> None:
    """Omitted uncertainty plus a matching warning caps at half credit."""
    source_text = "def edit() -> None:\n    risky_call()\n"
    _write_file(tmp_path, "main.py", source_text)
    edit_span = _span_for_snippet(source_text, "def edit() -> None:\n")
    uncertainty_span = _span_for_snippet(source_text, "risky_call()")
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.edit",
                role="edit",
                min_detail="summary",
                unit_id="def:main.py:main.edit",
                file_path="main.py",
                span=edit_span,
            ),
            _resolved_frontier_selector(
                file_path="main.py",
                access_text="risky_call",
                min_detail="summary",
                unit_id="frontier:main.py:risky_call",
                span=uncertainty_span,
            ),
        ),
    )
    result = _context_ir_result(
        selected_units=(
            EvalSelectedUnit(
                unit_id="def:main.py:main.edit",
                detail="summary",
                token_count=6,
                basis="heuristic_candidate",
            ),
        ),
        omitted_unit_ids=("frontier:main.py:risky_call",),
        warning_details=(
            EvalProviderWarning(
                code="omitted_uncertainty",
                unit_id="frontier:main.py:risky_call",
                message="frontier omitted",
            ),
        ),
        total_tokens=40,
    )

    metrics = eval_metrics.score_eval_run(setup, result)

    assert metrics.uncertainty_honesty == pytest.approx(0.5)


def test_baseline_raw_source_inclusion_does_not_award_uncertainty_credit(
    tmp_path: Path,
) -> None:
    """Whole-file baselines do not earn uncertainty honesty from source inclusion."""
    source_text = "def edit() -> None:\n    risky_call()\n"
    _write_file(tmp_path, "main.py", source_text)
    edit_span = _span_for_snippet(source_text, "def edit() -> None:\n")
    uncertainty_span = _span_for_snippet(source_text, "risky_call()")
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.edit",
                role="edit",
                min_detail="source",
                unit_id="def:main.py:main.edit",
                file_path="main.py",
                span=edit_span,
            ),
            _resolved_unsupported_selector(
                file_path="main.py",
                construct_text="risky_call()",
                min_detail="identity",
                unit_id="unsupported:main.py:risky_call",
                span=uncertainty_span,
            ),
        ),
    )
    result = _baseline_result(selected_files=("main.py",), total_tokens=40)

    metrics = eval_metrics.score_eval_run(setup, result)

    assert metrics.uncertainty_honesty == pytest.approx(0.0)
    assert metrics.credited_relevant_tokens == estimate_tokens("def edit() -> None:\n")


def test_overlapping_source_spans_are_merged_before_token_credit(
    tmp_path: Path,
) -> None:
    """Overlapping source-span credits merge by file before token counting."""
    source_text = "0123456789abcdef\n"
    _write_file(tmp_path, "main.py", source_text)
    first_span = _span_from_offsets(source_text, 0, 8)
    second_span = _span_from_offsets(source_text, 4, 12)
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.first",
                role="edit",
                min_detail="source",
                unit_id="def:main.py:main.first",
                file_path="main.py",
                span=first_span,
            ),
            _resolved_symbol_selector(
                qualified_name="main.second",
                role="support",
                min_detail="source",
                unit_id="def:main.py:main.second",
                file_path="main.py",
                span=second_span,
            ),
        ),
    )
    result = _baseline_result(selected_files=("main.py",), total_tokens=30)

    metrics = eval_metrics.score_eval_run(setup, result)

    assert metrics.credited_relevant_tokens == estimate_tokens("0123456789ab")


def test_scoring_does_not_mutate_inputs(tmp_path: Path) -> None:
    """Scoring is pure over the accepted oracle setup and provider result."""
    source_text = "def edit() -> None:\n    pass\n"
    _write_file(tmp_path, "main.py", source_text)
    edit_span = _span_for_snippet(source_text, "def edit() -> None:\n")
    setup = _setup(
        tmp_path,
        resolved_selectors=(
            _resolved_symbol_selector(
                qualified_name="main.edit",
                role="edit",
                min_detail="summary",
                unit_id="def:main.py:main.edit",
                file_path="main.py",
                span=edit_span,
            ),
        ),
    )
    result = _context_ir_result(
        selected_units=(
            EvalSelectedUnit(
                unit_id="def:main.py:main.edit",
                detail="summary",
                token_count=5,
                basis="heuristic_candidate",
            ),
        ),
    )
    setup_before = copy.deepcopy(setup)
    result_before = copy.deepcopy(result)

    eval_metrics.score_eval_run(setup, result)

    assert setup == setup_before
    assert result == result_before


def test_eval_metrics_stay_internal_and_do_not_add_report_fields() -> None:
    """Metric scoring remains internal and avoids report or ledger fields."""
    assert not hasattr(context_ir, "EvalRunMetrics")
    assert not hasattr(context_ir, "score_eval_run")

    metric_fields = set(eval_metrics.EvalRunMetrics.__dataclass_fields__)
    forbidden_fields = {
        "raw_jsonl_path",
        "markdown_report",
        "summary_table",
        "category_rollups",
        "public_claims",
    }

    assert forbidden_fields.isdisjoint(metric_fields)

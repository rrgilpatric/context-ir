"""Deterministic per-run eval metric scoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from context_ir.eval_oracles import EvalOracleSetup, ResolvedOracleSelector
from context_ir.eval_providers import (
    CONTEXT_IR_PROVIDER,
    EvalProviderResult,
    EvalSelectedUnit,
    estimate_tokens,
)
from context_ir.semantic_types import SourceSpan

_DETAIL_RANKS = {
    "identity": 1,
    "summary": 2,
    "source": 3,
}
_AGGREGATE_WEIGHTS = {
    "edit_coverage": 0.35,
    "support_coverage": 0.25,
    "representation_adequacy": 0.15,
    "uncertainty_honesty": 0.15,
    "noise_efficiency": 0.10,
}

_SelectorCategory = Literal["edit", "support", "uncertainty"]


@dataclass(frozen=True)
class EvalRunMetrics:
    """Deterministic metric outputs for one scored eval provider run."""

    provider_name: str
    task_id: str
    budget: int
    budget_compliant: bool
    edit_coverage: float
    support_coverage: float | None
    representation_adequacy: float
    uncertainty_honesty: float | None
    credited_relevant_tokens: int
    noise_tokens: int
    noise_ratio: float
    noise_efficiency: float
    aggregate_score: float
    total_expected_edit_selectors: int
    adequate_edit_selectors: int
    total_expected_support_selectors: int
    adequate_support_selectors: int
    total_expected_uncertainty_selectors: int
    represented_expected_selector_count: int
    too_shallow_selector_ids: tuple[str, ...] = ()
    omitted_expected_uncertainty_ids: tuple[str, ...] = ()
    selected_matched_selector_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class _MatchedSurface:
    represented: bool
    adequate: bool
    detail: str | None
    selected_unit: EvalSelectedUnit | None
    uses_source_span: bool


@dataclass(frozen=True)
class _CreditedSpan:
    file_path: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True)
class _SourceFileView:
    text: str
    line_offsets: tuple[int, ...]
    line_lengths: tuple[int, ...]


def score_eval_run(
    setup: EvalOracleSetup,
    result: EvalProviderResult,
) -> EvalRunMetrics:
    """Score one accepted oracle setup against one accepted provider result."""
    if setup.task.task_id != result.task_id:
        raise ValueError("oracle setup task_id must match provider result task_id")
    if result.total_tokens == 0:
        raise ValueError("provider result must have non-zero total_tokens")

    selected_units = {
        selected_unit.unit_id: selected_unit
        for selected_unit in result.metadata.selected_units
    }
    selected_files = frozenset(result.selected_files)
    omitted_unit_ids = frozenset(result.omitted_unit_ids)
    warning_unit_ids = frozenset(
        warning.unit_id
        for warning in result.metadata.warning_details
        if warning.unit_id is not None
    )

    total_edit = 0
    adequate_edit = 0
    total_support = 0
    adequate_support = 0
    total_uncertainty = 0
    represented_expected = 0
    uncertainty_credit_total = 0.0
    selected_token_credit = 0
    source_span_credits: list[_CreditedSpan] = []
    too_shallow_selector_ids: list[str] = []
    omitted_expected_uncertainty_ids: list[str] = []
    selected_matched_selector_ids: list[str] = []
    source_views: dict[str, _SourceFileView] = {}

    for resolved_selector in setup.resolved_selectors:
        selector_id = _selector_id(resolved_selector)
        category = _selector_category(resolved_selector)
        matched_surface = _matched_surface(
            resolved_selector=resolved_selector,
            result=result,
            selected_units=selected_units,
            selected_files=selected_files,
        )

        if matched_surface.represented:
            selected_matched_selector_ids.append(selector_id)
        if matched_surface.represented and not matched_surface.adequate:
            too_shallow_selector_ids.append(selector_id)

        if category == "edit":
            total_edit += 1
            if matched_surface.represented:
                represented_expected += 1
            if matched_surface.adequate:
                adequate_edit += 1
                selected_token_credit += _apply_relevant_token_credit(
                    matched_surface=matched_surface,
                    resolved_selector=resolved_selector,
                    setup=setup,
                    source_views=source_views,
                    source_span_credits=source_span_credits,
                )
            continue

        if category == "support":
            total_support += 1
            if matched_surface.represented:
                represented_expected += 1
            if matched_surface.adequate:
                adequate_support += 1
                selected_token_credit += _apply_relevant_token_credit(
                    matched_surface=matched_surface,
                    resolved_selector=resolved_selector,
                    setup=setup,
                    source_views=source_views,
                    source_span_credits=source_span_credits,
                )
            continue

        total_uncertainty += 1
        uncertainty_credit = _uncertainty_credit(
            selector_id=selector_id,
            matched_surface=matched_surface,
            omitted_unit_ids=omitted_unit_ids,
            warning_unit_ids=warning_unit_ids,
        )
        uncertainty_credit_total += uncertainty_credit
        if selector_id in omitted_unit_ids:
            omitted_expected_uncertainty_ids.append(selector_id)
        if uncertainty_credit == 1.0:
            selected_token_credit += _apply_relevant_token_credit(
                matched_surface=matched_surface,
                resolved_selector=resolved_selector,
                setup=setup,
                source_views=source_views,
                source_span_credits=source_span_credits,
            )

    if total_edit == 0:
        raise ValueError(
            "oracle setup must contain at least one expected edit selector"
        )

    source_token_credit = _merged_source_token_credit(
        repo_root=setup.semantic_program.repo_root,
        source_views=source_views,
        spans=tuple(source_span_credits),
    )
    credited_relevant_tokens = selected_token_credit + source_token_credit
    noise_tokens = max(0, result.total_tokens - credited_relevant_tokens)
    edit_coverage = adequate_edit / total_edit
    support_coverage = None if total_support == 0 else adequate_support / total_support
    representation_adequacy = (
        0.0
        if represented_expected == 0
        else (adequate_edit + adequate_support) / represented_expected
    )
    uncertainty_honesty = (
        None if total_uncertainty == 0 else uncertainty_credit_total / total_uncertainty
    )
    noise_ratio = noise_tokens / result.total_tokens
    noise_efficiency = credited_relevant_tokens / result.total_tokens
    aggregate_score = _aggregate_score(
        edit_coverage=edit_coverage,
        support_coverage=support_coverage,
        representation_adequacy=representation_adequacy,
        uncertainty_honesty=uncertainty_honesty,
        noise_efficiency=noise_efficiency,
    )

    return EvalRunMetrics(
        provider_name=result.provider_name,
        task_id=result.task_id,
        budget=result.budget,
        budget_compliant=result.total_tokens <= result.budget,
        edit_coverage=edit_coverage,
        support_coverage=support_coverage,
        representation_adequacy=representation_adequacy,
        uncertainty_honesty=uncertainty_honesty,
        credited_relevant_tokens=credited_relevant_tokens,
        noise_tokens=noise_tokens,
        noise_ratio=noise_ratio,
        noise_efficiency=noise_efficiency,
        aggregate_score=aggregate_score,
        total_expected_edit_selectors=total_edit,
        adequate_edit_selectors=adequate_edit,
        total_expected_support_selectors=total_support,
        adequate_support_selectors=adequate_support,
        total_expected_uncertainty_selectors=total_uncertainty,
        represented_expected_selector_count=represented_expected,
        too_shallow_selector_ids=tuple(too_shallow_selector_ids),
        omitted_expected_uncertainty_ids=tuple(omitted_expected_uncertainty_ids),
        selected_matched_selector_ids=tuple(selected_matched_selector_ids),
    )


def _apply_relevant_token_credit(
    *,
    matched_surface: _MatchedSurface,
    resolved_selector: ResolvedOracleSelector,
    setup: EvalOracleSetup,
    source_views: dict[str, _SourceFileView],
    source_span_credits: list[_CreditedSpan],
) -> int:
    """Record relevant token credit for one adequate selector match."""
    if matched_surface.uses_source_span:
        source_span_credits.append(
            _selector_span_credit(
                repo_root=setup.semantic_program.repo_root,
                resolved_selector=resolved_selector,
                source_views=source_views,
            )
        )
        return 0
    selected_unit = matched_surface.selected_unit
    if selected_unit is None:
        raise ValueError(
            "adequate non-source selector matches must expose a selected unit"
        )
    return selected_unit.token_count


def _aggregate_score(
    *,
    edit_coverage: float,
    support_coverage: float | None,
    representation_adequacy: float,
    uncertainty_honesty: float | None,
    noise_efficiency: float,
) -> float:
    """Return the weighted aggregate score with ``None`` components dropped."""
    active_components = [
        (edit_coverage, _AGGREGATE_WEIGHTS["edit_coverage"]),
        (representation_adequacy, _AGGREGATE_WEIGHTS["representation_adequacy"]),
        (noise_efficiency, _AGGREGATE_WEIGHTS["noise_efficiency"]),
    ]
    if support_coverage is not None:
        active_components.append(
            (support_coverage, _AGGREGATE_WEIGHTS["support_coverage"])
        )
    if uncertainty_honesty is not None:
        active_components.append(
            (uncertainty_honesty, _AGGREGATE_WEIGHTS["uncertainty_honesty"])
        )

    total_weight = sum(weight for _, weight in active_components)
    if total_weight == 0.0:
        raise ValueError("aggregate score requires at least one active component")
    return sum(
        component * (weight / total_weight) for component, weight in active_components
    )


def _merged_source_token_credit(
    *,
    repo_root: Path,
    source_views: dict[str, _SourceFileView],
    spans: tuple[_CreditedSpan, ...],
) -> int:
    """Return merged relevant-token credit for all source-span-based matches."""
    spans_by_file: dict[str, list[_CreditedSpan]] = {}
    for span in spans:
        spans_by_file.setdefault(span.file_path, []).append(span)

    total = 0
    for file_path, file_spans in spans_by_file.items():
        source_view = _source_view(
            repo_root=repo_root,
            file_path=file_path,
            source_views=source_views,
        )
        merged = sorted(
            file_spans,
            key=lambda item: (item.start_offset, item.end_offset),
        )
        current_start: int | None = None
        current_end: int | None = None
        for span in merged:
            if current_start is None or current_end is None:
                current_start = span.start_offset
                current_end = span.end_offset
                continue
            if span.start_offset < current_end:
                current_end = max(current_end, span.end_offset)
                continue
            total += estimate_tokens(source_view.text[current_start:current_end])
            current_start = span.start_offset
            current_end = span.end_offset

        if current_start is not None and current_end is not None:
            total += estimate_tokens(source_view.text[current_start:current_end])

    return total


def _selector_span_credit(
    *,
    repo_root: Path,
    resolved_selector: ResolvedOracleSelector,
    source_views: dict[str, _SourceFileView],
) -> _CreditedSpan:
    """Return one source-span token credit record for a resolved selector."""
    file_path = _required_file_path(resolved_selector)
    source_view = _source_view(
        repo_root=repo_root,
        file_path=file_path,
        source_views=source_views,
    )
    start_offset, end_offset = _span_offsets(
        source_view=source_view,
        span=_required_span(resolved_selector),
    )
    return _CreditedSpan(
        file_path=file_path,
        start_offset=start_offset,
        end_offset=end_offset,
    )


def _matched_surface(
    *,
    resolved_selector: ResolvedOracleSelector,
    result: EvalProviderResult,
    selected_units: dict[str, EvalSelectedUnit],
    selected_files: frozenset[str],
) -> _MatchedSurface:
    """Return whether the provider represented the selector and at what detail."""
    min_detail = _minimum_detail(resolved_selector)
    min_rank = _detail_rank(min_detail)
    selector_id = _selector_id(resolved_selector)
    if result.provider_name == CONTEXT_IR_PROVIDER:
        selected_unit = selected_units.get(selector_id)
        if selected_unit is None:
            return _MatchedSurface(
                represented=False,
                adequate=False,
                detail=None,
                selected_unit=None,
                uses_source_span=False,
            )
        selected_detail = selected_unit.detail
        selected_rank = _detail_rank(selected_detail)
        return _MatchedSurface(
            represented=True,
            adequate=selected_rank >= min_rank,
            detail=selected_detail,
            selected_unit=selected_unit,
            uses_source_span=selected_detail == "source",
        )

    represented = _required_file_path(resolved_selector) in selected_files
    return _MatchedSurface(
        represented=represented,
        adequate=represented,
        detail="source" if represented else None,
        selected_unit=None,
        uses_source_span=represented,
    )


def _uncertainty_credit(
    *,
    selector_id: str,
    matched_surface: _MatchedSurface,
    omitted_unit_ids: frozenset[str],
    warning_unit_ids: frozenset[str],
) -> float:
    """Return deterministic uncertainty honesty credit for one selector."""
    if matched_surface.represented:
        if matched_surface.adequate:
            return 1.0 if matched_surface.selected_unit is not None else 0.0
        return 0.5 if matched_surface.selected_unit is not None else 0.0

    credit = 0.0
    if selector_id in omitted_unit_ids:
        credit += 0.25
    if selector_id in warning_unit_ids:
        credit += 0.25
    return min(0.5, credit)


def _selector_category(resolved_selector: ResolvedOracleSelector) -> _SelectorCategory:
    """Return the scoring category for one resolved selector."""
    selector = resolved_selector.selector
    if selector.kind == "symbol":
        return selector.role
    return "uncertainty"


def _minimum_detail(resolved_selector: ResolvedOracleSelector) -> str:
    """Return the required minimum detail for one resolved selector."""
    return resolved_selector.selector.min_detail


def _detail_rank(detail: str) -> int:
    """Return the accepted total ordering rank for a detail label."""
    try:
        return _DETAIL_RANKS[detail]
    except KeyError as error:
        raise ValueError(f"unsupported eval detail rank: {detail}") from error


def _selector_id(resolved_selector: ResolvedOracleSelector) -> str:
    """Return the resolved selector unit identifier required for scoring."""
    unit_id = resolved_selector.resolved_unit_id
    if resolved_selector.resolution_status != "resolved" or unit_id is None:
        raise ValueError("score_eval_run requires a fully resolved oracle setup")
    return unit_id


def _required_file_path(resolved_selector: ResolvedOracleSelector) -> str:
    """Return the resolved selector file path or fail loudly."""
    file_path = resolved_selector.resolved_file_path
    if file_path is None:
        raise ValueError("resolved selectors must provide resolved_file_path")
    return file_path


def _required_span(resolved_selector: ResolvedOracleSelector) -> SourceSpan:
    """Return the resolved selector source span or fail loudly."""
    span = resolved_selector.resolved_span
    if span is None:
        raise ValueError("resolved selectors must provide resolved_span")
    return span


def _source_view(
    *,
    repo_root: Path,
    file_path: str,
    source_views: dict[str, _SourceFileView],
) -> _SourceFileView:
    """Return cached source text and line offsets for one repository file."""
    cached = source_views.get(file_path)
    if cached is not None:
        return cached

    text = (repo_root / file_path).read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    offsets: list[int] = []
    line_lengths: list[int] = []
    offset = 0
    for line in lines:
        offsets.append(offset)
        line_lengths.append(len(line))
        offset += len(line)

    view = _SourceFileView(
        text=text,
        line_offsets=tuple(offsets),
        line_lengths=tuple(line_lengths),
    )
    source_views[file_path] = view
    return view


def _span_offsets(
    *,
    source_view: _SourceFileView,
    span: SourceSpan,
) -> tuple[int, int]:
    """Return character offsets for one source span."""
    if span.start_line < 1 or span.end_line < span.start_line:
        raise ValueError("resolved span must use valid positive line numbers")

    if not source_view.line_lengths:
        if (
            span.start_line != 1
            or span.end_line != 1
            or span.start_column != 0
            or span.end_column != 0
        ):
            raise ValueError("resolved span exceeds empty source text")
        return (0, 0)

    if span.end_line > len(source_view.line_lengths):
        raise ValueError("resolved span exceeds source line count")

    start_line_index = span.start_line - 1
    end_line_index = span.end_line - 1
    start_line_length = source_view.line_lengths[start_line_index]
    end_line_length = source_view.line_lengths[end_line_index]
    if span.start_column < 0 or span.start_column > start_line_length:
        raise ValueError("resolved span start_column exceeds source line length")
    if span.end_column < 0 or span.end_column > end_line_length:
        raise ValueError("resolved span end_column exceeds source line length")

    start_offset = source_view.line_offsets[start_line_index] + span.start_column
    end_offset = source_view.line_offsets[end_line_index] + span.end_column
    if end_offset < start_offset:
        raise ValueError("resolved span must not end before it starts")
    return (start_offset, end_offset)

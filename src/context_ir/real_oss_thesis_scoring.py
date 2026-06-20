"""Internal real-OSS thesis scoring contracts."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath

from context_ir.real_oss_thesis_manifest import (
    REAL_OSS_THESIS_BUDGETS,
    REAL_OSS_THESIS_PROVIDERS,
    RealOssSelectedTask,
)

_PROVIDER_ORDER = {
    provider_name: index
    for index, provider_name in enumerate(REAL_OSS_THESIS_PROVIDERS)
}
_BUDGET_ORDER = {budget: index for index, budget in enumerate(REAL_OSS_THESIS_BUDGETS)}


@dataclass(frozen=True, order=True)
class RealOssLineUnit:
    """One repository path plus one 1-based line number."""

    path: str
    line_number: int

    def __post_init__(self) -> None:
        """Reject malformed line-unit identity."""
        _validate_repo_path(self.path, field_name="path")
        _validate_positive_int(self.line_number, field_name="line_number")


@dataclass(frozen=True)
class RealOssSelectedContextRecord:
    """One provider-selected context record with token accounting."""

    path: str
    start_line: int | None
    end_line: int | None
    token_count: int

    def __post_init__(self) -> None:
        """Reject malformed selected context coordinates or token counts."""
        _validate_repo_path(self.path, field_name="path")
        _validate_positive_int(self.token_count, field_name="token_count")
        if (self.start_line is None) != (self.end_line is None):
            raise ValueError("start_line and end_line must both be present or absent")
        if self.start_line is None:
            return

        start_line = self.start_line
        end_line = self.end_line
        if end_line is None:
            raise ValueError("end_line must be present when start_line is present")
        _validate_positive_int(start_line, field_name="start_line")
        _validate_positive_int(end_line, field_name="end_line")
        if end_line < start_line:
            raise ValueError("end_line must be greater than or equal to start_line")

    @property
    def selected_line_count(self) -> int:
        """Return the number of selected line units represented by the record."""
        if self.start_line is None or self.end_line is None:
            return 0
        return self.end_line - self.start_line + 1


@dataclass(frozen=True)
class RealOssProviderBudgetSelection:
    """Selected context records for one task, provider, and frozen budget."""

    task_id: str
    provider_name: str
    budget: int
    selected_records: tuple[RealOssSelectedContextRecord, ...]

    def __post_init__(self) -> None:
        """Reject provider, budget, record, or token-accounting drift."""
        _validate_non_empty_string(self.task_id, field_name="task_id")
        _validate_provider_name(self.provider_name)
        _validate_budget(self.budget)
        _validate_selected_records(self.selected_records, field_name="selected_records")
        if self.selected_tokens > self.budget:
            raise ValueError("selected_tokens must not exceed budget")

    @property
    def selected_tokens(self) -> int:
        """Return total selected tokens across all context records."""
        return sum(record.token_count for record in self.selected_records)


@dataclass(frozen=True)
class RealOssTaskBudgetScore:
    """Frozen metrics for one real-OSS task, provider, and budget."""

    task_id: str
    provider_name: str
    budget: int
    oracle_line_units: tuple[RealOssLineUnit, ...]
    covered_oracle_line_units: tuple[RealOssLineUnit, ...]
    edit_relevant_recall: float
    selected_tokens: int
    wasted_tokens: float
    waste_rate: float | None
    is_valid_for_comparison: bool

    def __post_init__(self) -> None:
        """Reject metric records that do not match the frozen formulas."""
        _validate_non_empty_string(self.task_id, field_name="task_id")
        _validate_provider_name(self.provider_name)
        _validate_budget(self.budget)
        _validate_line_units(self.oracle_line_units, field_name="oracle_line_units")
        _validate_line_units(
            self.covered_oracle_line_units,
            field_name="covered_oracle_line_units",
        )
        if not self.oracle_line_units:
            raise ValueError("oracle_line_units must be non-empty")
        if self.oracle_line_units != tuple(sorted(self.oracle_line_units)):
            raise ValueError("oracle_line_units must be sorted")
        if self.covered_oracle_line_units != tuple(
            sorted(self.covered_oracle_line_units)
        ):
            raise ValueError("covered_oracle_line_units must be sorted")
        if not set(self.covered_oracle_line_units).issubset(
            set(self.oracle_line_units)
        ):
            raise ValueError("covered_oracle_line_units must be oracle members")

        _validate_fraction(
            self.edit_relevant_recall,
            field_name="edit_relevant_recall",
        )
        _validate_non_negative_int(self.selected_tokens, field_name="selected_tokens")
        if self.selected_tokens > self.budget:
            raise ValueError("selected_tokens must not exceed budget")
        _validate_non_negative_float(self.wasted_tokens, field_name="wasted_tokens")
        if self.wasted_tokens > float(self.selected_tokens):
            raise ValueError("wasted_tokens must not exceed selected_tokens")
        if not isinstance(self.is_valid_for_comparison, bool):
            raise ValueError("is_valid_for_comparison must be boolean")

        expected_recall = self.covered_oracle_line_count / self.oracle_line_count
        if not _floats_close(self.edit_relevant_recall, expected_recall):
            raise ValueError("edit_relevant_recall does not match covered oracle lines")

        if self.selected_tokens == 0:
            if self.waste_rate is not None:
                raise ValueError("waste_rate must be None when selected_tokens is zero")
            if self.is_valid_for_comparison:
                raise ValueError("zero selected_tokens cannot be comparison-valid")
            return

        if self.waste_rate is None:
            raise ValueError(
                "waste_rate must be defined when selected_tokens is nonzero"
            )
        _validate_fraction(self.waste_rate, field_name="waste_rate")
        expected_waste_rate = self.wasted_tokens / self.selected_tokens
        if not _floats_close(self.waste_rate, expected_waste_rate):
            raise ValueError("waste_rate does not match wasted_tokens")
        if not self.is_valid_for_comparison:
            raise ValueError("nonzero selected_tokens must be comparison-valid")

    @property
    def oracle_line_count(self) -> int:
        """Return the total oracle line-unit count."""
        return len(self.oracle_line_units)

    @property
    def covered_oracle_line_count(self) -> int:
        """Return the covered oracle line-unit count."""
        return len(self.covered_oracle_line_units)


@dataclass(frozen=True)
class RealOssTaskProviderScore:
    """Frozen budget scores and recall AUC for one task/provider pair."""

    task_id: str
    provider_name: str
    budget_scores: tuple[RealOssTaskBudgetScore, ...]
    recall_auc: float

    def __post_init__(self) -> None:
        """Reject incomplete, unsorted, or internally inconsistent provider scores."""
        _validate_non_empty_string(self.task_id, field_name="task_id")
        _validate_provider_name(self.provider_name)
        _validate_budget_scores(self.budget_scores, field_name="budget_scores")
        if tuple(score.budget for score in self.budget_scores) != (
            REAL_OSS_THESIS_BUDGETS
        ):
            raise ValueError("budget_scores must cover the frozen budgets in order")
        for score in self.budget_scores:
            if score.task_id != self.task_id:
                raise ValueError("budget_scores must match task_id")
            if score.provider_name != self.provider_name:
                raise ValueError("budget_scores must match provider_name")
        _validate_fraction(self.recall_auc, field_name="recall_auc")
        expected_auc = calculate_real_oss_recall_auc(self.budget_scores)
        if not _floats_close(self.recall_auc, expected_auc):
            raise ValueError("recall_auc does not match budget scores")


def expand_real_oss_oracle_line_units(
    task: RealOssSelectedTask,
) -> tuple[RealOssLineUnit, ...]:
    """Expand a selected task's base-side changed ranges into line units."""
    _validate_selected_task(task)
    line_units: list[RealOssLineUnit] = []
    for changed_path in task.changed_python_paths:
        for line_range in changed_path.base_line_ranges:
            for line_number in range(line_range.start_line, line_range.end_line + 1):
                line_units.append(
                    RealOssLineUnit(
                        path=changed_path.path,
                        line_number=line_number,
                    )
                )
    return _dedupe_and_sort_line_units(line_units)


def expand_real_oss_selected_line_units(
    record: RealOssSelectedContextRecord,
) -> tuple[RealOssLineUnit, ...]:
    """Expand one provider-selected context record into line units."""
    if not isinstance(record, RealOssSelectedContextRecord):
        raise ValueError("record must be a RealOssSelectedContextRecord")
    if record.start_line is None or record.end_line is None:
        return ()
    return tuple(
        RealOssLineUnit(path=record.path, line_number=line_number)
        for line_number in range(record.start_line, record.end_line + 1)
    )


def score_real_oss_task_budget(
    task: RealOssSelectedTask,
    selection: RealOssProviderBudgetSelection,
) -> RealOssTaskBudgetScore:
    """Compute frozen per-budget metrics for one selected task."""
    _validate_selected_task(task)
    if not isinstance(selection, RealOssProviderBudgetSelection):
        raise ValueError("selection must be a RealOssProviderBudgetSelection")
    if selection.task_id != task.task_id:
        raise ValueError("selection task_id must match task.task_id")

    oracle_line_units = expand_real_oss_oracle_line_units(task)
    oracle_line_unit_set = frozenset(oracle_line_units)
    covered_line_units: list[RealOssLineUnit] = []
    wasted_tokens = 0.0

    for record in selection.selected_records:
        selected_line_units = expand_real_oss_selected_line_units(record)
        if not selected_line_units:
            wasted_tokens += float(record.token_count)
            continue

        covered_line_units.extend(
            line_unit
            for line_unit in selected_line_units
            if line_unit in oracle_line_unit_set
        )
        non_overlapping_line_count = sum(
            1
            for line_unit in selected_line_units
            if line_unit not in oracle_line_unit_set
        )
        wasted_tokens += (
            record.token_count * non_overlapping_line_count / len(selected_line_units)
        )

    covered_oracle_line_units = _dedupe_and_sort_line_units(covered_line_units)
    selected_tokens = selection.selected_tokens
    waste_rate = wasted_tokens / selected_tokens if selected_tokens else None
    return RealOssTaskBudgetScore(
        task_id=task.task_id,
        provider_name=selection.provider_name,
        budget=selection.budget,
        oracle_line_units=oracle_line_units,
        covered_oracle_line_units=covered_oracle_line_units,
        edit_relevant_recall=len(covered_oracle_line_units) / len(oracle_line_units),
        selected_tokens=selected_tokens,
        wasted_tokens=wasted_tokens,
        waste_rate=waste_rate,
        is_valid_for_comparison=selected_tokens > 0,
    )


def score_real_oss_task_provider(
    task: RealOssSelectedTask,
    selections: tuple[RealOssProviderBudgetSelection, ...],
) -> RealOssTaskProviderScore:
    """Compute all frozen-budget scores and recall AUC for one provider."""
    _validate_selected_task(task)
    _validate_selections(selections, field_name="selections")
    if not selections:
        raise ValueError("selections must be non-empty")

    provider_name = selections[0].provider_name
    for selection in selections:
        if selection.task_id != task.task_id:
            raise ValueError("all selections must match task.task_id")
        if selection.provider_name != provider_name:
            raise ValueError("all selections must use the same provider_name")

    sorted_selections = tuple(sorted(selections, key=_selection_budget_sort_key))
    if tuple(selection.budget for selection in sorted_selections) != (
        REAL_OSS_THESIS_BUDGETS
    ):
        raise ValueError("selections must cover the frozen budgets exactly once")

    budget_scores = tuple(
        score_real_oss_task_budget(task, selection) for selection in sorted_selections
    )
    return RealOssTaskProviderScore(
        task_id=task.task_id,
        provider_name=provider_name,
        budget_scores=budget_scores,
        recall_auc=calculate_real_oss_recall_auc(budget_scores),
    )


def score_real_oss_task_provider_batch(
    tasks: tuple[RealOssSelectedTask, ...],
    selections: tuple[RealOssProviderBudgetSelection, ...],
) -> tuple[RealOssTaskProviderScore, ...]:
    """Compute provider scores for grouped task/provider budget selections."""
    _validate_selected_tasks(tasks, field_name="tasks")
    _validate_selections(selections, field_name="selections")
    task_by_id = _task_by_id(tasks)
    grouped_selections: dict[
        tuple[str, str],
        list[RealOssProviderBudgetSelection],
    ] = {}
    for selection in selections:
        if selection.task_id not in task_by_id:
            raise ValueError("selection task_id is not present in tasks")
        group_key = (selection.task_id, selection.provider_name)
        grouped_selections.setdefault(group_key, []).append(selection)

    provider_scores: list[RealOssTaskProviderScore] = []
    for task_id, provider_name in sorted(
        grouped_selections,
        key=_task_provider_sort_key,
    ):
        provider_scores.append(
            score_real_oss_task_provider(
                task_by_id[task_id],
                tuple(grouped_selections[(task_id, provider_name)]),
            )
        )
    return tuple(provider_scores)


def calculate_real_oss_recall_auc(
    budget_scores: tuple[RealOssTaskBudgetScore, ...],
) -> float:
    """Return recall AUC across the frozen 2000/4000/8000 token budgets."""
    _validate_budget_scores(budget_scores, field_name="budget_scores")
    sorted_scores = tuple(sorted(budget_scores, key=_score_budget_sort_key))
    if tuple(score.budget for score in sorted_scores) != REAL_OSS_THESIS_BUDGETS:
        raise ValueError("budget_scores must cover the frozen budgets exactly once")

    task_id = sorted_scores[0].task_id
    provider_name = sorted_scores[0].provider_name
    for score in sorted_scores:
        if score.task_id != task_id:
            raise ValueError("budget_scores must share one task_id")
        if score.provider_name != provider_name:
            raise ValueError("budget_scores must share one provider_name")

    recall_by_budget = {
        score.budget: score.edit_relevant_recall for score in sorted_scores
    }
    low_budget, middle_budget, high_budget = REAL_OSS_THESIS_BUDGETS
    return (
        recall_by_budget[low_budget]
        + 2.0 * recall_by_budget[middle_budget]
        + recall_by_budget[high_budget]
    ) / 4.0


def _validate_selected_task(task: RealOssSelectedTask) -> None:
    if not isinstance(task, RealOssSelectedTask):
        raise ValueError("task must be a RealOssSelectedTask")


def _validate_selected_tasks(
    tasks: tuple[RealOssSelectedTask, ...],
    *,
    field_name: str,
) -> None:
    if not isinstance(tasks, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if any(not isinstance(task, RealOssSelectedTask) for task in tasks):
        raise ValueError(f"{field_name} must contain RealOssSelectedTask values")
    _task_by_id(tasks)


def _task_by_id(
    tasks: tuple[RealOssSelectedTask, ...],
) -> dict[str, RealOssSelectedTask]:
    task_by_id: dict[str, RealOssSelectedTask] = {}
    for task in tasks:
        if task.task_id in task_by_id:
            raise ValueError("duplicate task_id in tasks")
        task_by_id[task.task_id] = task
    return task_by_id


def _validate_selected_records(
    records: tuple[RealOssSelectedContextRecord, ...],
    *,
    field_name: str,
) -> None:
    if not isinstance(records, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if any(not isinstance(record, RealOssSelectedContextRecord) for record in records):
        raise ValueError(
            f"{field_name} must contain RealOssSelectedContextRecord values"
        )


def _validate_selections(
    selections: tuple[RealOssProviderBudgetSelection, ...],
    *,
    field_name: str,
) -> None:
    if not isinstance(selections, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if any(
        not isinstance(selection, RealOssProviderBudgetSelection)
        for selection in selections
    ):
        raise ValueError(
            f"{field_name} must contain RealOssProviderBudgetSelection values"
        )


def _validate_budget_scores(
    budget_scores: tuple[RealOssTaskBudgetScore, ...],
    *,
    field_name: str,
) -> None:
    if not isinstance(budget_scores, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if any(not isinstance(score, RealOssTaskBudgetScore) for score in budget_scores):
        raise ValueError(f"{field_name} must contain RealOssTaskBudgetScore values")
    if not budget_scores:
        raise ValueError(f"{field_name} must be non-empty")


def _validate_line_units(
    line_units: tuple[RealOssLineUnit, ...],
    *,
    field_name: str,
) -> None:
    if not isinstance(line_units, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if any(not isinstance(line_unit, RealOssLineUnit) for line_unit in line_units):
        raise ValueError(f"{field_name} must contain RealOssLineUnit values")
    if len(line_units) != len(set(line_units)):
        raise ValueError(f"{field_name} must not contain duplicates")


def _validate_provider_name(provider_name: str) -> None:
    if not isinstance(provider_name, str):
        raise ValueError("provider_name must be a string")
    if provider_name not in REAL_OSS_THESIS_PROVIDERS:
        raise ValueError("provider_name must be in the frozen provider set")


def _validate_budget(budget: int) -> None:
    _validate_positive_int(budget, field_name="budget")
    if budget not in REAL_OSS_THESIS_BUDGETS:
        raise ValueError("budget must be in the frozen budget set")


def _validate_repo_path(path: str, *, field_name: str) -> None:
    if not isinstance(path, str):
        raise ValueError(f"{field_name} must be a string")
    if not path:
        raise ValueError(f"{field_name} must be non-empty")
    if "\\" in path:
        raise ValueError(f"{field_name} must use POSIX separators")

    posix_path = PurePosixPath(path)
    if posix_path.as_posix() != path:
        raise ValueError(f"{field_name} must be a normalized POSIX path")
    if posix_path.is_absolute():
        raise ValueError(f"{field_name} must be repository-relative")
    if ".." in posix_path.parts:
        raise ValueError(f"{field_name} must not contain parent traversal")


def _validate_non_empty_string(value: str, *, field_name: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")


def _validate_positive_int(value: int, *, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_non_negative_int(value: int, *, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_non_negative_float(value: float, *, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    if value < 0.0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_fraction(value: float, *, field_name: str) -> None:
    _validate_non_negative_float(value, field_name=field_name)
    if value > 1.0:
        raise ValueError(f"{field_name} must be less than or equal to 1")


def _floats_close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def _dedupe_and_sort_line_units(
    line_units: Iterable[RealOssLineUnit],
) -> tuple[RealOssLineUnit, ...]:
    return tuple(sorted(set(line_units)))


def _selection_budget_sort_key(selection: RealOssProviderBudgetSelection) -> int:
    return _BUDGET_ORDER[selection.budget]


def _score_budget_sort_key(score: RealOssTaskBudgetScore) -> int:
    return _BUDGET_ORDER[score.budget]


def _task_provider_sort_key(task_provider: tuple[str, str]) -> tuple[str, int]:
    task_id, provider_name = task_provider
    return (task_id, _PROVIDER_ORDER[provider_name])


__all__ = [
    "RealOssLineUnit",
    "RealOssProviderBudgetSelection",
    "RealOssSelectedContextRecord",
    "RealOssTaskBudgetScore",
    "RealOssTaskProviderScore",
    "calculate_real_oss_recall_auc",
    "expand_real_oss_oracle_line_units",
    "expand_real_oss_selected_line_units",
    "score_real_oss_task_budget",
    "score_real_oss_task_provider",
    "score_real_oss_task_provider_batch",
]

"""Internal real-OSS thesis scoring contract tests."""

from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError

import pytest

import context_ir
import context_ir.real_oss_thesis_manifest as manifest
import context_ir.real_oss_thesis_scoring as scoring

_SHA_A = "a" * 40
_SHA_B = "b" * 40


def _task(
    task_id: str = "real_oss_thesis_v1:pallets__flask:pr-1",
    *,
    changed_python_paths: tuple[manifest.RealOssChangedPythonPath, ...] | None = None,
) -> manifest.RealOssSelectedTask:
    """Return one selected task with base-side oracle ranges."""
    return manifest.RealOssSelectedTask(
        task_id=task_id,
        repository_slug="pallets/flask",
        repository_url="https://github.com/pallets/flask",
        pr_number=1,
        base_sha=_SHA_A,
        head_sha=_SHA_B,
        query="Fix request handling without showing changed lines.",
        changed_python_paths=(
            changed_python_paths
            if changed_python_paths is not None
            else (
                manifest.RealOssChangedPythonPath(
                    path="pkg/a.py",
                    base_line_ranges=(
                        manifest.RealOssLineRange(10, 12),
                        manifest.RealOssLineRange(20, 20),
                    ),
                ),
                manifest.RealOssChangedPythonPath(
                    path="pkg/b.py",
                    base_line_ranges=(manifest.RealOssLineRange(5, 6),),
                ),
            )
        ),
        query_leakage_flags=manifest.RealOssQueryLeakageFlags(),
    )


def _record(
    path: str,
    start_line: int | None,
    end_line: int | None,
    token_count: int,
) -> scoring.RealOssSelectedContextRecord:
    """Return one selected context record."""
    return scoring.RealOssSelectedContextRecord(
        path=path,
        start_line=start_line,
        end_line=end_line,
        token_count=token_count,
    )


def _selection(
    task_id: str,
    *,
    provider_name: str = "context_ir_static",
    budget: int = 2000,
    records: tuple[scoring.RealOssSelectedContextRecord, ...] = (),
) -> scoring.RealOssProviderBudgetSelection:
    """Return one provider/budget selection."""
    return scoring.RealOssProviderBudgetSelection(
        task_id=task_id,
        provider_name=provider_name,
        budget=budget,
        selected_records=records,
    )


def _provider_selections(
    task_id: str,
    provider_name: str,
) -> tuple[scoring.RealOssProviderBudgetSelection, ...]:
    """Return empty selections for every frozen budget."""
    return tuple(
        _selection(task_id, provider_name=provider_name, budget=budget)
        for budget in manifest.REAL_OSS_THESIS_BUDGETS
    )


def test_dataclass_contracts_are_strict_and_frozen() -> None:
    """Scoring contracts reject malformed input and cannot be mutated."""
    line_unit = scoring.RealOssLineUnit("pkg/a.py", 1)

    with pytest.raises(FrozenInstanceError):
        line_unit.path = "pkg/b.py"  # type: ignore[misc]
    with pytest.raises(ValueError, match="repository-relative"):
        scoring.RealOssLineUnit("/pkg/a.py", 1)
    with pytest.raises(ValueError, match="parent traversal"):
        scoring.RealOssLineUnit("../pkg/a.py", 1)
    with pytest.raises(ValueError, match="POSIX"):
        scoring.RealOssLineUnit("pkg\\a.py", 1)
    with pytest.raises(ValueError, match="positive"):
        scoring.RealOssLineUnit("pkg/a.py", 0)
    with pytest.raises(ValueError, match="both be present"):
        _record("pkg/a.py", 1, None, 5)
    with pytest.raises(ValueError, match="positive"):
        _record("pkg/a.py", 1, 1, -1)
    with pytest.raises(ValueError, match="positive"):
        _record("pkg/a.py", 1, 1, 0)
    with pytest.raises(ValueError, match="greater than or equal"):
        _record("pkg/a.py", 2, 1, 1)
    with pytest.raises(ValueError, match="tuple"):
        scoring.RealOssProviderBudgetSelection(
            task_id=_task().task_id,
            provider_name="context_ir_static",
            budget=2000,
            selected_records=[],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="exceed budget"):
        _selection(
            _task().task_id,
            records=(_record("pkg/a.py", 1, 1, 2001),),
        )


def test_provider_and_budget_reject_non_frozen_values() -> None:
    """Provider names and token budgets must match the frozen manifest."""
    task = _task()

    with pytest.raises(ValueError, match="provider"):
        _selection(task.task_id, provider_name="reranker")
    with pytest.raises(ValueError, match="budget"):
        _selection(task.task_id, budget=3000)


def test_budget_score_rejects_selected_tokens_above_budget() -> None:
    """Frozen score records cannot manually exceed the selected budget."""
    line_unit = scoring.RealOssLineUnit("pkg/a.py", 10)

    with pytest.raises(ValueError, match="exceed budget"):
        scoring.RealOssTaskBudgetScore(
            task_id=_task().task_id,
            provider_name="context_ir_static",
            budget=2000,
            oracle_line_units=(line_unit,),
            covered_oracle_line_units=(line_unit,),
            edit_relevant_recall=1.0,
            selected_tokens=2001,
            wasted_tokens=0.0,
            waste_rate=0.0,
            is_valid_for_comparison=True,
        )


def test_oracle_line_unit_expansion_is_inclusive_unique_and_sorted() -> None:
    """Changed ranges expand into deterministic path/line oracle units."""
    task = _task(
        changed_python_paths=(
            manifest.RealOssChangedPythonPath(
                path="pkg/z.py",
                base_line_ranges=(
                    manifest.RealOssLineRange(4, 5),
                    manifest.RealOssLineRange(5, 6),
                ),
            ),
            manifest.RealOssChangedPythonPath(
                path="pkg/a.py",
                base_line_ranges=(manifest.RealOssLineRange(2, 2),),
            ),
        )
    )

    assert scoring.expand_real_oss_oracle_line_units(task) == (
        scoring.RealOssLineUnit("pkg/a.py", 2),
        scoring.RealOssLineUnit("pkg/z.py", 4),
        scoring.RealOssLineUnit("pkg/z.py", 5),
        scoring.RealOssLineUnit("pkg/z.py", 6),
    )


def test_coverage_and_edit_relevant_recall_are_deterministic() -> None:
    """Coverage uses unique oracle line units independent of record order."""
    task = _task()
    score = scoring.score_real_oss_task_budget(
        task,
        _selection(
            task.task_id,
            records=(
                _record("pkg/b.py", 99, 99, 10),
                _record("pkg/a.py", 20, 20, 5),
                _record("pkg/a.py", 10, 11, 20),
            ),
        ),
    )

    assert score.oracle_line_count == 6
    assert score.covered_oracle_line_units == (
        scoring.RealOssLineUnit("pkg/a.py", 10),
        scoring.RealOssLineUnit("pkg/a.py", 11),
        scoring.RealOssLineUnit("pkg/a.py", 20),
    )
    assert score.covered_oracle_line_count == 3
    assert score.edit_relevant_recall == pytest.approx(0.5)
    assert score.selected_tokens == 35
    assert score.wasted_tokens == pytest.approx(10.0)
    assert score.waste_rate == pytest.approx(10.0 / 35.0)
    assert score.is_valid_for_comparison


def test_selected_tokens_and_proportional_wasted_tokens_are_computed() -> None:
    """Multi-line records allocate token waste by non-overlapping line share."""
    task = _task()
    score = scoring.score_real_oss_task_budget(
        task,
        _selection(
            task.task_id,
            records=(
                _record("pkg/a.py", 10, 13, 40),
                _record("pkg/c.py", 1, 3, 9),
                _record("pkg/b.py", 4, 6, 30),
            ),
        ),
    )

    assert score.selected_tokens == 79
    assert score.wasted_tokens == pytest.approx(29.0)
    assert score.waste_rate == pytest.approx(29.0 / 79.0)


def test_zero_selected_tokens_are_invalid_with_undefined_waste_rate() -> None:
    """Zero selected tokens leave waste rate undefined for comparisons."""
    task = _task()
    score = scoring.score_real_oss_task_budget(task, _selection(task.task_id))

    assert score.selected_tokens == 0
    assert score.wasted_tokens == 0.0
    assert score.waste_rate is None
    assert not score.is_valid_for_comparison


def test_recall_auc_uses_frozen_budget_formula() -> None:
    """Recall AUC follows the pre-registered 2000/4000/8000 formula."""
    task = _task()
    provider_score = scoring.score_real_oss_task_provider(
        task,
        (
            _selection(
                task.task_id,
                budget=8000,
                records=(
                    _record("pkg/a.py", 10, 12, 30),
                    _record("pkg/a.py", 20, 20, 10),
                    _record("pkg/b.py", 5, 6, 20),
                ),
            ),
            _selection(
                task.task_id,
                budget=2000,
                records=(_record("pkg/a.py", 10, 10, 10),),
            ),
            _selection(
                task.task_id,
                budget=4000,
                records=(_record("pkg/a.py", 10, 12, 30),),
            ),
        ),
    )

    assert tuple(score.budget for score in provider_score.budget_scores) == (
        2000,
        4000,
        8000,
    )
    assert tuple(
        score.edit_relevant_recall for score in provider_score.budget_scores
    ) == pytest.approx((1.0 / 6.0, 3.0 / 6.0, 1.0))
    assert provider_score.recall_auc == pytest.approx(
        (1.0 / 6.0 + 2.0 * (3.0 / 6.0) + 1.0) / 4.0
    )
    assert scoring.calculate_real_oss_recall_auc(
        tuple(reversed(provider_score.budget_scores))
    ) == pytest.approx(provider_score.recall_auc)


def test_batch_scoring_returns_deterministic_result_ordering() -> None:
    """Batch scoring sorts task/provider outputs deterministically."""
    task_a = _task("task-a")
    task_b = _task("task-b")
    selections = (
        *_provider_selections(task_b.task_id, "bm25_chunks"),
        *_provider_selections(task_a.task_id, "embedding_chunks"),
        *_provider_selections(task_a.task_id, "context_ir_static"),
    )

    scores = scoring.score_real_oss_task_provider_batch(
        tasks=(task_b, task_a),
        selections=tuple(reversed(selections)),
    )

    assert tuple((score.task_id, score.provider_name) for score in scores) == (
        ("task-a", "context_ir_static"),
        ("task-a", "embedding_chunks"),
        ("task-b", "bm25_chunks"),
    )


def test_real_oss_scoring_contracts_remain_internal() -> None:
    """Scoring helpers are not package-root public API."""
    exported_names = set(scoring.__all__)

    assert exported_names.isdisjoint(set(context_ir.__all__))
    for exported_name in exported_names:
        assert not hasattr(context_ir, exported_name)


def test_contract_has_no_forbidden_runtime_or_analysis_dependencies() -> None:
    """The scoring module stays independent of disallowed experiment inputs."""
    source = inspect.getsource(scoring)
    forbidden_source_terms = (
        "eval_oracles",
        "eval_metrics",
        "eval_runs",
        "eval_summary",
        "eval_report",
        "eval_bundle",
        "eval_providers",
        "eval_pipeline",
        "fixtures",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "voyage",
        "api_key",
        "git",
    )

    for forbidden_source_term in forbidden_source_terms:
        assert forbidden_source_term not in source

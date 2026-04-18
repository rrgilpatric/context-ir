"""Focused methodology-tightening smoke eval asset tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import context_ir
import context_ir.eval_bundle as eval_bundle
import context_ir.eval_providers as eval_providers
import context_ir.eval_runs as eval_runs
import context_ir.semantic_types as semantic_types
from context_ir.eval_metrics import score_eval_run
from context_ir.eval_oracles import (
    FrontierOracleSelector,
    SymbolOracleSelector,
    UnsupportedOracleSelector,
    setup_eval_oracle_task,
)
from context_ir.eval_providers import EvalProviderRequest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_smoke"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_smoke.json"
RUN_SPEC_PATH = REPO_ROOT / "evals" / "run_specs" / "oracle_signal_smoke_matrix.json"
QUERY = "Fix missing step while keeping execution plan preview aligned"
TIGHT_BUDGET = 200
RELEVANT_SYMBOL_FILES = ("main.py", "pkg/planner.py", "pkg/presenter.py")


def _execute_signal_bundle(bundle_dir: Path) -> eval_bundle.EvalBundleArtifact:
    """Execute the signal-smoke run spec into one deterministic bundle."""
    return eval_bundle.execute_eval_bundle(
        RUN_SPEC_PATH,
        bundle_dir,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )


def _normalized_manifest(
    bundle: eval_bundle.EvalBundleArtifact,
) -> object:
    """Normalize caller-chosen artifact paths out of a bundle manifest."""
    return replace(
        bundle.manifest,
        ledger_path=Path("ledger.jsonl"),
        report_path=Path("report.md"),
    )


def _parsed_ledger_records(ledger_path: Path) -> list[dict[str, object]]:
    """Return parsed JSON objects from one JSONL ledger file."""
    return [
        cast(dict[str, object], json.loads(line))
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
    ]


def _provider_record_by_budget(
    records: list[dict[str, object]],
    *,
    provider_name: str,
    budget: int,
) -> dict[str, object]:
    """Return the unique raw ledger record for one provider/budget pair."""
    return next(
        record
        for record in records
        if record["provider_name"] == provider_name and record["budget"] == budget
    )


def _records_for_budget(
    records: list[dict[str, object]],
    budget: int,
) -> list[dict[str, object]]:
    """Return every raw ledger record for one budget."""
    return [record for record in records if record["budget"] == budget]


def test_signal_smoke_task_resolves_expected_selectors_deterministically() -> None:
    """The tightened signal smoke task resolves each intended selector once."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_smoke"
    assert setup.task.fixture_id == "oracle_signal_smoke"
    assert len(setup.task.expected_selectors) == 5
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[3], FrontierOracleSelector)
    assert isinstance(setup.task.expected_selectors[4], UnsupportedOracleSelector)

    assert (
        tuple(resolved.resolved_file_path for resolved in setup.resolved_selectors[:3])
        == RELEVANT_SYMBOL_FILES
    )
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.run_signal_smoke",
        "def:pkg/planner.py:pkg.planner.build_execution_plan",
        "def:pkg/presenter.py:pkg.presenter.render_patch_preview",
        "frontier:call:main.py:9:4",
        "unsupported:import:main.py:2:0:1:*:_",
    ]
    for resolved in setup.resolved_selectors:
        assert resolved.resolution_status == "resolved"
        assert resolved.candidate_count == 1
        assert resolved.failure_reason is None


def test_signal_smoke_run_spec_loads_cleanly_through_runner() -> None:
    """The tightened signal smoke run spec remains valid runner input."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_smoke_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_core_baselines"
    assert case.task_path == "evals/tasks/oracle_signal_smoke.json"
    assert case.query == QUERY
    assert case.budgets == (240, 200)
    assert case.providers == (
        eval_providers.CONTEXT_IR_PROVIDER,
        eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
        eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
    )


def test_signal_smoke_bundle_executes_deterministically_across_runs(
    tmp_path: Path,
) -> None:
    """Independent signal-smoke bundles match apart from chosen artifact paths."""
    first_bundle = _execute_signal_bundle(tmp_path / "first" / "bundle")
    second_bundle = _execute_signal_bundle(tmp_path / "second" / "bundle")

    assert first_bundle.manifest.plan_id == "oracle_signal_smoke_matrix"
    assert first_bundle.manifest.task_ids == ("oracle_signal_smoke",)
    assert first_bundle.manifest.provider_names == (
        "context_ir",
        "import_neighborhood_files",
        "lexical_top_k_files",
    )
    assert first_bundle.manifest.budgets == (200, 240)
    assert first_bundle.manifest.budget_violation_run_ids == ()
    assert first_bundle.pipeline_artifact.execution_result.record_count == 6
    assert second_bundle.pipeline_artifact.execution_result.record_count == 6

    assert first_bundle.paths.ledger_path.read_text(encoding="utf-8") == (
        second_bundle.paths.ledger_path.read_text(encoding="utf-8")
    )
    assert first_bundle.paths.report_path.read_text(encoding="utf-8") == (
        second_bundle.paths.report_path.read_text(encoding="utf-8")
    )
    assert _normalized_manifest(first_bundle) == _normalized_manifest(second_bundle)


def test_tight_budget_breaks_trivial_whole_file_saturation() -> None:
    """Tight budget prevents whole-file baselines from covering every symbol file."""
    setup = setup_eval_oracle_task(TASK_PATH)
    request = EvalProviderRequest(
        repo_root=FIXTURE_ROOT,
        task_id=setup.task.task_id,
        query=QUERY,
        budget=TIGHT_BUDGET,
    )
    relevant_symbol_files = frozenset(RELEVANT_SYMBOL_FILES)

    for result in (
        eval_providers.build_lexical_top_k_files_pack(request),
        eval_providers.build_import_neighborhood_files_pack(request),
    ):
        metrics = score_eval_run(setup, result)

        assert result.total_tokens <= TIGHT_BUDGET
        assert result.selected_files
        assert frozenset(result.selected_files).issubset(relevant_symbol_files)
        assert not relevant_symbol_files.issubset(result.selected_files)
        assert metrics.budget_compliant is True
        assert (
            metrics.adequate_edit_selectors + metrics.adequate_support_selectors
            < metrics.total_expected_edit_selectors
            + metrics.total_expected_support_selectors
        )
        assert metrics.support_coverage == 0.5


def test_signal_smoke_assets_stay_internal_and_leave_package_root_unchanged() -> None:
    """The new smoke assets remain under eval internals, not public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_smoke" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_smoke")


def test_signal_smoke_bundle_records_expected_tight_budget_baseline_gap(
    tmp_path: Path,
) -> None:
    """Bundle execution preserves the tight-budget baseline tradeoff in raw records."""
    bundle = _execute_signal_bundle(tmp_path / "bundle")
    records = _parsed_ledger_records(bundle.paths.ledger_path)
    tight_budget_baselines = [
        record
        for record in records
        if record["budget"] == TIGHT_BUDGET
        and record["provider_name"]
        in {
            eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
            eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
        }
    ]

    assert len(tight_budget_baselines) == 2
    for record in tight_budget_baselines:
        selected_files = frozenset(cast(list[str], record["selected_files"]))
        metrics = cast(dict[str, object], record["metrics"])
        assert not frozenset(RELEVANT_SYMBOL_FILES).issubset(selected_files)
        assert metrics["adequate_support_selectors"] == 1
        assert metrics["total_expected_support_selectors"] == 2


def test_signal_smoke_bundle_closes_context_ir_competitive_gap_across_budgets(
    tmp_path: Path,
) -> None:
    """The accepted runner path now closes the remaining smoke gap for Context IR."""
    bundle = _execute_signal_bundle(tmp_path / "bundle")
    records = _parsed_ledger_records(bundle.paths.ledger_path)
    expected_unit_ids_by_budget = {
        200: {
            "def:main.py:main.run_signal_smoke",
            "def:pkg/planner.py:pkg.planner.build_execution_plan",
            "def:pkg/presenter.py:pkg.presenter.render_patch_preview",
            "frontier:call:main.py:9:4",
            "unsupported:import:main.py:2:0:1:*:_",
        },
        240: {
            "def:main.py:main.run_signal_smoke",
            "def:pkg/planner.py:pkg.planner.build_execution_plan",
            "def:pkg/presenter.py:pkg.presenter.render_patch_preview",
            "frontier:call:main.py:9:4",
            "unsupported:import:main.py:2:0:1:*:_",
        },
    }

    for budget in (200, 240):
        budget_records = _records_for_budget(records, budget)
        budget_aggregates = sorted(
            (
                (
                    cast(
                        float,
                        cast(dict[str, object], record["metrics"])["aggregate_score"],
                    ),
                    cast(str, record["provider_name"]),
                )
                for record in budget_records
            ),
            reverse=True,
        )
        context_record = _provider_record_by_budget(
            records,
            provider_name=eval_providers.CONTEXT_IR_PROVIDER,
            budget=budget,
        )
        context_metrics = cast(dict[str, object], context_record["metrics"])
        context_metadata = cast(
            dict[str, object],
            context_record["provider_metadata"],
        )
        context_aggregate = cast(float, context_metrics["aggregate_score"])
        winning_aggregate = budget_aggregates[0][0]
        ranked_provider_names = [
            provider_name for _, provider_name in budget_aggregates
        ]

        assert cast(int, context_record["total_tokens"]) <= budget
        assert context_metrics["adequate_edit_selectors"] == 1
        assert context_metrics["edit_coverage"] == 1.0
        assert context_metrics["support_coverage"] == 1.0
        assert context_metrics["uncertainty_honesty"] == 1.0
        assert context_metrics["budget_compliant"] is True
        selected_unit_ids = cast(list[str], context_record["selected_unit_ids"])
        assert set(selected_unit_ids) == expected_unit_ids_by_budget[budget]
        assert cast(list[object], context_record["warnings"]) == []
        assert cast(list[object], context_metadata["selected_units"])
        assert winning_aggregate - context_aggregate <= 0.03
        assert ranked_provider_names[-1] != eval_providers.CONTEXT_IR_PROVIDER

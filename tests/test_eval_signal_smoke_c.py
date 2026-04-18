"""Third methodology-tightened signal eval asset tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import context_ir
import context_ir.eval_bundle as eval_bundle
import context_ir.eval_providers as eval_providers
import context_ir.eval_runs as eval_runs
import context_ir.eval_summary as eval_summary
import context_ir.semantic_types as semantic_types
from context_ir.eval_metrics import score_eval_run
from context_ir.eval_oracles import (
    FrontierOracleSelector,
    SymbolOracleSelector,
    setup_eval_oracle_task,
)
from context_ir.eval_providers import EvalProviderRequest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_smoke_c"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_smoke_c.json"
SINGLE_RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_smoke_c_matrix.json"
)
TRIPLE_RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_triple_matrix.json"
)
QUERY = "Fix missing handoff note while keeping owner alias and route summary aligned"
TIGHT_BUDGET = 200
RELEVANT_SYMBOL_FILES = (
    "main.py",
    "pkg/router.py",
    "pkg/registry.py",
    "pkg/summary.py",
)


def _execute_signal_smoke_c_bundle(bundle_dir: Path) -> eval_bundle.EvalBundleArtifact:
    """Execute the third signal-smoke run spec into one deterministic bundle."""
    return eval_bundle.execute_eval_bundle(
        SINGLE_RUN_SPEC_PATH,
        bundle_dir,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )


def _execute_signal_triple_bundle(bundle_dir: Path) -> eval_bundle.EvalBundleArtifact:
    """Execute the three-asset signal run spec into one deterministic bundle."""
    return eval_bundle.execute_eval_bundle(
        TRIPLE_RUN_SPEC_PATH,
        bundle_dir,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )


def _normalized_manifest(bundle: eval_bundle.EvalBundleArtifact) -> object:
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


def _provider_record_by_task_budget(
    records: list[dict[str, object]],
    *,
    task_id: str,
    provider_name: str,
    budget: int,
) -> dict[str, object]:
    """Return the unique raw ledger record for one task/provider/budget row."""
    return next(
        record
        for record in records
        if record["task_id"] == task_id
        and record["provider_name"] == provider_name
        and record["budget"] == budget
    )


def test_signal_smoke_c_task_resolves_expected_selectors_deterministically() -> None:
    """The third tightened signal task resolves each intended selector once."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_smoke_c"
    assert setup.task.fixture_id == "oracle_signal_smoke_c"
    assert len(setup.task.expected_selectors) == 5
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[3], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[4], FrontierOracleSelector)

    assert (
        tuple(resolved.resolved_file_path for resolved in setup.resolved_selectors[:4])
        == RELEVANT_SYMBOL_FILES
    )
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.run_signal_smoke_c",
        "def:pkg/router.py:pkg.router.build_handoff_route",
        "def:pkg/registry.py:pkg.registry.resolve_owner_alias",
        "def:pkg/summary.py:pkg.summary.render_route_summary",
        "frontier:call:pkg/router.py:7:4",
    ]
    for resolved in setup.resolved_selectors:
        assert resolved.resolution_status == "resolved"
        assert resolved.candidate_count == 1
        assert resolved.failure_reason is None


def test_signal_smoke_c_run_specs_load_cleanly_through_runner() -> None:
    """The new single-asset and triple-matrix run specs remain valid runner input."""
    single_spec = eval_runs.load_eval_run_spec(SINGLE_RUN_SPEC_PATH)
    triple_spec = eval_runs.load_eval_run_spec(TRIPLE_RUN_SPEC_PATH)

    assert single_spec.plan_id == "oracle_signal_smoke_c_matrix"
    assert len(single_spec.cases) == 1
    single_case = single_spec.cases[0]
    assert single_case.case_id == "signal_handoff_baselines"
    assert single_case.task_path == "evals/tasks/oracle_signal_smoke_c.json"
    assert single_case.query == QUERY
    assert single_case.budgets == (240, 200)
    assert single_case.providers == (
        eval_providers.CONTEXT_IR_PROVIDER,
        eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
        eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
    )

    assert triple_spec.plan_id == "oracle_signal_triple_matrix"
    assert len(triple_spec.cases) == 3
    assert [case.case_id for case in triple_spec.cases] == [
        "signal_core_baselines",
        "signal_digest_baselines",
        "signal_handoff_baselines",
    ]
    assert [case.task_path for case in triple_spec.cases] == [
        "evals/tasks/oracle_signal_smoke.json",
        "evals/tasks/oracle_signal_smoke_b.json",
        "evals/tasks/oracle_signal_smoke_c.json",
    ]
    assert [case.budgets for case in triple_spec.cases] == [
        (240, 200),
        (240, 200),
        (240, 200),
    ]
    assert all(
        case.providers
        == (
            eval_providers.CONTEXT_IR_PROVIDER,
            eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
            eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
        )
        for case in triple_spec.cases
    )


def test_signal_smoke_c_bundle_executes_deterministically_across_runs(
    tmp_path: Path,
) -> None:
    """Independent single-asset bundles match apart from chosen artifact paths."""
    first_bundle = _execute_signal_smoke_c_bundle(tmp_path / "first" / "bundle")
    second_bundle = _execute_signal_smoke_c_bundle(tmp_path / "second" / "bundle")

    assert first_bundle.manifest.plan_id == "oracle_signal_smoke_c_matrix"
    assert first_bundle.manifest.task_ids == ("oracle_signal_smoke_c",)
    assert first_bundle.manifest.provider_names == (
        "context_ir",
        "import_neighborhood_files",
        "lexical_top_k_files",
    )
    assert first_bundle.manifest.budgets == (200, 240)
    assert first_bundle.pipeline_artifact.execution_result.record_count == 6
    assert second_bundle.pipeline_artifact.execution_result.record_count == 6

    assert first_bundle.paths.ledger_path.read_text(encoding="utf-8") == (
        second_bundle.paths.ledger_path.read_text(encoding="utf-8")
    )
    assert first_bundle.paths.report_path.read_text(encoding="utf-8") == (
        second_bundle.paths.report_path.read_text(encoding="utf-8")
    )
    assert _normalized_manifest(first_bundle) == _normalized_manifest(second_bundle)


def test_signal_triple_bundle_executes_deterministically_across_runs(
    tmp_path: Path,
) -> None:
    """Independent triple-matrix bundles match apart from chosen artifact paths."""
    first_bundle = _execute_signal_triple_bundle(tmp_path / "first" / "bundle")
    second_bundle = _execute_signal_triple_bundle(tmp_path / "second" / "bundle")
    first_records = _parsed_ledger_records(first_bundle.paths.ledger_path)

    assert first_bundle.manifest.plan_id == "oracle_signal_triple_matrix"
    assert first_bundle.manifest.task_ids == (
        "oracle_signal_smoke",
        "oracle_signal_smoke_b",
        "oracle_signal_smoke_c",
    )
    assert first_bundle.manifest.provider_names == (
        "context_ir",
        "import_neighborhood_files",
        "lexical_top_k_files",
    )
    assert first_bundle.manifest.budgets == (200, 240)
    assert first_bundle.pipeline_artifact.execution_result.record_count == 18
    assert second_bundle.pipeline_artifact.execution_result.record_count == 18
    assert len(first_records) == 18
    assert (
        sum(1 for record in first_records if record["task_id"] == "oracle_signal_smoke")
        == 6
    )
    assert (
        sum(
            1
            for record in first_records
            if record["task_id"] == "oracle_signal_smoke_b"
        )
        == 6
    )
    assert (
        sum(
            1
            for record in first_records
            if record["task_id"] == "oracle_signal_smoke_c"
        )
        == 6
    )

    assert first_bundle.paths.ledger_path.read_text(encoding="utf-8") == (
        second_bundle.paths.ledger_path.read_text(encoding="utf-8")
    )
    assert first_bundle.paths.report_path.read_text(encoding="utf-8") == (
        second_bundle.paths.report_path.read_text(encoding="utf-8")
    )
    assert _normalized_manifest(first_bundle) == _normalized_manifest(second_bundle)


def test_tight_budget_breaks_trivial_whole_file_saturation_for_signal_smoke_c() -> None:
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
        assert frozenset(result.metadata.candidate_files).issuperset(
            relevant_symbol_files
        )
        assert frozenset(result.selected_files).issubset(relevant_symbol_files)
        assert not relevant_symbol_files.issubset(result.selected_files)
        assert frozenset(result.omitted_candidate_files) & relevant_symbol_files
        assert metrics.budget_compliant is True
        assert (
            metrics.adequate_edit_selectors + metrics.adequate_support_selectors
            < metrics.total_expected_edit_selectors
            + metrics.total_expected_support_selectors
        )
        assert metrics.total_expected_support_selectors == 3


def test_signal_smoke_c_assets_stay_internal_and_leave_package_root_unchanged() -> None:
    """The new signal assets remain under eval internals, not public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert SINGLE_RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert TRIPLE_RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_smoke_c" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_smoke_c")


def test_signal_triple_bundle_recovers_context_ir_on_smoke_c_without_regressions(
    tmp_path: Path,
) -> None:
    """The accepted triple bundle recovers smoke_c while preserving prior wins."""
    bundle = _execute_signal_triple_bundle(tmp_path / "bundle")
    records = _parsed_ledger_records(bundle.paths.ledger_path)
    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(bundle.paths.ledger_path)
    )
    smoke_c_expected_unit_ids = {
        "def:main.py:main.run_signal_smoke_c",
        "def:pkg/router.py:pkg.router.build_handoff_route",
        "def:pkg/registry.py:pkg.registry.resolve_owner_alias",
        "def:pkg/summary.py:pkg.summary.render_route_summary",
        "frontier:call:pkg/router.py:7:4",
    }

    smoke_c_240_context = _provider_record_by_task_budget(
        records,
        task_id="oracle_signal_smoke_c",
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=240,
    )
    smoke_c_240_metrics = cast(dict[str, object], smoke_c_240_context["metrics"])
    smoke_c_240_metadata = cast(
        dict[str, object],
        smoke_c_240_context["provider_metadata"],
    )
    smoke_c_240_aggregate = cast(float, smoke_c_240_metrics["aggregate_score"])
    smoke_c_240_baselines = [
        _provider_record_by_task_budget(
            records,
            task_id="oracle_signal_smoke_c",
            provider_name=provider_name,
            budget=240,
        )
        for provider_name in (
            eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
            eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
        )
    ]

    assert cast(int, smoke_c_240_context["total_tokens"]) <= 240
    assert smoke_c_240_metrics["edit_coverage"] == 1.0
    smoke_c_240_selected_unit_ids = cast(
        list[str],
        smoke_c_240_context["selected_unit_ids"],
    )
    assert smoke_c_240_metrics["support_coverage"] == 1.0
    assert cast(float, smoke_c_240_metrics["uncertainty_honesty"]) == 1.0
    assert set(smoke_c_240_selected_unit_ids) == smoke_c_expected_unit_ids
    assert cast(list[object], smoke_c_240_context["warnings"]) == []
    assert any(
        cast(str, selected_unit["unit_id"]) == "def:main.py:main.run_signal_smoke_c"
        for selected_unit in cast(
            list[dict[str, object]],
            smoke_c_240_metadata["selected_units"],
        )
    )
    assert all(
        cast(str, warning["unit_id"]) != "frontier:call:pkg/router.py:7:4"
        for warning in cast(
            list[dict[str, object]],
            smoke_c_240_metadata["warning_details"],
        )
    )
    assert all(
        smoke_c_240_aggregate
        >= cast(float, cast(dict[str, object], baseline["metrics"])["aggregate_score"])
        for baseline in smoke_c_240_baselines
    )

    smoke_c_200_context = _provider_record_by_task_budget(
        records,
        task_id="oracle_signal_smoke_c",
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=200,
    )
    smoke_c_200_metrics = cast(dict[str, object], smoke_c_200_context["metrics"])
    smoke_c_200_selected_unit_ids = cast(
        list[str],
        smoke_c_200_context["selected_unit_ids"],
    )
    assert cast(int, smoke_c_200_context["total_tokens"]) <= 200
    assert smoke_c_200_metrics["budget_compliant"] is True
    assert smoke_c_200_metrics["edit_coverage"] == 1.0
    assert smoke_c_200_metrics["support_coverage"] == 1.0
    assert cast(float, smoke_c_200_metrics["uncertainty_honesty"]) == 1.0
    assert set(smoke_c_200_selected_unit_ids) == smoke_c_expected_unit_ids
    assert cast(list[object], smoke_c_200_context["warnings"]) == []

    smoke_support_expectations = {
        200: 1.0,
        240: 1.0,
    }
    for budget, expected_support in smoke_support_expectations.items():
        smoke_record = _provider_record_by_task_budget(
            records,
            task_id="oracle_signal_smoke",
            provider_name=eval_providers.CONTEXT_IR_PROVIDER,
            budget=budget,
        )
        smoke_metrics = cast(dict[str, object], smoke_record["metrics"])

        assert smoke_metrics["support_coverage"] == expected_support

    smoke_b_200_record = _provider_record_by_task_budget(
        records,
        task_id="oracle_signal_smoke_b",
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=200,
    )
    smoke_b_200_metrics = cast(dict[str, object], smoke_b_200_record["metrics"])
    smoke_b_200_selected_unit_ids = cast(
        list[str], smoke_b_200_record["selected_unit_ids"]
    )
    assert smoke_b_200_metrics["edit_coverage"] == 1.0
    assert cast(float, smoke_b_200_metrics["support_coverage"]) >= (2.0 / 3.0)
    assert smoke_b_200_metrics["uncertainty_honesty"] == 1.0
    assert "def:main.py:main.run_signal_smoke_b" in smoke_b_200_selected_unit_ids
    assert "frontier:call:main.py:10:4" in smoke_b_200_selected_unit_ids
    assert (
        "def:pkg/collector.py:pkg.collector.collect_signal_rows"
        in smoke_b_200_selected_unit_ids
    )

    smoke_b_240_record = _provider_record_by_task_budget(
        records,
        task_id="oracle_signal_smoke_b",
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=240,
    )
    smoke_b_240_metrics = cast(dict[str, object], smoke_b_240_record["metrics"])
    smoke_b_240_selected_unit_ids = cast(
        list[str], smoke_b_240_record["selected_unit_ids"]
    )
    assert smoke_b_240_metrics["support_coverage"] == 1.0
    assert "def:main.py:main.run_signal_smoke_b" in smoke_b_240_selected_unit_ids
    assert "frontier:call:main.py:10:4" in smoke_b_240_selected_unit_ids
    assert (
        "def:pkg/collector.py:pkg.collector.collect_signal_rows"
        in smoke_b_240_selected_unit_ids
    )

    provider_aggregate_scores = {
        aggregate.provider_name: aggregate.average_aggregate_score
        for aggregate in summary.provider_aggregates
    }
    top_provider_name = max(
        provider_aggregate_scores,
        key=provider_aggregate_scores.__getitem__,
    )

    assert all(
        task_budget_result.winner_provider_names
        == (eval_providers.CONTEXT_IR_PROVIDER,)
        for task_budget_result in summary.task_budget_results
    )
    assert provider_aggregate_scores[eval_providers.CONTEXT_IR_PROVIDER] >= 0.972
    assert top_provider_name == eval_providers.CONTEXT_IR_PROVIDER

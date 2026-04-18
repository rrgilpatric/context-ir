"""Second methodology-tightened signal eval asset tests."""

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
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_smoke_b"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_smoke_b.json"
SINGLE_RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_smoke_b_matrix.json"
)
PAIR_RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_pair_matrix.json"
)
QUERY = (
    "Fix missing assignment note while keeping signal digest and priority labels "
    "aligned"
)
TIGHT_BUDGET = 200
RELEVANT_SYMBOL_FILES = (
    "main.py",
    "pkg/collector.py",
    "pkg/labels.py",
    "pkg/digest.py",
)


def _execute_signal_smoke_b_bundle(bundle_dir: Path) -> eval_bundle.EvalBundleArtifact:
    """Execute the second signal-smoke run spec into one deterministic bundle."""
    return eval_bundle.execute_eval_bundle(
        SINGLE_RUN_SPEC_PATH,
        bundle_dir,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )


def _execute_signal_pair_bundle(bundle_dir: Path) -> eval_bundle.EvalBundleArtifact:
    """Execute the two-asset signal pair run spec into one deterministic bundle."""
    return eval_bundle.execute_eval_bundle(
        PAIR_RUN_SPEC_PATH,
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


def test_signal_smoke_b_task_resolves_expected_selectors_deterministically() -> None:
    """The second tightened signal task resolves each intended selector once."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_smoke_b"
    assert setup.task.fixture_id == "oracle_signal_smoke_b"
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
        "def:main.py:main.run_signal_smoke_b",
        "def:pkg/collector.py:pkg.collector.collect_signal_rows",
        "def:pkg/labels.py:pkg.labels.build_priority_labels",
        "def:pkg/digest.py:pkg.digest.render_assignment_digest",
        "frontier:call:main.py:10:4",
    ]
    for resolved in setup.resolved_selectors:
        assert resolved.resolution_status == "resolved"
        assert resolved.candidate_count == 1
        assert resolved.failure_reason is None


def test_signal_smoke_b_run_specs_load_cleanly_through_runner() -> None:
    """The new single-asset and pair-matrix run specs remain valid runner input."""
    single_spec = eval_runs.load_eval_run_spec(SINGLE_RUN_SPEC_PATH)
    pair_spec = eval_runs.load_eval_run_spec(PAIR_RUN_SPEC_PATH)

    assert single_spec.plan_id == "oracle_signal_smoke_b_matrix"
    assert len(single_spec.cases) == 1
    single_case = single_spec.cases[0]
    assert single_case.case_id == "signal_digest_baselines"
    assert single_case.task_path == "evals/tasks/oracle_signal_smoke_b.json"
    assert single_case.query == QUERY
    assert single_case.budgets == (240, 200)
    assert single_case.providers == (
        eval_providers.CONTEXT_IR_PROVIDER,
        eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
        eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
    )

    assert pair_spec.plan_id == "oracle_signal_pair_matrix"
    assert len(pair_spec.cases) == 2
    assert [case.case_id for case in pair_spec.cases] == [
        "signal_core_baselines",
        "signal_digest_baselines",
    ]
    assert [case.task_path for case in pair_spec.cases] == [
        "evals/tasks/oracle_signal_smoke.json",
        "evals/tasks/oracle_signal_smoke_b.json",
    ]
    assert [case.budgets for case in pair_spec.cases] == [(240, 200), (240, 200)]
    assert all(
        case.providers
        == (
            eval_providers.CONTEXT_IR_PROVIDER,
            eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
            eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
        )
        for case in pair_spec.cases
    )


def test_signal_smoke_b_bundle_executes_deterministically_across_runs(
    tmp_path: Path,
) -> None:
    """Independent single-asset bundles match apart from chosen artifact paths."""
    first_bundle = _execute_signal_smoke_b_bundle(tmp_path / "first" / "bundle")
    second_bundle = _execute_signal_smoke_b_bundle(tmp_path / "second" / "bundle")

    assert first_bundle.manifest.plan_id == "oracle_signal_smoke_b_matrix"
    assert first_bundle.manifest.task_ids == ("oracle_signal_smoke_b",)
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


def test_signal_pair_bundle_executes_deterministically_across_runs(
    tmp_path: Path,
) -> None:
    """Independent pair bundles match apart from chosen artifact paths."""
    first_bundle = _execute_signal_pair_bundle(tmp_path / "first" / "bundle")
    second_bundle = _execute_signal_pair_bundle(tmp_path / "second" / "bundle")
    first_records = _parsed_ledger_records(first_bundle.paths.ledger_path)

    assert first_bundle.manifest.plan_id == "oracle_signal_pair_matrix"
    assert first_bundle.manifest.task_ids == (
        "oracle_signal_smoke",
        "oracle_signal_smoke_b",
    )
    assert first_bundle.manifest.provider_names == (
        "context_ir",
        "import_neighborhood_files",
        "lexical_top_k_files",
    )
    assert first_bundle.manifest.budgets == (200, 240)
    assert first_bundle.pipeline_artifact.execution_result.record_count == 12
    assert second_bundle.pipeline_artifact.execution_result.record_count == 12
    assert len(first_records) == 12
    assert (
        sum(
            1
            for record in first_records
            if record["task_id"] == "oracle_signal_smoke_b"
        )
        == 6
    )
    assert (
        sum(1 for record in first_records if record["task_id"] == "oracle_signal_smoke")
        == 6
    )

    assert first_bundle.paths.ledger_path.read_text(encoding="utf-8") == (
        second_bundle.paths.ledger_path.read_text(encoding="utf-8")
    )
    assert first_bundle.paths.report_path.read_text(encoding="utf-8") == (
        second_bundle.paths.report_path.read_text(encoding="utf-8")
    )
    assert _normalized_manifest(first_bundle) == _normalized_manifest(second_bundle)


def test_tight_budget_breaks_trivial_whole_file_saturation_for_signal_smoke_b() -> None:
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
        assert relevant_symbol_files.issubset(result.metadata.candidate_files)
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


def test_signal_smoke_b_assets_stay_internal_and_leave_package_root_unchanged() -> None:
    """The new signal assets remain under eval internals, not public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert SINGLE_RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert PAIR_RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_smoke_b" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_smoke_b")


def test_signal_pair_bundle_recovers_context_ir_on_smoke_b_without_regressing_smoke(
    tmp_path: Path,
) -> None:
    """The accepted pair bundle now recovers smoke_b while preserving smoke."""
    bundle = _execute_signal_pair_bundle(tmp_path / "bundle")
    records = _parsed_ledger_records(bundle.paths.ledger_path)
    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(bundle.paths.ledger_path)
    )
    smoke_b_expectations = {
        200: {"aggregate_min": 0.20, "honesty_min": 1.0},
        240: {"aggregate_min": 0.35, "honesty_min": 1.0},
    }
    smoke_b_floor_unit_ids = {
        "def:main.py:main.run_signal_smoke_b",
        "def:pkg/collector.py:pkg.collector.collect_signal_rows",
        "def:pkg/labels.py:pkg.labels.build_priority_labels",
        "frontier:call:main.py:10:4",
    }
    smoke_b_clean_unit_ids = {
        *smoke_b_floor_unit_ids,
        "def:pkg/digest.py:pkg.digest.render_assignment_digest",
    }

    for budget, expectation in smoke_b_expectations.items():
        context_record = _provider_record_by_task_budget(
            records,
            task_id="oracle_signal_smoke_b",
            provider_name=eval_providers.CONTEXT_IR_PROVIDER,
            budget=budget,
        )
        context_metrics = cast(dict[str, object], context_record["metrics"])
        context_metadata = cast(
            dict[str, object],
            context_record["provider_metadata"],
        )

        assert cast(int, context_record["total_tokens"]) <= budget
        assert cast(list[object], context_record["selected_unit_ids"])
        assert cast(list[object], context_metadata["selected_units"])
        assert context_metrics["adequate_edit_selectors"] == 1
        assert context_metrics["edit_coverage"] == 1.0
        assert cast(float, context_metrics["representation_adequacy"]) > 0.0
        assert (
            cast(float, context_metrics["aggregate_score"])
            > expectation["aggregate_min"]
        )
        assert (
            cast(float, context_metrics["uncertainty_honesty"])
            >= expectation["honesty_min"]
        )
        selected_unit_ids = cast(list[str], context_record["selected_unit_ids"])
        assert "def:main.py:main.run_signal_smoke_b" in selected_unit_ids
        assert "frontier:call:main.py:10:4" in selected_unit_ids
        assert (
            "def:pkg/collector.py:pkg.collector.collect_signal_rows"
            in selected_unit_ids
        )
        if budget == 200:
            assert smoke_b_floor_unit_ids.issubset(selected_unit_ids)
            assert cast(float, context_metrics["support_coverage"]) >= (2.0 / 3.0)
            assert "frontier:call:pkg/collector.py:2:20" not in selected_unit_ids
        if budget == 240:
            assert set(selected_unit_ids) == smoke_b_clean_unit_ids
            assert context_metrics["support_coverage"] == 1.0
            assert cast(list[object], context_record["warnings"]) == []

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

    provider_aggregate_scores = {
        aggregate.provider_name: aggregate.average_aggregate_score
        for aggregate in summary.provider_aggregates
    }
    top_provider_name = max(
        provider_aggregate_scores,
        key=provider_aggregate_scores.__getitem__,
    )

    assert top_provider_name == eval_providers.CONTEXT_IR_PROVIDER

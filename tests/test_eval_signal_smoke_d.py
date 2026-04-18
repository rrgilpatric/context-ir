"""Fourth methodology-tightened signal eval asset tests."""

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
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_smoke_d"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_smoke_d.json"
SINGLE_RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_smoke_d_matrix.json"
)
QUAD_RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_quad_matrix.json"
)
QUERY = (
    "Fix missing digest note while keeping inherited formatter, review envelope, "
    "and presenter aligned"
)
TIGHT_BUDGET = 200
RELEVANT_SYMBOL_FILES = (
    "pkg/service.py",
    "pkg/base.py",
    "pkg/models.py",
)


def _execute_signal_smoke_d_bundle(bundle_dir: Path) -> eval_bundle.EvalBundleArtifact:
    """Execute the fourth signal-smoke run spec into one deterministic bundle."""
    return eval_bundle.execute_eval_bundle(
        SINGLE_RUN_SPEC_PATH,
        bundle_dir,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )


def _execute_signal_quad_bundle(bundle_dir: Path) -> eval_bundle.EvalBundleArtifact:
    """Execute the four-asset signal run spec into one deterministic bundle."""
    return eval_bundle.execute_eval_bundle(
        QUAD_RUN_SPEC_PATH,
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


def test_signal_smoke_d_task_resolves_expected_selectors_deterministically() -> None:
    """The fourth tightened signal task resolves each intended selector once."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_smoke_d"
    assert setup.task.fixture_id == "oracle_signal_smoke_d"
    assert len(setup.task.expected_selectors) == 4
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[3], FrontierOracleSelector)

    assert (
        tuple(resolved.resolved_file_path for resolved in setup.resolved_selectors[:3])
        == RELEVANT_SYMBOL_FILES
    )
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:pkg/service.py:pkg.service.EnvelopeCompiler.compile_digest",
        "def:pkg/base.py:pkg.base.LayoutBase",
        "def:pkg/models.py:pkg.models.ReviewEnvelope",
        "frontier:call:pkg/service.py:13:8",
    ]
    for resolved in setup.resolved_selectors:
        assert resolved.resolution_status == "resolved"
        assert resolved.candidate_count == 1
        assert resolved.failure_reason is None


def test_signal_smoke_d_run_specs_load_cleanly_through_runner() -> None:
    """The new single-asset and quad-matrix run specs remain valid runner input."""
    single_spec = eval_runs.load_eval_run_spec(SINGLE_RUN_SPEC_PATH)
    quad_spec = eval_runs.load_eval_run_spec(QUAD_RUN_SPEC_PATH)

    assert single_spec.plan_id == "oracle_signal_smoke_d_matrix"
    assert len(single_spec.cases) == 1
    single_case = single_spec.cases[0]
    assert single_case.case_id == "signal_method_baselines"
    assert single_case.task_path == "evals/tasks/oracle_signal_smoke_d.json"
    assert single_case.query == QUERY
    assert single_case.budgets == (240, 200)
    assert single_case.providers == (
        eval_providers.CONTEXT_IR_PROVIDER,
        eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
        eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
    )

    assert quad_spec.plan_id == "oracle_signal_quad_matrix"
    assert len(quad_spec.cases) == 4
    assert [case.case_id for case in quad_spec.cases] == [
        "signal_core_baselines",
        "signal_digest_baselines",
        "signal_handoff_baselines",
        "signal_method_baselines",
    ]
    assert [case.task_path for case in quad_spec.cases] == [
        "evals/tasks/oracle_signal_smoke.json",
        "evals/tasks/oracle_signal_smoke_b.json",
        "evals/tasks/oracle_signal_smoke_c.json",
        "evals/tasks/oracle_signal_smoke_d.json",
    ]
    assert [case.budgets for case in quad_spec.cases] == [
        (240, 200),
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
        for case in quad_spec.cases
    )


def test_signal_smoke_d_bundle_executes_deterministically_across_runs(
    tmp_path: Path,
) -> None:
    """Independent single-asset bundles match apart from chosen artifact paths."""
    first_bundle = _execute_signal_smoke_d_bundle(tmp_path / "first" / "bundle")
    second_bundle = _execute_signal_smoke_d_bundle(tmp_path / "second" / "bundle")

    assert first_bundle.manifest.plan_id == "oracle_signal_smoke_d_matrix"
    assert first_bundle.manifest.task_ids == ("oracle_signal_smoke_d",)
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


def test_signal_quad_bundle_executes_deterministically_across_runs(
    tmp_path: Path,
) -> None:
    """Independent quad-matrix bundles match apart from chosen artifact paths."""
    first_bundle = _execute_signal_quad_bundle(tmp_path / "first" / "bundle")
    second_bundle = _execute_signal_quad_bundle(tmp_path / "second" / "bundle")
    first_records = _parsed_ledger_records(first_bundle.paths.ledger_path)

    assert first_bundle.manifest.plan_id == "oracle_signal_quad_matrix"
    assert first_bundle.manifest.task_ids == (
        "oracle_signal_smoke",
        "oracle_signal_smoke_b",
        "oracle_signal_smoke_c",
        "oracle_signal_smoke_d",
    )
    assert first_bundle.manifest.provider_names == (
        "context_ir",
        "import_neighborhood_files",
        "lexical_top_k_files",
    )
    assert first_bundle.manifest.budgets == (200, 240)
    assert first_bundle.pipeline_artifact.execution_result.record_count == 24
    assert second_bundle.pipeline_artifact.execution_result.record_count == 24
    assert len(first_records) == 24
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
    assert (
        sum(
            1
            for record in first_records
            if record["task_id"] == "oracle_signal_smoke_d"
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


def test_tight_budget_breaks_trivial_whole_file_saturation_for_signal_smoke_d() -> None:
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
        assert frozenset(result.selected_files).issubset(
            frozenset(result.metadata.candidate_files)
        )
        assert metrics.budget_compliant is True
        assert (
            metrics.adequate_edit_selectors + metrics.adequate_support_selectors
            < metrics.total_expected_edit_selectors
            + metrics.total_expected_support_selectors
        )
        assert metrics.total_expected_support_selectors == 2


def test_signal_smoke_d_assets_stay_internal_and_leave_package_root_unchanged() -> None:
    """The new signal assets remain under eval internals, not public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert SINGLE_RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert QUAD_RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_smoke_d" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_smoke_d")


def test_signal_quad_bundle_preserves_provider_lead_and_smoke_b_budget_pressure(
    tmp_path: Path,
) -> None:
    """The quad bundle adds smoke_d without reopening the accepted smoke_b blemish."""
    bundle = _execute_signal_quad_bundle(tmp_path / "bundle")
    records = _parsed_ledger_records(bundle.paths.ledger_path)
    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(bundle.paths.ledger_path)
    )
    smoke_d_expected_unit_ids = {
        200: {
            "def:pkg/service.py:pkg.service.EnvelopeCompiler.compile_digest",
            "def:pkg/models.py:pkg.models.ReviewEnvelope",
            "frontier:call:pkg/service.py:13:8",
            "unsupported:call:pkg/service.py:12:17",
            "frontier:call:pkg/service.py:12:17",
        },
        240: {
            "def:pkg/service.py:pkg.service.EnvelopeCompiler.compile_digest",
            "def:pkg/models.py:pkg.models.ReviewEnvelope",
            "def:pkg/base.py:pkg.base.LayoutBase",
            "def:pkg/base.py:pkg.base.LayoutBase.format_digest",
            "frontier:call:pkg/service.py:13:8",
            "unsupported:call:pkg/service.py:12:17",
            "frontier:call:pkg/service.py:12:17",
        },
    }
    smoke_d_expected_support_coverage = {
        200: 0.5,
        240: 1.0,
    }
    smoke_d_expected_warnings = {
        200: [],
        240: [],
    }

    for budget in (200, 240):
        smoke_d_record = _provider_record_by_task_budget(
            records,
            task_id="oracle_signal_smoke_d",
            provider_name=eval_providers.CONTEXT_IR_PROVIDER,
            budget=budget,
        )
        smoke_d_metrics = cast(dict[str, object], smoke_d_record["metrics"])
        smoke_d_metadata = cast(
            dict[str, object],
            smoke_d_record["provider_metadata"],
        )
        smoke_d_aggregate = cast(float, smoke_d_metrics["aggregate_score"])
        smoke_d_baselines = [
            _provider_record_by_task_budget(
                records,
                task_id="oracle_signal_smoke_d",
                provider_name=provider_name,
                budget=budget,
            )
            for provider_name in (
                eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
                eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
            )
        ]

        assert cast(int, smoke_d_record["total_tokens"]) <= budget
        assert smoke_d_metrics["budget_compliant"] is True
        assert smoke_d_metrics["adequate_edit_selectors"] == 1
        assert cast(int, smoke_d_metrics["adequate_support_selectors"]) == (
            1 if budget == 200 else 2
        )
        assert smoke_d_metrics["edit_coverage"] == 1.0
        assert (
            cast(float, smoke_d_metrics["support_coverage"])
            == (smoke_d_expected_support_coverage[budget])
        )
        assert cast(float, smoke_d_metrics["uncertainty_honesty"]) == 1.0
        smoke_d_selected_unit_ids = cast(list[str], smoke_d_record["selected_unit_ids"])
        assert set(smoke_d_selected_unit_ids) == smoke_d_expected_unit_ids[budget]
        assert (
            cast(list[object], smoke_d_record["warnings"])
            == (smoke_d_expected_warnings[budget])
        )
        assert cast(list[object], smoke_d_metadata["selected_units"])
        assert all(
            smoke_d_aggregate
            >= cast(
                float,
                cast(dict[str, object], baseline["metrics"])["aggregate_score"],
            )
            for baseline in smoke_d_baselines
        )

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
    assert cast(list[object], smoke_b_200_record["warnings"]) == ["budget_pressure"]
    assert "def:main.py:main.run_signal_smoke_b" in smoke_b_200_selected_unit_ids
    assert "frontier:call:main.py:10:4" in smoke_b_200_selected_unit_ids
    assert (
        "def:pkg/collector.py:pkg.collector.collect_signal_rows"
        in smoke_b_200_selected_unit_ids
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
    assert top_provider_name == eval_providers.CONTEXT_IR_PROVIDER

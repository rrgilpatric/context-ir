"""Member-heavy internal signal eval asset tests."""

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
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_smoke_e"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_smoke_e.json"
RUN_SPEC_PATH = REPO_ROOT / "evals" / "run_specs" / "oracle_signal_smoke_e_matrix.json"
QUERY = "Fix missing member note while keeping owner label and report aligned"
TIGHT_BUDGET = 200
RELEVANT_SYMBOL_FILES = (
    "pkg/service.py",
    "pkg/service.py",
    "pkg/labels.py",
)


def _execute_signal_smoke_e_bundle(bundle_dir: Path) -> eval_bundle.EvalBundleArtifact:
    """Execute the member-heavy signal run spec into one deterministic bundle."""
    return eval_bundle.execute_eval_bundle(
        RUN_SPEC_PATH,
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


def test_signal_smoke_e_task_resolves_expected_selectors_deterministically() -> None:
    """The member-heavy smoke task resolves each intended selector once."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_smoke_e"
    assert setup.task.fixture_id == "oracle_signal_smoke_e"
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
        "def:pkg/service.py:pkg.service.MemberSignalCompiler.compile_member_digest",
        "def:pkg/service.py:pkg.service.MemberSignalCompiler.resolve_owner_alias",
        "def:pkg/labels.py:pkg.labels.build_member_label",
        "frontier:call:pkg/service.py:10:8",
    ]
    for resolved in setup.resolved_selectors:
        assert resolved.resolution_status == "resolved"
        assert resolved.candidate_count == 1
        assert resolved.failure_reason is None


def test_signal_smoke_e_run_spec_loads_cleanly_through_runner() -> None:
    """The member-heavy smoke run spec remains valid runner input."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_smoke_e_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_member_baselines"
    assert case.task_path == "evals/tasks/oracle_signal_smoke_e.json"
    assert case.query == QUERY
    assert case.budgets == (240, 200)
    assert case.providers == (
        eval_providers.CONTEXT_IR_PROVIDER,
        eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
        eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
    )


def test_signal_smoke_e_bundle_executes_deterministically_across_runs(
    tmp_path: Path,
) -> None:
    """Independent single-asset bundles match apart from chosen artifact paths."""
    first_bundle = _execute_signal_smoke_e_bundle(tmp_path / "first" / "bundle")
    second_bundle = _execute_signal_smoke_e_bundle(tmp_path / "second" / "bundle")

    assert first_bundle.manifest.plan_id == "oracle_signal_smoke_e_matrix"
    assert first_bundle.manifest.task_ids == ("oracle_signal_smoke_e",)
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


def test_tight_budget_breaks_trivial_whole_file_saturation_for_signal_smoke_e() -> None:
    """Tight budget leaves baselines with only the shallow label support surface."""
    setup = setup_eval_oracle_task(TASK_PATH)
    request = EvalProviderRequest(
        repo_root=FIXTURE_ROOT,
        task_id=setup.task.task_id,
        query=QUERY,
        budget=TIGHT_BUDGET,
    )

    for result in (
        eval_providers.build_lexical_top_k_files_pack(request),
        eval_providers.build_import_neighborhood_files_pack(request),
    ):
        metrics = score_eval_run(setup, result)

        assert result.total_tokens <= TIGHT_BUDGET
        assert result.selected_files
        assert frozenset(result.selected_files).issubset(
            frozenset(result.metadata.candidate_files)
        )
        assert metrics.budget_compliant is True
        assert metrics.edit_coverage == 0.0
        assert metrics.support_coverage == 0.5
        assert metrics.uncertainty_honesty == 0.0
        assert metrics.adequate_edit_selectors == 0
        assert metrics.adequate_support_selectors == 1
        assert metrics.selected_matched_selector_ids == (
            "def:pkg/labels.py:pkg.labels.build_member_label",
        )


def test_signal_smoke_e_assets_stay_internal_and_leave_package_root_unchanged() -> None:
    """The member-heavy smoke assets remain under eval internals, not public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_smoke_e" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_smoke_e")


def test_signal_smoke_e_bundle_preserves_member_heavy_surfaces(
    tmp_path: Path,
) -> None:
    """The member-heavy bundle keeps proof surfaces and alias-chain honesty stable."""
    bundle = _execute_signal_smoke_e_bundle(tmp_path / "bundle")
    records = _parsed_ledger_records(bundle.paths.ledger_path)
    summary = eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(bundle.paths.ledger_path)
    )
    expected_unit_ids = {
        200: {
            "def:pkg/service.py:pkg.service.MemberSignalCompiler.compile_member_digest",
            "def:pkg/service.py:pkg.service.MemberSignalCompiler.resolve_owner_alias",
            "def:pkg/labels.py:pkg.labels.build_member_label",
            "frontier:attribute:pkg/service.py:10:8:10:24",
        },
        240: {
            "def:pkg/service.py:pkg.service.MemberSignalCompiler.compile_member_digest",
            "def:pkg/service.py:pkg.service.MemberSignalCompiler.resolve_owner_alias",
            "def:pkg/labels.py:pkg.labels.build_member_label",
            "frontier:call:pkg/service.py:10:8",
            "frontier:attribute:pkg/service.py:10:8:10:24",
        },
    }
    expected_warnings = {
        200: ["omitted_uncertainty"],
        240: [],
    }
    expected_omitted_uncertainty_ids = {
        200: ["frontier:call:pkg/service.py:10:8"],
        240: [],
    }

    for budget in (200, 240):
        record = _provider_record_by_budget(
            records,
            provider_name=eval_providers.CONTEXT_IR_PROVIDER,
            budget=budget,
        )
        metrics = cast(dict[str, object], record["metrics"])
        aggregate_score = cast(float, metrics["aggregate_score"])
        baselines = [
            _provider_record_by_budget(
                records,
                provider_name=provider_name,
                budget=budget,
            )
            for provider_name in (
                eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
                eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
            )
        ]

        assert cast(int, record["total_tokens"]) <= budget
        assert metrics["budget_compliant"] is True
        assert metrics["adequate_edit_selectors"] == 1
        assert cast(int, metrics["adequate_support_selectors"]) == 2
        assert metrics["edit_coverage"] == 1.0
        assert cast(float, metrics["support_coverage"]) == 1.0
        assert cast(float, metrics["uncertainty_honesty"]) == (
            0.5 if budget == 200 else 1.0
        )
        assert cast(list[object], record["warnings"]) == expected_warnings[budget]
        assert (
            cast(list[object], metrics["omitted_expected_uncertainty_ids"])
            == (expected_omitted_uncertainty_ids[budget])
        )
        assert (
            set(cast(list[str], record["selected_unit_ids"]))
            == (expected_unit_ids[budget])
        )
        assert all(
            aggregate_score
            >= cast(
                float,
                cast(dict[str, object], baseline["metrics"])["aggregate_score"],
            )
            for baseline in baselines
        )

    assert summary.provider_names == (
        "context_ir",
        "import_neighborhood_files",
        "lexical_top_k_files",
    )

"""Member-heavy internal signal eval asset tests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_bundle as eval_bundle
import context_ir.eval_providers as eval_providers
import context_ir.eval_runs as eval_runs
import context_ir.eval_summary as eval_summary
import context_ir.semantic_optimizer as semantic_optimizer
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
TASK3_QUERY = (
    "Fix transitive sole-provider self-call resolution for "
    "MemberSignalCompiler.compile_member_digest while preserving alias_chain "
    "frontier on pkg_alias.labels.build_member_label"
)
TIGHT_BUDGET = 200
RELEVANT_SYMBOL_FILES = (
    "pkg/service.py",
    "pkg/service.py",
    "pkg/labels.py",
)
FULL_REPO_TASK3_COMPILE_ID = (
    "def:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:"
    "evals.fixtures.oracle_signal_smoke_e.pkg.service.MemberSignalCompiler."
    "compile_member_digest"
)
FULL_REPO_TASK3_RESOLVER_ID = (
    "def:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:"
    "evals.fixtures.oracle_signal_smoke_e.pkg.service.MemberSignalCompiler."
    "resolve_owner_alias"
)
FULL_REPO_TASK3_LABEL_ID = (
    "def:evals/fixtures/oracle_signal_smoke_e/pkg/labels.py:"
    "evals.fixtures.oracle_signal_smoke_e.pkg.labels.build_member_label"
)
FULL_REPO_TASK3_PARENT_ID = (
    "def:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:"
    "evals.fixtures.oracle_signal_smoke_e.pkg.service.MemberSignalCompiler"
)
FULL_REPO_TASK3_ALIAS_UNCERTAINTY_ID = (
    "unsupported:call:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:10:8"
)
FULL_REPO_TASK3_FRONTIER_CALL_ID = (
    "frontier:call:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:10:8"
)
FULL_REPO_TASK3_OMITTED_WARNING_IDS = (
    "frontier:call:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:8:22",
    "frontier:attribute:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:10:8:10:24",
    "frontier:attribute:evals/fixtures/oracle_signal_smoke_e/pkg/service.py:8:22:8:32",
)
FULL_REPO_TASK3_RESOLVER_NOISE_ID = (
    "def:src/context_ir/resolver.py:"
    "src.context_ir.resolver._resolve_transitive_sole_provider_self_call_symbol_id"
)
FIXTURE_TASK3_DOCUMENT_SHA256 = (
    "e576ae0dff78ab31871f38e6cf8e705274516164bb67dd841a7a433a5d34c4ae"
)
FULL_REPO_TASK3_DOCUMENT_SHA256 = (
    "78fecbd29120a25c273873649cdf1c74785df2519f5567e7d5bfdc7f26ba70e2"
)
FULL_REPO_TASK3_CONFIDENCE = 0.001903652569243661


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


def test_signal_smoke_e_task3_query_keeps_child_method_support_pack() -> None:
    """The fixture-root Task 3 query keeps method support and frontier at 280."""
    result = eval_providers.build_context_ir_provider_pack(
        EvalProviderRequest(
            repo_root=FIXTURE_ROOT,
            task_id="oracle_signal_smoke_e_task3_regression",
            query=TASK3_QUERY,
            budget=280,
        )
    )
    selected_units = {unit.unit_id: unit for unit in result.metadata.selected_units}
    expected_unit_ids = {
        "def:pkg/service.py:pkg.service.MemberSignalCompiler.compile_member_digest",
        "def:pkg/labels.py:pkg.labels.build_member_label",
        "frontier:call:pkg/service.py:10:8",
        "def:pkg/service.py:pkg.service.MemberSignalCompiler.resolve_owner_alias",
        "frontier:attribute:pkg/service.py:10:8:10:24",
    }

    assert result.total_tokens <= 280
    assert (
        hashlib.sha256(result.document.encode("utf-8")).hexdigest()
        == FIXTURE_TASK3_DOCUMENT_SHA256
    )
    assert set(selected_units) == expected_unit_ids
    assert (
        selected_units[
            "def:pkg/service.py:pkg.service.MemberSignalCompiler.compile_member_digest"
        ].detail
        == "source"
    )
    assert (
        selected_units["def:pkg/labels.py:pkg.labels.build_member_label"].detail
        == "source"
    )
    assert selected_units[
        "def:pkg/service.py:pkg.service.MemberSignalCompiler.resolve_owner_alias"
    ].detail in {"summary", "source"}
    assert selected_units["frontier:call:pkg/service.py:10:8"].detail == "identity"
    parent_class = selected_units.get(
        "def:pkg/service.py:pkg.service.MemberSignalCompiler"
    )
    assert parent_class is None or parent_class.detail != "source"
    assert result.warnings == ()


def test_signal_smoke_e_task3_query_selects_full_repo_exact_units(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The full-repo Task 3 query keeps exact fixture units over repo noise."""
    original_probe = semantic_optimizer._SemanticOptimizerSession.probe
    original_build_warnings = semantic_optimizer._build_warnings
    original_confidence = semantic_optimizer._confidence
    probe_budgets: list[int] = []
    warning_call_count = 0
    confidence_values: list[float] = []

    def counting_probe(
        self: semantic_optimizer._SemanticOptimizerSession,
        budget: int,
    ) -> semantic_optimizer._SemanticOptimizationProbe:
        probe_budgets.append(budget)
        return original_probe(self, budget)

    def counting_build_warnings(
        *,
        candidates: tuple[semantic_optimizer._SemanticCandidate, ...]
        | list[semantic_optimizer._SemanticCandidate],
        selections: tuple[semantic_types.SemanticSelectionRecord, ...],
        omitted_unit_ids: tuple[str, ...],
        focus_unit_ids: frozenset[str],
        suppressed_uncertainty_unit_ids: frozenset[str],
        program: semantic_types.SemanticProgram,
    ) -> list[semantic_types.SemanticOptimizationWarning]:
        nonlocal warning_call_count
        warning_call_count += 1
        return original_build_warnings(
            candidates=candidates,
            selections=selections,
            omitted_unit_ids=omitted_unit_ids,
            focus_unit_ids=focus_unit_ids,
            suppressed_uncertainty_unit_ids=suppressed_uncertainty_unit_ids,
            program=program,
        )

    def counting_confidence(
        *,
        candidates: tuple[semantic_optimizer._SemanticCandidate, ...]
        | list[semantic_optimizer._SemanticCandidate],
        selections: tuple[semantic_types.SemanticSelectionRecord, ...],
    ) -> float:
        confidence = original_confidence(
            candidates=candidates,
            selections=selections,
        )
        confidence_values.append(confidence)
        return confidence

    monkeypatch.setattr(
        semantic_optimizer._SemanticOptimizerSession,
        "probe",
        counting_probe,
    )
    monkeypatch.setattr(
        semantic_optimizer,
        "_build_warnings",
        counting_build_warnings,
    )
    monkeypatch.setattr(
        semantic_optimizer,
        "_confidence",
        counting_confidence,
    )

    for budget in (280, 400):
        probe_budgets.clear()
        warning_call_count = 0
        confidence_values.clear()
        result = eval_providers.build_context_ir_provider_pack(
            EvalProviderRequest(
                repo_root=REPO_ROOT,
                task_id="oracle_signal_smoke_e_task3_full_repo_regression",
                query=TASK3_QUERY,
                budget=budget,
            )
        )
        selected_units = {unit.unit_id: unit for unit in result.metadata.selected_units}

        assert result.total_tokens <= budget
        assert selected_units[FULL_REPO_TASK3_COMPILE_ID].detail == "source"
        assert selected_units[FULL_REPO_TASK3_LABEL_ID].detail == "source"
        assert selected_units[FULL_REPO_TASK3_RESOLVER_ID].detail in {
            "summary",
            "source",
        }
        assert selected_units[FULL_REPO_TASK3_ALIAS_UNCERTAINTY_ID].detail == "identity"
        assert FULL_REPO_TASK3_ALIAS_UNCERTAINTY_ID in (
            result.metadata.unsupported_unit_ids
        )
        assert FULL_REPO_TASK3_FRONTIER_CALL_ID not in (
            result.metadata.unresolved_unit_ids
        )
        assert FULL_REPO_TASK3_RESOLVER_NOISE_ID not in selected_units
        if budget == 280:
            assert result.total_tokens == 274
            assert (
                hashlib.sha256(result.document.encode("utf-8")).hexdigest()
                == FULL_REPO_TASK3_DOCUMENT_SHA256
            )
            assert result.warnings == ("omitted_uncertainty",) * 3
            assert (
                tuple(warning.unit_id for warning in result.metadata.warning_details)
                == FULL_REPO_TASK3_OMITTED_WARNING_IDS
            )
            assert tuple(unit.unit_id for unit in result.metadata.selected_units) == (
                FULL_REPO_TASK3_COMPILE_ID,
                FULL_REPO_TASK3_LABEL_ID,
                FULL_REPO_TASK3_RESOLVER_ID,
                FULL_REPO_TASK3_ALIAS_UNCERTAINTY_ID,
            )
            assert selected_units[FULL_REPO_TASK3_RESOLVER_ID].detail == "source"
            assert len(probe_budgets) < 8
            assert warning_call_count == 1
            assert confidence_values == [FULL_REPO_TASK3_CONFIDENCE]
        parent_class = selected_units.get(FULL_REPO_TASK3_PARENT_ID)
        assert parent_class is None or parent_class.detail != "source"


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

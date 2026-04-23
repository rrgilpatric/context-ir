"""Deterministic multi-run eval ledger orchestration tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_runs as eval_runs
import context_ir.semantic_types as semantic_types
from context_ir.eval_oracles import EvalOracleSetup, setup_eval_oracle_task
from context_ir.eval_providers import (
    CONTEXT_IR_PROVIDER,
    FILE_ORDER_FLOOR_PROVIDER,
    IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
    LEXICAL_TOP_K_FILES_PROVIDER,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_SPEC_PATH = REPO_ROOT / "evals" / "run_specs" / "oracle_smoke_matrix.json"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_smoke.json"
PROBE_RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_dynamic_import_probe_matrix.json"
)
HASATTR_PROBE_RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_hasattr_probe_matrix.json"
)
PROBE_BUDGETS = (220, 180)
HASATTR_PROBE_BUDGETS = (220,)
PROBE_PROVIDERS = (
    CONTEXT_IR_PROVIDER,
    LEXICAL_TOP_K_FILES_PROVIDER,
    IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
BASELINE_PROVIDERS = (
    LEXICAL_TOP_K_FILES_PROVIDER,
    IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
_RAW_RECORD_KEYS = {
    "spec_version",
    "run_id",
    "task_id",
    "fixture_id",
    "fixture_repo_root",
    "fixture_file_hashes",
    "git_commit",
    "python_version",
    "package_version",
    "provider_name",
    "provider_algorithm_version",
    "provider_config",
    "query",
    "budget",
    "total_tokens",
    "document",
    "selected_files",
    "selected_unit_ids",
    "omitted_unit_ids",
    "warnings",
    "provider_metadata",
    "resolved_selectors",
    "metrics",
}
_PROVIDER_CONFIG_KEYS = {"max_candidates", "seed_count", "diagnostic_only"}
_PROVIDER_METADATA_KEYS = {
    "diagnostic_only",
    "candidate_files",
    "omitted_candidate_files",
    "lexical_scores",
    "selected_units",
    "warning_details",
    "unresolved_unit_ids",
    "unsupported_unit_ids",
    "syntax_diagnostic_ids",
    "semantic_diagnostic_ids",
}
_RESOLVED_SELECTOR_KEYS = {
    "original_selector",
    "resolution_status",
    "resolved_unit_id",
    "resolved_file_path",
    "resolved_span",
    "failure_reason",
    "candidate_count",
    "candidate_summaries",
    "primary_capability_tier",
    "primary_evidence_origin",
    "primary_replay_status",
    "has_attached_runtime_provenance",
    "attached_runtime_provenance_record_ids",
}
_METRIC_KEYS = {
    "provider_name",
    "task_id",
    "budget",
    "budget_compliant",
    "edit_coverage",
    "support_coverage",
    "representation_adequacy",
    "uncertainty_honesty",
    "credited_relevant_tokens",
    "noise_tokens",
    "noise_ratio",
    "noise_efficiency",
    "aggregate_score",
    "total_expected_edit_selectors",
    "adequate_edit_selectors",
    "total_expected_support_selectors",
    "adequate_support_selectors",
    "total_expected_uncertainty_selectors",
    "represented_expected_selector_count",
    "too_shallow_selector_ids",
    "omitted_expected_uncertainty_ids",
    "selected_matched_selector_ids",
}


def _load_run_spec_record(path: Path = RUN_SPEC_PATH) -> dict[str, object]:
    """Load one run spec JSON asset as a mutable record."""
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return cast(dict[str, object], raw)


def _case_record(
    spec_record: dict[str, object],
    index: int,
) -> dict[str, object]:
    """Return one mutable case record from a run spec copy."""
    cases = spec_record["cases"]
    assert isinstance(cases, list)
    case = cases[index]
    assert isinstance(case, dict)
    return cast(dict[str, object], case)


def _write_run_spec_record(
    tmp_path: Path,
    spec_record: dict[str, object],
) -> Path:
    """Write a copied run spec record to a temporary JSON file."""
    spec_path = tmp_path / "run_spec.json"
    spec_path.write_text(json.dumps(spec_record), encoding="utf-8")
    return spec_path


def _parsed_ledger_records(ledger_path: Path) -> list[dict[str, object]]:
    """Return parsed JSON objects from one JSONL ledger file."""
    return [
        cast(dict[str, object], json.loads(line))
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
    ]


def _record_for(
    records: list[dict[str, object]],
    *,
    provider_name: str,
    budget: int,
) -> dict[str, object]:
    """Return one raw ledger record by provider and budget."""
    return next(
        record
        for record in records
        if record["provider_name"] == provider_name and record["budget"] == budget
    )


def _selected_units(record: dict[str, object]) -> list[dict[str, object]]:
    """Return structured selected-unit metadata from one raw ledger record."""
    provider_metadata = cast(dict[str, object], record["provider_metadata"])
    return cast(list[dict[str, object]], provider_metadata["selected_units"])


def _smoke_setup() -> EvalOracleSetup:
    """Return the accepted smoke oracle setup."""
    return setup_eval_oracle_task(TASK_PATH)


def test_run_spec_json_loads_into_typed_dataclasses() -> None:
    """The durable run spec asset loads into typed case dataclasses."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_smoke_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]

    assert isinstance(case, eval_runs.EvalRunCase)
    assert case.case_id == "smoke_core_baselines"
    assert case.task_path == "evals/tasks/oracle_smoke.json"
    assert case.query == "Fix missing_call in run without breaking helper usage"
    assert case.budgets == (200, 120)
    assert case.providers == (
        CONTEXT_IR_PROVIDER,
        LEXICAL_TOP_K_FILES_PROVIDER,
        IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
    )


def test_unknown_top_level_run_spec_fields_are_rejected(tmp_path: Path) -> None:
    """Durable run spec JSON rejects unknown top-level fields."""
    spec_record = _load_run_spec_record()
    spec_record["planId"] = "oracle_smoke_matrix"
    spec_path = _write_run_spec_record(tmp_path, spec_record)

    with pytest.raises(
        eval_runs.EvalRunSpecError,
        match=r"unknown field 'planId'",
    ):
        eval_runs.load_eval_run_spec(spec_path)


def test_unknown_case_fields_are_rejected(tmp_path: Path) -> None:
    """Run spec cases reject unknown fields."""
    spec_record = _load_run_spec_record()
    _case_record(spec_record, 0)["provider"] = [CONTEXT_IR_PROVIDER]
    spec_path = _write_run_spec_record(tmp_path, spec_record)

    with pytest.raises(
        eval_runs.EvalRunSpecError,
        match=r"unknown field 'provider'",
    ):
        eval_runs.load_eval_run_spec(spec_path)


def test_unknown_provider_names_fail_loudly(tmp_path: Path) -> None:
    """Run spec providers are limited to accepted internal provider names."""
    spec_record = _load_run_spec_record()
    _case_record(spec_record, 0)["providers"] = ["unknown_provider"]
    spec_path = _write_run_spec_record(tmp_path, spec_record)

    with pytest.raises(
        eval_runs.EvalRunSpecError,
        match=(
            r"must be one of context_ir, lexical_top_k_files, "
            r"import_neighborhood_files, file_order_floor"
        ),
    ):
        eval_runs.load_eval_run_spec(spec_path)


def test_provider_dispatch_map_covers_accepted_internal_names() -> None:
    """Provider dispatch maps only the accepted internal provider builders."""
    assert eval_runs._provider_builder(CONTEXT_IR_PROVIDER) is (
        eval_runs.build_context_ir_provider_pack
    )
    assert eval_runs._provider_builder(LEXICAL_TOP_K_FILES_PROVIDER) is (
        eval_runs.build_lexical_top_k_files_pack
    )
    assert eval_runs._provider_builder(IMPORT_NEIGHBORHOOD_FILES_PROVIDER) is (
        eval_runs.build_import_neighborhood_files_pack
    )
    assert eval_runs._provider_builder(FILE_ORDER_FLOOR_PROVIDER) is (
        eval_runs.build_file_order_floor_pack
    )


def test_empty_case_list_fails_loudly(tmp_path: Path) -> None:
    """Run specs must contain at least one case."""
    spec_record = _load_run_spec_record()
    spec_record["cases"] = []
    spec_path = _write_run_spec_record(tmp_path, spec_record)

    with pytest.raises(
        eval_runs.EvalRunSpecError,
        match="run spec must contain at least one case",
    ):
        eval_runs.load_eval_run_spec(spec_path)


def test_empty_budget_list_fails_loudly(tmp_path: Path) -> None:
    """Each run case must declare at least one budget."""
    spec_record = _load_run_spec_record()
    _case_record(spec_record, 0)["budgets"] = []
    spec_path = _write_run_spec_record(tmp_path, spec_record)

    with pytest.raises(
        eval_runs.EvalRunSpecError,
        match=r"\$\.cases\[0\]\.budgets must contain at least one budget",
    ):
        eval_runs.load_eval_run_spec(spec_path)


def test_non_positive_budgets_fail_loudly(tmp_path: Path) -> None:
    """Run cases reject zero or negative budgets."""
    spec_record = _load_run_spec_record()
    _case_record(spec_record, 0)["budgets"] = [0]
    spec_path = _write_run_spec_record(tmp_path, spec_record)

    with pytest.raises(
        eval_runs.EvalRunSpecError,
        match=r"\$\.cases\[0\]\.budgets\[0\] must be a positive integer",
    ):
        eval_runs.load_eval_run_spec(spec_path)


def test_execute_eval_run_spec_writes_one_raw_record_per_combination(
    tmp_path: Path,
) -> None:
    """One task x provider x budget matrix appends one raw JSON object per run."""
    ledger_path = tmp_path / "ledgers" / "raw.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    parsed_records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_smoke_matrix"
    assert execution.output_path == ledger_path
    assert execution.record_count == 6
    assert len(parsed_records) == 6
    assert execution.written_run_ids == tuple(
        cast(str, record["run_id"]) for record in parsed_records
    )

    for record in parsed_records:
        assert set(record) == _RAW_RECORD_KEYS
        assert record["spec_version"] == "v1"
        assert record["task_id"] == "oracle_smoke"
        assert record["fixture_id"] == "oracle_smoke"
        assert record["provider_name"] in {
            CONTEXT_IR_PROVIDER,
            LEXICAL_TOP_K_FILES_PROVIDER,
            IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
        }
        assert isinstance(record["document"], str)
        assert set(cast(dict[str, object], record["provider_config"])) == (
            _PROVIDER_CONFIG_KEYS
        )
        assert set(cast(dict[str, object], record["provider_metadata"])) == (
            _PROVIDER_METADATA_KEYS
        )
        metrics = cast(dict[str, object], record["metrics"])
        assert set(metrics) == _METRIC_KEYS
        resolved_selectors = cast(list[object], record["resolved_selectors"])
        assert resolved_selectors
        for selector in resolved_selectors:
            assert isinstance(selector, dict)
            assert set(selector) == _RESOLVED_SELECTOR_KEYS


def test_execute_eval_run_spec_populates_runtime_backed_fields_for_probe(
    tmp_path: Path,
) -> None:
    """Probe run execution keeps tier-aware raw fields non-null under spec v1."""
    ledger_path = tmp_path / "probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        PROBE_RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    parsed_records = _parsed_ledger_records(ledger_path)
    assert execution.record_count == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert len(parsed_records) == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert {
        (record["provider_name"], record["budget"]) for record in parsed_records
    } == {
        (provider_name, budget)
        for provider_name in PROBE_PROVIDERS
        for budget in PROBE_BUDGETS
    }

    for provider_name in BASELINE_PROVIDERS:
        for budget in PROBE_BUDGETS:
            baseline_record = _record_for(
                parsed_records,
                provider_name=provider_name,
                budget=budget,
            )
            assert baseline_record["selected_unit_ids"] == []
            assert _selected_units(baseline_record) == []

    record = _record_for(
        parsed_records,
        provider_name=CONTEXT_IR_PROVIDER,
        budget=220,
    )
    unsupported_selector = next(
        selector
        for selector in cast(list[dict[str, object]], record["resolved_selectors"])
        if selector["resolved_unit_id"] == "unsupported:call:main.py:5:13"
    )
    unsupported_selected_unit = next(
        unit
        for unit in _selected_units(record)
        if unit["unit_id"] == "unsupported:call:main.py:5:13"
    )

    assert record["spec_version"] == "v1"
    assert record["provider_name"] == CONTEXT_IR_PROVIDER
    assert record["budget"] == 220
    assert (
        cast(dict[str, object], unsupported_selector["original_selector"])[
            "expected_primary_capability_tier"
        ]
        == "unsupported/opaque"
    )
    assert (
        cast(dict[str, object], unsupported_selector["original_selector"])[
            "expect_attached_runtime_provenance"
        ]
        is True
    )
    assert unsupported_selector["primary_capability_tier"] == "unsupported/opaque"
    assert unsupported_selector["has_attached_runtime_provenance"] is True
    assert cast(
        list[str],
        unsupported_selector["attached_runtime_provenance_record_ids"],
    )
    assert unsupported_selected_unit["primary_capability_tier"] == "unsupported/opaque"
    assert unsupported_selected_unit["has_attached_runtime_provenance"] is True
    assert cast(
        list[str],
        unsupported_selected_unit["attached_runtime_provenance_record_ids"],
    )


def test_execute_eval_run_spec_populates_runtime_backed_fields_for_hasattr_probe(
    tmp_path: Path,
) -> None:
    """The ``hasattr`` pilot keeps runtime-backed fields additive under spec v1."""
    ledger_path = tmp_path / "hasattr_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        HASATTR_PROBE_RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    parsed_records = _parsed_ledger_records(ledger_path)
    assert execution.record_count == len(PROBE_PROVIDERS) * len(HASATTR_PROBE_BUDGETS)
    assert len(parsed_records) == len(PROBE_PROVIDERS) * len(HASATTR_PROBE_BUDGETS)

    for provider_name in BASELINE_PROVIDERS:
        baseline_record = _record_for(
            parsed_records,
            provider_name=provider_name,
            budget=220,
        )
        assert baseline_record["selected_unit_ids"] == []
        assert _selected_units(baseline_record) == []

    record = _record_for(
        parsed_records,
        provider_name=CONTEXT_IR_PROVIDER,
        budget=220,
    )
    unsupported_selector = next(
        selector
        for selector in cast(list[dict[str, object]], record["resolved_selectors"])
        if selector["resolved_unit_id"] == "unsupported:call:main.py:2:11"
    )
    unsupported_selected_unit = next(
        unit
        for unit in _selected_units(record)
        if unit["unit_id"] == "unsupported:call:main.py:2:11"
    )

    assert record["spec_version"] == "v1"
    assert record["provider_name"] == CONTEXT_IR_PROVIDER
    assert record["budget"] == 220
    assert unsupported_selector["primary_capability_tier"] == "unsupported/opaque"
    assert unsupported_selector["has_attached_runtime_provenance"] is True
    assert unsupported_selected_unit["primary_capability_tier"] == "unsupported/opaque"
    assert unsupported_selected_unit["has_attached_runtime_provenance"] is True
    assert cast(
        list[str],
        unsupported_selected_unit["attached_runtime_provenance_record_ids"],
    )


def test_execution_order_is_deterministic_and_reuses_setup_once_per_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Execution preserves case/provider order, sorts budgets, and reuses setup."""
    spec_record = {
        "plan_id": "ordered_plan",
        "cases": [
            {
                "case_id": "alpha",
                "task_path": "evals/tasks/oracle_smoke.json",
                "query": "Fix missing_call in run without breaking helper usage",
                "budgets": [160, 96],
                "providers": [
                    LEXICAL_TOP_K_FILES_PROVIDER,
                    CONTEXT_IR_PROVIDER,
                ],
            },
            {
                "case_id": "beta",
                "task_path": "evals/tasks/oracle_smoke.json",
                "query": "Trace helper usage around run",
                "budgets": [120],
                "providers": [IMPORT_NEIGHBORHOOD_FILES_PROVIDER],
            },
        ],
    }
    spec_path = _write_run_spec_record(tmp_path, spec_record)
    ledger_path = tmp_path / "ordered.jsonl"
    setup_calls: list[Path] = []
    original_setup = eval_runs.setup_eval_oracle_task

    def counting_setup(task_path: Path | str) -> EvalOracleSetup:
        resolved = Path(task_path)
        setup_calls.append(resolved)
        return original_setup(resolved)

    monkeypatch.setattr(eval_runs, "setup_eval_oracle_task", counting_setup)

    execution = eval_runs.execute_eval_run_spec(
        spec_path,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    assert setup_calls == [
        REPO_ROOT / "evals" / "tasks" / "oracle_smoke.json",
        REPO_ROOT / "evals" / "tasks" / "oracle_smoke.json",
    ]
    assert execution.case_record_counts == (
        eval_runs.EvalRunCaseExecutionCount(case_id="alpha", record_count=4),
        eval_runs.EvalRunCaseExecutionCount(case_id="beta", record_count=1),
    )

    parsed_records = _parsed_ledger_records(ledger_path)
    run_ids = [cast(str, record["run_id"]) for record in parsed_records]
    assert run_ids == [
        "ordered_plan:alpha:lexical_top_k_files:96",
        "ordered_plan:alpha:lexical_top_k_files:160",
        "ordered_plan:alpha:context_ir:96",
        "ordered_plan:alpha:context_ir:160",
        "ordered_plan:beta:import_neighborhood_files:120",
    ]


def test_execute_eval_run_spec_does_not_mutate_specs_or_resolved_setups(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Execution treats loaded run specs and resolved oracle setups as immutable."""
    spec = eval_runs.EvalRunSpec(
        plan_id="immutability_plan",
        cases=(
            eval_runs.EvalRunCase(
                case_id="immutability_case",
                task_path="evals/tasks/oracle_smoke.json",
                query="Fix missing_call in run without breaking helper usage",
                budgets=(120,),
                providers=(CONTEXT_IR_PROVIDER,),
            ),
        ),
    )
    setup = _smoke_setup()
    spec_before = copy.deepcopy(spec)
    setup_before = copy.deepcopy(setup)

    monkeypatch.setattr(eval_runs, "load_eval_run_spec", lambda _: spec)
    monkeypatch.setattr(eval_runs, "setup_eval_oracle_task", lambda _: setup)

    eval_runs.execute_eval_run_spec(
        "ignored.json",
        tmp_path / "immutability.jsonl",
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    assert spec == spec_before
    assert setup == setup_before


def test_eval_runs_stay_internal_and_do_not_add_report_or_public_surfaces() -> None:
    """Run orchestration stays internal and avoids report or public surfaces."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "execute_eval_run_spec" not in context_ir.__all__
    assert not hasattr(context_ir, "execute_eval_run_spec")
    assert not hasattr(eval_runs, "build_markdown_report")
    assert not hasattr(eval_runs, "render_result_table")
    assert not hasattr(eval_runs, "export_public_eval_summary")

    result_fields = set(eval_runs.EvalRunExecutionResult.__dataclass_fields__)
    forbidden_fields = {
        "markdown_report",
        "category_rollups",
        "public_claims",
        "result_table",
        "claim_gate",
    }

    assert forbidden_fields.isdisjoint(result_fields)

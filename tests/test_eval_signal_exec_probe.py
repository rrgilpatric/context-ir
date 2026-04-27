"""Isolated bounded ``exec(source)`` runtime-backed eval pilot tests."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import cast

import context_ir
import context_ir.eval_providers as eval_providers
import context_ir.eval_runs as eval_runs
import context_ir.semantic_types as semantic_types
from context_ir.eval_oracles import (
    SymbolOracleSelector,
    UnsupportedOracleSelector,
    load_fixture_exec_runtime_observations,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_exec_probe"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_exec_probe.json"
RUN_SPEC_PATH = (
    REPO_ROOT / "evals" / "run_specs" / "oracle_signal_exec_probe_matrix.json"
)
PROBE_BUDGETS = (220,)
PROBE_PROVIDERS = (
    eval_providers.CONTEXT_IR_PROVIDER,
    eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
    eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
BASELINE_PROVIDERS = (
    eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
    eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
QUERY = "exec(source) completed literal_statement"
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:3:4"
EXECUTED_SOURCE = "pass"
SOURCE_SHA256 = hashlib.sha256(EXECUTED_SOURCE.encode("utf-8")).hexdigest()


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


def _resolved_selectors(record: dict[str, object]) -> list[dict[str, object]]:
    """Return structured resolved-selector metadata from one raw ledger record."""
    return cast(list[dict[str, object]], record["resolved_selectors"])


def test_exec_probe_task_resolves_expected_selectors_deterministically() -> None:
    """The isolated exec(source) probe resolves the intended selectors."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_exec_probe"
    assert setup.task.fixture_id == "oracle_signal_exec_probe"
    assert len(setup.task.expected_selectors) == 3
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], UnsupportedOracleSelector)
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.probe_exec_source",
        "def:main.py:main.render_probe_digest",
        UNSUPPORTED_UNIT_ID,
    ]

    unsupported = setup.resolved_selectors[2]
    assert unsupported.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        unsupported.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported.has_attached_runtime_provenance is True
    assert unsupported.attached_runtime_provenance_record_ids
    assert all(
        UNSUPPORTED_UNIT_ID
        not in (dependency.source_symbol_id, dependency.target_symbol_id)
        for dependency in setup.semantic_program.proven_dependencies
    )
    assert all(
        dependency.evidence_site_id != "site:call:main.py:3:4"
        for dependency in setup.semantic_program.proven_dependencies
    )
    assert all(
        symbol.qualified_name != "pass"
        for symbol in setup.semantic_program.resolved_symbols.values()
    )


def test_exec_probe_run_spec_loads_cleanly_through_runner() -> None:
    """The isolated exec(source) probe run spec stays valid runner input."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_exec_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_exec_probe"
    assert case.task_path == "evals/tasks/oracle_signal_exec_probe.json"
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_exec_probe_fixture_uses_bounded_literal_source_shape() -> None:
    """The fixture preserves the eval-only bounded ``exec(source)`` branch."""
    source = (FIXTURE_ROOT / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    observations = load_fixture_exec_runtime_observations(FIXTURE_ROOT)

    exec_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "exec"
    ]
    eval_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "eval"
    ]
    probe_function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "probe_exec_source"
    )
    source_assignment = next(
        statement
        for statement in probe_function.body
        if isinstance(statement, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "source"
            for target in statement.targets
        )
    )
    executed_source = cast(ast.Constant, source_assignment.value)
    executed_tree = ast.parse(cast(str, executed_source.value))

    assert source.count('source = "pass"') == 1
    assert source.count("exec(source)") == 1
    assert 'exec("pass")' not in source
    assert "exec(source + " not in source
    assert "exec(source=" not in source
    assert "exec(source," not in source
    assert "builtins.exec" not in source
    assert "eval(" not in source
    assert len(exec_calls) == 1
    assert eval_calls == []
    assert len(exec_calls[0].args) == 1
    assert exec_calls[0].keywords == []
    assert isinstance(exec_calls[0].args[0], ast.Name)
    assert exec_calls[0].args[0].id == "source"
    assert isinstance(executed_source.value, str)
    assert executed_source.value == EXECUTED_SOURCE
    assert len(executed_tree.body) == 1
    assert isinstance(executed_tree.body[0], ast.Pass)
    assert len(observations) == 1
    assert observations[0].site.snippet == "exec(source)"
    assert observations[0].site.span.start_line == 3
    assert observations[0].site.span.start_column == 4
    assert tuple(
        (field.key, field.value) for field in observations[0].replay_inputs
    ) == (
        ("source_shape", "literal_statement"),
        ("source_sha256", SOURCE_SHA256),
    )
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (
        ("execution_outcome", "completed"),
        ("statement_kind", "pass"),
    )
    assert observations[0].durable_payload_reference


def test_exec_probe_assets_stay_internal() -> None:
    """The isolated exec(source) probe does not widen public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_exec_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_exec_probe")


def test_exec_probe_run_executes_with_additive_runtime_provenance(
    tmp_path: Path,
) -> None:
    """Run execution preserves unsupported primary truth plus runtime support."""
    ledger_path = tmp_path / "exec_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_exec_probe_matrix"
    assert execution.record_count == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert len(records) == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert {(record["provider_name"], record["budget"]) for record in records} == {
        (provider_name, budget)
        for provider_name in PROBE_PROVIDERS
        for budget in PROBE_BUDGETS
    }

    for provider_name in BASELINE_PROVIDERS:
        baseline_record = _record_for(
            records,
            provider_name=provider_name,
            budget=220,
        )
        assert baseline_record["selected_unit_ids"] == []
        assert _selected_units(baseline_record) == []

    record = _record_for(
        records,
        provider_name=eval_providers.CONTEXT_IR_PROVIDER,
        budget=220,
    )
    metrics = cast(dict[str, object], record["metrics"])
    runtime_provenance_records = cast(
        list[dict[str, object]],
        record["runtime_provenance_records"],
    )
    unsupported_selector = next(
        selector
        for selector in _resolved_selectors(record)
        if selector["resolved_unit_id"] == UNSUPPORTED_UNIT_ID
    )
    unsupported_unit = next(
        unit
        for unit in _selected_units(record)
        if unit["unit_id"] == UNSUPPORTED_UNIT_ID
    )

    assert record["spec_version"] == "v1"
    assert record["provider_name"] == eval_providers.CONTEXT_IR_PROVIDER
    assert record["budget"] == 220
    assert UNSUPPORTED_UNIT_ID in cast(list[str], record["selected_unit_ids"])
    assert metrics["uncertainty_honesty"] == 1.0
    assert unsupported_selector["primary_capability_tier"] == "unsupported/opaque"
    assert unsupported_selector["primary_evidence_origin"] == (
        "unsupported_reason_code"
    )
    assert unsupported_selector["primary_replay_status"] == "opaque_boundary"
    assert unsupported_selector["has_attached_runtime_provenance"] is True
    assert unsupported_unit["primary_capability_tier"] == "unsupported/opaque"
    assert unsupported_unit["primary_evidence_origin"] == "unsupported_reason_code"
    assert unsupported_unit["primary_replay_status"] == "opaque_boundary"
    assert unsupported_unit["has_attached_runtime_provenance"] is True
    assert cast(
        list[str],
        unsupported_unit["attached_runtime_provenance_record_ids"],
    )
    assert len(runtime_provenance_records) == 1
    assert runtime_provenance_records[0]["normalized_payload"] == {
        "execution_outcome": "completed",
        "statement_kind": "pass",
    }

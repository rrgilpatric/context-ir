"""Direct-literal ``setattr`` runtime-backed eval pilot tests."""

from __future__ import annotations

import ast
import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import cast

import context_ir
import context_ir.eval_providers as eval_providers
import context_ir.eval_runs as eval_runs
import context_ir.semantic_types as semantic_types
from context_ir.eval_oracles import (
    SymbolOracleSelector,
    UnsupportedOracleSelector,
    load_fixture_setattr_runtime_observations,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
    UnresolvedReasonCode,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_signal_setattr_literal_probe"
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_signal_setattr_literal_probe.json"
RUN_SPEC_PATH = (
    REPO_ROOT
    / "evals"
    / "run_specs"
    / "oracle_signal_setattr_literal_probe_matrix.json"
)
PROBE_BUDGETS = (220, 100)
PROBE_PROVIDERS = (
    eval_providers.CONTEXT_IR_PROVIDER,
    eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
    eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
BASELINE_PROVIDERS = (
    eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
    eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
EXPECTED_BASELINE_SELECTED_FILES = {
    (eval_providers.LEXICAL_TOP_K_FILES_PROVIDER, 100): [],
    (eval_providers.LEXICAL_TOP_K_FILES_PROVIDER, 220): ["main.py"],
    (eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER, 100): [],
    (eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER, 220): ["main.py"],
}
EXPECTED_CONTEXT_IR_SELECTED_UNIT_IDS = {
    100: (
        "def:main.py:main.probe_set_literal_attribute",
        "def:main.py:main.render_probe_digest",
        "unsupported:call:main.py:7:4",
    ),
    220: (
        "def:main.py:main.probe_set_literal_attribute",
        "def:main.py:main.render_probe_digest",
        "def:main.py:main.ProbeTarget",
        "unsupported:call:main.py:7:4",
    ),
}
QUERY = (
    'Fix probe_set_literal_attribute unsupported setattr(obj, "flag", value) '
    "returned None and keep digest output aligned"
)
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:7:4"
UNSUPPORTED_SITE_ID = "site:call:main.py:7:4"


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


def _load_fixture_module() -> ModuleType:
    """Load the isolated fixture module so its digest branch can be checked."""
    spec = importlib.util.spec_from_file_location(
        "oracle_signal_setattr_literal_probe_fixture",
        FIXTURE_ROOT / "main.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_setattr_literal_probe_fixture_uses_only_direct_literal_shape() -> None:
    """The fixture preserves exactly ``setattr(obj, "flag", value)``."""
    source = (FIXTURE_ROOT / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    observations = load_fixture_setattr_runtime_observations(FIXTURE_ROOT)

    setattr_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setattr"
    ]
    forbidden_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"getattr", "hasattr", "delattr", "vars", "dir"}
    ]
    name_assignments = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "name"
            for target in node.targets
        )
    ]
    name_loads = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Name) and node.id == "name"
    ]
    call = setattr_calls[0]

    assert source.count('setattr(obj, "flag", value)') == 1
    assert "setattr(obj, name, value)" not in source
    assert "getattr(" not in source
    assert "hasattr(" not in source
    assert "delattr(" not in source
    assert "vars(" not in source
    assert "dir(" not in source
    assert len(setattr_calls) == 1
    assert len(call.args) == 3
    assert call.keywords == []
    assert isinstance(call.args[0], ast.Name)
    assert call.args[0].id == "obj"
    assert isinstance(call.args[1], ast.Constant)
    assert call.args[1].value == "flag"
    assert isinstance(call.args[2], ast.Name)
    assert call.args[2].id == "value"
    assert name_assignments == []
    assert name_loads == []
    assert forbidden_calls == []
    assert len(observations) == 1
    assert observations[0].site.site_id == UNSUPPORTED_SITE_ID
    assert observations[0].site.snippet == 'setattr(obj, "flag", value)'
    assert observations[0].site.span.start_line == 7
    assert observations[0].site.span.start_column == 4
    assert observations[0].site.span.end_line == 7
    assert observations[0].site.span.end_column == 31
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (("mutation_outcome", "returned_none"),)
    assert observations[0].durable_payload_reference


def test_setattr_literal_probe_resolves_without_static_attribute_proof() -> None:
    """Runtime evidence stays additive and does not prove ``flag`` statically."""
    setup = setup_eval_oracle_task(TASK_PATH)
    program = setup.semantic_program
    unsupported_construct = next(
        construct
        for construct in program.unsupported_constructs
        if construct.construct_id == UNSUPPORTED_UNIT_ID
    )

    assert setup.task.task_id == "oracle_signal_setattr_literal_probe"
    assert setup.task.fixture_id == "oracle_signal_setattr_literal_probe"
    assert len(setup.task.expected_selectors) == 3
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], UnsupportedOracleSelector)
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.probe_set_literal_attribute",
        "def:main.py:main.render_probe_digest",
        UNSUPPORTED_UNIT_ID,
    ]
    assert unsupported_construct.reason_code is UnresolvedReasonCode.RUNTIME_MUTATION
    assert unsupported_construct.site.snippet == 'setattr(obj, "flag", value)'

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
        "flag" not in (symbol.symbol_id, symbol.qualified_name)
        for symbol in program.resolved_symbols.values()
    )
    assert all(
        "flag" not in (dependency.source_symbol_id, dependency.target_symbol_id)
        for dependency in program.proven_dependencies
    )
    assert all(
        dependency.evidence_site_id != UNSUPPORTED_SITE_ID
        for dependency in program.proven_dependencies
    )


def test_setattr_literal_probe_run_spec_loads_two_budget_matrix() -> None:
    """The run spec stays at 1 task x 2 budgets x 3 providers."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_setattr_literal_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_setattr_literal_probe"
    assert case.task_path == "evals/tasks/oracle_signal_setattr_literal_probe.json"
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_setattr_literal_probe_digest_is_deterministic() -> None:
    """The direct-literal fixture executes the assignment branch."""
    module = _load_fixture_module()
    render_probe_digest = cast(Callable[[], str], module.render_probe_digest)

    assert render_probe_digest() == "setattr_literal:ready"


def test_setattr_literal_probe_assets_stay_internal() -> None:
    """The direct-literal pilot remains internal and does not widen exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_setattr_literal_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_setattr_literal_probe")


def test_setattr_literal_probe_run_preserves_additive_runtime_boundary(
    tmp_path: Path,
) -> None:
    """The matrix locks selected units, baselines, and additive provenance."""
    ledger_path = tmp_path / "setattr_literal_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_setattr_literal_probe_matrix"
    assert execution.record_count == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert len(records) == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert {(record["provider_name"], record["budget"]) for record in records} == {
        (provider_name, budget)
        for provider_name in PROBE_PROVIDERS
        for budget in PROBE_BUDGETS
    }

    for provider_name in BASELINE_PROVIDERS:
        for budget in PROBE_BUDGETS:
            baseline_record = _record_for(
                records,
                provider_name=provider_name,
                budget=budget,
            )
            assert (
                baseline_record["selected_files"]
                == EXPECTED_BASELINE_SELECTED_FILES[(provider_name, budget)]
            )
            assert baseline_record["selected_unit_ids"] == []
            assert _selected_units(baseline_record) == []

    for budget in PROBE_BUDGETS:
        record = _record_for(
            records,
            provider_name=eval_providers.CONTEXT_IR_PROVIDER,
            budget=budget,
        )
        metrics = cast(dict[str, object], record["metrics"])
        runtime_provenance_records = cast(
            list[dict[str, object]],
            record["runtime_provenance_records"],
        )
        selected_units = _selected_units(record)
        selected_unit_ids = cast(list[str], record["selected_unit_ids"])
        selected_unit_primary_tiers = {
            cast(str, unit["unit_id"]): cast(str, unit["primary_capability_tier"])
            for unit in selected_units
        }
        unsupported_selector = next(
            selector
            for selector in _resolved_selectors(record)
            if selector["resolved_unit_id"] == UNSUPPORTED_UNIT_ID
        )
        unsupported_unit = next(
            unit for unit in selected_units if unit["unit_id"] == UNSUPPORTED_UNIT_ID
        )

        assert record["spec_version"] == "v1"
        assert record["provider_name"] == eval_providers.CONTEXT_IR_PROVIDER
        assert record["budget"] == budget
        assert record["selected_files"] == []
        assert tuple(selected_unit_ids) == EXPECTED_CONTEXT_IR_SELECTED_UNIT_IDS[budget]
        assert selected_unit_primary_tiers[UNSUPPORTED_UNIT_ID] == "unsupported/opaque"
        assert metrics["uncertainty_honesty"] == 1.0
        assert all("flag" not in cast(str, unit["unit_id"]) for unit in selected_units)
        assert unsupported_selector["primary_capability_tier"] == "unsupported/opaque"
        assert unsupported_selector["primary_evidence_origin"] == (
            "unsupported_reason_code"
        )
        assert unsupported_selector["primary_replay_status"] == "opaque_boundary"
        assert unsupported_selector["has_attached_runtime_provenance"] is True
        assert unsupported_unit["primary_capability_tier"] == "unsupported/opaque"
        assert unsupported_unit["primary_evidence_origin"] == (
            "unsupported_reason_code"
        )
        assert unsupported_unit["primary_replay_status"] == "opaque_boundary"
        assert unsupported_unit["has_attached_runtime_provenance"] is True
        assert cast(
            list[str],
            unsupported_unit["attached_runtime_provenance_record_ids"],
        )
        assert len(runtime_provenance_records) == 1
        assert runtime_provenance_records[0]["normalized_payload"] == {
            "mutation_outcome": "returned_none"
        }

"""Root ``importlib`` alias runtime-backed eval pilot tests."""

from __future__ import annotations

import ast
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
    load_fixture_dynamic_import_runtime_observations,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (
    REPO_ROOT / "evals" / "fixtures" / "oracle_signal_dynamic_import_root_alias_probe"
)
TASK_PATH = (
    REPO_ROOT / "evals" / "tasks" / "oracle_signal_dynamic_import_root_alias_probe.json"
)
RUN_SPEC_PATH = (
    REPO_ROOT
    / "evals"
    / "run_specs"
    / "oracle_signal_dynamic_import_root_alias_probe_matrix.json"
)
PROBE_BUDGETS = (220,)
PROBE_PROVIDERS = (
    eval_providers.CONTEXT_IR_PROVIDER,
    eval_providers.LEXICAL_TOP_K_FILES_PROVIDER,
    eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
)
QUERY = (
    "Fix unsupported dynamic import loader.import_module(name) "
    "while keeping probe digest output aligned"
)
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:6:13"
UNSUPPORTED_SITE_ID = "site:call:main.py:6:13"


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


def test_dynamic_import_root_alias_probe_task_resolves_expected_selectors() -> None:
    """The root importlib alias probe resolves symbol and boundary selectors."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_dynamic_import_root_alias_probe"
    assert setup.task.fixture_id == "oracle_signal_dynamic_import_root_alias_probe"
    assert len(setup.task.expected_selectors) == 3
    assert isinstance(setup.task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(setup.task.expected_selectors[2], UnsupportedOracleSelector)
    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.load_weather_plugin",
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


def test_dynamic_import_root_alias_probe_run_spec_loads_single_budget_matrix() -> None:
    """The run spec stays at 1 task x 1 budget x 3 providers."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_dynamic_import_root_alias_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_dynamic_import_root_alias_probe"
    assert case.task_path == (
        "evals/tasks/oracle_signal_dynamic_import_root_alias_probe.json"
    )
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_dynamic_import_root_alias_probe_fixture_uses_only_alias_shape() -> None:
    """The fixture preserves only ``import importlib as loader`` alias form."""
    source = (FIXTURE_ROOT / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    observations = load_fixture_dynamic_import_runtime_observations(FIXTURE_ROOT)

    aliased_importlib_imports = [
        node
        for node in module.body
        if isinstance(node, ast.Import)
        and any(
            alias.name == "importlib" and alias.asname == "loader"
            for alias in node.names
        )
    ]
    plain_importlib_imports = [
        node
        for node in module.body
        if isinstance(node, ast.Import)
        and any(
            alias.name == "importlib" and alias.asname is None for alias in node.names
        )
    ]
    importlib_from_imports = [
        node
        for node in module.body
        if isinstance(node, ast.ImportFrom) and node.module == "importlib"
    ]
    root_alias_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "import_module"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "loader"
    ]
    forbidden_root_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "import_module"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "importlib"
    ]
    forbidden_name_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"__import__", "import_module", "load_module"}
    ]
    probe_function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "load_weather_plugin"
    )
    name_assignment = next(
        statement
        for statement in probe_function.body
        if isinstance(statement, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "name"
            for target in statement.targets
        )
    )
    plugin_name = cast(ast.Constant, name_assignment.value)

    assert source.count("import importlib as loader") == 1
    assert source.count('name = "plugins.weather"') == 1
    assert source.count("loader.import_module(name)") == 1
    assert "import importlib\n" not in source
    assert "from importlib import import_module" not in source
    assert 'import_module("plugins.weather")' not in source
    assert "__import__(name)" not in source
    assert "import_module(name, " not in source
    assert "globals" not in source
    assert "locals" not in source
    assert "fromlist" not in source
    assert len(aliased_importlib_imports) == 1
    assert plain_importlib_imports == []
    assert importlib_from_imports == []
    assert len(root_alias_calls) == 1
    assert len(root_alias_calls[0].args) == 1
    assert root_alias_calls[0].keywords == []
    assert isinstance(root_alias_calls[0].args[0], ast.Name)
    assert root_alias_calls[0].args[0].id == "name"
    assert forbidden_root_calls == []
    assert forbidden_name_calls == []
    assert plugin_name.value == "plugins.weather"
    assert len(observations) == 1
    assert observations[0].site.site_id == UNSUPPORTED_SITE_ID
    assert observations[0].site.snippet == "loader.import_module(name)"
    assert observations[0].site.span.start_line == 6
    assert observations[0].site.span.start_column == 13
    assert observations[0].site.span.end_line == 6
    assert observations[0].site.span.end_column == 39
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (("imported_module", "plugins.weather"),)
    assert observations[0].durable_payload_reference


def test_dynamic_import_root_alias_probe_assets_stay_internal() -> None:
    """The root importlib alias probe stays internal and adds no public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_dynamic_import_root_alias_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_dynamic_import_root_alias_probe")


def test_dynamic_import_root_alias_probe_keeps_runtime_module_out_of_static_edges() -> (
    None
):
    """Dynamic runtime evidence does not turn the imported module into static proof."""
    setup = setup_eval_oracle_task(TASK_PATH)
    program = setup.semantic_program
    symbols_by_id = program.resolved_symbols
    load_weather_symbol_id = next(
        symbol.symbol_id
        for symbol in symbols_by_id.values()
        if symbol.qualified_name == "main.load_weather_plugin"
    )
    weather_symbol_ids = {
        symbol.symbol_id
        for symbol in symbols_by_id.values()
        if symbol.definition_site.file_path == "plugins/weather.py"
    }
    weather_module_symbols = [
        symbol
        for symbol in symbols_by_id.values()
        if symbol.qualified_name == "plugins.weather"
    ]

    assert weather_symbol_ids
    assert weather_module_symbols
    assert all(
        symbol.definition_site.file_path == "plugins/weather.py"
        for symbol in weather_module_symbols
    )
    assert all(
        resolved_import.target_qualified_name != "plugins.weather"
        for resolved_import in program.resolved_imports
    )
    assert all(
        UNSUPPORTED_UNIT_ID
        not in (dependency.source_symbol_id, dependency.target_symbol_id)
        for dependency in program.proven_dependencies
    )
    assert all(
        dependency.evidence_site_id != UNSUPPORTED_SITE_ID
        for dependency in program.proven_dependencies
    )
    assert all(
        not (
            dependency.source_symbol_id == load_weather_symbol_id
            and dependency.target_symbol_id in weather_symbol_ids
        )
        for dependency in program.proven_dependencies
    )
    assert all(
        selector.resolved_unit_id not in weather_symbol_ids
        for selector in setup.resolved_selectors
    )


def test_dynamic_import_root_alias_probe_run_executes_with_runtime_provenance(
    tmp_path: Path,
) -> None:
    """Context IR attaches additive runtime provenance while truth stays opaque."""
    ledger_path = tmp_path / "dynamic_import_root_alias_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_dynamic_import_root_alias_probe_matrix"
    assert execution.record_count == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert len(records) == len(PROBE_PROVIDERS) * len(PROBE_BUDGETS)
    assert {(record["provider_name"], record["budget"]) for record in records} == {
        (provider_name, budget)
        for provider_name in PROBE_PROVIDERS
        for budget in PROBE_BUDGETS
    }

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
    selected_units = _selected_units(record)
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
    assert record["budget"] == 220
    assert UNSUPPORTED_UNIT_ID in cast(list[str], record["selected_unit_ids"])
    assert all(
        "plugins/weather.py" not in cast(str, unit["unit_id"])
        for unit in selected_units
    )
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
        "imported_module": "plugins.weather"
    }

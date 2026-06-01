"""Root ``importlib.import_module("plugins.weather")`` eval pilot tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_providers as eval_providers
import context_ir.eval_runs as eval_runs
import context_ir.runtime_probe_results as runtime_probe_results
import context_ir.semantic_types as semantic_types
import context_ir.tool_facade as tool_facade
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
    REPO_ROOT / "evals" / "fixtures" / "oracle_signal_dynamic_import_root_literal_probe"
)
TASK_PATH = (
    REPO_ROOT
    / "evals"
    / "tasks"
    / "oracle_signal_dynamic_import_root_literal_probe.json"
)
RUN_SPEC_PATH = (
    REPO_ROOT
    / "evals"
    / "run_specs"
    / "oracle_signal_dynamic_import_root_literal_probe_matrix.json"
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
    (eval_providers.LEXICAL_TOP_K_FILES_PROVIDER, 100): ["plugins/__init__.py"],
    (eval_providers.LEXICAL_TOP_K_FILES_PROVIDER, 220): [
        "main.py",
        "plugins/__init__.py",
        "plugins/weather.py",
    ],
    (eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER, 100): [],
    (eval_providers.IMPORT_NEIGHBORHOOD_FILES_PROVIDER, 220): [
        "main.py",
        "plugins/__init__.py",
    ],
}
QUERY = (
    'Fix unsupported dynamic import importlib.import_module("plugins.weather") '
    "while keeping probe digest output aligned"
)
UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:5:13"
UNSUPPORTED_SITE_ID = "site:call:main.py:5:13"
CONTEXT_IR_SELECTED_UNIT_IDS = (
    "def:main.py:main.load_weather_plugin",
    UNSUPPORTED_UNIT_ID,
    "frontier:call:main.py:6:11",
)
DEFAULT_LOCAL_PROVIDER_SELECTED_UNIT_IDS = (
    UNSUPPORTED_UNIT_ID,
    "def:main.py:main.load_weather_plugin",
    "frontier:call:main.py:6:11",
)
UNSUPPORTED_DYNAMIC_IMPORT_SIBLING_TASK_IDS = (
    "oracle_signal_dynamic_import_builtin_probe",
    "oracle_signal_dynamic_import_builtins_alias_probe",
    "oracle_signal_dynamic_import_builtins_attr_probe",
    "oracle_signal_dynamic_import_root_alias_probe",
    "oracle_signal_dynamic_import_root_probe",
)


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


def test_dynamic_import_root_literal_probe_resolves_expected_selectors() -> None:
    """The root literal probe resolves the intended symbol and boundary selectors."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_signal_dynamic_import_root_literal_probe"
    assert setup.task.fixture_id == "oracle_signal_dynamic_import_root_literal_probe"
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


def test_dynamic_import_root_literal_probe_run_spec_loads_two_budget_matrix() -> None:
    """The run spec stays at 1 task x 2 budgets x 3 providers."""
    spec = eval_runs.load_eval_run_spec(RUN_SPEC_PATH)

    assert spec.plan_id == "oracle_signal_dynamic_import_root_literal_probe_matrix"
    assert len(spec.cases) == 1
    case = spec.cases[0]
    assert case.case_id == "signal_dynamic_import_root_literal_probe"
    assert case.task_path == (
        "evals/tasks/oracle_signal_dynamic_import_root_literal_probe.json"
    )
    assert case.query == QUERY
    assert case.budgets == PROBE_BUDGETS
    assert case.providers == PROBE_PROVIDERS


def test_dynamic_import_root_literal_probe_fixture_uses_only_literal_shape() -> None:
    """The fixture preserves only the root-module literal importlib call."""
    source = (FIXTURE_ROOT / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    observations = load_fixture_dynamic_import_runtime_observations(FIXTURE_ROOT)

    importlib_imports = [
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
    root_importlib_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "import_module"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "importlib"
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
    forbidden_name_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"__import__", "import_module", "load_module"}
    ]
    forbidden_loader_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "import_module"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "loader"
    ]
    call_arg = root_importlib_calls[0].args[0]

    assert source.count("import importlib") == 1
    assert source.count('module = importlib.import_module("plugins.weather")') == 1
    assert 'name = "plugins.weather"' not in source
    assert "importlib.import_module(name)" not in source
    assert "from importlib import import_module" not in source
    assert "__import__(" not in source
    assert "load_module(" not in source
    assert "loader.import_module(" not in source
    assert len(importlib_imports) == 1
    assert importlib_from_imports == []
    assert len(root_importlib_calls) == 1
    assert len(root_importlib_calls[0].args) == 1
    assert root_importlib_calls[0].keywords == []
    assert isinstance(call_arg, ast.Constant)
    assert call_arg.value == "plugins.weather"
    assert name_assignments == []
    assert forbidden_name_calls == []
    assert forbidden_loader_calls == []
    assert len(observations) == 1
    assert observations[0].site.site_id == UNSUPPORTED_SITE_ID
    assert observations[0].site.snippet == (
        'importlib.import_module("plugins.weather")'
    )
    assert observations[0].site.span.start_line == 5
    assert observations[0].site.span.start_column == 13
    assert observations[0].site.span.end_line == 5
    assert observations[0].site.span.end_column == 55
    assert tuple(
        (field.key, field.value) for field in observations[0].normalized_payload
    ) == (("imported_module", "plugins.weather"),)
    assert observations[0].durable_payload_reference


def test_dynamic_import_root_literal_probe_assets_stay_internal() -> None:
    """The root literal probe remains internal and does not widen public exports."""
    assert FIXTURE_ROOT.is_relative_to(REPO_ROOT / "evals")
    assert TASK_PATH.is_relative_to(REPO_ROOT / "evals")
    assert RUN_SPEC_PATH.is_relative_to(REPO_ROOT / "evals")
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "oracle_signal_dynamic_import_root_literal_probe" not in context_ir.__all__
    assert not hasattr(context_ir, "oracle_signal_dynamic_import_root_literal_probe")


def test_root_literal_probe_keeps_runtime_module_out_of_static_proof() -> None:
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


def test_root_literal_probe_default_local_provider_replays_exact_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default local-Python provider admits only this dynamic-import literal."""
    captured_responses: list[
        tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileResponse
    ] = []
    real_recompile = eval_providers.tool_facade.recompile_repository_context_with_dynamic_import_local_python_subprocess  # noqa: E501

    def capture_dynamic_import_recompile(
        recompile_request: (
            tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileRequest
        ),
    ) -> tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileResponse:
        response = real_recompile(recompile_request)
        captured_responses.append(response)
        return response

    monkeypatch.setattr(
        eval_providers.tool_facade,
        "recompile_repository_context_with_dynamic_import_local_python_subprocess",
        capture_dynamic_import_recompile,
    )

    result = eval_providers.build_context_ir_default_local_python_subprocess_pack(
        eval_providers.EvalProviderRequest(
            repo_root=FIXTURE_ROOT,
            task_id="oracle_signal_dynamic_import_root_literal_probe",
            query=QUERY,
            budget=220,
        )
    )
    unsupported_unit = next(
        unit
        for unit in result.metadata.selected_units
        if unit.unit_id == UNSUPPORTED_UNIT_ID
    )
    static_units = tuple(
        unit
        for unit in result.metadata.selected_units
        if unit.unit_id != UNSUPPORTED_UNIT_ID
    )
    provenance_record = result.runtime_provenance_records[0]
    origin_detail = cast(dict[str, object], json.loads(provenance_record.origin_detail))
    previous_response = eval_providers.tool_facade.compile_repository_context(
        tool_facade.SemanticContextRequest(
            repo_root=FIXTURE_ROOT,
            query=QUERY,
            budget=220,
        )
    )
    fixture = eval_providers._default_local_python_subprocess_fixture(
        "oracle_signal_dynamic_import_root_literal_probe"
    )
    miss_evidence = semantic_types.SemanticMissEvidence(
        kind=semantic_types.SemanticMissKind.ABSENT_SYMBOL,
        evidence='importlib.import_module("plugins.weather")',
    )
    diagnostic = eval_providers.diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    planned_request = (
        eval_providers._require_default_local_python_runtime_probe_request(
            diagnostic,
            fixture,
        )
    )
    weather_symbol_ids = {
        symbol.symbol_id
        for symbol in previous_response.program.resolved_symbols.values()
        if symbol.definition_site.file_path == "plugins/weather.py"
    }
    load_weather_symbol_id = next(
        symbol.symbol_id
        for symbol in previous_response.program.resolved_symbols.values()
        if symbol.qualified_name == "main.load_weather_plugin"
    )

    assert result.provider_name == (
        eval_providers.CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    )
    assert result.task_id == "oracle_signal_dynamic_import_root_literal_probe"
    assert result.budget == 220
    assert result.selected_files == ()
    assert result.selected_unit_ids == DEFAULT_LOCAL_PROVIDER_SELECTED_UNIT_IDS
    assert result.warnings == ()
    assert planned_request.subject_id == UNSUPPORTED_UNIT_ID
    assert planned_request.boundary_text == (
        'importlib.import_module("plugins.weather")'
    )
    assert (
        planned_request.family_label is eval_providers.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert planned_request.form_label == "dynamic_import:importlib.import_module/1"
    assert planned_request.replay_target_seed == "main.load_weather_plugin"
    assert planned_request.replay_selector_seed == (
        "call:main.load_weather_plugin:dynamic_import:"
        "importlib.import_module/1@main.py:5:13:5:55"
    )
    assert len(captured_responses) == 1
    runner_attempts = captured_responses[0].runner_attempt_collection.attempts
    runner_results = captured_responses[
        0
    ].runner_attempt_collection.result_batch.results
    assert len(runner_attempts) == 1
    assert len(runner_results) == 1
    assert runner_attempts[0].request == planned_request
    assert runner_attempts[0].outcome is (
        runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    )
    assert runner_attempts[0].observed_replay_inputs == ()
    assert tuple(
        (field.key, field.value) for field in runner_attempts[0].normalized_payload
    ) == (("imported_module", "plugins.weather"),)
    assert isinstance(
        runner_results[0],
        runtime_probe_results.RuntimeProbeObservedResult,
    )
    assert runner_results[0].request == planned_request
    assert tuple(
        (field.key, field.value) for field in runner_results[0].normalized_payload
    ) == (("imported_module", "plugins.weather"),)
    assert len(result.runtime_provenance_records) == 1
    assert origin_detail["normalized_payload"] == {"imported_module": "plugins.weather"}
    assert origin_detail["replay_target"] == "main.load_weather_plugin"
    assert origin_detail["replay_selector"] == (
        "call:main.load_weather_plugin:dynamic_import:"
        "importlib.import_module/1@main.py:5:13:5:55"
    )
    assert "observed_replay_inputs" not in origin_detail
    assert unsupported_unit.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        unsupported_unit.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported_unit.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported_unit.has_attached_runtime_provenance is True
    assert unsupported_unit.attached_runtime_provenance_record_ids == (
        provenance_record.record_id,
    )
    assert all(
        unit.primary_capability_tier is not CapabilityTier.RUNTIME_BACKED
        for unit in result.metadata.selected_units
    )
    assert all(
        unit.primary_capability_tier
        in {CapabilityTier.STATICALLY_PROVED, CapabilityTier.HEURISTIC_FRONTIER}
        for unit in static_units
    )
    assert all(unit.has_attached_runtime_provenance is False for unit in static_units)
    assert all(
        "plugins/weather.py" not in unit.unit_id
        and "plugins.weather" not in unit.unit_id
        for unit in result.metadata.selected_units
    )
    assert all(
        resolved_import.target_qualified_name != "plugins.weather"
        for resolved_import in previous_response.program.resolved_imports
    )
    assert all(
        dependency.evidence_site_id != UNSUPPORTED_SITE_ID
        for dependency in previous_response.program.proven_dependencies
    )
    assert all(
        not (
            dependency.source_symbol_id == load_weather_symbol_id
            and dependency.target_symbol_id in weather_symbol_ids
        )
        for dependency in previous_response.program.proven_dependencies
    )


def test_root_literal_probe_default_local_provider_rejects_wrong_plan_fields() -> None:
    """The provider fails closed when the planned probe identity drifts."""
    previous_response = eval_providers.tool_facade.compile_repository_context(
        tool_facade.SemanticContextRequest(
            repo_root=FIXTURE_ROOT,
            query=QUERY,
            budget=220,
        )
    )
    fixture = eval_providers._default_local_python_subprocess_fixture(
        "oracle_signal_dynamic_import_root_literal_probe"
    )
    miss_evidence = semantic_types.SemanticMissEvidence(
        kind=semantic_types.SemanticMissKind.ABSENT_SYMBOL,
        evidence='importlib.import_module("plugins.weather")',
    )
    diagnostic = eval_providers.diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    assert len(plan.requests) == 1
    object.__setattr__(
        plan.requests[0], "replay_target_seed", "main.render_probe_digest"
    )

    with pytest.raises(ValueError, match="wrong replay target"):
        eval_providers._require_default_local_python_runtime_probe_request(
            diagnostic,
            fixture,
        )


@pytest.mark.parametrize("task_id", UNSUPPORTED_DYNAMIC_IMPORT_SIBLING_TASK_IDS)
def test_root_literal_probe_default_local_provider_rejects_dynamic_import_siblings(
    task_id: str,
) -> None:
    """Dynamic-import sibling forms remain outside this exact provider slice."""
    sibling_fixture_root = REPO_ROOT / "evals" / "fixtures" / task_id

    with pytest.raises(ValueError, match="only supports"):
        eval_providers.build_context_ir_default_local_python_subprocess_pack(
            eval_providers.EvalProviderRequest(
                repo_root=sibling_fixture_root,
                task_id=task_id,
                query=QUERY,
                budget=220,
            )
        )


def test_root_literal_probe_run_executes_with_additive_runtime_provenance(
    tmp_path: Path,
) -> None:
    """Context IR attaches runtime provenance while primary truth stays opaque."""
    ledger_path = tmp_path / "dynamic_import_root_literal_probe.jsonl"

    execution = eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        ledger_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    records = _parsed_ledger_records(ledger_path)
    assert execution.plan_id == "oracle_signal_dynamic_import_root_literal_probe_matrix"
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
            expected_selected_files = EXPECTED_BASELINE_SELECTED_FILES[
                (provider_name, budget)
            ]
            assert baseline_record["selected_files"] == expected_selected_files
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
        unsupported_selector = next(
            (
                selector
                for selector in _resolved_selectors(record)
                if selector["resolved_unit_id"] == UNSUPPORTED_UNIT_ID
            ),
            None,
        )
        unsupported_unit = next(
            (unit for unit in selected_units if unit["unit_id"] == UNSUPPORTED_UNIT_ID),
            None,
        )
        selected_unit_ids = cast(list[str], record["selected_unit_ids"])

        assert record["spec_version"] == "v1"
        assert record["provider_name"] == eval_providers.CONTEXT_IR_PROVIDER
        assert record["budget"] == budget
        assert unsupported_selector is not None
        assert record["selected_files"] == []
        assert tuple(selected_unit_ids) == CONTEXT_IR_SELECTED_UNIT_IDS
        assert UNSUPPORTED_UNIT_ID in selected_unit_ids
        assert unsupported_unit is not None
        assert metrics["uncertainty_honesty"] == 1.0
        assert all(
            "plugins/weather.py" not in cast(str, unit["unit_id"])
            for unit in selected_units
        )
        assert unsupported_selector["primary_capability_tier"] == "unsupported/opaque"
        assert unsupported_selector["primary_evidence_origin"] == (
            "unsupported_reason_code"
        )
        assert unsupported_selector["primary_replay_status"] == "opaque_boundary"
        assert unsupported_selector["has_attached_runtime_provenance"] is True
        if unsupported_unit is not None:
            assert unsupported_unit["primary_capability_tier"] == "unsupported/opaque"
            assert (
                unsupported_unit["primary_evidence_origin"] == "unsupported_reason_code"
            )
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

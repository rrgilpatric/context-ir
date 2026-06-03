"""Deterministic internal eval context providers and baselines."""

from __future__ import annotations

import ast
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import context_ir.tool_facade as tool_facade
from context_ir.eval_oracles import (
    load_fixture_delattr_runtime_observations,
    load_fixture_dir_runtime_observations,
    load_fixture_dynamic_import_runtime_observations,
    load_fixture_eval_runtime_observations,
    load_fixture_exec_runtime_observations,
    load_fixture_getattr_runtime_observations,
    load_fixture_globals_runtime_observations,
    load_fixture_hasattr_runtime_observations,
    load_fixture_locals_runtime_observations,
    load_fixture_metaclass_behavior_runtime_observations,
    load_fixture_setattr_runtime_observations,
    load_fixture_vars_runtime_observations,
)
from context_ir.parser import _eligible_python_source_files
from context_ir.runtime_probe_requests import RuntimeProbeFamily, RuntimeProbeRequest
from context_ir.runtime_probe_results import (
    RuntimeProbeObservedResult,
    RuntimeProbeReplayField,
)
from context_ir.semantic_diagnostics import diagnose_semantic_miss
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
    RepositorySnapshotBasis,
    SemanticDiagnosticResult,
    SemanticMissEvidence,
    SemanticMissKind,
    SemanticOptimizationWarning,
    SemanticProvenanceRecord,
    SemanticSelectionRecord,
    SemanticUnitTraceSummary,
)

CONTEXT_IR_PROVIDER = "context_ir"
CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER = (
    "context_ir_default_local_python_subprocess"
)
LEXICAL_TOP_K_FILES_PROVIDER = "lexical_top_k_files"
IMPORT_NEIGHBORHOOD_FILES_PROVIDER = "import_neighborhood_files"
FILE_ORDER_FLOOR_PROVIDER = "file_order_floor"
PROVIDER_ALGORITHM_VERSION = "v1"
LEXICAL_MAX_CANDIDATES = 8
IMPORT_SEED_COUNT = 2
_LOCALS_PROBE_TASK_ID = "oracle_signal_locals_probe"
_LOCALS_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:3:11"
_LOCALS_RUNTIME_PAYLOAD = (("lookup_outcome", "returned_namespace"),)
_GLOBALS_PROBE_TASK_ID = "oracle_signal_globals_probe"
_GLOBALS_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
_GLOBALS_RUNTIME_PAYLOAD = (("lookup_outcome", "returned_namespace"),)
_VARS_ZERO_PROBE_TASK_ID = "oracle_signal_vars_zero_probe"
_VARS_ZERO_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
_VARS_ZERO_RUNTIME_PAYLOAD = (("lookup_outcome", "returned_namespace"),)
_DIR_ZERO_PROBE_TASK_ID = "oracle_signal_dir_zero_probe"
_DIR_ZERO_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
_DIR_ZERO_RUNTIME_PAYLOAD = (("listing_entry_count", "0"),)
_HASATTR_PROBE_TASK_ID = "oracle_signal_hasattr_probe"
_HASATTR_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
_HASATTR_RUNTIME_PAYLOAD = (("attribute_present", "true"),)
_HASATTR_FALSE_PROBE_TASK_ID = "oracle_signal_hasattr_false_probe"
_HASATTR_FALSE_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
_HASATTR_FALSE_RUNTIME_PAYLOAD = (("attribute_present", "false"),)
_GETATTR_PROBE_TASK_ID = "oracle_signal_getattr_probe"
_GETATTR_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
_GETATTR_RUNTIME_PAYLOAD = (("lookup_outcome", "returned_value"),)
_GETATTR_ATTRIBUTE_ERROR_PROBE_TASK_ID = "oracle_signal_getattr_attribute_error_probe"
_GETATTR_ATTRIBUTE_ERROR_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
_GETATTR_ATTRIBUTE_ERROR_RUNTIME_PAYLOAD = (
    ("lookup_outcome", "raised_attribute_error"),
)
_HASATTR_LITERAL_PROBE_TASK_ID = "oracle_signal_hasattr_literal_probe"
_HASATTR_LITERAL_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
_HASATTR_LITERAL_RUNTIME_PAYLOAD = (("attribute_present", "true"),)
_GETATTR_LITERAL_PROBE_TASK_ID = "oracle_signal_getattr_literal_probe"
_GETATTR_LITERAL_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:2:11"
_GETATTR_LITERAL_RUNTIME_PAYLOAD = (("lookup_outcome", "returned_value"),)
_DYNAMIC_IMPORT_ROOT_LITERAL_PROBE_TASK_ID = (
    "oracle_signal_dynamic_import_root_literal_probe"
)
_DYNAMIC_IMPORT_ROOT_PROBE_TASK_ID = "oracle_signal_dynamic_import_root_probe"
_DYNAMIC_IMPORT_ROOT_ALIAS_PROBE_TASK_ID = (
    "oracle_signal_dynamic_import_root_alias_probe"
)
_DYNAMIC_IMPORT_BUILTIN_PROBE_TASK_ID = "oracle_signal_dynamic_import_builtin_probe"
_DYNAMIC_IMPORT_BUILTINS_ATTR_PROBE_TASK_ID = (
    "oracle_signal_dynamic_import_builtins_attr_probe"
)
_DYNAMIC_IMPORT_BUILTINS_ALIAS_PROBE_TASK_ID = (
    "oracle_signal_dynamic_import_builtins_alias_probe"
)
_DYNAMIC_IMPORT_IMPORTED_NAME_PROBE_TASK_ID = (
    "oracle_signal_dynamic_import_imported_name_probe"
)
_DYNAMIC_IMPORT_IMPORTED_ALIAS_PROBE_TASK_ID = (
    "oracle_signal_dynamic_import_imported_alias_probe"
)
_DYNAMIC_IMPORT_LITERAL_PROBE_TASK_ID = "oracle_signal_dynamic_import_probe"
_DYNAMIC_IMPORT_RUNTIME_PAYLOAD = (("imported_module", "plugins.weather"),)
_DYNAMIC_IMPORT_REPLAY_TARGET_SEED = "main.load_weather_plugin"
_DYNAMIC_IMPORT_SOURCE_FILE_PATH = "main.py"
_SETATTR_LITERAL_PROBE_TASK_ID = "oracle_signal_setattr_literal_probe"
_SETATTR_LITERAL_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:7:4"
_SETATTR_LITERAL_RUNTIME_PAYLOAD = (("mutation_outcome", "returned_none"),)
_DELATTR_LITERAL_PROBE_TASK_ID = "oracle_signal_delattr_literal_probe"
_DELATTR_LITERAL_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:7:4"
_DELATTR_LITERAL_RUNTIME_PAYLOAD = (("mutation_outcome", "deleted_attribute"),)
_EXEC_PROBE_TASK_ID = "oracle_signal_exec_probe"
_EXEC_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:3:4"
_EXEC_RUNTIME_PAYLOAD = (
    ("execution_outcome", "completed"),
    ("statement_kind", "pass"),
)
_EVAL_PROBE_TASK_ID = "oracle_signal_eval_probe"
_EVAL_UNSUPPORTED_UNIT_ID = "unsupported:call:main.py:3:11"
_EVAL_RUNTIME_PAYLOAD = (
    ("evaluation_outcome", "returned_value"),
    ("result_type", "builtins.str"),
)
_METACLASS_BEHAVIOR_PROBE_TASK_ID = "oracle_signal_metaclass_behavior_probe"
_METACLASS_BEHAVIOR_UNSUPPORTED_UNIT_ID = (
    "unsupported:metaclass:main.py:9:20:def:main.py:main.Example:1"
)
_METACLASS_BEHAVIOR_RUNTIME_PAYLOAD = (
    ("class_creation_outcome", "created_class"),
    ("created_class_qualified_name", "main.Example"),
    ("selected_metaclass_qualified_name", "main.Meta"),
)
_DEFAULT_LOCAL_PYTHON_INVOCATION_CONTRACT_REVISION = (
    "runtime-probe-local-python-subprocess:context-ir-eval-provider.1"
)
_DEFAULT_LOCAL_PYTHON_COMPLETION_CONTRACT_REVISION = (
    "runtime-probe-local-python-completion:context-ir-eval-provider.1"
)
_DEFAULT_LOCAL_PYTHON_PROBE_CONTRACT_REVISION = (
    "runtime-probe-contract:context-ir-eval-provider.1"
)
_DEFAULT_LOCAL_PYTHON_RUNNER_CONTRACT_REVISION = (
    "runtime-probe-runner:context-ir-eval-provider.1"
)
_SEMANTIC_SELECTED_UNIT_PROVIDERS = frozenset(
    {
        CONTEXT_IR_PROVIDER,
        CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER,
    }
)

_RAW_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9]+")
_CAMEL_PART_PATTERN = re.compile(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|[0-9]+")


@dataclass(frozen=True)
class EvalProviderRequest:
    """Inputs shared by deterministic eval context providers."""

    repo_root: Path | str
    task_id: str
    query: str
    budget: int

    def __post_init__(self) -> None:
        """Reject invalid task identity and impossible budgets."""
        if not self.task_id:
            raise ValueError("task_id must be non-empty")
        if self.budget < 0:
            raise ValueError("budget must be >= 0")


@dataclass(frozen=True)
class EvalProviderConfig:
    """Typed provider configuration recorded with each provider output."""

    max_candidates: int | None = None
    seed_count: int | None = None
    diagnostic_only: bool = False


@dataclass(frozen=True)
class LexicalFileScore:
    """Deterministic lexical score metadata for one repository file."""

    file_path: str
    score: float
    token_count: int


@dataclass(frozen=True)
class EvalSelectedUnit:
    """Structured selected-unit trace metadata preserved for eval scoring."""

    unit_id: str
    detail: str
    token_count: int
    basis: str
    reason: str | None = None
    edit_score: float | None = None
    support_score: float | None = None
    primary_capability_tier: CapabilityTier | None = None
    primary_evidence_origin: EvidenceOriginKind | None = None
    primary_replay_status: ReplayStatus | None = None
    has_attached_runtime_provenance: bool | None = None
    attached_runtime_provenance_record_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject empty identifiers and impossible selection metadata."""
        if not self.unit_id:
            raise ValueError("unit_id must be non-empty")
        if not self.detail:
            raise ValueError("detail must be non-empty")
        if self.token_count < 0:
            raise ValueError("token_count must be >= 0")
        if not self.basis:
            raise ValueError("basis must be non-empty")
        if self.reason == "":
            raise ValueError("reason must be non-empty when provided")
        if self.edit_score is not None and not 0.0 <= self.edit_score <= 1.0:
            raise ValueError("edit_score must be within [0.0, 1.0]")
        if self.support_score is not None and not 0.0 <= self.support_score <= 1.0:
            raise ValueError("support_score must be within [0.0, 1.0]")
        if self.primary_capability_tier is None:
            if (
                self.primary_evidence_origin is not None
                or self.primary_replay_status is not None
                or self.has_attached_runtime_provenance is not None
                or self.attached_runtime_provenance_record_ids
            ):
                raise ValueError(
                    "selected-unit tier snapshot fields must be absent together"
                )
            return
        if (
            self.primary_evidence_origin is None
            or self.primary_replay_status is None
            or self.has_attached_runtime_provenance is None
        ):
            raise ValueError(
                "selected-unit tier snapshot fields must be present together"
            )
        if self.primary_capability_tier is CapabilityTier.RUNTIME_BACKED:
            raise ValueError(
                "primary_capability_tier may not be runtime-backed; "
                "runtime evidence remains additive"
            )
        if (
            self.has_attached_runtime_provenance
            and not self.attached_runtime_provenance_record_ids
        ):
            raise ValueError("attached runtime provenance requires record identifiers")
        if (
            not self.has_attached_runtime_provenance
            and self.attached_runtime_provenance_record_ids
        ):
            raise ValueError(
                "attached runtime provenance record identifiers require support=True"
            )


@dataclass(frozen=True)
class EvalProviderWarning:
    """Structured provider warning metadata preserved for eval scoring."""

    code: str
    unit_id: str | None
    message: str

    def __post_init__(self) -> None:
        """Reject empty warning fields."""
        if not self.code:
            raise ValueError("code must be non-empty")
        if self.unit_id == "":
            raise ValueError("unit_id must be non-empty when provided")
        if not self.message:
            raise ValueError("message must be non-empty")


@dataclass(frozen=True)
class EvalProviderMetadata:
    """Structured provider metadata reserved for later eval scoring and reports."""

    diagnostic_only: bool = False
    candidate_files: tuple[str, ...] = ()
    omitted_candidate_files: tuple[str, ...] = ()
    lexical_scores: tuple[LexicalFileScore, ...] = ()
    selected_units: tuple[EvalSelectedUnit, ...] = ()
    warning_details: tuple[EvalProviderWarning, ...] = ()
    unresolved_unit_ids: tuple[str, ...] = ()
    unsupported_unit_ids: tuple[str, ...] = ()
    syntax_diagnostic_ids: tuple[str, ...] = ()
    semantic_diagnostic_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvalProviderResult:
    """Internal deterministic provider output for one eval task request."""

    provider_name: str
    provider_algorithm_version: str
    provider_config: EvalProviderConfig
    task_id: str
    query: str
    budget: int
    document: str
    total_tokens: int
    selected_files: tuple[str, ...]
    omitted_candidate_files: tuple[str, ...]
    selected_unit_ids: tuple[str, ...]
    omitted_unit_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    metadata: EvalProviderMetadata
    runtime_provenance_records: tuple[SemanticProvenanceRecord, ...] = ()

    def __post_init__(self) -> None:
        """Keep provider outputs budget-honest and internally consistent."""
        if not self.provider_name:
            raise ValueError("provider_name must be non-empty")
        if not self.provider_algorithm_version:
            raise ValueError("provider_algorithm_version must be non-empty")
        if not self.task_id:
            raise ValueError("task_id must be non-empty")
        if not self.document:
            raise ValueError("document must be non-empty")
        if self.budget < 0:
            raise ValueError("budget must be >= 0")
        if self.total_tokens < 0:
            raise ValueError("total_tokens must be >= 0")
        if self.total_tokens > self.budget:
            raise ValueError("provider output exceeds budget")
        if self.total_tokens != estimate_tokens(self.document):
            raise ValueError("total_tokens must match the provider token estimator")
        if self.omitted_candidate_files != self.metadata.omitted_candidate_files:
            raise ValueError("omitted_candidate_files must mirror metadata")
        provenance_record_ids = tuple(
            record.record_id for record in self.runtime_provenance_records
        )
        if len(provenance_record_ids) != len(set(provenance_record_ids)):
            raise ValueError("runtime_provenance_records must have unique record_ids")
        for record in self.runtime_provenance_records:
            if record.capability_tier is not CapabilityTier.RUNTIME_BACKED:
                raise ValueError(
                    "runtime_provenance_records must contain runtime-backed records"
                )
        if self.provider_name in _SEMANTIC_SELECTED_UNIT_PROVIDERS:
            if self.selected_unit_ids != tuple(
                unit.unit_id for unit in self.metadata.selected_units
            ):
                raise ValueError(
                    "selected_unit_ids must mirror structured selected-unit metadata"
                )
            if self.warnings != tuple(
                warning.code for warning in self.metadata.warning_details
            ):
                raise ValueError("warnings must mirror structured warning metadata")


@dataclass(frozen=True)
class _DefaultLocalPythonSubprocessFixture:
    """Exact eval fixture contract for the default local-Python subprocess provider."""

    unsupported_unit_id: str
    miss_evidence_text: str
    family_label: RuntimeProbeFamily
    form_label: str
    boundary_text: str
    replay_target_seed: str
    snapshot_id: str
    runtime_payload: tuple[tuple[str, str], ...]
    runtime_replay_input_tail: tuple[tuple[str, str], ...] = ()
    source_site_id: str | None = None
    source_file_path: str | None = None
    source_start_line: int | None = None
    source_start_column: int | None = None
    source_end_line: int | None = None
    source_end_column: int | None = None
    replay_selector_seed: str | None = None


@dataclass(frozen=True)
class _DynamicImportDefaultLocalFixtureContract:
    """Exact dynamic-import fixture metadata for the default local provider."""

    task_id: str
    unsupported_unit_id: str
    boundary_text: str
    form_label: str
    source_site_id: str | None = None
    source_start_line: int | None = None
    source_start_column: int | None = None
    source_end_line: int | None = None
    source_end_column: int | None = None
    replay_selector_seed: str | None = None
    context_budget: int | None = None


_DYNAMIC_IMPORT_DEFAULT_LOCAL_FIXTURE_CONTRACTS = (
    _DynamicImportDefaultLocalFixtureContract(
        task_id=_DYNAMIC_IMPORT_ROOT_LITERAL_PROBE_TASK_ID,
        unsupported_unit_id="unsupported:call:main.py:5:13",
        boundary_text='importlib.import_module("plugins.weather")',
        form_label="dynamic_import:importlib.import_module/1",
    ),
    _DynamicImportDefaultLocalFixtureContract(
        task_id=_DYNAMIC_IMPORT_ROOT_PROBE_TASK_ID,
        unsupported_unit_id="unsupported:call:main.py:6:13",
        boundary_text="importlib.import_module(name)",
        form_label="dynamic_import:importlib.import_module/1",
        source_site_id="site:call:main.py:6:13",
        source_start_line=6,
        source_start_column=13,
        source_end_line=6,
        source_end_column=42,
        replay_selector_seed=(
            "call:main.load_weather_plugin:dynamic_import:"
            "importlib.import_module/1@main.py:6:13:6:42"
        ),
        context_budget=220,
    ),
    _DynamicImportDefaultLocalFixtureContract(
        task_id=_DYNAMIC_IMPORT_ROOT_ALIAS_PROBE_TASK_ID,
        unsupported_unit_id="unsupported:call:main.py:6:13",
        boundary_text="loader.import_module(name)",
        form_label="dynamic_import:loader.import_module/1",
        source_site_id="site:call:main.py:6:13",
        source_start_line=6,
        source_start_column=13,
        source_end_line=6,
        source_end_column=39,
        replay_selector_seed=(
            "call:main.load_weather_plugin:dynamic_import:"
            "loader.import_module/1@main.py:6:13:6:39"
        ),
        context_budget=220,
    ),
    _DynamicImportDefaultLocalFixtureContract(
        task_id=_DYNAMIC_IMPORT_BUILTIN_PROBE_TASK_ID,
        unsupported_unit_id="unsupported:call:main.py:6:4",
        boundary_text="__import__(name)",
        form_label="dynamic_import:__import__/1",
        source_site_id="site:call:main.py:6:4",
        source_start_line=6,
        source_start_column=4,
        source_end_line=6,
        source_end_column=20,
        replay_selector_seed=(
            "call:main.load_weather_plugin:dynamic_import:__import__/1@main.py:6:4:6:20"
        ),
        context_budget=220,
    ),
    _DynamicImportDefaultLocalFixtureContract(
        task_id=_DYNAMIC_IMPORT_BUILTINS_ATTR_PROBE_TASK_ID,
        unsupported_unit_id="unsupported:call:main.py:7:4",
        boundary_text="builtins.__import__(name)",
        form_label="dynamic_import:builtins.__import__/1",
        source_site_id="site:call:main.py:7:4",
        source_start_line=7,
        source_start_column=4,
        source_end_line=7,
        source_end_column=29,
        replay_selector_seed=(
            "call:main.load_weather_plugin:dynamic_import:"
            "builtins.__import__/1@main.py:7:4:7:29"
        ),
        context_budget=220,
    ),
    _DynamicImportDefaultLocalFixtureContract(
        task_id=_DYNAMIC_IMPORT_BUILTINS_ALIAS_PROBE_TASK_ID,
        unsupported_unit_id="unsupported:call:main.py:7:4",
        boundary_text="loader.__import__(name)",
        form_label="dynamic_import:loader.__import__/1",
        source_site_id="site:call:main.py:7:4",
        source_start_line=7,
        source_start_column=4,
        source_end_line=7,
        source_end_column=27,
        replay_selector_seed=(
            "call:main.load_weather_plugin:dynamic_import:"
            "loader.__import__/1@main.py:7:4:7:27"
        ),
        context_budget=220,
    ),
    _DynamicImportDefaultLocalFixtureContract(
        task_id=_DYNAMIC_IMPORT_IMPORTED_NAME_PROBE_TASK_ID,
        unsupported_unit_id="unsupported:call:main.py:6:13",
        boundary_text="import_module(name)",
        form_label="dynamic_import:import_module/1",
        source_site_id="site:call:main.py:6:13",
        source_start_line=6,
        source_start_column=13,
        source_end_line=6,
        source_end_column=32,
        replay_selector_seed=(
            "call:main.load_weather_plugin:dynamic_import:"
            "import_module/1@main.py:6:13:6:32"
        ),
        context_budget=220,
    ),
    _DynamicImportDefaultLocalFixtureContract(
        task_id=_DYNAMIC_IMPORT_IMPORTED_ALIAS_PROBE_TASK_ID,
        unsupported_unit_id="unsupported:call:main.py:6:13",
        boundary_text="load_module(name)",
        form_label="dynamic_import:load_module/1",
        source_site_id="site:call:main.py:6:13",
        source_start_line=6,
        source_start_column=13,
        source_end_line=6,
        source_end_column=30,
        replay_selector_seed=(
            "call:main.load_weather_plugin:dynamic_import:"
            "load_module/1@main.py:6:13:6:30"
        ),
        context_budget=220,
    ),
    _DynamicImportDefaultLocalFixtureContract(
        task_id=_DYNAMIC_IMPORT_LITERAL_PROBE_TASK_ID,
        unsupported_unit_id="unsupported:call:main.py:5:13",
        boundary_text='import_module("plugins.weather")',
        form_label="dynamic_import:import_module/1",
        context_budget=180,
    ),
)


def _dynamic_import_default_local_python_subprocess_fixture(
    contract: _DynamicImportDefaultLocalFixtureContract,
) -> _DefaultLocalPythonSubprocessFixture:
    """Return the provider fixture encoded by one dynamic-import contract."""
    return _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=contract.unsupported_unit_id,
        miss_evidence_text=contract.boundary_text,
        family_label=RuntimeProbeFamily.DYNAMIC_IMPORT,
        form_label=contract.form_label,
        boundary_text=contract.boundary_text,
        replay_target_seed=_DYNAMIC_IMPORT_REPLAY_TARGET_SEED,
        snapshot_id=f"{contract.task_id}@default-local-python:v1",
        runtime_payload=_DYNAMIC_IMPORT_RUNTIME_PAYLOAD,
        source_site_id=contract.source_site_id,
        source_file_path=(
            _DYNAMIC_IMPORT_SOURCE_FILE_PATH
            if contract.source_site_id is not None
            else None
        ),
        source_start_line=contract.source_start_line,
        source_start_column=contract.source_start_column,
        source_end_line=contract.source_end_line,
        source_end_column=contract.source_end_column,
        replay_selector_seed=contract.replay_selector_seed,
    )


_DYNAMIC_IMPORT_DEFAULT_LOCAL_FIXTURES = {
    contract.task_id: _dynamic_import_default_local_python_subprocess_fixture(contract)
    for contract in _DYNAMIC_IMPORT_DEFAULT_LOCAL_FIXTURE_CONTRACTS
}
_DYNAMIC_IMPORT_DEFAULT_LOCAL_CONTEXT_BUDGETS = {
    contract.task_id: contract.context_budget
    for contract in _DYNAMIC_IMPORT_DEFAULT_LOCAL_FIXTURE_CONTRACTS
    if contract.context_budget is not None
}


_DEFAULT_LOCAL_PYTHON_SUBPROCESS_FIXTURES = {
    _LOCALS_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_LOCALS_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="locals()",
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label="runtime_mutation:locals/0",
        boundary_text="locals()",
        replay_target_seed="main.probe_local_namespace",
        snapshot_id="oracle_signal_locals_probe@default-local-python:v1",
        runtime_payload=_LOCALS_RUNTIME_PAYLOAD,
    ),
    _GLOBALS_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_GLOBALS_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="globals()",
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label="runtime_mutation:globals/0",
        boundary_text="globals()",
        replay_target_seed="main.probe_global_namespace",
        snapshot_id="oracle_signal_globals_probe@default-local-python:v1",
        runtime_payload=_GLOBALS_RUNTIME_PAYLOAD,
    ),
    _VARS_ZERO_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_VARS_ZERO_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="vars()",
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:vars/0",
        boundary_text="vars()",
        replay_target_seed="main.probe_local_namespace",
        snapshot_id="oracle_signal_vars_zero_probe@default-local-python:v1",
        runtime_payload=_VARS_ZERO_RUNTIME_PAYLOAD,
    ),
    _DIR_ZERO_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_DIR_ZERO_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="dir()",
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:dir/0",
        boundary_text="dir()",
        replay_target_seed="main.probe_directory",
        snapshot_id="oracle_signal_dir_zero_probe@default-local-python:v1",
        runtime_payload=_DIR_ZERO_RUNTIME_PAYLOAD,
    ),
    _HASATTR_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_HASATTR_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="hasattr(obj, name)",
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:hasattr/2",
        boundary_text="hasattr(obj, name)",
        replay_target_seed="main.probe_attribute",
        snapshot_id="oracle_signal_hasattr_probe@default-local-python:v1",
        runtime_payload=_HASATTR_RUNTIME_PAYLOAD,
    ),
    _HASATTR_FALSE_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_HASATTR_FALSE_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="hasattr(obj, name)",
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:hasattr/2",
        boundary_text="hasattr(obj, name)",
        replay_target_seed="main.probe_attribute",
        snapshot_id="oracle_signal_hasattr_false_probe@default-local-python:v1",
        runtime_payload=_HASATTR_FALSE_RUNTIME_PAYLOAD,
        runtime_replay_input_tail=(
            ("object_type", "builtins.int"),
            ("attribute_name", "definitely_missing_attribute"),
        ),
    ),
    _GETATTR_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_GETATTR_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="getattr(obj, name)",
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:getattr/2",
        boundary_text="getattr(obj, name)",
        replay_target_seed="main.probe_attribute",
        snapshot_id="oracle_signal_getattr_probe@default-local-python:v1",
        runtime_payload=_GETATTR_RUNTIME_PAYLOAD,
        runtime_replay_input_tail=(
            ("object_type", "builtins.int"),
            ("attribute_name", "bit_length"),
        ),
    ),
    _GETATTR_ATTRIBUTE_ERROR_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_GETATTR_ATTRIBUTE_ERROR_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="getattr(obj, name)",
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:getattr/2",
        boundary_text="getattr(obj, name)",
        replay_target_seed="main.probe_attribute",
        snapshot_id=(
            "oracle_signal_getattr_attribute_error_probe@default-local-python:v1"
        ),
        runtime_payload=_GETATTR_ATTRIBUTE_ERROR_RUNTIME_PAYLOAD,
        runtime_replay_input_tail=(
            ("object_type", "builtins.int"),
            ("attribute_name", "definitely_missing_attribute"),
        ),
    ),
    _HASATTR_LITERAL_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_HASATTR_LITERAL_UNSUPPORTED_UNIT_ID,
        miss_evidence_text='hasattr(obj, "bit_length")',
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:hasattr/2",
        boundary_text='hasattr(obj, "bit_length")',
        replay_target_seed="main.probe_literal_attribute",
        snapshot_id="oracle_signal_hasattr_literal_probe@default-local-python:v1",
        runtime_payload=_HASATTR_LITERAL_RUNTIME_PAYLOAD,
    ),
    _GETATTR_LITERAL_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_GETATTR_LITERAL_UNSUPPORTED_UNIT_ID,
        miss_evidence_text='getattr(obj, "bit_length")',
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label="reflective_builtin:getattr/2",
        boundary_text='getattr(obj, "bit_length")',
        replay_target_seed="main.probe_literal_attribute",
        snapshot_id="oracle_signal_getattr_literal_probe@default-local-python:v1",
        runtime_payload=_GETATTR_LITERAL_RUNTIME_PAYLOAD,
    ),
    **_DYNAMIC_IMPORT_DEFAULT_LOCAL_FIXTURES,
    _SETATTR_LITERAL_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_SETATTR_LITERAL_UNSUPPORTED_UNIT_ID,
        miss_evidence_text='setattr(obj, "flag", value)',
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label="runtime_mutation:setattr/3",
        boundary_text='setattr(obj, "flag", value)',
        replay_target_seed="main.probe_set_literal_attribute",
        snapshot_id="oracle_signal_setattr_literal_probe@default-local-python:v1",
        runtime_payload=_SETATTR_LITERAL_RUNTIME_PAYLOAD,
        runtime_replay_input_tail=(
            ("object_type", "main.ProbeTarget"),
            ("attribute_name", "flag"),
            ("assigned_value_type", "builtins.str"),
            ("assigned_value_literal", "ready"),
        ),
    ),
    _DELATTR_LITERAL_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_DELATTR_LITERAL_UNSUPPORTED_UNIT_ID,
        miss_evidence_text='delattr(obj, "flag")',
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label="runtime_mutation:delattr/2",
        boundary_text='delattr(obj, "flag")',
        replay_target_seed="main.probe_delete_literal_attribute",
        snapshot_id="oracle_signal_delattr_literal_probe@default-local-python:v1",
        runtime_payload=_DELATTR_LITERAL_RUNTIME_PAYLOAD,
    ),
    _EXEC_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_EXEC_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="exec(source)",
        family_label=RuntimeProbeFamily.EXEC_OR_EVAL,
        form_label="exec_or_eval:exec/1",
        boundary_text="exec(source)",
        replay_target_seed="main.probe_exec_source",
        snapshot_id="oracle_signal_exec_probe@default-local-python:v1",
        runtime_payload=_EXEC_RUNTIME_PAYLOAD,
    ),
    _EVAL_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_EVAL_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="eval(source)",
        family_label=RuntimeProbeFamily.EXEC_OR_EVAL,
        form_label="exec_or_eval:eval/1",
        boundary_text="eval(source)",
        replay_target_seed="main.probe_eval_source",
        snapshot_id="oracle_signal_eval_probe@default-local-python:v1",
        runtime_payload=_EVAL_RUNTIME_PAYLOAD,
    ),
    _METACLASS_BEHAVIOR_PROBE_TASK_ID: _DefaultLocalPythonSubprocessFixture(
        unsupported_unit_id=_METACLASS_BEHAVIOR_UNSUPPORTED_UNIT_ID,
        miss_evidence_text="metaclass=Meta",
        family_label=RuntimeProbeFamily.METACLASS_BEHAVIOR,
        form_label="metaclass_behavior:keyword",
        boundary_text="metaclass=Meta",
        replay_target_seed="main.Example",
        snapshot_id=("oracle_signal_metaclass_behavior_probe@default-local-python:v1"),
        runtime_payload=_METACLASS_BEHAVIOR_RUNTIME_PAYLOAD,
    ),
}


@dataclass(frozen=True)
class _BaselineFile:
    """Repository file candidate used by deterministic file baselines."""

    relative_path: str
    text: str
    token_count: int


@dataclass(frozen=True)
class _ScoredBaselineFile:
    """Lexically scored repository file candidate."""

    file: _BaselineFile
    score: float
    content_terms: Counter[str]
    path_terms: tuple[str, ...]


def estimate_tokens(text: str) -> int:
    """Estimate token count using the accepted eval provider heuristic."""
    return max(1, (len(text) + 3) // 4)


def lexical_tokens(text: str) -> tuple[str, ...]:
    """Tokenize text for deterministic lexical baseline scoring."""
    terms: list[str] = []
    for raw_token in _RAW_TOKEN_PATTERN.split(text):
        if not raw_token:
            continue
        terms.append(raw_token.lower())
        terms.extend(part.lower() for part in _CAMEL_PART_PATTERN.findall(raw_token))
    return tuple(term for term in terms if term)


def build_context_ir_provider_pack(request: EvalProviderRequest) -> EvalProviderResult:
    """Compile a Context IR provider pack through the accepted tool facade."""
    dynamic_import_runtime_observations = (
        load_fixture_dynamic_import_runtime_observations(request.repo_root)
    )
    eval_runtime_observations = load_fixture_eval_runtime_observations(
        request.repo_root
    )
    exec_runtime_observations = load_fixture_exec_runtime_observations(
        request.repo_root
    )
    getattr_runtime_observations = load_fixture_getattr_runtime_observations(
        request.repo_root
    )
    dir_runtime_observations = load_fixture_dir_runtime_observations(request.repo_root)
    hasattr_runtime_observations = load_fixture_hasattr_runtime_observations(
        request.repo_root
    )
    vars_runtime_observations = load_fixture_vars_runtime_observations(
        request.repo_root
    )
    globals_runtime_observations = load_fixture_globals_runtime_observations(
        request.repo_root
    )
    locals_runtime_observations = load_fixture_locals_runtime_observations(
        request.repo_root
    )
    setattr_runtime_observations = load_fixture_setattr_runtime_observations(
        request.repo_root
    )
    delattr_runtime_observations = load_fixture_delattr_runtime_observations(
        request.repo_root
    )
    metaclass_behavior_runtime_observations = (
        load_fixture_metaclass_behavior_runtime_observations(request.repo_root)
    )
    response = tool_facade.compile_repository_context(
        tool_facade.SemanticContextRequest(
            repo_root=request.repo_root,
            query=request.query,
            budget=request.budget,
            embed_fn=None,
            dynamic_import_runtime_observations=(
                dynamic_import_runtime_observations
                if dynamic_import_runtime_observations
                else None
            ),
            eval_runtime_observations=(
                eval_runtime_observations if eval_runtime_observations else None
            ),
            exec_runtime_observations=(
                exec_runtime_observations if exec_runtime_observations else None
            ),
            hasattr_runtime_observations=(
                hasattr_runtime_observations if hasattr_runtime_observations else None
            ),
            getattr_runtime_observations=(
                getattr_runtime_observations if getattr_runtime_observations else None
            ),
            dir_runtime_observations=(
                dir_runtime_observations if dir_runtime_observations else None
            ),
            vars_runtime_observations=(
                vars_runtime_observations if vars_runtime_observations else None
            ),
            globals_runtime_observations=(
                globals_runtime_observations if globals_runtime_observations else None
            ),
            locals_runtime_observations=(
                locals_runtime_observations if locals_runtime_observations else None
            ),
            setattr_runtime_observations=(
                setattr_runtime_observations if setattr_runtime_observations else None
            ),
            delattr_runtime_observations=(
                delattr_runtime_observations if delattr_runtime_observations else None
            ),
            metaclass_behavior_runtime_observations=(
                metaclass_behavior_runtime_observations
                if metaclass_behavior_runtime_observations
                else None
            ),
        )
    )
    selected_units = tuple(
        _selected_unit_metadata(record) for record in response.selection_trace
    )
    warning_details = tuple(
        _provider_warning_metadata(warning)
        for warning in response.optimization_warnings
    )
    selected_unit_ids = tuple(record.unit_id for record in selected_units)
    warnings = tuple(warning.code for warning in warning_details)
    metadata = EvalProviderMetadata(
        selected_units=selected_units,
        warning_details=warning_details,
        unresolved_unit_ids=tuple(
            access.access_id for access in response.unresolved_frontier
        ),
        unsupported_unit_ids=tuple(
            construct.construct_id for construct in response.unsupported_constructs
        ),
        syntax_diagnostic_ids=tuple(
            diagnostic.diagnostic_id for diagnostic in response.syntax_diagnostics
        ),
        semantic_diagnostic_ids=tuple(
            diagnostic.diagnostic_id for diagnostic in response.semantic_diagnostics
        ),
    )
    return EvalProviderResult(
        provider_name=CONTEXT_IR_PROVIDER,
        provider_algorithm_version=PROVIDER_ALGORITHM_VERSION,
        provider_config=EvalProviderConfig(),
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        document=response.compile_result.document,
        total_tokens=response.compile_total_tokens,
        selected_files=(),
        omitted_candidate_files=(),
        selected_unit_ids=selected_unit_ids,
        omitted_unit_ids=response.omitted_unit_ids,
        warnings=warnings,
        metadata=metadata,
    )


def build_context_ir_default_local_python_subprocess_pack(
    request: EvalProviderRequest,
) -> EvalProviderResult:
    """Replay exact probe fixtures through the default local-Python facade."""
    fixture = _default_local_python_subprocess_fixture(request.task_id)

    repo_root = Path(request.repo_root).resolve()
    context_budget = _default_local_python_context_budget(request)
    previous_response = tool_facade.compile_repository_context(
        tool_facade.SemanticContextRequest(
            repo_root=repo_root,
            query=request.query,
            budget=context_budget,
        )
    )
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence=fixture.miss_evidence_text,
    )
    diagnostic = diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    planned_request = _require_default_local_python_runtime_probe_request(
        diagnostic,
        fixture,
    )
    response: (
        tool_facade.SemanticDefaultLocalPythonSubprocessRecompileResponse
        | tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileResponse
    )
    if fixture.family_label is RuntimeProbeFamily.DYNAMIC_IMPORT:
        dynamic_recompile_request = (
            tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileRequest(
                previous_response=previous_response,
                diagnostic=diagnostic,
                miss_evidence=miss_evidence,
                delta_budget=0,
                python_executable=sys.executable,
                invocation_contract_revision=(
                    _DEFAULT_LOCAL_PYTHON_INVOCATION_CONTRACT_REVISION
                ),
                completion_contract_revision=(
                    _DEFAULT_LOCAL_PYTHON_COMPLETION_CONTRACT_REVISION
                ),
                repository_snapshot_basis=RepositorySnapshotBasis(
                    snapshot_kind="eval_fixture",
                    snapshot_id=fixture.snapshot_id,
                    is_dirty_worktree=False,
                ),
                probe_contract_revision=_DEFAULT_LOCAL_PYTHON_PROBE_CONTRACT_REVISION,
                runtime_assumptions=_default_local_python_runtime_assumptions(),
                runner_contract_revision=_DEFAULT_LOCAL_PYTHON_RUNNER_CONTRACT_REVISION,
                timeout_seconds=30,
                runner_environment=_default_local_python_runner_environment(repo_root),
                runner_assumptions=_default_local_python_runner_assumptions(),
            )
        )
        dynamic_recompile = tool_facade.recompile_repository_context_with_dynamic_import_local_python_subprocess  # noqa: E501
        response = dynamic_recompile(dynamic_recompile_request)
    else:
        default_recompile_request = (
            tool_facade.SemanticDefaultLocalPythonSubprocessRecompileRequest(
                previous_response=previous_response,
                diagnostic=diagnostic,
                miss_evidence=miss_evidence,
                delta_budget=0,
                python_executable=sys.executable,
                invocation_contract_revision=(
                    _DEFAULT_LOCAL_PYTHON_INVOCATION_CONTRACT_REVISION
                ),
                completion_contract_revision=(
                    _DEFAULT_LOCAL_PYTHON_COMPLETION_CONTRACT_REVISION
                ),
                repository_snapshot_basis=RepositorySnapshotBasis(
                    snapshot_kind="eval_fixture",
                    snapshot_id=fixture.snapshot_id,
                    is_dirty_worktree=False,
                ),
                probe_contract_revision=_DEFAULT_LOCAL_PYTHON_PROBE_CONTRACT_REVISION,
                runtime_assumptions=_default_local_python_runtime_assumptions(),
                runner_contract_revision=_DEFAULT_LOCAL_PYTHON_RUNNER_CONTRACT_REVISION,
                timeout_seconds=30,
                runner_environment=_default_local_python_runner_environment(repo_root),
                runner_assumptions=_default_local_python_runner_assumptions(),
            )
        )
        recompile = tool_facade.recompile_repository_context_with_default_local_python_subprocess  # noqa: E501
        response = recompile(default_recompile_request)

    _require_default_local_python_runtime_probe_attempt(response, planned_request)
    _require_default_local_python_runtime_payload(response, fixture)

    selected_units = tuple(
        _selected_unit_metadata(record)
        for record in response.compile_result.optimization.selections
    )
    warning_details = tuple(
        _provider_warning_metadata(warning)
        for warning in response.compile_result.optimization.warnings
    )
    selected_unit_ids = tuple(record.unit_id for record in selected_units)
    warnings = tuple(warning.code for warning in warning_details)
    metadata = EvalProviderMetadata(
        selected_units=selected_units,
        warning_details=warning_details,
        unresolved_unit_ids=tuple(
            access.access_id for access in response.program.unresolved_frontier
        ),
        unsupported_unit_ids=tuple(
            construct.construct_id
            for construct in response.program.unsupported_constructs
        ),
        syntax_diagnostic_ids=tuple(
            diagnostic.diagnostic_id
            for diagnostic in response.program.syntax.diagnostics
        ),
        semantic_diagnostic_ids=tuple(
            diagnostic.diagnostic_id for diagnostic in response.program.diagnostics
        ),
    )
    return EvalProviderResult(
        provider_name=CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER,
        provider_algorithm_version=PROVIDER_ALGORITHM_VERSION,
        provider_config=EvalProviderConfig(),
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        document=response.compile_result.document,
        total_tokens=response.compile_total_tokens,
        selected_files=(),
        omitted_candidate_files=(),
        selected_unit_ids=selected_unit_ids,
        omitted_unit_ids=response.compile_result.omitted_unit_ids,
        warnings=warnings,
        metadata=metadata,
        runtime_provenance_records=tuple(response.program.provenance_records),
    )


def build_lexical_top_k_files_pack(request: EvalProviderRequest) -> EvalProviderResult:
    """Build the deterministic lexical top-k whole-file baseline pack."""
    scored_files = _score_baseline_files(request.repo_root, request.query)
    positive_candidates = tuple(
        scored.file for scored in scored_files if scored.score > 0.0
    )
    candidate_files = positive_candidates[:LEXICAL_MAX_CANDIDATES]
    warnings: tuple[str, ...] = ()
    if not candidate_files:
        warnings = ("no_positive_lexical_score",)

    packed = _pack_baseline_files(
        baseline_name=LEXICAL_TOP_K_FILES_PROVIDER,
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        candidates=candidate_files,
        warnings=warnings,
    )
    metadata = EvalProviderMetadata(
        candidate_files=tuple(file.relative_path for file in candidate_files),
        omitted_candidate_files=tuple(file.relative_path for file in packed.omitted),
        lexical_scores=_lexical_score_metadata(scored_files),
    )
    return _baseline_result(
        provider_name=LEXICAL_TOP_K_FILES_PROVIDER,
        config=EvalProviderConfig(max_candidates=LEXICAL_MAX_CANDIDATES),
        request=request,
        packed=packed,
        warnings=warnings,
        metadata=metadata,
    )


def build_import_neighborhood_files_pack(
    request: EvalProviderRequest,
) -> EvalProviderResult:
    """Build the deterministic lexical-seed import-neighborhood baseline pack."""
    repo_root = Path(request.repo_root)
    baseline_files = _discover_baseline_files(repo_root)
    module_to_file = _module_map(baseline_files)
    path_to_module = {
        file.relative_path: module for module, file in module_to_file.items()
    }
    scored_files = _score_files(baseline_files, request.query)
    positive_candidates = tuple(
        scored.file for scored in scored_files if scored.score > 0.0
    )
    seeds = positive_candidates[:IMPORT_SEED_COUNT]
    warnings: list[str] = []
    if not seeds:
        _append_warning(warnings, "no_positive_seed")

    ordered_candidates = _import_neighborhood_candidates(
        seeds=seeds,
        module_to_file=module_to_file,
        path_to_module=path_to_module,
        warnings=warnings,
    )
    warning_tuple = tuple(warnings)
    packed = _pack_baseline_files(
        baseline_name=IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        candidates=ordered_candidates,
        warnings=warning_tuple,
    )
    metadata = EvalProviderMetadata(
        candidate_files=tuple(file.relative_path for file in ordered_candidates),
        omitted_candidate_files=tuple(file.relative_path for file in packed.omitted),
        lexical_scores=_lexical_score_metadata(scored_files),
    )
    return _baseline_result(
        provider_name=IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
        config=EvalProviderConfig(seed_count=IMPORT_SEED_COUNT),
        request=request,
        packed=packed,
        warnings=warning_tuple,
        metadata=metadata,
    )


def build_file_order_floor_pack(request: EvalProviderRequest) -> EvalProviderResult:
    """Build the deterministic file-order diagnostic baseline pack."""
    candidate_files = _discover_baseline_files(Path(request.repo_root))
    packed = _pack_baseline_files(
        baseline_name=FILE_ORDER_FLOOR_PROVIDER,
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        candidates=candidate_files,
        warnings=(),
    )
    metadata = EvalProviderMetadata(
        diagnostic_only=True,
        candidate_files=tuple(file.relative_path for file in candidate_files),
        omitted_candidate_files=tuple(file.relative_path for file in packed.omitted),
    )
    return _baseline_result(
        provider_name=FILE_ORDER_FLOOR_PROVIDER,
        config=EvalProviderConfig(diagnostic_only=True),
        request=request,
        packed=packed,
        warnings=(),
        metadata=metadata,
    )


@dataclass(frozen=True)
class _PackedBaseline:
    """Budget-packed baseline document and selected file metadata."""

    document: str
    total_tokens: int
    selected: tuple[_BaselineFile, ...]
    omitted: tuple[_BaselineFile, ...]


def _baseline_result(
    *,
    provider_name: str,
    config: EvalProviderConfig,
    request: EvalProviderRequest,
    packed: _PackedBaseline,
    warnings: tuple[str, ...],
    metadata: EvalProviderMetadata,
) -> EvalProviderResult:
    """Build the standard provider result for a whole-file baseline."""
    return EvalProviderResult(
        provider_name=provider_name,
        provider_algorithm_version=PROVIDER_ALGORITHM_VERSION,
        provider_config=config,
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        document=packed.document,
        total_tokens=packed.total_tokens,
        selected_files=tuple(file.relative_path for file in packed.selected),
        omitted_candidate_files=tuple(file.relative_path for file in packed.omitted),
        selected_unit_ids=(),
        omitted_unit_ids=(),
        warnings=warnings,
        metadata=metadata,
    )


def _discover_baseline_files(repo_root: Path) -> tuple[_BaselineFile, ...]:
    """Return all regular UTF-8 Python files below ``repo_root`` in path order."""
    discovered: list[_BaselineFile] = []
    for path in _eligible_python_source_files(repo_root):
        if not path.is_file():
            continue
        relative_path = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        discovered.append(
            _BaselineFile(
                relative_path=relative_path,
                text=text,
                token_count=estimate_tokens(text),
            )
        )
    return tuple(sorted(discovered, key=lambda file: file.relative_path))


def _score_baseline_files(
    repo_root: Path | str,
    query: str,
) -> tuple[_ScoredBaselineFile, ...]:
    """Discover and lexically score baseline files for ``query``."""
    return _score_files(_discover_baseline_files(Path(repo_root)), query)


def _score_files(
    files: tuple[_BaselineFile, ...],
    query: str,
) -> tuple[_ScoredBaselineFile, ...]:
    """Return files sorted by lexical baseline candidate order."""
    query_terms = _unique_terms(lexical_tokens(query))
    scored = tuple(_score_file(file, query_terms) for file in files)
    return tuple(
        sorted(
            scored,
            key=lambda scored_file: (
                -scored_file.score,
                scored_file.file.token_count,
                scored_file.file.relative_path,
            ),
        )
    )


def _score_file(
    file: _BaselineFile,
    query_terms: tuple[str, ...],
) -> _ScoredBaselineFile:
    """Score one file according to the frozen lexical baseline formula."""
    content_terms = Counter(lexical_tokens(file.text))
    path_terms = lexical_tokens(file.relative_path)
    if not query_terms:
        score = 0.0
    else:
        content_matches = sum(1 for term in query_terms if content_terms[term] > 0)
        path_matches = sum(1 for term in query_terms if term in path_terms)
        occurrence = min(
            1.0,
            sum(min(content_terms[term], 3) for term in query_terms)
            / (3 * len(query_terms)),
        )
        score = (
            0.75 * (content_matches / len(query_terms))
            + 0.20 * (path_matches / len(query_terms))
            + 0.05 * occurrence
        )
    return _ScoredBaselineFile(
        file=file,
        score=score,
        content_terms=content_terms,
        path_terms=path_terms,
    )


def _unique_terms(terms: tuple[str, ...]) -> tuple[str, ...]:
    """Return lexical terms unique in first-seen order."""
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        if term in seen:
            continue
        seen.add(term)
        unique.append(term)
    return tuple(unique)


def _lexical_score_metadata(
    scored_files: tuple[_ScoredBaselineFile, ...],
) -> tuple[LexicalFileScore, ...]:
    """Return compact lexical score metadata for provider output."""
    return tuple(
        LexicalFileScore(
            file_path=scored.file.relative_path,
            score=scored.score,
            token_count=scored.file.token_count,
        )
        for scored in scored_files
    )


def _pack_baseline_files(
    *,
    baseline_name: str,
    task_id: str,
    query: str,
    budget: int,
    candidates: tuple[_BaselineFile, ...],
    warnings: tuple[str, ...],
) -> _PackedBaseline:
    """Greedily pack whole files while keeping final document tokens in budget."""
    selected: list[_BaselineFile] = []
    for candidate in candidates:
        tentative = tuple([*selected, candidate])
        document = _assemble_baseline_document(
            baseline_name=baseline_name,
            task_id=task_id,
            query=query,
            budget=budget,
            selected_files=tentative,
            omitted_candidate_file_count=len(candidates) - len(tentative),
            warnings=warnings,
        )
        if estimate_tokens(document) <= budget:
            selected.append(candidate)

    selected_tuple = tuple(selected)
    omitted = tuple(
        candidate for candidate in candidates if candidate not in selected_tuple
    )
    document = _assemble_baseline_document(
        baseline_name=baseline_name,
        task_id=task_id,
        query=query,
        budget=budget,
        selected_files=selected_tuple,
        omitted_candidate_file_count=len(omitted),
        warnings=warnings,
    )
    while selected_tuple and estimate_tokens(document) > budget:
        selected_tuple = selected_tuple[:-1]
        omitted = tuple(
            candidate for candidate in candidates if candidate not in selected_tuple
        )
        document = _assemble_baseline_document(
            baseline_name=baseline_name,
            task_id=task_id,
            query=query,
            budget=budget,
            selected_files=selected_tuple,
            omitted_candidate_file_count=len(omitted),
            warnings=warnings,
        )

    total_tokens = estimate_tokens(document)
    if total_tokens > budget:
        raise ValueError(
            f"budget {budget} is too small for {baseline_name} baseline envelope"
        )
    return _PackedBaseline(
        document=document,
        total_tokens=total_tokens,
        selected=selected_tuple,
        omitted=omitted,
    )


def _assemble_baseline_document(
    *,
    baseline_name: str,
    task_id: str,
    query: str,
    budget: int,
    selected_files: tuple[_BaselineFile, ...],
    omitted_candidate_file_count: int,
    warnings: tuple[str, ...],
) -> str:
    """Assemble the accepted baseline document format."""
    lines = [
        "# Baseline Context",
        f"baseline: {baseline_name}",
        f"task_id: {task_id}",
        f"query: {query or '<empty>'}",
        f"budget: {budget}",
        f"selected_files: {len(selected_files)}",
        f"omitted_candidate_files: {omitted_candidate_file_count}",
    ]
    if warnings:
        lines.append(f"warnings: {len(warnings)}")
    document = "\n".join(lines)
    for file in selected_files:
        document = f"{document}\n\n## {file.relative_path}\n{file.text}"
    return document


def _module_map(files: tuple[_BaselineFile, ...]) -> dict[str, _BaselineFile]:
    """Map resolvable repository module names to Python source files."""
    modules: dict[str, _BaselineFile] = {}
    for file in files:
        modules[_module_name(file.relative_path)] = file
    return modules


def _module_name(relative_path: str) -> str:
    """Return the importable module name for one repository-relative path."""
    path = PurePosixPath(relative_path)
    if path.name == "__init__.py":
        if path.parent == PurePosixPath("."):
            return "__init__"
        return ".".join(path.parent.parts)
    return ".".join(path.with_suffix("").parts)


def _import_neighborhood_candidates(
    *,
    seeds: tuple[_BaselineFile, ...],
    module_to_file: dict[str, _BaselineFile],
    path_to_module: dict[str, str],
    warnings: list[str],
) -> tuple[_BaselineFile, ...]:
    """Return seeds followed by first-hop repo import files."""
    ordered: list[_BaselineFile] = []
    seen_paths: set[str] = set()
    for seed in seeds:
        _append_file(ordered, seen_paths, seed)

    for seed in seeds:
        try:
            tree = ast.parse(seed.text, filename=seed.relative_path)
        except SyntaxError:
            _append_warning(warnings, "import_parse_error")
            continue
        seed_module = path_to_module[seed.relative_path]
        for node in _iter_import_nodes(tree):
            for imported_file in _resolve_import_node(
                source_file=seed,
                source_module=seed_module,
                node=node,
                module_to_file=module_to_file,
                warnings=warnings,
            ):
                _append_file(ordered, seen_paths, imported_file)
    return tuple(ordered)


def _append_file(
    ordered: list[_BaselineFile],
    seen_paths: set[str],
    file: _BaselineFile,
) -> None:
    """Append ``file`` once, preserving first occurrence order."""
    if file.relative_path in seen_paths:
        return
    seen_paths.add(file.relative_path)
    ordered.append(file)


def _iter_import_nodes(tree: ast.AST) -> tuple[ast.Import | ast.ImportFrom, ...]:
    """Return import nodes in deterministic AST preorder traversal."""
    nodes: list[ast.Import | ast.ImportFrom] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.Import | ast.ImportFrom):
            nodes.append(node)
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return tuple(nodes)


def _resolve_import_node(
    *,
    source_file: _BaselineFile,
    source_module: str,
    node: ast.Import | ast.ImportFrom,
    module_to_file: dict[str, _BaselineFile],
    warnings: list[str],
) -> tuple[_BaselineFile, ...]:
    """Resolve direct repository imports from one import AST node."""
    if isinstance(node, ast.Import):
        return _resolve_import_aliases(node, module_to_file, warnings)
    return _resolve_from_import_aliases(
        source_file=source_file,
        source_module=source_module,
        node=node,
        module_to_file=module_to_file,
        warnings=warnings,
    )


def _resolve_import_aliases(
    node: ast.Import,
    module_to_file: dict[str, _BaselineFile],
    warnings: list[str],
) -> tuple[_BaselineFile, ...]:
    """Resolve ``import M`` aliases by exact module name only."""
    resolved: list[_BaselineFile] = []
    for alias in node.names:
        imported_file = module_to_file.get(alias.name)
        if imported_file is None:
            _append_warning(warnings, "import_not_resolved")
            continue
        resolved.append(imported_file)
    return tuple(resolved)


def _resolve_from_import_aliases(
    *,
    source_file: _BaselineFile,
    source_module: str,
    node: ast.ImportFrom,
    module_to_file: dict[str, _BaselineFile],
    warnings: list[str],
) -> tuple[_BaselineFile, ...]:
    """Resolve ``from M import name`` aliases against repository modules."""
    base_module = _from_import_base_module(
        source_file=source_file,
        source_module=source_module,
        imported_module=node.module,
        level=node.level,
    )
    if base_module is None:
        _append_warning(warnings, "unsupported_relative_import")
        return ()

    resolved: list[_BaselineFile] = []
    for alias in node.names:
        if alias.name == "*":
            _append_warning(warnings, "star_import_not_expanded")
            imported_file = module_to_file.get(base_module)
            if imported_file is None:
                _append_warning(warnings, "import_not_resolved")
                continue
            resolved.append(imported_file)
            continue

        target_module = f"{base_module}.{alias.name}" if base_module else alias.name
        imported_file = module_to_file.get(target_module)
        if imported_file is None and base_module:
            imported_file = module_to_file.get(base_module)
        if imported_file is None:
            _append_warning(warnings, "import_not_resolved")
            continue
        resolved.append(imported_file)
    return tuple(resolved)


def _from_import_base_module(
    *,
    source_file: _BaselineFile,
    source_module: str,
    imported_module: str | None,
    level: int,
) -> str | None:
    """Resolve the base module for absolute and relative ``from`` imports."""
    if level == 0:
        return imported_module or ""

    current_package = _current_package(source_file.relative_path, source_module)
    parts = [] if not current_package else current_package.split(".")
    ascents = level - 1
    if ascents > len(parts):
        return None
    if ascents:
        parts = parts[:-ascents]
    if imported_module:
        parts.extend(imported_module.split("."))
    return ".".join(parts)


def _current_package(relative_path: str, module_name: str) -> str:
    """Return the current package for resolving a relative import."""
    if PurePosixPath(relative_path).name == "__init__.py":
        return module_name
    if "." not in module_name:
        return ""
    return module_name.rsplit(".", 1)[0]


def _append_warning(warnings: list[str], code: str) -> None:
    """Append a warning code only on its first occurrence."""
    if code not in warnings:
        warnings.append(code)


def _default_local_python_subprocess_fixture(
    task_id: str,
) -> _DefaultLocalPythonSubprocessFixture:
    """Return the exact fixture supported by the local-Python subprocess provider."""
    fixture = _DEFAULT_LOCAL_PYTHON_SUBPROCESS_FIXTURES.get(task_id)
    if fixture is None:
        raise ValueError(
            "context_ir_default_local_python_subprocess only supports "
            "oracle_signal_locals_probe, oracle_signal_globals_probe, "
            "oracle_signal_vars_zero_probe, oracle_signal_dir_zero_probe, "
            "oracle_signal_hasattr_probe, oracle_signal_hasattr_false_probe, "
            "oracle_signal_hasattr_literal_probe, "
            "oracle_signal_getattr_probe, "
            "oracle_signal_getattr_attribute_error_probe, "
            "oracle_signal_getattr_literal_probe, "
            "oracle_signal_dynamic_import_root_literal_probe, "
            "oracle_signal_dynamic_import_root_probe, "
            "oracle_signal_dynamic_import_root_alias_probe, "
            "oracle_signal_dynamic_import_builtin_probe, "
            "oracle_signal_dynamic_import_builtins_attr_probe, "
            "oracle_signal_dynamic_import_builtins_alias_probe, "
            "oracle_signal_dynamic_import_imported_name_probe, "
            "oracle_signal_dynamic_import_imported_alias_probe, "
            "oracle_signal_dynamic_import_probe, "
            "oracle_signal_setattr_literal_probe, "
            "oracle_signal_delattr_literal_probe, oracle_signal_exec_probe, "
            "oracle_signal_eval_probe, or "
            "oracle_signal_metaclass_behavior_probe"
        )
    return fixture


def _default_local_python_context_budget(request: EvalProviderRequest) -> int:
    """Return the honest compile budget for exact subprocess provider fixtures."""
    required_budget = _DYNAMIC_IMPORT_DEFAULT_LOCAL_CONTEXT_BUDGETS.get(request.task_id)
    if required_budget is not None and request.budget != required_budget:
        raise ValueError(
            "context_ir_default_local_python_subprocess only supports "
            f"budget {required_budget} for {request.task_id}"
        )
    return request.budget


def _require_default_local_python_runtime_probe_request(
    diagnostic: SemanticDiagnosticResult,
    fixture: _DefaultLocalPythonSubprocessFixture,
) -> RuntimeProbeRequest:
    """Return the single accepted runtime-probe request or fail closed."""
    plan = diagnostic.planned_runtime_probe_request_plan
    if plan is None:
        raise ValueError("default local-Python provider requires a runtime probe plan")
    if diagnostic.planned_runtime_probe_requests != plan.requests:
        raise ValueError(
            "default local-Python provider requires mirrored planned requests"
        )
    if len(plan.requests) != 1:
        raise ValueError(
            "default local-Python provider requires exactly one planned request"
        )
    request = plan.requests[0]
    if request.subject_id != fixture.unsupported_unit_id:
        raise ValueError(
            "default local-Python provider planned request targets the wrong subject"
        )
    if request.family_label is not fixture.family_label:
        raise ValueError(
            "default local-Python provider planned request has the wrong family"
        )
    if request.form_label != fixture.form_label:
        raise ValueError(
            "default local-Python provider planned request has the wrong form"
        )
    if request.boundary_text != fixture.boundary_text:
        raise ValueError(
            "default local-Python provider planned request has the wrong boundary"
        )
    if request.replay_target_seed != fixture.replay_target_seed:
        raise ValueError(
            "default local-Python provider planned request has the wrong replay target"
        )
    if (
        fixture.source_site_id is not None
        and request.source_site.site_id != fixture.source_site_id
    ):
        raise ValueError(
            "default local-Python provider planned request has the wrong source site"
        )
    if (
        fixture.source_file_path is not None
        and request.source_site.file_path != fixture.source_file_path
    ):
        raise ValueError(
            "default local-Python provider planned request has the wrong source file"
        )
    if (
        fixture.source_start_line is not None
        and request.source_site.span.start_line != fixture.source_start_line
    ):
        raise ValueError(
            "default local-Python provider planned request has the wrong source span"
        )
    if (
        fixture.source_start_column is not None
        and request.source_site.span.start_column != fixture.source_start_column
    ):
        raise ValueError(
            "default local-Python provider planned request has the wrong source span"
        )
    if (
        fixture.source_end_line is not None
        and request.source_site.span.end_line != fixture.source_end_line
    ):
        raise ValueError(
            "default local-Python provider planned request has the wrong source span"
        )
    if (
        fixture.source_end_column is not None
        and request.source_site.span.end_column != fixture.source_end_column
    ):
        raise ValueError(
            "default local-Python provider planned request has the wrong source span"
        )
    if (
        fixture.replay_selector_seed is not None
        and request.replay_selector_seed != fixture.replay_selector_seed
    ):
        raise ValueError(
            "default local-Python provider planned request has the wrong replay "
            "selector"
        )
    return request


def _require_default_local_python_runtime_probe_attempt(
    response: (
        tool_facade.SemanticDefaultLocalPythonSubprocessRecompileResponse
        | tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileResponse
    ),
    planned_request: RuntimeProbeRequest,
) -> None:
    """Require the subprocess attempt collection to replay the planned request."""
    attempts = response.runner_attempt_collection.attempts
    if len(attempts) != 1:
        raise ValueError("default local-Python provider requires one runner attempt")
    if attempts[0].request != planned_request:
        raise ValueError(
            "default local-Python provider runner attempt must replay planned request"
        )


def _require_default_local_python_runtime_payload(
    response: (
        tool_facade.SemanticDefaultLocalPythonSubprocessRecompileResponse
        | tool_facade.SemanticDynamicImportLocalPythonSubprocessRecompileResponse
    ),
    fixture: _DefaultLocalPythonSubprocessFixture,
) -> None:
    """Require the observed payload to match the exact eval oracle signal."""
    results = response.runner_attempt_collection.result_batch.results
    if len(results) != 1:
        raise ValueError("default local-Python provider requires one runner result")
    result = results[0]
    if not isinstance(result, RuntimeProbeObservedResult):
        raise ValueError("default local-Python provider requires an observed result")
    observed_payload = tuple(
        (field.key, field.value) for field in result.normalized_payload
    )
    if observed_payload != fixture.runtime_payload:
        raise ValueError(
            "default local-Python provider observed an unexpected runtime payload"
        )
    if fixture.runtime_replay_input_tail:
        observed_replay_input_tail = tuple(
            (field.key, field.value)
            for field in result.replay_artifact.replay_inputs[
                -len(fixture.runtime_replay_input_tail) :
            ]
        )
        if observed_replay_input_tail != fixture.runtime_replay_input_tail:
            raise ValueError(
                "default local-Python provider observed unexpected runtime replay "
                "inputs"
            )


def _default_local_python_runtime_assumptions() -> tuple[
    RuntimeProbeReplayField,
    ...,
]:
    """Return explicit runtime assumptions for exact local fixture replay."""
    return (
        _runtime_probe_field("python_version", "test"),
        _runtime_probe_field("dependency_mode", "offline-fixture"),
    )


def _default_local_python_runner_environment(
    repo_root: Path,
) -> tuple[RuntimeProbeReplayField, ...]:
    """Return absolute local-Python runner environment fields for the fixture."""
    source_root = Path(__file__).resolve().parents[1]
    if not repo_root.is_absolute():
        raise ValueError("default local-Python provider repo_root must be absolute")
    if not source_root.is_absolute():
        raise ValueError("default local-Python provider source root must be absolute")
    return (
        _runtime_probe_field("repository_root", str(repo_root)),
        _runtime_probe_field("working_directory", str(repo_root)),
        _runtime_probe_field("python_path_entry", str(source_root)),
    )


def _default_local_python_runner_assumptions() -> tuple[
    RuntimeProbeReplayField,
    ...,
]:
    """Return explicit runner assumptions for exact local fixture replay."""
    return (
        _runtime_probe_field("network", "disabled"),
        _runtime_probe_field("filesystem_mode", "read_only_fixture"),
    )


def _runtime_probe_field(key: str, value: str) -> RuntimeProbeReplayField:
    """Return one local subprocess replay field."""
    return RuntimeProbeReplayField(key=key, value=value)


def _selected_unit_metadata(
    record: SemanticSelectionRecord,
) -> EvalSelectedUnit:
    """Return structured selected-unit metadata from one semantic trace record."""
    trace_summary = record.trace_summary
    return EvalSelectedUnit(
        unit_id=record.unit_id,
        detail=record.detail,
        token_count=record.token_count,
        basis=record.basis.value,
        reason=record.reason,
        edit_score=record.edit_score,
        support_score=record.support_score,
        primary_capability_tier=(
            None if trace_summary is None else trace_summary.primary_capability_tier
        ),
        primary_evidence_origin=(
            None if trace_summary is None else trace_summary.primary_evidence_origin
        ),
        primary_replay_status=(
            None if trace_summary is None else trace_summary.primary_replay_status
        ),
        has_attached_runtime_provenance=_attached_runtime_support(trace_summary),
        attached_runtime_provenance_record_ids=(
            ()
            if trace_summary is None
            else trace_summary.attached_runtime_provenance_record_ids
        ),
    )


def _provider_warning_metadata(
    warning: SemanticOptimizationWarning,
) -> EvalProviderWarning:
    """Return structured warning metadata from one semantic warning."""
    return EvalProviderWarning(
        code=warning.code.value,
        unit_id=warning.unit_id,
        message=warning.message,
    )


def _attached_runtime_support(
    trace_summary: SemanticUnitTraceSummary | None,
) -> bool | None:
    """Return whether a trace summary carries additive runtime-backed support."""
    if trace_summary is None:
        return None
    return trace_summary.has_attached_runtime_provenance


__all__ = [
    "CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER",
    "CONTEXT_IR_PROVIDER",
    "FILE_ORDER_FLOOR_PROVIDER",
    "IMPORT_NEIGHBORHOOD_FILES_PROVIDER",
    "IMPORT_SEED_COUNT",
    "LEXICAL_MAX_CANDIDATES",
    "LEXICAL_TOP_K_FILES_PROVIDER",
    "PROVIDER_ALGORITHM_VERSION",
    "EvalProviderConfig",
    "EvalProviderMetadata",
    "EvalProviderRequest",
    "EvalProviderResult",
    "EvalProviderWarning",
    "EvalSelectedUnit",
    "LexicalFileScore",
    "build_context_ir_default_local_python_subprocess_pack",
    "build_context_ir_provider_pack",
    "build_file_order_floor_pack",
    "build_import_neighborhood_files_pack",
    "build_lexical_top_k_files_pack",
    "estimate_tokens",
    "lexical_tokens",
]

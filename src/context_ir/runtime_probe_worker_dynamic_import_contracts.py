"""Private dynamic-import worker contract constants."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

_DYNAMIC_IMPORT_WORKER_FORM_LABEL = "dynamic_import:importlib.import_module/1"
_DYNAMIC_IMPORT_WORKER_LOADER_FORM_LABEL = "dynamic_import:loader.import_module/1"
_DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL = "dynamic_import:import_module/1"
_DYNAMIC_IMPORT_WORKER_LOAD_MODULE_FORM_LABEL = "dynamic_import:load_module/1"
_DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL = "dynamic_import:__import__/1"
_DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL = (
    "dynamic_import:builtins.__import__/1"
)
_DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL = (
    "dynamic_import:loader.__import__/1"
)
_DYNAMIC_IMPORT_WORKER_FORM_LABELS = (
    _DYNAMIC_IMPORT_WORKER_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_LOADER_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_LOAD_MODULE_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL,
    _DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL,
)
_DYNAMIC_IMPORT_WORKER_IMPORT_MODULE_GLOBAL_NAME = "import_module"
_DYNAMIC_IMPORT_WORKER_LOAD_MODULE_GLOBAL_NAME = "load_module"
_DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAME = "builtins"
_DYNAMIC_IMPORT_WORKER_LOADER_GLOBAL_NAME = "loader"


@dataclass(frozen=True)
class _DynamicImportWorkerRenderCardContract:
    """Exact worker metadata for one supported render_card fixture."""

    subject_id: str
    source_site_id: str
    source_file_path: str
    source_start_line: int
    source_start_column: int
    source_end_line: int
    source_end_column: int
    boundary_text: str
    form_label: str
    replay_target_seed: str
    replay_selector_seed: str
    imported_module: str
    error_label: str


_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH = "main.py"
_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET = "main.load_weather_plugin"
_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE = "plugins.weather"
_DYNAMIC_IMPORT_WORKER_RENDER_CARD_CONTRACTS: Mapping[
    str,
    _DynamicImportWorkerRenderCardContract,
] = MappingProxyType(
    {
        "root_literal": _DynamicImportWorkerRenderCardContract(
            subject_id="unsupported:call:main.py:5:13",
            source_site_id="site:call:main.py:5:13",
            source_file_path=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH,
            source_start_line=5,
            source_start_column=13,
            source_end_line=5,
            source_end_column=55,
            boundary_text='importlib.import_module("plugins.weather")',
            form_label=_DYNAMIC_IMPORT_WORKER_FORM_LABEL,
            replay_target_seed=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET,
            replay_selector_seed=(
                "call:main.load_weather_plugin:dynamic_import:"
                "importlib.import_module/1@main.py:5:13:5:55"
            ),
            imported_module=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE,
            error_label="root literal",
        ),
        "root_name": _DynamicImportWorkerRenderCardContract(
            subject_id="unsupported:call:main.py:6:13",
            source_site_id="site:call:main.py:6:13",
            source_file_path=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH,
            source_start_line=6,
            source_start_column=13,
            source_end_line=6,
            source_end_column=42,
            boundary_text="importlib.import_module(name)",
            form_label=_DYNAMIC_IMPORT_WORKER_FORM_LABEL,
            replay_target_seed=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET,
            replay_selector_seed=(
                "call:main.load_weather_plugin:dynamic_import:"
                "importlib.import_module/1@main.py:6:13:6:42"
            ),
            imported_module=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE,
            error_label="root name",
        ),
        "root_alias": _DynamicImportWorkerRenderCardContract(
            subject_id="unsupported:call:main.py:6:13",
            source_site_id="site:call:main.py:6:13",
            source_file_path=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH,
            source_start_line=6,
            source_start_column=13,
            source_end_line=6,
            source_end_column=39,
            boundary_text="loader.import_module(name)",
            form_label=_DYNAMIC_IMPORT_WORKER_LOADER_FORM_LABEL,
            replay_target_seed=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET,
            replay_selector_seed=(
                "call:main.load_weather_plugin:dynamic_import:"
                "loader.import_module/1@main.py:6:13:6:39"
            ),
            imported_module=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE,
            error_label="root alias",
        ),
        "builtin": _DynamicImportWorkerRenderCardContract(
            subject_id="unsupported:call:main.py:6:4",
            source_site_id="site:call:main.py:6:4",
            source_file_path=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH,
            source_start_line=6,
            source_start_column=4,
            source_end_line=6,
            source_end_column=20,
            boundary_text="__import__(name)",
            form_label=_DYNAMIC_IMPORT_WORKER_BUILTIN_IMPORT_FORM_LABEL,
            replay_target_seed=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET,
            replay_selector_seed=(
                "call:main.load_weather_plugin:dynamic_import:"
                "__import__/1@main.py:6:4:6:20"
            ),
            imported_module=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE,
            error_label="builtin",
        ),
        "builtins_attr": _DynamicImportWorkerRenderCardContract(
            subject_id="unsupported:call:main.py:7:4",
            source_site_id="site:call:main.py:7:4",
            source_file_path=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH,
            source_start_line=7,
            source_start_column=4,
            source_end_line=7,
            source_end_column=29,
            boundary_text="builtins.__import__(name)",
            form_label=_DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL,
            replay_target_seed=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET,
            replay_selector_seed=(
                "call:main.load_weather_plugin:dynamic_import:"
                "builtins.__import__/1@main.py:7:4:7:29"
            ),
            imported_module=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE,
            error_label="builtins attribute",
        ),
        "builtins_alias": _DynamicImportWorkerRenderCardContract(
            subject_id="unsupported:call:main.py:7:4",
            source_site_id="site:call:main.py:7:4",
            source_file_path=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH,
            source_start_line=7,
            source_start_column=4,
            source_end_line=7,
            source_end_column=27,
            boundary_text="loader.__import__(name)",
            form_label=_DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL,
            replay_target_seed=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET,
            replay_selector_seed=(
                "call:main.load_weather_plugin:dynamic_import:"
                "loader.__import__/1@main.py:7:4:7:27"
            ),
            imported_module=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE,
            error_label="builtins alias",
        ),
        "imported_name": _DynamicImportWorkerRenderCardContract(
            subject_id="unsupported:call:main.py:6:13",
            source_site_id="site:call:main.py:6:13",
            source_file_path=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH,
            source_start_line=6,
            source_start_column=13,
            source_end_line=6,
            source_end_column=32,
            boundary_text="import_module(name)",
            form_label=_DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL,
            replay_target_seed=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET,
            replay_selector_seed=(
                "call:main.load_weather_plugin:dynamic_import:"
                "import_module/1@main.py:6:13:6:32"
            ),
            imported_module=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE,
            error_label="imported name",
        ),
        "imported_alias": _DynamicImportWorkerRenderCardContract(
            subject_id="unsupported:call:main.py:6:13",
            source_site_id="site:call:main.py:6:13",
            source_file_path=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH,
            source_start_line=6,
            source_start_column=13,
            source_end_line=6,
            source_end_column=30,
            boundary_text="load_module(name)",
            form_label=_DYNAMIC_IMPORT_WORKER_LOAD_MODULE_FORM_LABEL,
            replay_target_seed=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET,
            replay_selector_seed=(
                "call:main.load_weather_plugin:dynamic_import:"
                "load_module/1@main.py:6:13:6:30"
            ),
            imported_module=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE,
            error_label="imported alias",
        ),
        "imported_literal": _DynamicImportWorkerRenderCardContract(
            subject_id="unsupported:call:main.py:5:13",
            source_site_id="site:call:main.py:5:13",
            source_file_path=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_SOURCE_FILE_PATH,
            source_start_line=5,
            source_start_column=13,
            source_end_line=5,
            source_end_column=45,
            boundary_text='import_module("plugins.weather")',
            form_label=_DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL,
            replay_target_seed=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_REPLAY_TARGET,
            replay_selector_seed=(
                "call:main.load_weather_plugin:dynamic_import:"
                "import_module/1@main.py:5:13:5:45"
            ),
            imported_module=_DYNAMIC_IMPORT_WORKER_RENDER_CARD_IMPORTED_MODULE,
            error_label="imported literal",
        ),
    }
)
_DYNAMIC_IMPORT_WORKER_SOURCE_GLOBAL_NAMES_BY_FORM_LABEL: Mapping[str, str] = (
    MappingProxyType(
        {
            _DYNAMIC_IMPORT_WORKER_IMPORTED_FORM_LABEL: (
                _DYNAMIC_IMPORT_WORKER_IMPORT_MODULE_GLOBAL_NAME
            ),
            _DYNAMIC_IMPORT_WORKER_LOAD_MODULE_FORM_LABEL: (
                _DYNAMIC_IMPORT_WORKER_LOAD_MODULE_GLOBAL_NAME
            ),
        }
    )
)
_DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAMES_BY_FORM_LABEL: Mapping[str, str] = (
    MappingProxyType(
        {
            _DYNAMIC_IMPORT_WORKER_BUILTINS_IMPORT_FORM_LABEL: (
                _DYNAMIC_IMPORT_WORKER_BUILTINS_GLOBAL_NAME
            ),
            _DYNAMIC_IMPORT_WORKER_LOADER_BUILTIN_IMPORT_FORM_LABEL: (
                _DYNAMIC_IMPORT_WORKER_LOADER_GLOBAL_NAME
            ),
        }
    )
)

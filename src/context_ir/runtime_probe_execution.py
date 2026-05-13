"""Internal materialization of planned runtime probe execution inputs."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import TypeAlias

import context_ir.runtime_acquisition as runtime_acquisition
from context_ir.runtime_probe_requests import (
    RuntimeProbeFamily,
    RuntimeProbeRequest,
    RuntimeProbeRequestPlan,
    build_runtime_probe_request_plan,
)
from context_ir.runtime_probe_results import (
    RuntimeProbeNonProofResult,
    RuntimeProbeObservedResult,
    RuntimeProbeReplayArtifact,
    RuntimeProbeReplayField,
    RuntimeProbeResult,
    RuntimeProbeResultBatch,
    RuntimeProbeResultOutcome,
)
from context_ir.semantic_types import RepositorySnapshotBasis, SemanticDiagnosticResult

_RUNTIME_PROBE_EXECUTION_INPUT_BATCH_CONTRACT_VERSION = (
    "runtime_probe_execution_input_batch:v1"
)
_RUNTIME_PROBE_RUNNER_REQUEST_BATCH_CONTRACT_VERSION = (
    "runtime_probe_runner_request_batch:v1"
)
_RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION = (
    "runtime_probe_local_python_stdout_protocol:v1"
)
_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_PAYLOAD_CONTRACT_VERSION = (
    "runtime_probe_local_python_worker_request_payload:v1"
)
_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_STDIN_TRANSPORT_CONTRACT_REVISION = (
    "runtime_probe_local_python_worker_request_stdin_transport:v1"
)
_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME = "context_ir.runtime_probe_worker"
_RUNTIME_PROBE_DYNAMIC_IMPORT_LOCAL_PYTHON_FORM_LABEL = (
    "dynamic_import:importlib.import_module/1"
)
_RUNTIME_PROBE_DYNAMIC_IMPORT_LOADER_LOCAL_PYTHON_FORM_LABEL = (
    "dynamic_import:loader.import_module/1"
)
_RUNTIME_PROBE_DYNAMIC_IMPORT_IMPORTED_LOCAL_PYTHON_FORM_LABEL = (
    "dynamic_import:import_module/1"
)
_RUNTIME_PROBE_DYNAMIC_IMPORT_LOAD_MODULE_LOCAL_PYTHON_FORM_LABEL = (
    "dynamic_import:load_module/1"
)
_RUNTIME_PROBE_DYNAMIC_IMPORT_BUILTIN_IMPORT_LOCAL_PYTHON_FORM_LABEL = (
    "dynamic_import:__import__/1"
)
_RUNTIME_PROBE_DYNAMIC_IMPORT_BUILTINS_IMPORT_LOCAL_PYTHON_FORM_LABEL = (
    "dynamic_import:builtins.__import__/1"
)
_RUNTIME_PROBE_DYNAMIC_IMPORT_LOADER_BUILTIN_IMPORT_LOCAL_PYTHON_FORM_LABEL = (
    "dynamic_import:loader.__import__/1"
)
_RUNTIME_PROBE_REFLECTIVE_HASATTR_LOCAL_PYTHON_FORM_LABEL = (
    "reflective_builtin:hasattr/2"
)
_RUNTIME_PROBE_REFLECTIVE_GETATTR_LOCAL_PYTHON_FORM_LABEL = (
    "reflective_builtin:getattr/2"
)
_RUNTIME_PROBE_REFLECTIVE_GETATTR_DEFAULT_LOCAL_PYTHON_FORM_LABEL = (
    "reflective_builtin:getattr/3"
)
_RUNTIME_PROBE_REFLECTIVE_VARS_LOCAL_PYTHON_FORM_LABEL = "reflective_builtin:vars/1"
_RUNTIME_PROBE_REFLECTIVE_VARS_ZERO_LOCAL_PYTHON_FORM_LABEL = (
    "reflective_builtin:vars/0"
)
_RUNTIME_PROBE_REFLECTIVE_DIR_LOCAL_PYTHON_FORM_LABEL = "reflective_builtin:dir/1"
_RUNTIME_PROBE_REFLECTIVE_DIR_ZERO_LOCAL_PYTHON_FORM_LABEL = "reflective_builtin:dir/0"
_RUNTIME_PROBE_RUNTIME_MUTATION_GLOBALS_ZERO_LOCAL_PYTHON_FORM_LABEL = (
    "runtime_mutation:globals/0"
)
_RUNTIME_PROBE_RUNTIME_MUTATION_LOCALS_ZERO_LOCAL_PYTHON_FORM_LABEL = (
    "runtime_mutation:locals/0"
)
_RUNTIME_PROBE_RUNTIME_MUTATION_SETATTR_LOCAL_PYTHON_FORM_LABEL = (
    "runtime_mutation:setattr/3"
)
_RUNTIME_PROBE_RUNTIME_MUTATION_DELATTR_LOCAL_PYTHON_FORM_LABEL = (
    "runtime_mutation:delattr/2"
)
_RUNTIME_PROBE_DYNAMIC_IMPORT_LOCAL_PYTHON_FORM_LABELS = (
    _RUNTIME_PROBE_DYNAMIC_IMPORT_LOCAL_PYTHON_FORM_LABEL,
    _RUNTIME_PROBE_DYNAMIC_IMPORT_LOADER_LOCAL_PYTHON_FORM_LABEL,
    _RUNTIME_PROBE_DYNAMIC_IMPORT_IMPORTED_LOCAL_PYTHON_FORM_LABEL,
    _RUNTIME_PROBE_DYNAMIC_IMPORT_LOAD_MODULE_LOCAL_PYTHON_FORM_LABEL,
    _RUNTIME_PROBE_DYNAMIC_IMPORT_BUILTINS_IMPORT_LOCAL_PYTHON_FORM_LABEL,
    _RUNTIME_PROBE_DYNAMIC_IMPORT_LOADER_BUILTIN_IMPORT_LOCAL_PYTHON_FORM_LABEL,
    _RUNTIME_PROBE_DYNAMIC_IMPORT_BUILTIN_IMPORT_LOCAL_PYTHON_FORM_LABEL,
)
_RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION_KEY = (
    "runtime_probe_stdout_protocol_revision"
)
_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_PAYLOAD_KEYS = frozenset(
    {
        "contract_version",
        "plan_id",
        "request_id",
        "family_label",
        "form_label",
        "replay_target_seed",
        "replay_selector_seed",
        "request_replay_payload_fields",
        "runtime_assumptions",
        "runner_contract_revision",
        "runner_environment",
        "runner_assumptions",
        "invocation_contract_revision",
        "invocation_identity",
        "argv",
        "working_directory",
        "python_path_entries",
        "timeout_seconds",
    }
)
_RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_KEYS = frozenset(
    {
        _RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION_KEY,
        "normalized_payload",
        "durable_artifact_reference",
    }
)
_NON_PROOF_ATTEMPT_OUTCOMES = frozenset(
    {
        RuntimeProbeResultOutcome.CRASHED,
        RuntimeProbeResultOutcome.TIMED_OUT,
        RuntimeProbeResultOutcome.MISSING_ENVIRONMENT,
        RuntimeProbeResultOutcome.SETUP_FAILED,
    }
)
_LOCAL_PYTHON_REPOSITORY_ROOT_ENVIRONMENT_KEY = "repository_root"
_LOCAL_PYTHON_WORKING_DIRECTORY_ENVIRONMENT_KEY = "working_directory"
_LOCAL_PYTHON_PATH_ENTRY_ENVIRONMENT_KEY = "python_path_entry"
_LOCAL_PYTHON_REQUIRED_SINGLETON_ENVIRONMENT_KEYS = frozenset(
    {
        _LOCAL_PYTHON_REPOSITORY_ROOT_ENVIRONMENT_KEY,
        _LOCAL_PYTHON_WORKING_DIRECTORY_ENVIRONMENT_KEY,
    }
)
_LOCAL_PYTHON_REPEATED_ENVIRONMENT_KEYS = frozenset(
    {
        _LOCAL_PYTHON_PATH_ENTRY_ENVIRONMENT_KEY,
    }
)
_REQUIRED_WORKER_REQUEST_REPLAY_FIELD_KEYS = (
    "plan_id",
    "request_id",
    "subject_kind",
    "subject_id",
    "source_site_id",
    "source_file_path",
    "source_start_line",
    "source_start_column",
    "source_end_line",
    "source_end_column",
    "reason_code",
    "boundary_text",
    "family_label",
    "form_label",
    "replay_target_seed",
    "replay_selector_seed",
)

_SourceSiteIdentity: TypeAlias = tuple[str, int, int, int, int]
RuntimeProbeRunnerHandlerKey: TypeAlias = tuple[RuntimeProbeFamily, str]
_LocalPythonEnvironmentParts: TypeAlias = tuple[str, str, tuple[str, ...]]


@dataclass(frozen=True)
class RuntimeProbeExecutionInput:
    """Internal, non-executing work item for one planned runtime probe request."""

    plan_id: str
    request_id: str
    request: RuntimeProbeRequest
    source_site_identity: _SourceSiteIdentity
    family_label: RuntimeProbeFamily
    form_label: str
    replay_target_seed: str
    replay_selector_seed: str
    replay_artifact: RuntimeProbeReplayArtifact

    def __post_init__(self) -> None:
        """Reject materialized execution inputs that drift from their request."""
        if not self.plan_id.strip():
            raise ValueError("plan_id must be non-empty")
        if not self.request_id.strip():
            raise ValueError("request_id must be non-empty")
        if self.request_id != self.request.request_id:
            raise ValueError(
                "runtime probe execution input request_id must match request.request_id"
            )
        if self.source_site_identity != runtime_acquisition._source_site_identity(
            self.request.source_site
        ):
            raise ValueError(
                "runtime probe execution input source site must match request "
                "source site"
            )
        if self.family_label is not self.request.family_label:
            raise ValueError(
                "runtime probe execution input family_label must match request"
            )
        if self.form_label != self.request.form_label:
            raise ValueError(
                "runtime probe execution input form_label must match request"
            )
        if self.replay_target_seed != self.request.replay_target_seed:
            raise ValueError(
                "runtime probe execution input replay target must match request"
            )
        if self.replay_selector_seed != self.request.replay_selector_seed:
            raise ValueError(
                "runtime probe execution input replay selector must match request"
            )

        replay_artifact = self.replay_artifact
        if replay_artifact.probe_identifier != _runtime_probe_identifier(
            plan_id=self.plan_id,
            request_id=self.request_id,
            request=self.request,
        ):
            raise ValueError(
                "runtime probe execution input probe_identifier must match "
                "planned request identity"
            )
        if replay_artifact.replay_target != self.replay_target_seed:
            raise ValueError(
                "runtime probe execution input replay_artifact target must match "
                "request seed"
            )
        if replay_artifact.replay_selector != self.replay_selector_seed:
            raise ValueError(
                "runtime probe execution input replay_artifact selector must match "
                "request seed"
            )
        if replay_artifact.replay_inputs != _replay_inputs_for_request(
            plan_id=self.plan_id,
            request_id=self.request_id,
            request=self.request,
        ):
            raise ValueError(
                "runtime probe execution input replay_inputs must match planned "
                "request identity"
            )
        if not replay_artifact.runtime_assumptions:
            raise ValueError(
                "runtime probe execution inputs require runtime_assumptions"
            )


@dataclass(frozen=True)
class RuntimeProbeExecutionInputBatch:
    """Ordered internal execution-input batch for one runtime request plan."""

    plan_id: str
    request_ids: tuple[str, ...]
    inputs: tuple[RuntimeProbeExecutionInput, ...]
    contract_version: str = field(
        default=_RUNTIME_PROBE_EXECUTION_INPUT_BATCH_CONTRACT_VERSION,
        init=False,
    )

    def __post_init__(self) -> None:
        """Reject batches whose request order or plan identity has drifted."""
        if not self.plan_id.strip():
            raise ValueError("plan_id must be non-empty")
        input_request_ids = tuple(input_item.request_id for input_item in self.inputs)
        if self.request_ids != input_request_ids:
            raise ValueError(
                "runtime probe execution input batch request_ids must match inputs"
            )

        seen_request_ids: set[str] = set()
        for input_item in self.inputs:
            if input_item.plan_id != self.plan_id:
                raise ValueError(
                    "runtime probe execution input batch plan_id must match inputs"
                )
            if input_item.request_id in seen_request_ids:
                raise ValueError("duplicate runtime probe execution input request_id")
            seen_request_ids.add(input_item.request_id)


@dataclass(frozen=True)
class RuntimeProbeRunnerRequest:
    """Internal, non-executing handoff request for a future runtime probe runner."""

    plan_id: str
    request_id: str
    request: RuntimeProbeRequest
    execution_input: RuntimeProbeExecutionInput
    replay_artifact: RuntimeProbeReplayArtifact
    runner_contract_revision: str
    timeout_seconds: int
    runner_environment: tuple[RuntimeProbeReplayField, ...]
    runner_assumptions: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject runner handoff requests whose replay contract has drifted."""
        if not self.plan_id.strip():
            raise ValueError("plan_id must be non-empty")
        if not self.request_id.strip():
            raise ValueError("request_id must be non-empty")
        if self.plan_id != self.execution_input.plan_id:
            raise ValueError(
                "runtime probe runner request plan_id must match execution input"
            )
        if self.request_id != self.execution_input.request_id:
            raise ValueError(
                "runtime probe runner request request_id must match execution input"
            )
        if self.request is not self.execution_input.request:
            raise ValueError(
                "runtime probe runner request request must be execution input request"
            )
        if self.replay_artifact is not self.execution_input.replay_artifact:
            raise ValueError(
                "runtime probe runner request replay_artifact must be execution "
                "input replay_artifact"
            )
        _validate_execution_input(self.execution_input)
        _validate_runner_handoff_metadata(
            runner_contract_revision=self.runner_contract_revision,
            timeout_seconds=self.timeout_seconds,
            runner_environment=self.runner_environment,
            runner_assumptions=self.runner_assumptions,
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonEnvironmentContext:
    """Frozen local-Python runner environment derived from replay metadata."""

    repository_root: str
    working_directory: str
    python_path_entries: tuple[str, ...]
    runner_contract_revision: str
    timeout_seconds: int
    runner_environment: tuple[RuntimeProbeReplayField, ...]
    runner_assumptions: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject contexts that drift from their source runner metadata."""
        if not self.runner_contract_revision.strip():
            raise ValueError("runner_contract_revision must be non-empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not isinstance(self.python_path_entries, tuple):
            raise ValueError("python_path_entries must be a tuple")
        _validate_replay_fields(
            self.runner_environment,
            field_name="runner_environment",
        )
        _validate_replay_fields(
            self.runner_assumptions,
            field_name="runner_assumptions",
        )
        (
            repository_root,
            working_directory,
            python_path_entries,
        ) = _local_python_environment_parts_from_fields(self.runner_environment)
        if self.repository_root != repository_root:
            raise ValueError(
                "local Python repository_root must match runner_environment"
            )
        if self.working_directory != working_directory:
            raise ValueError(
                "local Python working_directory must match runner_environment"
            )
        if self.python_path_entries != python_path_entries:
            raise ValueError(
                "local Python python_path_entries must match runner_environment"
            )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonWorkerRequestPayload:
    """Frozen strict JSON request payload for future local-Python workers."""

    plan_id: str
    request_id: str
    family_label: RuntimeProbeFamily
    form_label: str
    replay_target_seed: str
    replay_selector_seed: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    runtime_assumptions: tuple[RuntimeProbeReplayField, ...]
    runner_contract_revision: str
    runner_environment: tuple[RuntimeProbeReplayField, ...]
    runner_assumptions: tuple[RuntimeProbeReplayField, ...]
    invocation_contract_revision: str
    invocation_identity: str
    argv: tuple[str, ...]
    working_directory: str
    python_path_entries: tuple[str, ...]
    timeout_seconds: int
    contract_version: str = field(
        default=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_PAYLOAD_CONTRACT_VERSION,
        init=False,
    )

    def __post_init__(self) -> None:
        """Reject worker request payloads with drifted duplicate metadata."""
        _validate_local_python_worker_request_payload_parts(
            contract_version=self.contract_version,
            plan_id=self.plan_id,
            request_id=self.request_id,
            family_label=self.family_label,
            form_label=self.form_label,
            replay_target_seed=self.replay_target_seed,
            replay_selector_seed=self.replay_selector_seed,
            request_replay_payload_fields=self.request_replay_payload_fields,
            runtime_assumptions=self.runtime_assumptions,
            runner_contract_revision=self.runner_contract_revision,
            runner_environment=self.runner_environment,
            runner_assumptions=self.runner_assumptions,
            invocation_contract_revision=self.invocation_contract_revision,
            invocation_identity=self.invocation_identity,
            argv=self.argv,
            working_directory=self.working_directory,
            python_path_entries=self.python_path_entries,
            timeout_seconds=self.timeout_seconds,
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonSubprocessInvocation:
    """Frozen, shell-free local-Python subprocess invocation contract."""

    runner_request: RuntimeProbeRunnerRequest
    environment_context: RuntimeProbeLocalPythonEnvironmentContext
    python_executable: str
    argv: tuple[str, ...]
    working_directory: str
    python_path_entries: tuple[str, ...]
    timeout_seconds: int
    invocation_contract_revision: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject invocation contracts that drift from their runner request."""
        _validate_runner_request(self.runner_request)
        _validate_local_python_environment_context(self.environment_context)

        expected_context = derive_runtime_probe_local_python_environment_context(
            self.runner_request
        )
        if self.environment_context != expected_context:
            raise ValueError(
                "local Python subprocess invocation environment_context must be "
                "derived from runner request"
            )

        if not self.invocation_contract_revision.strip():
            raise ValueError("invocation_contract_revision must be non-empty")
        _validate_absolute_path_metadata(
            self.python_executable,
            field_name="python_executable",
        )
        _validate_local_python_subprocess_argv(
            self.argv,
            python_executable=self.python_executable,
        )
        _validate_absolute_path_metadata(
            self.working_directory,
            field_name="working_directory",
        )
        if self.working_directory != self.environment_context.working_directory:
            raise ValueError(
                "local Python subprocess invocation working_directory must match "
                "environment context"
            )
        if self.timeout_seconds != self.environment_context.timeout_seconds:
            raise ValueError(
                "local Python subprocess invocation timeout_seconds must match "
                "environment context"
            )
        if not isinstance(self.python_path_entries, tuple):
            raise ValueError(
                "local Python subprocess invocation python_path_entries must be a tuple"
            )
        for python_path_entry in self.python_path_entries:
            _validate_absolute_path_metadata(
                python_path_entry,
                field_name="python_path_entry",
            )
        if self.python_path_entries != self.environment_context.python_path_entries:
            raise ValueError(
                "local Python subprocess invocation python_path_entries must match "
                "environment context"
            )
        _validate_replay_fields(
            self.request_replay_payload_fields,
            field_name="request_replay_payload_fields",
        )
        if (
            self.request_replay_payload_fields
            != self.runner_request.replay_artifact.replay_inputs
        ):
            raise ValueError(
                "local Python subprocess invocation replay payload fields must match "
                "runner request replay inputs"
            )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonWorkerRequestStdinTransport:
    """Frozen stdin handoff contract for future local-Python workers."""

    invocation: RuntimeProbeLocalPythonSubprocessInvocation
    payload: RuntimeProbeLocalPythonWorkerRequestPayload
    stdin_text: str
    invocation_identity: str
    argv: tuple[str, ...]
    working_directory: str
    python_path_entries: tuple[str, ...]
    timeout_seconds: int
    plan_id: str
    request_id: str
    family_label: RuntimeProbeFamily
    form_label: str
    replay_target_seed: str
    replay_selector_seed: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]
    stdin_transport_contract_revision: str = (
        _RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_STDIN_TRANSPORT_CONTRACT_REVISION
    )

    def __post_init__(self) -> None:
        """Reject stdin transports that drift from invocation or payload JSON."""
        _validate_local_python_worker_request_stdin_transport(self)


@dataclass(frozen=True)
class RuntimeProbeLocalPythonSubprocessHandlerConfig:
    """Configured family/form adapter metadata for a local-Python probe worker."""

    family_label: RuntimeProbeFamily
    form_label: str
    python_executable: str
    module_name: str
    invocation_contract_revision: str
    completion_contract_revision: str
    module_argv: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject handler metadata before it can reach subprocess execution."""
        _validate_runtime_probe_local_python_subprocess_handler_config(self)


@dataclass(frozen=True)
class _RuntimeProbeLocalPythonSubprocessHandler:
    """Callable adapter from runner requests to local-Python subprocess attempts."""

    config: RuntimeProbeLocalPythonSubprocessHandlerConfig

    def __post_init__(self) -> None:
        """Reject incomplete local-Python handler configuration."""
        _validate_runtime_probe_local_python_subprocess_handler_config(self.config)

    def __call__(
        self,
        runner_request: RuntimeProbeRunnerRequest,
    ) -> RuntimeProbeExecutionAttempt:
        """Materialize, execute, and normalize one configured local-Python probe."""
        _validate_runner_request(runner_request)
        _validate_runtime_probe_local_python_subprocess_handler_config(self.config)
        _validate_local_python_subprocess_handler_request_key(
            runner_request,
            self.config,
        )
        invocation = materialize_runtime_probe_local_python_subprocess_invocation(
            runner_request,
            python_executable=self.config.python_executable,
            module_name=self.config.module_name,
            invocation_contract_revision=self.config.invocation_contract_revision,
            module_argv=self.config.module_argv,
        )
        return execute_runtime_probe_local_python_subprocess_invocation_attempt(
            invocation,
            completion_contract_revision=self.config.completion_contract_revision,
        )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonProcessCompletion:
    """Frozen raw local-Python process completion contract."""

    invocation: RuntimeProbeLocalPythonSubprocessInvocation
    invocation_identity: str
    argv: tuple[str, ...]
    working_directory: str
    python_path_entries: tuple[str, ...]
    timeout_seconds: int
    returncode: int
    stdout_text: str
    stderr_text: str
    completion_contract_revision: str
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...]

    def __post_init__(self) -> None:
        """Reject raw completions that drift from their source invocation."""
        _validate_local_python_subprocess_invocation(self.invocation)

        if self.invocation_identity != _runtime_probe_local_python_invocation_identity(
            self.invocation
        ):
            raise ValueError(
                "local Python process completion invocation_identity must match "
                "invocation"
            )
        if self.argv != self.invocation.argv:
            raise ValueError(
                "local Python process completion argv must match invocation"
            )
        if self.working_directory != self.invocation.working_directory:
            raise ValueError(
                "local Python process completion working_directory must match "
                "invocation"
            )
        if self.python_path_entries != self.invocation.python_path_entries:
            raise ValueError(
                "local Python process completion python_path_entries must match "
                "invocation"
            )
        if self.timeout_seconds != self.invocation.timeout_seconds:
            raise ValueError(
                "local Python process completion timeout_seconds must match invocation"
            )

        _validate_local_python_process_returncode(self.returncode)
        _validate_local_python_raw_text(
            self.stdout_text,
            field_name="stdout_text",
        )
        _validate_local_python_raw_text(
            self.stderr_text,
            field_name="stderr_text",
        )
        _validate_contract_revision(
            self.completion_contract_revision,
            field_name="completion_contract_revision",
        )
        _validate_replay_fields(
            self.request_replay_payload_fields,
            field_name="request_replay_payload_fields",
        )
        if (
            self.request_replay_payload_fields
            != self.invocation.request_replay_payload_fields
        ):
            raise ValueError(
                "local Python process completion replay payload fields must match "
                "invocation"
            )


@dataclass(frozen=True)
class RuntimeProbeLocalPythonStdoutProtocolResult:
    """Typed internal success protocol parsed from local-Python stdout."""

    completion: RuntimeProbeLocalPythonProcessCompletion
    stdout_protocol_revision: str
    normalized_payload: tuple[RuntimeProbeReplayField, ...]
    durable_artifact_reference: str | None = None

    def __post_init__(self) -> None:
        """Reject parsed success payloads whose carried completion is invalid."""
        _validate_local_python_process_completion(self.completion)
        if self.completion.returncode != 0:
            raise ValueError(
                "local Python stdout protocol results require zero returncode"
            )
        if (
            self.stdout_protocol_revision
            != _RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION
        ):
            raise ValueError("local Python stdout protocol revision is unsupported")
        _validate_replay_fields(
            self.normalized_payload,
            field_name="normalized_payload",
        )
        _parse_runtime_probe_local_python_durable_artifact_reference(
            self.durable_artifact_reference
        )
        if not self.normalized_payload and self.durable_artifact_reference is None:
            raise ValueError(
                "local Python stdout protocol results require normalized_payload "
                "or durable_artifact_reference"
            )


@dataclass(frozen=True)
class RuntimeProbeRunnerRequestBatch:
    """Ordered internal runner-request batch for one execution-input batch."""

    plan_id: str
    request_ids: tuple[str, ...]
    runner_requests: tuple[RuntimeProbeRunnerRequest, ...]
    runner_contract_revision: str
    timeout_seconds: int
    runner_environment: tuple[RuntimeProbeReplayField, ...]
    runner_assumptions: tuple[RuntimeProbeReplayField, ...]
    contract_version: str = field(
        default=_RUNTIME_PROBE_RUNNER_REQUEST_BATCH_CONTRACT_VERSION,
        init=False,
    )

    def __post_init__(self) -> None:
        """Reject runner-request batches whose order or identity has drifted."""
        if not self.plan_id.strip():
            raise ValueError("plan_id must be non-empty")
        _validate_runner_handoff_metadata(
            runner_contract_revision=self.runner_contract_revision,
            timeout_seconds=self.timeout_seconds,
            runner_environment=self.runner_environment,
            runner_assumptions=self.runner_assumptions,
        )
        runner_request_ids = tuple(
            runner_request.request_id for runner_request in self.runner_requests
        )
        if self.request_ids != runner_request_ids:
            raise ValueError(
                "runtime probe runner request batch request_ids must match requests"
            )

        seen_request_ids: set[str] = set()
        for runner_request in self.runner_requests:
            _validate_runner_request(runner_request)
            if runner_request.plan_id != self.plan_id:
                raise ValueError(
                    "runtime probe runner request batch plan_id must match requests"
                )
            if runner_request.runner_contract_revision != self.runner_contract_revision:
                raise ValueError(
                    "runtime probe runner request batch runner_contract_revision "
                    "must match requests"
                )
            if runner_request.timeout_seconds != self.timeout_seconds:
                raise ValueError(
                    "runtime probe runner request batch timeout_seconds must match "
                    "requests"
                )
            if runner_request.runner_environment != self.runner_environment:
                raise ValueError(
                    "runtime probe runner request batch runner_environment must "
                    "match requests"
                )
            if runner_request.runner_assumptions != self.runner_assumptions:
                raise ValueError(
                    "runtime probe runner request batch runner_assumptions must "
                    "match requests"
                )
            if runner_request.request_id in seen_request_ids:
                raise ValueError("duplicate runtime probe runner request_id")
            seen_request_ids.add(runner_request.request_id)


@dataclass(frozen=True)
class RuntimeProbeDiagnosticRunnerRequestPreparation:
    """Internal diagnostic-gated, non-executing runner-request preparation."""

    diagnostic: SemanticDiagnosticResult
    request_plan: RuntimeProbeRequestPlan
    execution_input_batch: RuntimeProbeExecutionInputBatch
    runner_request_batch: RuntimeProbeRunnerRequestBatch

    def __post_init__(self) -> None:
        """Reject prepared runner requests that drift from the diagnostic plan."""
        _validate_diagnostic_request_plan(self.diagnostic, self.request_plan)
        _validate_execution_input_batch(self.execution_input_batch)
        _validate_runner_request_batch(self.runner_request_batch)

        if self.execution_input_batch.plan_id != self.request_plan.plan_id:
            raise ValueError(
                "runtime probe preparation execution input batch plan_id must "
                "match diagnostic request plan"
            )
        if self.execution_input_batch.request_ids != self.request_plan.request_ids:
            raise ValueError(
                "runtime probe preparation execution input batch request_ids must "
                "match diagnostic request plan"
            )
        if self.runner_request_batch.plan_id != self.request_plan.plan_id:
            raise ValueError(
                "runtime probe preparation runner request batch plan_id must match "
                "diagnostic request plan"
            )
        if self.runner_request_batch.request_ids != self.request_plan.request_ids:
            raise ValueError(
                "runtime probe preparation runner request batch request_ids must "
                "match diagnostic request plan"
            )

        for request, input_item, runner_request in zip(
            self.request_plan.requests,
            self.execution_input_batch.inputs,
            self.runner_request_batch.runner_requests,
            strict=True,
        ):
            if input_item.request is not request:
                raise ValueError(
                    "runtime probe preparation execution input request must be the "
                    "diagnostic request plan request"
                )
            if runner_request.request is not request:
                raise ValueError(
                    "runtime probe preparation runner request must be the diagnostic "
                    "request plan request"
                )
            if runner_request.execution_input is not input_item:
                raise ValueError(
                    "runtime probe preparation runner request must use the prepared "
                    "execution input"
                )
            if runner_request.replay_artifact is not input_item.replay_artifact:
                raise ValueError(
                    "runtime probe preparation runner request replay_artifact must "
                    "be the prepared execution input replay_artifact"
                )


@dataclass(frozen=True)
class RuntimeProbeExecutionAttempt:
    """Internal normalized runner output for one non-executing probe input."""

    plan_id: str
    request_id: str
    request: RuntimeProbeRequest
    execution_input: RuntimeProbeExecutionInput
    outcome: RuntimeProbeResultOutcome
    normalized_payload: tuple[RuntimeProbeReplayField, ...] = ()
    durable_artifact_reference: str | None = None
    failure_summary: str | None = None
    failure_detail_fields: tuple[RuntimeProbeReplayField, ...] = ()

    def __post_init__(self) -> None:
        """Reject attempts whose normalized result metadata cannot be trusted."""
        if self.plan_id != self.execution_input.plan_id:
            raise ValueError(
                "runtime probe execution attempt plan_id must match execution input"
            )
        if self.request_id != self.execution_input.request_id:
            raise ValueError(
                "runtime probe execution attempt request_id must match execution input"
            )
        if self.request is not self.execution_input.request:
            raise ValueError(
                "runtime probe execution attempt request must be execution input "
                "request"
            )

        _validate_optional_reference(
            self.durable_artifact_reference,
            field_name="durable_artifact_reference",
        )
        _validate_replay_fields(
            self.normalized_payload,
            field_name="normalized_payload",
        )
        _validate_replay_fields(
            self.failure_detail_fields,
            field_name="failure_detail_fields",
        )

        if self.outcome is RuntimeProbeResultOutcome.OBSERVED:
            _validate_observed_attempt_metadata(self)
            return
        if self.outcome in _NON_PROOF_ATTEMPT_OUTCOMES:
            _validate_non_proof_attempt_metadata(self)
            return
        raise ValueError("runtime probe execution attempt outcome is not supported")


RuntimeProbeRunnerCallable: TypeAlias = Callable[
    [RuntimeProbeRunnerRequest],
    RuntimeProbeExecutionAttempt,
]


@dataclass(frozen=True)
class RuntimeProbeRunnerHandlerEntry:
    """Typed dispatch-table entry for one runtime probe family/form handler."""

    family_label: RuntimeProbeFamily
    form_label: str
    handler: RuntimeProbeRunnerCallable

    def __post_init__(self) -> None:
        """Reject incomplete dispatch handler metadata."""
        _validate_runtime_probe_runner_handler_entry(self)


@dataclass(frozen=True)
class RuntimeProbeDispatchingRunner:
    """Runner callable that dispatches requests to family/form handlers."""

    handler_entries: tuple[RuntimeProbeRunnerHandlerEntry, ...]
    missing_handler_outcome: RuntimeProbeResultOutcome = (
        RuntimeProbeResultOutcome.SETUP_FAILED
    )
    _handlers_by_key: Mapping[
        RuntimeProbeRunnerHandlerKey,
        RuntimeProbeRunnerCallable,
    ] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Reject ambiguous dispatch tables and proof-bearing miss outcomes."""
        handlers_by_key = _index_runtime_probe_runner_handler_entries(
            self.handler_entries
        )
        _validate_failure_normalization_outcome(self.missing_handler_outcome)
        object.__setattr__(
            self,
            "_handlers_by_key",
            MappingProxyType(handlers_by_key),
        )

    def __call__(
        self,
        runner_request: RuntimeProbeRunnerRequest,
    ) -> RuntimeProbeExecutionAttempt:
        """Dispatch a validated request by its carried family and form labels."""
        _validate_runner_request(runner_request)
        handler = self._handlers_by_key.get(
            _runtime_probe_runner_request_handler_key(runner_request)
        )
        if handler is None:
            return _runtime_probe_missing_handler_attempt(
                runner_request,
                outcome=self.missing_handler_outcome,
            )
        attempt = handler(runner_request)
        if not isinstance(attempt, RuntimeProbeExecutionAttempt):
            raise ValueError(
                "runtime probe runner callable must return typed runtime probe "
                "execution attempts"
            )
        return attempt


@dataclass(frozen=True)
class RuntimeProbeFailureNormalizingRunner:
    """Adapter that converts runner-raised exceptions into non-proof attempts."""

    runner: RuntimeProbeRunnerCallable
    outcome: RuntimeProbeResultOutcome = RuntimeProbeResultOutcome.CRASHED

    def __post_init__(self) -> None:
        """Reject normalization outcomes that could be mistaken for proof."""
        _validate_failure_normalization_outcome(self.outcome)

    def __call__(
        self,
        runner_request: RuntimeProbeRunnerRequest,
    ) -> RuntimeProbeExecutionAttempt:
        """Run the wrapped runner and normalize raised Exceptions only."""
        _validate_runner_request(runner_request)
        try:
            attempt = self.runner(runner_request)
        except Exception as exception:
            return _runtime_probe_failure_attempt_from_runner_exception(
                runner_request,
                outcome=self.outcome,
                exception=exception,
            )
        if not isinstance(attempt, RuntimeProbeExecutionAttempt):
            raise ValueError(
                "runtime probe runner callable must return typed runtime probe "
                "execution attempts"
            )
        return attempt


@dataclass(frozen=True)
class RuntimeProbeRunnerAttemptCollection:
    """Internal runner-callable boundary for validated probe attempts."""

    runner_request_batch: RuntimeProbeRunnerRequestBatch
    attempts: tuple[RuntimeProbeExecutionAttempt, ...]
    result_batch: RuntimeProbeResultBatch

    def __post_init__(self) -> None:
        """Reject collections that bypass runner-request-gated assembly."""
        _validate_runner_request_batch(self.runner_request_batch)
        if not isinstance(self.attempts, tuple):
            raise ValueError(
                "runtime probe runner attempt collection attempts must be a tuple"
            )
        for attempt in self.attempts:
            _validate_execution_attempt(attempt)

        attempt_request_ids = tuple(attempt.request_id for attempt in self.attempts)
        if attempt_request_ids != self.runner_request_batch.request_ids:
            raise ValueError(
                "runtime probe runner attempt collection attempts must be in "
                "runner request order"
            )

        expected_result_batch = (
            assemble_runtime_probe_result_batch_from_runner_request_attempts(
                self.runner_request_batch,
                self.attempts,
            )
        )
        _validate_runner_attempt_collection_result_batch(
            self.runner_request_batch,
            self.result_batch,
        )
        if self.result_batch != expected_result_batch:
            raise ValueError(
                "runtime probe runner attempt collection result_batch must match "
                "assembled runner-request attempts"
            )


def materialize_runtime_probe_execution_input_batch(
    plan: RuntimeProbeRequestPlan,
    *,
    repository_snapshot_basis: RepositorySnapshotBasis,
    probe_contract_revision: str,
    runtime_assumptions: Iterable[RuntimeProbeReplayField],
) -> RuntimeProbeExecutionInputBatch:
    """Materialize replay-ready, non-executing inputs for a planned probe batch."""
    _validate_request_plan(plan)
    if not probe_contract_revision.strip():
        raise ValueError("probe_contract_revision must be non-empty")
    assumptions = tuple(runtime_assumptions)
    if not assumptions:
        raise ValueError("runtime probe execution inputs require runtime_assumptions")

    inputs = tuple(
        _materialize_runtime_probe_execution_input(
            plan_id=plan.plan_id,
            request_id=request_id,
            request=request,
            repository_snapshot_basis=repository_snapshot_basis,
            probe_contract_revision=probe_contract_revision,
            runtime_assumptions=assumptions,
        )
        for request, request_id in zip(plan.requests, plan.request_ids, strict=True)
    )
    return RuntimeProbeExecutionInputBatch(
        plan_id=plan.plan_id,
        request_ids=plan.request_ids,
        inputs=inputs,
    )


def materialize_runtime_probe_runner_request_batch(
    input_batch: RuntimeProbeExecutionInputBatch,
    *,
    runner_contract_revision: str,
    timeout_seconds: int,
    runner_environment: Iterable[RuntimeProbeReplayField],
    runner_assumptions: Iterable[RuntimeProbeReplayField],
) -> RuntimeProbeRunnerRequestBatch:
    """Materialize replay-ready inputs into non-executing runner handoff requests."""
    _validate_execution_input_batch(input_batch)

    environment = tuple(runner_environment)
    assumptions = tuple(runner_assumptions)
    _validate_runner_handoff_metadata(
        runner_contract_revision=runner_contract_revision,
        timeout_seconds=timeout_seconds,
        runner_environment=environment,
        runner_assumptions=assumptions,
    )

    runner_requests = tuple(
        RuntimeProbeRunnerRequest(
            plan_id=input_item.plan_id,
            request_id=input_item.request_id,
            request=input_item.request,
            execution_input=input_item,
            replay_artifact=input_item.replay_artifact,
            runner_contract_revision=runner_contract_revision,
            timeout_seconds=timeout_seconds,
            runner_environment=environment,
            runner_assumptions=assumptions,
        )
        for input_item in input_batch.inputs
    )
    return RuntimeProbeRunnerRequestBatch(
        plan_id=input_batch.plan_id,
        request_ids=input_batch.request_ids,
        runner_requests=runner_requests,
        runner_contract_revision=runner_contract_revision,
        timeout_seconds=timeout_seconds,
        runner_environment=environment,
        runner_assumptions=assumptions,
    )


def prepare_runtime_probe_runner_requests_for_diagnostic(
    diagnostic: SemanticDiagnosticResult,
    *,
    repository_snapshot_basis: RepositorySnapshotBasis,
    probe_contract_revision: str,
    runtime_assumptions: Iterable[RuntimeProbeReplayField],
    runner_contract_revision: str,
    timeout_seconds: int,
    runner_environment: Iterable[RuntimeProbeReplayField],
    runner_assumptions: Iterable[RuntimeProbeReplayField],
) -> RuntimeProbeDiagnosticRunnerRequestPreparation:
    """Prepare diagnostic-planned runner requests without executing probes."""
    request_plan = _request_plan_for_diagnostic_preparation(diagnostic)
    execution_input_batch = materialize_runtime_probe_execution_input_batch(
        request_plan,
        repository_snapshot_basis=repository_snapshot_basis,
        probe_contract_revision=probe_contract_revision,
        runtime_assumptions=runtime_assumptions,
    )
    runner_request_batch = materialize_runtime_probe_runner_request_batch(
        execution_input_batch,
        runner_contract_revision=runner_contract_revision,
        timeout_seconds=timeout_seconds,
        runner_environment=runner_environment,
        runner_assumptions=runner_assumptions,
    )
    return RuntimeProbeDiagnosticRunnerRequestPreparation(
        diagnostic=diagnostic,
        request_plan=request_plan,
        execution_input_batch=execution_input_batch,
        runner_request_batch=runner_request_batch,
    )


def derive_runtime_probe_local_python_environment_context(
    runner_request: RuntimeProbeRunnerRequest,
) -> RuntimeProbeLocalPythonEnvironmentContext:
    """Derive typed local-Python metadata from a validated runner request."""
    _validate_runner_request(runner_request)
    (
        repository_root,
        working_directory,
        python_path_entries,
    ) = _local_python_environment_parts_from_fields(runner_request.runner_environment)
    return RuntimeProbeLocalPythonEnvironmentContext(
        repository_root=repository_root,
        working_directory=working_directory,
        python_path_entries=python_path_entries,
        runner_contract_revision=runner_request.runner_contract_revision,
        timeout_seconds=runner_request.timeout_seconds,
        runner_environment=runner_request.runner_environment,
        runner_assumptions=runner_request.runner_assumptions,
    )


def materialize_runtime_probe_local_python_worker_request_payload(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
) -> RuntimeProbeLocalPythonWorkerRequestPayload:
    """Build a frozen local-Python worker JSON payload without executing code."""
    _validate_local_python_subprocess_invocation(invocation)
    runner_request = invocation.runner_request
    _validate_runner_request(runner_request)
    request = runner_request.request
    return RuntimeProbeLocalPythonWorkerRequestPayload(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        request_replay_payload_fields=invocation.request_replay_payload_fields,
        runtime_assumptions=runner_request.replay_artifact.runtime_assumptions,
        runner_contract_revision=runner_request.runner_contract_revision,
        runner_environment=runner_request.runner_environment,
        runner_assumptions=runner_request.runner_assumptions,
        invocation_contract_revision=invocation.invocation_contract_revision,
        invocation_identity=_runtime_probe_local_python_invocation_identity(invocation),
        argv=invocation.argv,
        working_directory=invocation.working_directory,
        python_path_entries=invocation.python_path_entries,
        timeout_seconds=invocation.timeout_seconds,
    )


def serialize_runtime_probe_local_python_worker_request_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> str:
    """Serialize a local-Python worker request payload as deterministic JSON."""
    _validate_local_python_worker_request_payload(payload)
    return json.dumps(
        _runtime_probe_local_python_worker_request_payload_json_object(payload),
        separators=(",", ":"),
    )


def parse_runtime_probe_local_python_worker_request_payload(
    payload_json: str,
) -> RuntimeProbeLocalPythonWorkerRequestPayload:
    """Parse a strict local-Python worker request payload JSON document."""
    payload_object = _parse_runtime_probe_local_python_worker_request_payload_object(
        payload_json
    )
    contract_version = _parse_local_python_worker_payload_string_field(
        payload_object["contract_version"],
        field_name="contract_version",
    )
    if (
        contract_version
        != _RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_PAYLOAD_CONTRACT_VERSION
    ):
        raise ValueError(
            "local Python worker request payload contract_version is unsupported"
        )

    return RuntimeProbeLocalPythonWorkerRequestPayload(
        plan_id=_parse_local_python_worker_payload_string_field(
            payload_object["plan_id"],
            field_name="plan_id",
        ),
        request_id=_parse_local_python_worker_payload_string_field(
            payload_object["request_id"],
            field_name="request_id",
        ),
        family_label=_parse_runtime_probe_worker_payload_family_label(
            payload_object["family_label"]
        ),
        form_label=_parse_local_python_worker_payload_string_field(
            payload_object["form_label"],
            field_name="form_label",
        ),
        replay_target_seed=_parse_local_python_worker_payload_string_field(
            payload_object["replay_target_seed"],
            field_name="replay_target_seed",
        ),
        replay_selector_seed=_parse_local_python_worker_payload_string_field(
            payload_object["replay_selector_seed"],
            field_name="replay_selector_seed",
        ),
        request_replay_payload_fields=(
            _parse_runtime_probe_worker_payload_replay_fields(
                payload_object["request_replay_payload_fields"],
                field_name="request_replay_payload_fields",
            )
        ),
        runtime_assumptions=_parse_runtime_probe_worker_payload_replay_fields(
            payload_object["runtime_assumptions"],
            field_name="runtime_assumptions",
        ),
        runner_contract_revision=_parse_local_python_worker_payload_string_field(
            payload_object["runner_contract_revision"],
            field_name="runner_contract_revision",
        ),
        runner_environment=_parse_runtime_probe_worker_payload_replay_fields(
            payload_object["runner_environment"],
            field_name="runner_environment",
        ),
        runner_assumptions=_parse_runtime_probe_worker_payload_replay_fields(
            payload_object["runner_assumptions"],
            field_name="runner_assumptions",
        ),
        invocation_contract_revision=(
            _parse_local_python_worker_payload_string_field(
                payload_object["invocation_contract_revision"],
                field_name="invocation_contract_revision",
            )
        ),
        invocation_identity=_parse_local_python_worker_payload_string_field(
            payload_object["invocation_identity"],
            field_name="invocation_identity",
        ),
        argv=_parse_local_python_worker_payload_argv(payload_object["argv"]),
        working_directory=_parse_local_python_worker_payload_absolute_path(
            payload_object["working_directory"],
            field_name="working_directory",
        ),
        python_path_entries=(
            _parse_local_python_worker_payload_python_path_entries(
                payload_object["python_path_entries"]
            )
        ),
        timeout_seconds=_parse_local_python_worker_payload_timeout_seconds(
            payload_object["timeout_seconds"]
        ),
    )


def materialize_runtime_probe_local_python_worker_request_stdin_transport(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
) -> RuntimeProbeLocalPythonWorkerRequestStdinTransport:
    """Build deterministic stdin text for a local-Python worker request."""
    _validate_local_python_subprocess_invocation(invocation)
    payload = materialize_runtime_probe_local_python_worker_request_payload(invocation)
    stdin_text = serialize_runtime_probe_local_python_worker_request_payload(payload)
    parsed_payload = parse_runtime_probe_local_python_worker_request_payload(stdin_text)
    if parsed_payload != payload:
        raise ValueError(
            "local Python worker request stdin transport payload failed strict "
            "round trip"
        )

    runner_request = invocation.runner_request
    return RuntimeProbeLocalPythonWorkerRequestStdinTransport(
        invocation=invocation,
        payload=payload,
        stdin_text=stdin_text,
        invocation_identity=payload.invocation_identity,
        argv=invocation.argv,
        working_directory=invocation.working_directory,
        python_path_entries=invocation.python_path_entries,
        timeout_seconds=invocation.timeout_seconds,
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        family_label=runner_request.request.family_label,
        form_label=runner_request.request.form_label,
        replay_target_seed=runner_request.request.replay_target_seed,
        replay_selector_seed=runner_request.request.replay_selector_seed,
        request_replay_payload_fields=invocation.request_replay_payload_fields,
    )


def materialize_runtime_probe_local_python_subprocess_invocation(
    runner_request: RuntimeProbeRunnerRequest,
    *,
    python_executable: str,
    module_name: str,
    invocation_contract_revision: str,
    module_argv: Iterable[str] = (),
) -> RuntimeProbeLocalPythonSubprocessInvocation:
    """Build a frozen local-Python subprocess invocation without executing it."""
    _validate_runner_request(runner_request)
    environment_context = derive_runtime_probe_local_python_environment_context(
        runner_request
    )
    executable = _validate_absolute_path_metadata(
        python_executable,
        field_name="python_executable",
    )
    validated_module_name = _validate_local_python_module_name(module_name)
    validated_module_argv = tuple(
        _validate_local_python_argv_token(token, field_name="module_argv")
        for token in module_argv
    )

    return RuntimeProbeLocalPythonSubprocessInvocation(
        runner_request=runner_request,
        environment_context=environment_context,
        python_executable=executable,
        argv=(executable, "-m", validated_module_name, *validated_module_argv),
        working_directory=environment_context.working_directory,
        python_path_entries=environment_context.python_path_entries,
        timeout_seconds=environment_context.timeout_seconds,
        invocation_contract_revision=invocation_contract_revision,
        request_replay_payload_fields=runner_request.replay_artifact.replay_inputs,
    )


def materialize_runtime_probe_local_python_process_completion(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
    *,
    returncode: int,
    stdout_text: str,
    stderr_text: str,
    completion_contract_revision: str,
) -> RuntimeProbeLocalPythonProcessCompletion:
    """Build a frozen raw process completion without interpreting output."""
    _validate_local_python_subprocess_invocation(invocation)
    validated_returncode = _validate_local_python_process_returncode(returncode)
    validated_stdout = _validate_local_python_raw_text(
        stdout_text,
        field_name="stdout_text",
    )
    validated_stderr = _validate_local_python_raw_text(
        stderr_text,
        field_name="stderr_text",
    )
    validated_revision = _validate_contract_revision(
        completion_contract_revision,
        field_name="completion_contract_revision",
    )

    return RuntimeProbeLocalPythonProcessCompletion(
        invocation=invocation,
        invocation_identity=_runtime_probe_local_python_invocation_identity(invocation),
        argv=invocation.argv,
        working_directory=invocation.working_directory,
        python_path_entries=invocation.python_path_entries,
        timeout_seconds=invocation.timeout_seconds,
        returncode=validated_returncode,
        stdout_text=validated_stdout,
        stderr_text=validated_stderr,
        completion_contract_revision=validated_revision,
        request_replay_payload_fields=invocation.request_replay_payload_fields,
    )


def materialize_runtime_probe_local_python_stdout_protocol_result(
    completion: RuntimeProbeLocalPythonProcessCompletion,
) -> RuntimeProbeLocalPythonStdoutProtocolResult:
    """Parse a zero-returncode local-Python completion stdout protocol."""
    _validate_local_python_process_completion(completion)
    if completion.returncode != 0:
        raise ValueError(
            "local Python stdout protocol materialization requires zero returncode"
        )
    (
        stdout_protocol_revision,
        normalized_payload,
        durable_artifact_reference,
    ) = _parse_runtime_probe_local_python_stdout_protocol(completion.stdout_text)
    return RuntimeProbeLocalPythonStdoutProtocolResult(
        completion=completion,
        stdout_protocol_revision=stdout_protocol_revision,
        normalized_payload=normalized_payload,
        durable_artifact_reference=durable_artifact_reference,
    )


def materialize_runtime_probe_local_python_stdout_protocol_attempt(
    protocol_result: RuntimeProbeLocalPythonStdoutProtocolResult,
) -> RuntimeProbeExecutionAttempt:
    """Convert a typed local-Python stdout success protocol into an attempt."""
    _validate_local_python_stdout_protocol_result(protocol_result)
    completion = protocol_result.completion
    invocation = completion.invocation
    runner_request = invocation.runner_request
    return RuntimeProbeExecutionAttempt(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        outcome=RuntimeProbeResultOutcome.OBSERVED,
        normalized_payload=protocol_result.normalized_payload,
        durable_artifact_reference=protocol_result.durable_artifact_reference,
    )


def execute_runtime_probe_local_python_subprocess_invocation(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
    *,
    completion_contract_revision: str,
) -> RuntimeProbeLocalPythonProcessCompletion:
    """Execute one local-Python invocation and return its raw process completion."""
    _validate_local_python_subprocess_invocation(invocation)
    validated_revision = _validate_contract_revision(
        completion_contract_revision,
        field_name="completion_contract_revision",
    )
    stdin_transport = (
        materialize_runtime_probe_local_python_worker_request_stdin_transport(
            invocation
        )
    )
    _validate_local_python_worker_request_stdin_transport(stdin_transport)
    completed_process: subprocess.CompletedProcess[str] = subprocess.run(
        invocation.argv,
        cwd=invocation.working_directory,
        env=_local_python_subprocess_child_environment(invocation),
        input=stdin_transport.stdin_text,
        timeout=invocation.timeout_seconds,
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    return materialize_runtime_probe_local_python_process_completion(
        invocation,
        returncode=completed_process.returncode,
        stdout_text=completed_process.stdout,
        stderr_text=completed_process.stderr,
        completion_contract_revision=validated_revision,
    )


def materialize_runtime_probe_local_python_subprocess_exception_attempt(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
    exception: Exception,
) -> RuntimeProbeExecutionAttempt:
    """Convert a local-Python subprocess exception into a non-proof attempt."""
    _validate_local_python_subprocess_invocation(invocation)
    _validate_runner_request(invocation.runner_request)
    if not isinstance(exception, Exception):
        raise ValueError("local Python subprocess exception must be an Exception")
    if isinstance(exception, subprocess.TimeoutExpired):
        return _runtime_probe_local_python_subprocess_timeout_attempt(
            invocation,
        )
    return _runtime_probe_local_python_subprocess_exception_attempt(
        invocation,
        exception,
    )


def materialize_runtime_probe_local_python_process_completion_attempt(
    completion: RuntimeProbeLocalPythonProcessCompletion,
    *,
    outcome: RuntimeProbeResultOutcome = RuntimeProbeResultOutcome.CRASHED,
) -> RuntimeProbeExecutionAttempt:
    """Convert a nonzero local-Python process completion into a non-proof attempt."""
    _validate_local_python_process_completion(completion)
    _validate_failure_normalization_outcome(outcome)
    if completion.returncode == 0:
        raise ValueError(
            "zero-returncode local Python process completions are deferred and "
            "cannot materialize failure attempts"
        )
    runner_request = completion.invocation.runner_request
    return RuntimeProbeExecutionAttempt(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        outcome=outcome,
        failure_summary=(
            "local Python subprocess exited with returncode "
            f"{completion.returncode}; recorded as {outcome.value}"
        ),
        failure_detail_fields=(
            RuntimeProbeReplayField(
                key="failure_source",
                value="local_python_process_completion",
            ),
            RuntimeProbeReplayField(
                key="normalized_outcome",
                value=outcome.value,
            ),
            RuntimeProbeReplayField(
                key="returncode",
                value=str(completion.returncode),
            ),
        ),
    )


def materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
    completion: RuntimeProbeLocalPythonProcessCompletion,
    exception: Exception,
    *,
    outcome: RuntimeProbeResultOutcome = RuntimeProbeResultOutcome.SETUP_FAILED,
) -> RuntimeProbeExecutionAttempt:
    """Convert malformed zero-exit local-Python stdout into a non-proof attempt."""
    _validate_local_python_process_completion(completion)
    _validate_local_python_subprocess_invocation(completion.invocation)
    _validate_runner_request(completion.invocation.runner_request)
    _validate_failure_normalization_outcome(outcome)
    if completion.returncode != 0:
        raise ValueError(
            "local Python stdout protocol failure materialization requires zero "
            "returncode"
        )
    if not isinstance(exception, Exception):
        raise ValueError("local Python stdout protocol failure must be an Exception")

    runner_request = completion.invocation.runner_request
    exception_type = type(exception)
    exception_type_label = f"{exception_type.__module__}.{exception_type.__name__}"
    return RuntimeProbeExecutionAttempt(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        outcome=outcome,
        failure_summary=(
            "local Python stdout protocol failed after zero returncode; recorded "
            f"as {outcome.value}"
        ),
        failure_detail_fields=(
            RuntimeProbeReplayField(
                key="failure_source",
                value="local_python_stdout_protocol_failure",
            ),
            RuntimeProbeReplayField(
                key="normalized_outcome",
                value=outcome.value,
            ),
            RuntimeProbeReplayField(
                key="returncode",
                value=str(completion.returncode),
            ),
            RuntimeProbeReplayField(
                key="exception_type",
                value=exception_type_label,
            ),
        ),
    )


def execute_runtime_probe_local_python_subprocess_invocation_attempt(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
    *,
    completion_contract_revision: str,
) -> RuntimeProbeExecutionAttempt:
    """Execute a local-Python subprocess invocation as one normalized attempt."""
    _validate_local_python_subprocess_invocation(invocation)
    validated_revision = _validate_contract_revision(
        completion_contract_revision,
        field_name="completion_contract_revision",
    )
    try:
        completion = execute_runtime_probe_local_python_subprocess_invocation(
            invocation,
            completion_contract_revision=validated_revision,
        )
    except Exception as exception:
        return materialize_runtime_probe_local_python_subprocess_exception_attempt(
            invocation,
            exception,
        )

    if completion.returncode != 0:
        return materialize_runtime_probe_local_python_process_completion_attempt(
            completion
        )

    try:
        protocol_result = materialize_runtime_probe_local_python_stdout_protocol_result(
            completion
        )
    except Exception as exception:
        return materialize_runtime_probe_local_python_stdout_protocol_failure_attempt(
            completion,
            exception,
        )
    return materialize_runtime_probe_local_python_stdout_protocol_attempt(
        protocol_result
    )


def assemble_runtime_probe_result_batch_from_execution_attempts(
    input_batch: RuntimeProbeExecutionInputBatch,
    attempts: Iterable[RuntimeProbeExecutionAttempt],
) -> RuntimeProbeResultBatch:
    """Convert a complete typed attempt set into an ordered result batch."""
    attempts_by_request_id = _index_execution_attempts_for_input_batch(
        input_batch,
        attempts,
    )
    results = tuple(
        _runtime_probe_result_from_attempt(attempts_by_request_id[request_id])
        for request_id in input_batch.request_ids
    )
    return RuntimeProbeResultBatch(plan_id=input_batch.plan_id, results=results)


def assemble_runtime_probe_result_batch_from_runner_request_attempts(
    runner_request_batch: RuntimeProbeRunnerRequestBatch,
    attempts: Iterable[RuntimeProbeExecutionAttempt],
) -> RuntimeProbeResultBatch:
    """Convert runner-request attempts into an ordered result batch."""
    attempts_by_request_id = _index_execution_attempts_for_runner_request_batch(
        runner_request_batch,
        attempts,
    )
    results = tuple(
        _runtime_probe_result_from_runner_request_attempt(
            runner_request,
            attempts_by_request_id[runner_request.request_id],
        )
        for runner_request in runner_request_batch.runner_requests
    )
    return RuntimeProbeResultBatch(
        plan_id=runner_request_batch.plan_id,
        results=results,
    )


def collect_runtime_probe_execution_attempts_from_runner_requests(
    runner_request_batch: RuntimeProbeRunnerRequestBatch,
    runner: RuntimeProbeRunnerCallable,
) -> RuntimeProbeRunnerAttemptCollection:
    """Invoke a typed runner once per runner request and assemble its results."""
    _validate_runner_request_batch(runner_request_batch)
    attempts = tuple(
        _runtime_probe_execution_attempt_from_runner(
            runner_request,
            runner,
        )
        for runner_request in runner_request_batch.runner_requests
    )
    result_batch = assemble_runtime_probe_result_batch_from_runner_request_attempts(
        runner_request_batch,
        attempts,
    )
    return RuntimeProbeRunnerAttemptCollection(
        runner_request_batch=runner_request_batch,
        attempts=attempts,
        result_batch=result_batch,
    )


def make_failure_normalizing_runtime_probe_runner(
    runner: RuntimeProbeRunnerCallable,
    *,
    outcome: RuntimeProbeResultOutcome = RuntimeProbeResultOutcome.CRASHED,
) -> RuntimeProbeRunnerCallable:
    """Return an opt-in adapter that normalizes runner-raised Exceptions."""
    return RuntimeProbeFailureNormalizingRunner(
        runner=runner,
        outcome=outcome,
    )


def make_dispatching_runtime_probe_runner(
    handler_entries: Iterable[RuntimeProbeRunnerHandlerEntry],
    *,
    missing_handler_outcome: RuntimeProbeResultOutcome = (
        RuntimeProbeResultOutcome.SETUP_FAILED
    ),
) -> RuntimeProbeRunnerCallable:
    """Return a runner that dispatches by runtime probe family and form labels."""
    return RuntimeProbeDispatchingRunner(
        handler_entries=tuple(handler_entries),
        missing_handler_outcome=missing_handler_outcome,
    )


def make_runtime_probe_local_python_subprocess_handler_entry(
    *,
    family_label: RuntimeProbeFamily,
    form_label: str,
    python_executable: str,
    module_name: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
    module_argv: Iterable[str] = (),
) -> RuntimeProbeRunnerHandlerEntry:
    """Return a dispatch entry backed by one local-Python subprocess worker."""
    config = RuntimeProbeLocalPythonSubprocessHandlerConfig(
        family_label=family_label,
        form_label=form_label,
        python_executable=python_executable,
        module_name=module_name,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
        module_argv=_local_python_subprocess_handler_module_argv(module_argv),
    )
    handler = _RuntimeProbeLocalPythonSubprocessHandler(config=config)
    return RuntimeProbeRunnerHandlerEntry(
        family_label=config.family_label,
        form_label=config.form_label,
        handler=handler,
    )


def make_runtime_probe_dynamic_import_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for the default dynamic-import worker."""
    handler_entries = tuple(
        make_runtime_probe_local_python_subprocess_handler_entry(
            family_label=RuntimeProbeFamily.DYNAMIC_IMPORT,
            form_label=form_label,
            python_executable=python_executable,
            module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
            invocation_contract_revision=invocation_contract_revision,
            completion_contract_revision=completion_contract_revision,
        )
        for form_label in _RUNTIME_PROBE_DYNAMIC_IMPORT_LOCAL_PYTHON_FORM_LABELS
    )
    return make_dispatching_runtime_probe_runner(handler_entries)


def make_runtime_probe_reflective_hasattr_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact reflective ``hasattr/2``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_RUNTIME_PROBE_REFLECTIVE_HASATTR_LOCAL_PYTHON_FORM_LABEL,
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_reflective_getattr_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact reflective ``getattr/2``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_RUNTIME_PROBE_REFLECTIVE_GETATTR_LOCAL_PYTHON_FORM_LABEL,
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_reflective_getattr_default_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact reflective ``getattr/3``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_RUNTIME_PROBE_REFLECTIVE_GETATTR_DEFAULT_LOCAL_PYTHON_FORM_LABEL,
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_reflective_vars_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact reflective ``vars/1``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_RUNTIME_PROBE_REFLECTIVE_VARS_LOCAL_PYTHON_FORM_LABEL,
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact reflective ``vars/0``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_RUNTIME_PROBE_REFLECTIVE_VARS_ZERO_LOCAL_PYTHON_FORM_LABEL,
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_reflective_dir_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact reflective ``dir/1``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_RUNTIME_PROBE_REFLECTIVE_DIR_LOCAL_PYTHON_FORM_LABEL,
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact reflective ``dir/0``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
        form_label=_RUNTIME_PROBE_REFLECTIVE_DIR_ZERO_LOCAL_PYTHON_FORM_LABEL,
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_runtime_mutation_globals_zero_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact runtime-mutation ``globals/0``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=(
            _RUNTIME_PROBE_RUNTIME_MUTATION_GLOBALS_ZERO_LOCAL_PYTHON_FORM_LABEL
        ),
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_runtime_mutation_locals_zero_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact runtime-mutation ``locals/0``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=(
            _RUNTIME_PROBE_RUNTIME_MUTATION_LOCALS_ZERO_LOCAL_PYTHON_FORM_LABEL
        ),
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_runtime_mutation_setattr_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact runtime-mutation ``setattr/3``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=_RUNTIME_PROBE_RUNTIME_MUTATION_SETATTR_LOCAL_PYTHON_FORM_LABEL,
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def make_runtime_probe_runtime_mutation_delattr_local_python_subprocess_runner(
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
) -> RuntimeProbeRunnerCallable:
    """Return the local-Python runner for exact runtime-mutation ``delattr/2``."""
    handler_entry = make_runtime_probe_local_python_subprocess_handler_entry(
        family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
        form_label=_RUNTIME_PROBE_RUNTIME_MUTATION_DELATTR_LOCAL_PYTHON_FORM_LABEL,
        python_executable=python_executable,
        module_name=_RUNTIME_PROBE_LOCAL_PYTHON_WORKER_MODULE_NAME,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return make_dispatching_runtime_probe_runner((handler_entry,))


def _materialize_runtime_probe_execution_input(
    *,
    plan_id: str,
    request_id: str,
    request: RuntimeProbeRequest,
    repository_snapshot_basis: RepositorySnapshotBasis,
    probe_contract_revision: str,
    runtime_assumptions: tuple[RuntimeProbeReplayField, ...],
) -> RuntimeProbeExecutionInput:
    """Build one typed work item without executing or observing a probe."""
    return RuntimeProbeExecutionInput(
        plan_id=plan_id,
        request_id=request_id,
        request=request,
        source_site_identity=runtime_acquisition._source_site_identity(
            request.source_site
        ),
        family_label=request.family_label,
        form_label=request.form_label,
        replay_target_seed=request.replay_target_seed,
        replay_selector_seed=request.replay_selector_seed,
        replay_artifact=RuntimeProbeReplayArtifact(
            probe_identifier=_runtime_probe_identifier(
                plan_id=plan_id,
                request_id=request_id,
                request=request,
            ),
            probe_contract_revision=probe_contract_revision,
            repository_snapshot_basis=repository_snapshot_basis,
            replay_target=request.replay_target_seed,
            replay_selector=request.replay_selector_seed,
            replay_inputs=_replay_inputs_for_request(
                plan_id=plan_id,
                request_id=request_id,
                request=request,
            ),
            runtime_assumptions=runtime_assumptions,
        ),
    )


def _runtime_probe_execution_attempt_from_runner(
    runner_request: RuntimeProbeRunnerRequest,
    runner: RuntimeProbeRunnerCallable,
) -> RuntimeProbeExecutionAttempt:
    """Return one typed execution attempt from the supplied runner callable."""
    attempt = runner(runner_request)
    if not isinstance(attempt, RuntimeProbeExecutionAttempt):
        raise ValueError(
            "runtime probe runner callable must return typed runtime probe "
            "execution attempts"
        )
    return attempt


def _runtime_probe_failure_attempt_from_runner_exception(
    runner_request: RuntimeProbeRunnerRequest,
    *,
    outcome: RuntimeProbeResultOutcome,
    exception: Exception,
) -> RuntimeProbeExecutionAttempt:
    """Normalize one runner exception without stack traces or process-local data."""
    _validate_failure_normalization_outcome(outcome)
    exception_type = type(exception)
    exception_type_name = exception_type.__name__
    exception_type_label = f"{exception_type.__module__}.{exception_type_name}"
    return RuntimeProbeExecutionAttempt(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        outcome=outcome,
        failure_summary=(
            "runtime probe runner raised "
            f"{exception_type_name}; normalized as {outcome.value}"
        ),
        failure_detail_fields=(
            RuntimeProbeReplayField(
                key="failure_normalization_source",
                value="runner_exception",
            ),
            RuntimeProbeReplayField(
                key="normalized_outcome",
                value=outcome.value,
            ),
            RuntimeProbeReplayField(
                key="exception_type",
                value=exception_type_label,
            ),
        ),
    )


def _runtime_probe_local_python_subprocess_timeout_attempt(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
) -> RuntimeProbeExecutionAttempt:
    """Normalize a local-Python timeout without subprocess-local data."""
    runner_request = invocation.runner_request
    return RuntimeProbeExecutionAttempt(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        outcome=RuntimeProbeResultOutcome.TIMED_OUT,
        failure_summary="local Python subprocess timed out; recorded as timed_out",
        failure_detail_fields=(
            RuntimeProbeReplayField(
                key="failure_source",
                value="local_python_subprocess_timeout",
            ),
            RuntimeProbeReplayField(
                key="normalized_outcome",
                value=RuntimeProbeResultOutcome.TIMED_OUT.value,
            ),
            RuntimeProbeReplayField(
                key="exception_type",
                value="subprocess.TimeoutExpired",
            ),
            RuntimeProbeReplayField(
                key="timeout_seconds",
                value=str(invocation.timeout_seconds),
            ),
        ),
    )


def _runtime_probe_local_python_subprocess_exception_attempt(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
    exception: Exception,
) -> RuntimeProbeExecutionAttempt:
    """Normalize a local-Python subprocess exception without raw exception text."""
    runner_request = invocation.runner_request
    exception_type = type(exception)
    exception_type_name = exception_type.__name__
    exception_type_label = f"{exception_type.__module__}.{exception_type_name}"
    return RuntimeProbeExecutionAttempt(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        outcome=RuntimeProbeResultOutcome.CRASHED,
        failure_summary=(
            f"local Python subprocess raised {exception_type_name}; recorded as crashed"
        ),
        failure_detail_fields=(
            RuntimeProbeReplayField(
                key="failure_source",
                value="local_python_subprocess_exception",
            ),
            RuntimeProbeReplayField(
                key="normalized_outcome",
                value=RuntimeProbeResultOutcome.CRASHED.value,
            ),
            RuntimeProbeReplayField(
                key="exception_type",
                value=exception_type_label,
            ),
        ),
    )


def _runtime_probe_missing_handler_attempt(
    runner_request: RuntimeProbeRunnerRequest,
    *,
    outcome: RuntimeProbeResultOutcome,
) -> RuntimeProbeExecutionAttempt:
    """Return a deterministic non-proof attempt for an unimplemented handler key."""
    _validate_runner_request(runner_request)
    _validate_failure_normalization_outcome(outcome)
    handler_key = _runtime_probe_runner_request_handler_key(runner_request)
    family_label, form_label = handler_key
    return RuntimeProbeExecutionAttempt(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        outcome=outcome,
        failure_summary=(
            "runtime probe runner has no handler for "
            f"{family_label.value} form {form_label}; recorded as {outcome.value}"
        ),
        failure_detail_fields=(
            RuntimeProbeReplayField(
                key="failure_source",
                value="missing_runtime_probe_handler",
            ),
            RuntimeProbeReplayField(
                key="family_label",
                value=family_label.value,
            ),
            RuntimeProbeReplayField(
                key="form_label",
                value=form_label,
            ),
            RuntimeProbeReplayField(
                key="missing_handler_outcome",
                value=outcome.value,
            ),
        ),
    )


def _index_execution_attempts_for_runner_request_batch(
    runner_request_batch: RuntimeProbeRunnerRequestBatch,
    attempts: Iterable[RuntimeProbeExecutionAttempt],
) -> dict[str, RuntimeProbeExecutionAttempt]:
    """Return attempts keyed by request ID after runner-request validation."""
    _validate_runner_request_batch(runner_request_batch)
    runner_requests_by_request_id = {
        runner_request.request_id: runner_request
        for runner_request in runner_request_batch.runner_requests
    }
    attempts_by_request_id: dict[str, RuntimeProbeExecutionAttempt] = {}

    for attempt in attempts:
        _validate_execution_attempt(attempt)
        if attempt.request_id in attempts_by_request_id:
            raise ValueError("duplicate runtime probe execution attempt request_id")
        runner_request = runner_requests_by_request_id.get(attempt.request_id)
        if runner_request is None:
            raise ValueError(
                "runtime probe execution attempt request_id is not present in "
                "runner request batch"
            )
        if attempt.plan_id != runner_request_batch.plan_id:
            raise ValueError(
                "runtime probe execution attempt plan_id must match runner request "
                "batch"
            )
        if attempt.request is not runner_request.request:
            raise ValueError(
                "runtime probe execution attempt request must be the runner request "
                "request"
            )
        if attempt.execution_input is not runner_request.execution_input:
            raise ValueError(
                "runtime probe execution attempt input must be the runner request "
                "execution input"
            )
        replay_artifact = attempt.execution_input.replay_artifact
        if replay_artifact is not runner_request.replay_artifact:
            raise ValueError(
                "runtime probe execution attempt replay_artifact must be the runner "
                "request replay_artifact"
            )
        attempts_by_request_id[attempt.request_id] = attempt

    missing_request_ids = tuple(
        request_id
        for request_id in runner_request_batch.request_ids
        if request_id not in attempts_by_request_id
    )
    if missing_request_ids:
        raise ValueError(
            "missing runtime probe execution attempt for runner request batch "
            "request_id"
        )
    return attempts_by_request_id


def _index_execution_attempts_for_input_batch(
    input_batch: RuntimeProbeExecutionInputBatch,
    attempts: Iterable[RuntimeProbeExecutionAttempt],
) -> dict[str, RuntimeProbeExecutionAttempt]:
    """Return attempts keyed by request ID after validating batch completeness."""
    inputs_by_request_id = {
        input_item.request_id: input_item for input_item in input_batch.inputs
    }
    attempts_by_request_id: dict[str, RuntimeProbeExecutionAttempt] = {}

    for attempt in attempts:
        if attempt.request_id in attempts_by_request_id:
            raise ValueError("duplicate runtime probe execution attempt request_id")
        input_item = inputs_by_request_id.get(attempt.request_id)
        if input_item is None:
            raise ValueError(
                "runtime probe execution attempt request_id is not present in "
                "input batch"
            )
        if attempt.plan_id != input_batch.plan_id:
            raise ValueError(
                "runtime probe execution attempt plan_id must match input batch"
            )
        if attempt.execution_input is not input_item:
            raise ValueError(
                "runtime probe execution attempt input must be the planned batch input"
            )
        if attempt.request is not input_item.request:
            raise ValueError(
                "runtime probe execution attempt request must be the planned batch "
                "request"
            )
        attempts_by_request_id[attempt.request_id] = attempt

    missing_request_ids = tuple(
        request_id
        for request_id in input_batch.request_ids
        if request_id not in attempts_by_request_id
    )
    if missing_request_ids:
        raise ValueError(
            "missing runtime probe execution attempt for input batch request_id"
        )
    return attempts_by_request_id


def _validate_execution_input_batch(
    input_batch: RuntimeProbeExecutionInputBatch,
) -> None:
    """Re-check an execution-input batch before handing it to a runner."""
    RuntimeProbeExecutionInputBatch(
        plan_id=input_batch.plan_id,
        request_ids=input_batch.request_ids,
        inputs=input_batch.inputs,
    )
    for input_item in input_batch.inputs:
        _validate_execution_input(input_item)


def _validate_execution_input(input_item: RuntimeProbeExecutionInput) -> None:
    """Re-check one execution input and its replay fields for tampering."""
    RuntimeProbeExecutionInput(
        plan_id=input_item.plan_id,
        request_id=input_item.request_id,
        request=input_item.request,
        source_site_identity=input_item.source_site_identity,
        family_label=input_item.family_label,
        form_label=input_item.form_label,
        replay_target_seed=input_item.replay_target_seed,
        replay_selector_seed=input_item.replay_selector_seed,
        replay_artifact=input_item.replay_artifact,
    )
    _validate_replay_fields(
        input_item.replay_artifact.replay_inputs,
        field_name="replay_inputs",
    )
    _validate_replay_fields(
        input_item.replay_artifact.runtime_assumptions,
        field_name="runtime_assumptions",
    )


def _validate_runner_request_batch(
    runner_request_batch: RuntimeProbeRunnerRequestBatch,
) -> None:
    """Re-check a runner-request batch before accepting runner attempts."""
    RuntimeProbeRunnerRequestBatch(
        plan_id=runner_request_batch.plan_id,
        request_ids=runner_request_batch.request_ids,
        runner_requests=runner_request_batch.runner_requests,
        runner_contract_revision=runner_request_batch.runner_contract_revision,
        timeout_seconds=runner_request_batch.timeout_seconds,
        runner_environment=runner_request_batch.runner_environment,
        runner_assumptions=runner_request_batch.runner_assumptions,
    )


def _validate_runner_attempt_collection_result_batch(
    runner_request_batch: RuntimeProbeRunnerRequestBatch,
    result_batch: RuntimeProbeResultBatch,
) -> None:
    """Re-check collected result batch identity against runner requests."""
    if not isinstance(result_batch, RuntimeProbeResultBatch):
        raise ValueError(
            "runtime probe runner attempt collection result_batch must be a result "
            "batch"
        )
    RuntimeProbeResultBatch(
        plan_id=result_batch.plan_id,
        results=result_batch.results,
    )
    if result_batch.plan_id != runner_request_batch.plan_id:
        raise ValueError(
            "runtime probe runner attempt collection result_batch plan_id must match "
            "runner request batch"
        )
    result_request_ids = tuple(result.request_id for result in result_batch.results)
    if result_request_ids != runner_request_batch.request_ids:
        raise ValueError(
            "runtime probe runner attempt collection result_batch must be in runner "
            "request order"
        )
    for result, runner_request in zip(
        result_batch.results,
        runner_request_batch.runner_requests,
        strict=True,
    ):
        if result.request is not runner_request.request:
            raise ValueError(
                "runtime probe runner attempt collection result request must be "
                "runner request request"
            )
        if result.replay_artifact is not runner_request.replay_artifact:
            raise ValueError(
                "runtime probe runner attempt collection result replay_artifact must "
                "be runner request replay_artifact"
            )


def _request_plan_for_diagnostic_preparation(
    diagnostic: SemanticDiagnosticResult,
) -> RuntimeProbeRequestPlan:
    """Return the diagnostic's attached request plan after revalidation."""
    request_plan = diagnostic.planned_runtime_probe_request_plan
    if request_plan is None:
        raise ValueError(
            "planned_runtime_probe_request_plan is required for runtime probe "
            "runner request preparation"
        )
    _validate_diagnostic_request_plan(diagnostic, request_plan)
    return request_plan


def _validate_diagnostic_request_plan(
    diagnostic: SemanticDiagnosticResult,
    request_plan: RuntimeProbeRequestPlan,
) -> None:
    """Reject diagnostics whose attached runtime request plan has drifted."""
    if request_plan is not diagnostic.planned_runtime_probe_request_plan:
        raise ValueError(
            "request_plan must be diagnostic.planned_runtime_probe_request_plan"
        )
    _validate_request_plan(request_plan)
    if request_plan.requests != diagnostic.planned_runtime_probe_requests:
        raise ValueError(
            "planned_runtime_probe_request_plan requests must match "
            "planned_runtime_probe_requests"
        )
    for plan_request, diagnostic_request in zip(
        request_plan.requests,
        diagnostic.planned_runtime_probe_requests,
        strict=True,
    ):
        if plan_request is not diagnostic_request:
            raise ValueError(
                "planned_runtime_probe_request_plan requests must preserve "
                "diagnostic request identities"
            )


def _validate_runner_request(runner_request: RuntimeProbeRunnerRequest) -> None:
    """Re-check one runner handoff request for tampering."""
    RuntimeProbeRunnerRequest(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        replay_artifact=runner_request.replay_artifact,
        runner_contract_revision=runner_request.runner_contract_revision,
        timeout_seconds=runner_request.timeout_seconds,
        runner_environment=runner_request.runner_environment,
        runner_assumptions=runner_request.runner_assumptions,
    )


def _validate_runtime_probe_runner_handler_entry(
    handler_entry: RuntimeProbeRunnerHandlerEntry,
) -> None:
    """Reject handler entries without a concrete family/form callable key."""
    if not isinstance(handler_entry.family_label, RuntimeProbeFamily):
        raise ValueError(
            "runtime probe runner handler family_label must be a runtime probe family"
        )
    if not isinstance(handler_entry.form_label, str) or (
        not handler_entry.form_label.strip()
    ):
        raise ValueError("runtime probe runner handler form_label must be non-empty")
    if not callable(handler_entry.handler):
        raise ValueError("runtime probe runner handler must be callable")


def _validate_runtime_probe_local_python_subprocess_handler_config(
    config: RuntimeProbeLocalPythonSubprocessHandlerConfig,
) -> None:
    """Reject local-Python handler metadata that cannot produce safe invocations."""
    if not isinstance(config, RuntimeProbeLocalPythonSubprocessHandlerConfig):
        raise ValueError("runtime probe local Python handler config must be typed")
    if not isinstance(config.family_label, RuntimeProbeFamily):
        raise ValueError(
            "runtime probe local Python handler family_label must be a runtime "
            "probe family"
        )
    if not isinstance(config.form_label, str) or not config.form_label.strip():
        raise ValueError(
            "runtime probe local Python handler form_label must be non-empty"
        )
    if config.form_label != config.form_label.strip() or _contains_control_character(
        config.form_label
    ):
        raise ValueError("runtime probe local Python handler form_label is malformed")
    _validate_absolute_path_metadata(
        config.python_executable,
        field_name="runtime probe local Python handler python_executable",
    )
    _validate_local_python_module_name(config.module_name)
    _validate_contract_revision(
        config.invocation_contract_revision,
        field_name="invocation_contract_revision",
    )
    _validate_contract_revision(
        config.completion_contract_revision,
        field_name="completion_contract_revision",
    )
    if not isinstance(config.module_argv, tuple):
        raise ValueError(
            "runtime probe local Python handler module_argv must be a tuple"
        )
    for token in config.module_argv:
        _validate_local_python_argv_token(
            token,
            field_name="handler module_argv",
        )


def _validate_local_python_subprocess_handler_request_key(
    runner_request: RuntimeProbeRunnerRequest,
    config: RuntimeProbeLocalPythonSubprocessHandlerConfig,
) -> None:
    """Reject runner requests not matching the configured handler key."""
    if _runtime_probe_runner_request_handler_key(runner_request) != (
        config.family_label,
        config.form_label,
    ):
        raise ValueError(
            "runtime probe local Python handler request family/form must match "
            "configured handler"
        )


def _local_python_subprocess_handler_module_argv(
    module_argv: Iterable[str],
) -> tuple[str, ...]:
    """Return handler argv metadata as a tuple without treating text as a sequence."""
    if isinstance(module_argv, str):
        raise ValueError(
            "runtime probe local Python handler module_argv must be tokens"
        )
    try:
        return tuple(module_argv)
    except TypeError as error:
        raise ValueError(
            "runtime probe local Python handler module_argv must be iterable"
        ) from error


def _index_runtime_probe_runner_handler_entries(
    handler_entries: tuple[RuntimeProbeRunnerHandlerEntry, ...],
) -> dict[RuntimeProbeRunnerHandlerKey, RuntimeProbeRunnerCallable]:
    """Return dispatch handlers keyed by family/form after duplicate checks."""
    if not isinstance(handler_entries, tuple):
        raise ValueError("runtime probe runner handler entries must be a tuple")
    handlers_by_key: dict[RuntimeProbeRunnerHandlerKey, RuntimeProbeRunnerCallable] = {}
    for handler_entry in handler_entries:
        _validate_runtime_probe_runner_handler_entry(handler_entry)
        handler_key = _runtime_probe_runner_handler_entry_key(handler_entry)
        if handler_key in handlers_by_key:
            raise ValueError("duplicate runtime probe runner handler key")
        handlers_by_key[handler_key] = handler_entry.handler
    return handlers_by_key


def _runtime_probe_runner_handler_entry_key(
    handler_entry: RuntimeProbeRunnerHandlerEntry,
) -> RuntimeProbeRunnerHandlerKey:
    """Return the dispatch-table key carried by one handler entry."""
    return (handler_entry.family_label, handler_entry.form_label)


def _runtime_probe_runner_request_handler_key(
    runner_request: RuntimeProbeRunnerRequest,
) -> RuntimeProbeRunnerHandlerKey:
    """Return the dispatch key carried by one runner request."""
    return (
        runner_request.request.family_label,
        runner_request.request.form_label,
    )


def _validate_failure_normalization_outcome(
    outcome: RuntimeProbeResultOutcome,
) -> None:
    """Reject failure normalization outcomes that could produce runtime proof."""
    if outcome not in _NON_PROOF_ATTEMPT_OUTCOMES:
        raise ValueError(
            "runtime probe failure normalization outcome must be a non-proof outcome"
        )


def _validate_execution_attempt(attempt: RuntimeProbeExecutionAttempt) -> None:
    """Re-check one execution attempt for tampered normalized metadata."""
    if not isinstance(attempt, RuntimeProbeExecutionAttempt):
        raise ValueError("runtime probe execution attempts must be typed attempts")
    RuntimeProbeExecutionAttempt(
        plan_id=attempt.plan_id,
        request_id=attempt.request_id,
        request=attempt.request,
        execution_input=attempt.execution_input,
        outcome=attempt.outcome,
        normalized_payload=attempt.normalized_payload,
        durable_artifact_reference=attempt.durable_artifact_reference,
        failure_summary=attempt.failure_summary,
        failure_detail_fields=attempt.failure_detail_fields,
    )


def _validate_local_python_worker_request_payload(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> None:
    """Re-check one local-Python worker request payload for tampering."""
    if not isinstance(payload, RuntimeProbeLocalPythonWorkerRequestPayload):
        raise ValueError("local Python worker request payload must be typed")
    _validate_local_python_worker_request_payload_parts(
        contract_version=payload.contract_version,
        plan_id=payload.plan_id,
        request_id=payload.request_id,
        family_label=payload.family_label,
        form_label=payload.form_label,
        replay_target_seed=payload.replay_target_seed,
        replay_selector_seed=payload.replay_selector_seed,
        request_replay_payload_fields=payload.request_replay_payload_fields,
        runtime_assumptions=payload.runtime_assumptions,
        runner_contract_revision=payload.runner_contract_revision,
        runner_environment=payload.runner_environment,
        runner_assumptions=payload.runner_assumptions,
        invocation_contract_revision=payload.invocation_contract_revision,
        invocation_identity=payload.invocation_identity,
        argv=payload.argv,
        working_directory=payload.working_directory,
        python_path_entries=payload.python_path_entries,
        timeout_seconds=payload.timeout_seconds,
    )


def _validate_local_python_worker_request_stdin_transport(
    transport: RuntimeProbeLocalPythonWorkerRequestStdinTransport,
) -> None:
    """Re-check one local-Python worker stdin transport for tampering."""
    if not isinstance(transport, RuntimeProbeLocalPythonWorkerRequestStdinTransport):
        raise ValueError("local Python worker request stdin transport must be typed")
    _validate_local_python_subprocess_invocation(transport.invocation)
    _validate_local_python_worker_request_payload(transport.payload)
    _validate_contract_revision(
        transport.stdin_transport_contract_revision,
        field_name=("local Python worker request stdin transport contract revision"),
    )
    if (
        transport.stdin_transport_contract_revision
        != _RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_STDIN_TRANSPORT_CONTRACT_REVISION
    ):
        raise ValueError(
            "local Python worker request stdin transport contract revision is "
            "unsupported"
        )
    if not isinstance(transport.stdin_text, str) or not transport.stdin_text.strip():
        raise ValueError(
            "local Python worker request stdin transport stdin_text must be "
            "non-empty text"
        )

    expected_payload = materialize_runtime_probe_local_python_worker_request_payload(
        transport.invocation
    )
    if transport.payload != expected_payload:
        raise ValueError(
            "local Python worker request stdin transport payload must match invocation"
        )

    expected_stdin_text = serialize_runtime_probe_local_python_worker_request_payload(
        transport.payload
    )
    parsed_payload = parse_runtime_probe_local_python_worker_request_payload(
        transport.stdin_text
    )
    if transport.stdin_text != expected_stdin_text:
        raise ValueError(
            "local Python worker request stdin transport stdin_text must match "
            "deterministic serialized payload"
        )
    if parsed_payload != transport.payload:
        raise ValueError(
            "local Python worker request stdin transport stdin_text payload must "
            "match payload"
        )

    _validate_local_python_worker_request_stdin_transport_identity(transport)


def _validate_local_python_worker_request_stdin_transport_identity(
    transport: RuntimeProbeLocalPythonWorkerRequestStdinTransport,
) -> None:
    """Reject stdin transport metadata that drifted from invocation or payload."""
    invocation = transport.invocation
    payload = transport.payload
    runner_request = invocation.runner_request
    expected_invocation_identity = _runtime_probe_local_python_invocation_identity(
        invocation
    )
    if transport.invocation_identity != expected_invocation_identity:
        raise ValueError(
            "local Python worker request stdin transport invocation_identity must "
            "match invocation"
        )
    if payload.invocation_identity != transport.invocation_identity:
        raise ValueError(
            "local Python worker request stdin transport payload invocation_identity "
            "must match transport"
        )
    if transport.argv != invocation.argv or transport.argv != payload.argv:
        raise ValueError(
            "local Python worker request stdin transport argv must match invocation "
            "and payload"
        )
    if (
        transport.working_directory != invocation.working_directory
        or transport.working_directory != payload.working_directory
    ):
        raise ValueError(
            "local Python worker request stdin transport working_directory must "
            "match invocation and payload"
        )
    if (
        transport.python_path_entries != invocation.python_path_entries
        or transport.python_path_entries != payload.python_path_entries
    ):
        raise ValueError(
            "local Python worker request stdin transport python_path_entries must "
            "match invocation and payload"
        )
    if (
        transport.timeout_seconds != invocation.timeout_seconds
        or transport.timeout_seconds != payload.timeout_seconds
    ):
        raise ValueError(
            "local Python worker request stdin transport timeout_seconds must match "
            "invocation and payload"
        )
    if (
        transport.plan_id != runner_request.plan_id
        or transport.plan_id != payload.plan_id
    ):
        raise ValueError(
            "local Python worker request stdin transport plan_id must match "
            "invocation and payload"
        )
    if (
        transport.request_id != runner_request.request_id
        or transport.request_id != payload.request_id
    ):
        raise ValueError(
            "local Python worker request stdin transport request_id must match "
            "invocation and payload"
        )
    if (
        transport.family_label is not runner_request.request.family_label
        or transport.family_label is not payload.family_label
    ):
        raise ValueError(
            "local Python worker request stdin transport family_label must match "
            "invocation and payload"
        )
    if (
        transport.form_label != runner_request.request.form_label
        or transport.form_label != payload.form_label
    ):
        raise ValueError(
            "local Python worker request stdin transport form_label must match "
            "invocation and payload"
        )
    if (
        transport.replay_target_seed != runner_request.request.replay_target_seed
        or transport.replay_target_seed != payload.replay_target_seed
    ):
        raise ValueError(
            "local Python worker request stdin transport replay_target_seed must "
            "match invocation and payload"
        )
    if (
        transport.replay_selector_seed != runner_request.request.replay_selector_seed
        or transport.replay_selector_seed != payload.replay_selector_seed
    ):
        raise ValueError(
            "local Python worker request stdin transport replay_selector_seed must "
            "match invocation and payload"
        )
    if (
        transport.request_replay_payload_fields
        != invocation.request_replay_payload_fields
        or transport.request_replay_payload_fields
        != payload.request_replay_payload_fields
    ):
        raise ValueError(
            "local Python worker request stdin transport request_replay_payload_fields "
            "must match invocation and payload"
        )


def _validate_local_python_worker_request_payload_parts(
    *,
    contract_version: str,
    plan_id: str,
    request_id: str,
    family_label: RuntimeProbeFamily,
    form_label: str,
    replay_target_seed: str,
    replay_selector_seed: str,
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...],
    runtime_assumptions: tuple[RuntimeProbeReplayField, ...],
    runner_contract_revision: str,
    runner_environment: tuple[RuntimeProbeReplayField, ...],
    runner_assumptions: tuple[RuntimeProbeReplayField, ...],
    invocation_contract_revision: str,
    invocation_identity: str,
    argv: tuple[str, ...],
    working_directory: str,
    python_path_entries: tuple[str, ...],
    timeout_seconds: int,
) -> None:
    """Reject local-Python worker payload fields that cannot round-trip safely."""
    _validate_contract_revision(
        contract_version,
        field_name="local Python worker request payload contract_version",
    )
    if (
        contract_version
        != _RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_PAYLOAD_CONTRACT_VERSION
    ):
        raise ValueError(
            "local Python worker request payload contract_version is unsupported"
        )
    _validate_local_python_worker_payload_metadata_text(
        plan_id,
        field_name="plan_id",
    )
    _validate_local_python_worker_payload_metadata_text(
        request_id,
        field_name="request_id",
    )
    if not isinstance(family_label, RuntimeProbeFamily):
        raise ValueError(
            "local Python worker request payload family_label must be a runtime "
            "probe family"
        )
    _validate_local_python_worker_payload_metadata_text(
        form_label,
        field_name="form_label",
    )
    _validate_local_python_worker_payload_metadata_text(
        replay_target_seed,
        field_name="replay_target_seed",
    )
    _validate_local_python_worker_payload_metadata_text(
        replay_selector_seed,
        field_name="replay_selector_seed",
    )
    if not request_replay_payload_fields:
        raise ValueError(
            "local Python worker request payload requires request replay fields"
        )
    if not runtime_assumptions:
        raise ValueError(
            "local Python worker request payload requires runtime_assumptions"
        )
    _validate_replay_fields(
        request_replay_payload_fields,
        field_name="request_replay_payload_fields",
    )
    _validate_replay_fields(
        runtime_assumptions,
        field_name="runtime_assumptions",
    )
    _validate_runner_handoff_metadata(
        runner_contract_revision=runner_contract_revision,
        timeout_seconds=timeout_seconds,
        runner_environment=runner_environment,
        runner_assumptions=runner_assumptions,
    )
    (
        _environment_repository_root,
        environment_working_directory,
        environment_python_path_entries,
    ) = _local_python_environment_parts_from_fields(runner_environment)
    _validate_contract_revision(
        invocation_contract_revision,
        field_name="local Python worker request payload invocation_contract_revision",
    )
    _validate_local_python_worker_payload_metadata_text(
        invocation_identity,
        field_name="invocation_identity",
    )
    _validate_local_python_worker_payload_invocation_argv(argv)
    _validate_absolute_path_metadata(
        working_directory,
        field_name="local Python worker request payload working_directory",
    )
    if working_directory != environment_working_directory:
        raise ValueError(
            "local Python worker request payload working_directory must match "
            "runner environment"
        )
    _validate_local_python_worker_payload_python_path_entries(
        python_path_entries,
    )
    if python_path_entries != environment_python_path_entries:
        raise ValueError(
            "local Python worker request payload python_path_entries must match "
            "runner environment"
        )
    _validate_worker_payload_replay_field_match(
        request_replay_payload_fields,
        field_key="plan_id",
        expected_value=plan_id,
    )
    _validate_worker_payload_replay_field_match(
        request_replay_payload_fields,
        field_key="request_id",
        expected_value=request_id,
    )
    _validate_worker_payload_replay_field_match(
        request_replay_payload_fields,
        field_key="family_label",
        expected_value=family_label.value,
    )
    _validate_worker_payload_replay_field_match(
        request_replay_payload_fields,
        field_key="form_label",
        expected_value=form_label,
    )
    _validate_worker_payload_replay_field_match(
        request_replay_payload_fields,
        field_key="replay_target_seed",
        expected_value=replay_target_seed,
    )
    _validate_worker_payload_replay_field_match(
        request_replay_payload_fields,
        field_key="replay_selector_seed",
        expected_value=replay_selector_seed,
    )
    _validate_worker_payload_required_replay_fields(request_replay_payload_fields)
    expected_invocation_identity = (
        _runtime_probe_local_python_invocation_identity_from_parts(
            plan_id=plan_id,
            request_id=request_id,
            invocation_contract_revision=invocation_contract_revision,
            argv=argv,
            working_directory=working_directory,
            python_path_entries=python_path_entries,
            timeout_seconds=timeout_seconds,
            request_replay_payload_fields=request_replay_payload_fields,
        )
    )
    if invocation_identity != expected_invocation_identity:
        raise ValueError(
            "local Python worker request payload invocation_identity must match "
            "invocation"
        )


def _validate_worker_payload_replay_field_match(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    field_key: str,
    expected_value: str,
) -> None:
    """Require one request replay field to match its top-level payload twin."""
    matching_fields = tuple(field for field in fields if field.key == field_key)
    if len(matching_fields) != 1:
        raise ValueError(
            "local Python worker request payload request_replay_payload_fields "
            f"must contain exactly one {field_key}"
        )
    if matching_fields[0].value != expected_value:
        raise ValueError(
            "local Python worker request payload "
            f"{field_key} must match request replay payload fields"
        )


def _validate_worker_payload_required_replay_fields(
    fields: tuple[RuntimeProbeReplayField, ...],
) -> None:
    """Require worker payload replay fields to carry every request identity key."""
    field_counts = {
        required_key: sum(1 for field in fields if field.key == required_key)
        for required_key in _REQUIRED_WORKER_REQUEST_REPLAY_FIELD_KEYS
    }
    for required_key, field_count in field_counts.items():
        if field_count != 1:
            raise ValueError(
                "local Python worker request payload request_replay_payload_fields "
                f"must contain exactly one {required_key}"
            )


def _validate_local_python_worker_payload_metadata_text(
    value: str,
    *,
    field_name: str,
) -> str:
    """Reject blank or malformed worker payload metadata text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"local Python worker request payload {field_name} must be non-empty"
        )
    if value != value.strip() or _contains_control_character(value):
        raise ValueError(
            f"local Python worker request payload {field_name} is malformed"
        )
    return value


def _validate_local_python_subprocess_invocation(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
) -> None:
    """Re-check one local-Python subprocess invocation for tampering."""
    if not isinstance(invocation, RuntimeProbeLocalPythonSubprocessInvocation):
        raise ValueError("local Python subprocess invocation must be typed")
    RuntimeProbeLocalPythonSubprocessInvocation(
        runner_request=invocation.runner_request,
        environment_context=invocation.environment_context,
        python_executable=invocation.python_executable,
        argv=invocation.argv,
        working_directory=invocation.working_directory,
        python_path_entries=invocation.python_path_entries,
        timeout_seconds=invocation.timeout_seconds,
        invocation_contract_revision=invocation.invocation_contract_revision,
        request_replay_payload_fields=invocation.request_replay_payload_fields,
    )


def _validate_local_python_process_completion(
    completion: RuntimeProbeLocalPythonProcessCompletion,
) -> None:
    """Re-check one raw local-Python process completion for tampering."""
    if not isinstance(completion, RuntimeProbeLocalPythonProcessCompletion):
        raise ValueError("local Python process completion must be typed")
    RuntimeProbeLocalPythonProcessCompletion(
        invocation=completion.invocation,
        invocation_identity=completion.invocation_identity,
        argv=completion.argv,
        working_directory=completion.working_directory,
        python_path_entries=completion.python_path_entries,
        timeout_seconds=completion.timeout_seconds,
        returncode=completion.returncode,
        stdout_text=completion.stdout_text,
        stderr_text=completion.stderr_text,
        completion_contract_revision=completion.completion_contract_revision,
        request_replay_payload_fields=completion.request_replay_payload_fields,
    )
    _validate_local_python_subprocess_invocation(completion.invocation)
    _validate_runner_request(completion.invocation.runner_request)


def _validate_local_python_stdout_protocol_result(
    protocol_result: RuntimeProbeLocalPythonStdoutProtocolResult,
) -> None:
    """Re-check one local-Python stdout protocol result for tampering."""
    if not isinstance(protocol_result, RuntimeProbeLocalPythonStdoutProtocolResult):
        raise ValueError("local Python stdout protocol result must be typed")
    RuntimeProbeLocalPythonStdoutProtocolResult(
        completion=protocol_result.completion,
        stdout_protocol_revision=protocol_result.stdout_protocol_revision,
        normalized_payload=protocol_result.normalized_payload,
        durable_artifact_reference=protocol_result.durable_artifact_reference,
    )
    _validate_local_python_process_completion(protocol_result.completion)
    _validate_local_python_subprocess_invocation(protocol_result.completion.invocation)
    _validate_runner_request(
        protocol_result.completion.invocation.runner_request,
    )


def _runtime_probe_local_python_worker_request_payload_json_object(
    payload: RuntimeProbeLocalPythonWorkerRequestPayload,
) -> dict[str, object]:
    """Return the stable JSON object shape for a local-Python worker payload."""
    _validate_local_python_worker_request_payload(payload)
    return {
        "contract_version": payload.contract_version,
        "plan_id": payload.plan_id,
        "request_id": payload.request_id,
        "family_label": payload.family_label.value,
        "form_label": payload.form_label,
        "replay_target_seed": payload.replay_target_seed,
        "replay_selector_seed": payload.replay_selector_seed,
        "request_replay_payload_fields": _replay_fields_json_array(
            payload.request_replay_payload_fields,
            field_name="request_replay_payload_fields",
        ),
        "runtime_assumptions": _replay_fields_json_array(
            payload.runtime_assumptions,
            field_name="runtime_assumptions",
        ),
        "runner_contract_revision": payload.runner_contract_revision,
        "runner_environment": _replay_fields_json_array(
            payload.runner_environment,
            field_name="runner_environment",
        ),
        "runner_assumptions": _replay_fields_json_array(
            payload.runner_assumptions,
            field_name="runner_assumptions",
        ),
        "invocation_contract_revision": payload.invocation_contract_revision,
        "invocation_identity": payload.invocation_identity,
        "argv": list(payload.argv),
        "working_directory": payload.working_directory,
        "python_path_entries": list(payload.python_path_entries),
        "timeout_seconds": payload.timeout_seconds,
    }


def _replay_fields_json_array(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    field_name: str,
) -> list[dict[str, str]]:
    """Return replay fields as ordered strict JSON key/value objects."""
    _validate_replay_fields(fields, field_name=field_name)
    return [{"key": field.key, "value": field.value} for field in fields]


def _parse_runtime_probe_local_python_worker_request_payload_object(
    payload_json: str,
) -> dict[object, object]:
    """Parse the top-level worker payload JSON object with exact keys."""
    _validate_local_python_worker_payload_json_text(payload_json)
    try:
        decoded: object = json.loads(
            payload_json,
            object_pairs_hook=_local_python_worker_payload_json_object_from_pairs,
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "local Python worker request payload must be valid JSON"
        ) from error
    if not isinstance(decoded, dict):
        raise ValueError("local Python worker request payload must be a JSON object")

    payload_object: dict[object, object] = decoded
    if any(not isinstance(key, str) for key in payload_object):
        raise ValueError("local Python worker request payload keys must be strings")
    payload_keys = set(payload_object)
    unknown_keys = (
        payload_keys - _RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_PAYLOAD_KEYS
    )
    if unknown_keys:
        raise ValueError("local Python worker request payload contains unknown keys")
    missing_keys = (
        _RUNTIME_PROBE_LOCAL_PYTHON_WORKER_REQUEST_PAYLOAD_KEYS - payload_keys
    )
    if missing_keys:
        raise ValueError("local Python worker request payload is missing required keys")
    return payload_object


def _local_python_worker_payload_json_object_from_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    """Reject duplicate object keys while decoding strict payload JSON."""
    payload_object: dict[str, object] = {}
    for key, value in pairs:
        if key in payload_object:
            raise ValueError(
                "local Python worker request payload contains duplicate JSON keys"
            )
        payload_object[key] = value
    return payload_object


def _validate_local_python_worker_payload_json_text(value: str) -> None:
    """Reject untyped or blank worker payload JSON text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "local Python worker request payload JSON must be non-empty text"
        )


def _parse_local_python_worker_payload_string_field(
    value: object,
    *,
    field_name: str,
) -> str:
    """Parse one strict string field from the worker request payload."""
    if not isinstance(value, str):
        raise ValueError(
            f"local Python worker request payload {field_name} must be a string"
        )
    return _validate_local_python_worker_payload_metadata_text(
        value,
        field_name=field_name,
    )


def _parse_runtime_probe_worker_payload_family_label(
    value: object,
) -> RuntimeProbeFamily:
    """Parse one runtime probe family label from the worker request payload."""
    family_label = _parse_local_python_worker_payload_string_field(
        value,
        field_name="family_label",
    )
    try:
        return RuntimeProbeFamily(family_label)
    except ValueError as error:
        raise ValueError(
            "local Python worker request payload family_label is unsupported"
        ) from error


def _parse_local_python_worker_payload_timeout_seconds(value: object) -> int:
    """Parse a positive integer timeout from the worker request payload."""
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(
            "local Python worker request payload timeout_seconds must be a "
            "positive integer"
        )
    return value


def _parse_local_python_worker_payload_argv(value: object) -> tuple[str, ...]:
    """Parse the subprocess argv list from a worker request payload."""
    if not isinstance(value, list):
        raise ValueError("local Python worker request payload argv must be a list")
    argv = tuple(
        _parse_local_python_worker_payload_string_field(token, field_name="argv")
        for token in value
    )
    return _validate_local_python_worker_payload_invocation_argv(argv)


def _parse_local_python_worker_payload_absolute_path(
    value: object,
    *,
    field_name: str,
) -> str:
    """Parse one absolute path string from a worker request payload."""
    path_value = _parse_local_python_worker_payload_string_field(
        value,
        field_name=field_name,
    )
    return _validate_absolute_path_metadata(
        path_value,
        field_name=f"local Python worker request payload {field_name}",
    )


def _parse_local_python_worker_payload_python_path_entries(
    value: object,
) -> tuple[str, ...]:
    """Parse ordered Python path entries from a worker request payload."""
    if not isinstance(value, list):
        raise ValueError(
            "local Python worker request payload python_path_entries must be a list"
        )
    python_path_entries = tuple(
        _parse_local_python_worker_payload_absolute_path(
            entry,
            field_name="python_path_entries",
        )
        for entry in value
    )
    return _validate_local_python_worker_payload_python_path_entries(
        python_path_entries,
    )


def _validate_local_python_worker_payload_invocation_argv(
    argv: tuple[str, ...],
) -> tuple[str, ...]:
    """Reject worker payload argv values that do not retain invocation shape."""
    if not isinstance(argv, tuple) or not argv:
        raise ValueError("local Python worker request payload argv must be a tuple")
    _validate_absolute_path_metadata(
        argv[0],
        field_name="local Python worker request payload argv executable",
    )
    return _validate_local_python_subprocess_argv(
        argv,
        python_executable=argv[0],
    )


def _validate_local_python_worker_payload_python_path_entries(
    python_path_entries: tuple[str, ...],
) -> tuple[str, ...]:
    """Reject unordered-container or malformed worker payload Python path data."""
    if not isinstance(python_path_entries, tuple):
        raise ValueError(
            "local Python worker request payload python_path_entries must be a tuple"
        )
    if not python_path_entries:
        raise ValueError(
            "local Python worker request payload python_path_entries must be non-empty"
        )
    for python_path_entry in python_path_entries:
        _validate_absolute_path_metadata(
            python_path_entry,
            field_name="local Python worker request payload python_path_entries",
        )
    return python_path_entries


def _parse_runtime_probe_worker_payload_replay_fields(
    value: object,
    *,
    field_name: str,
) -> tuple[RuntimeProbeReplayField, ...]:
    """Parse ordered replay fields from a worker request payload array."""
    if not isinstance(value, list):
        raise ValueError(
            f"local Python worker request payload {field_name} must be a list"
        )
    fields: list[RuntimeProbeReplayField] = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError(
                f"local Python worker request payload {field_name} entries must "
                "be objects"
            )
        entry_object: dict[object, object] = entry
        if set(entry_object) != {"key", "value"}:
            raise ValueError(
                f"local Python worker request payload {field_name} entries must "
                "contain key and value"
            )
        field_key = entry_object["key"]
        field_value = entry_object["value"]
        if not isinstance(field_key, str) or not isinstance(field_value, str):
            raise ValueError(
                f"local Python worker request payload {field_name} key and value "
                "must be strings"
            )
        fields.append(RuntimeProbeReplayField(key=field_key, value=field_value))
    parsed_fields = tuple(fields)
    _validate_replay_fields(parsed_fields, field_name=field_name)
    return parsed_fields


def _parse_runtime_probe_local_python_stdout_protocol(
    stdout_text: str,
) -> tuple[str, tuple[RuntimeProbeReplayField, ...], str | None]:
    """Parse the strict internal JSON stdout protocol without leaking raw output."""
    _validate_local_python_raw_text(stdout_text, field_name="stdout_text")
    try:
        decoded: object = json.loads(stdout_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            "local Python stdout protocol must be a valid JSON object"
        ) from error
    if not isinstance(decoded, dict):
        raise ValueError("local Python stdout protocol must be a JSON object")

    protocol_object: dict[object, object] = decoded
    if any(not isinstance(key, str) for key in protocol_object):
        raise ValueError("local Python stdout protocol keys must be strings")
    protocol_keys = set(protocol_object)
    unknown_keys = protocol_keys - _RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_KEYS
    if unknown_keys:
        raise ValueError("local Python stdout protocol contains unknown keys")

    revision_value = protocol_object.get(
        _RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION_KEY
    )
    if not isinstance(revision_value, str) or not revision_value.strip():
        raise ValueError("local Python stdout protocol revision must be non-empty")
    if revision_value != revision_value.strip() or _contains_control_character(
        revision_value
    ):
        raise ValueError("local Python stdout protocol revision is malformed")
    if revision_value != _RUNTIME_PROBE_LOCAL_PYTHON_STDOUT_PROTOCOL_REVISION:
        raise ValueError("local Python stdout protocol revision is unsupported")

    normalized_payload = _parse_runtime_probe_local_python_normalized_payload(
        protocol_object.get("normalized_payload")
    )
    durable_artifact_reference = (
        _parse_runtime_probe_local_python_durable_artifact_reference(
            protocol_object.get("durable_artifact_reference")
        )
        if "durable_artifact_reference" in protocol_object
        else None
    )
    if not normalized_payload and durable_artifact_reference is None:
        raise ValueError(
            "local Python stdout protocol requires normalized_payload or "
            "durable_artifact_reference"
        )
    return (revision_value, normalized_payload, durable_artifact_reference)


def _parse_runtime_probe_local_python_normalized_payload(
    value: object,
) -> tuple[RuntimeProbeReplayField, ...]:
    """Parse ordered normalized payload entries from the stdout protocol."""
    if not isinstance(value, list):
        raise ValueError(
            "local Python stdout protocol normalized_payload must be a list"
        )
    fields: list[RuntimeProbeReplayField] = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError(
                "local Python stdout protocol normalized_payload entries must "
                "be objects"
            )
        entry_object: dict[object, object] = entry
        if set(entry_object) != {"key", "value"}:
            raise ValueError(
                "local Python stdout protocol normalized_payload entries must "
                "contain key and value"
            )
        field_key = entry_object["key"]
        field_value = entry_object["value"]
        if not isinstance(field_key, str) or not isinstance(field_value, str):
            raise ValueError(
                "local Python stdout protocol normalized_payload key and value "
                "must be strings"
            )
        if not field_key.strip() or not field_value.strip():
            raise ValueError(
                "local Python stdout protocol normalized_payload must not contain "
                "blank fields"
            )
        fields.append(RuntimeProbeReplayField(key=field_key, value=field_value))
    normalized_payload = tuple(fields)
    _validate_replay_fields(
        normalized_payload,
        field_name="normalized_payload",
    )
    return normalized_payload


def _parse_runtime_probe_local_python_durable_artifact_reference(
    value: object,
) -> str | None:
    """Parse an optional durable artifact reference from the stdout protocol."""
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "local Python stdout protocol durable_artifact_reference must be "
            "a non-empty string or null"
        )
    if value != value.strip() or _contains_control_character(value):
        raise ValueError(
            "local Python stdout protocol durable_artifact_reference is malformed"
        )
    return value


def _validate_local_python_environment_context(
    environment_context: RuntimeProbeLocalPythonEnvironmentContext,
) -> None:
    """Re-check one local-Python environment context for tampering."""
    if not isinstance(environment_context, RuntimeProbeLocalPythonEnvironmentContext):
        raise ValueError(
            "local Python subprocess invocation environment_context must be typed"
        )
    RuntimeProbeLocalPythonEnvironmentContext(
        repository_root=environment_context.repository_root,
        working_directory=environment_context.working_directory,
        python_path_entries=environment_context.python_path_entries,
        runner_contract_revision=environment_context.runner_contract_revision,
        timeout_seconds=environment_context.timeout_seconds,
        runner_environment=environment_context.runner_environment,
        runner_assumptions=environment_context.runner_assumptions,
    )


def _validate_local_python_subprocess_argv(
    argv: tuple[str, ...],
    *,
    python_executable: str,
) -> tuple[str, ...]:
    """Reject invocation argv that cannot represent ``python -m module`` safely."""
    if not isinstance(argv, tuple):
        raise ValueError("local Python subprocess invocation argv must be a tuple")
    if len(argv) < 3:
        raise ValueError(
            "local Python subprocess invocation argv must include executable, -m, "
            "and module name"
        )
    if argv[0] != python_executable:
        raise ValueError(
            "local Python subprocess invocation argv executable must match "
            "python_executable"
        )
    if argv[1] != "-m":
        raise ValueError("local Python subprocess invocation argv must use python -m")
    _validate_local_python_module_name(argv[2])
    for token in argv[3:]:
        _validate_local_python_argv_token(token, field_name="argv")
    return argv


def _validate_local_python_module_name(module_name: str) -> str:
    """Reject module names that are not strict dotted Python identifiers."""
    if not isinstance(module_name, str) or not module_name.strip():
        raise ValueError("local Python module name must be non-empty")
    if module_name != module_name.strip() or _contains_control_character(module_name):
        raise ValueError("local Python module name is malformed")
    module_parts = module_name.split(".")
    if any(not module_part.isidentifier() for module_part in module_parts):
        raise ValueError("local Python module name must be a dotted identifier")
    return module_name


def _validate_local_python_argv_token(token: str, *, field_name: str) -> str:
    """Reject blank or malformed local-Python argv tokens."""
    if not isinstance(token, str) or not token.strip():
        raise ValueError(f"local Python {field_name} tokens must be non-empty")
    if token != token.strip() or _contains_control_character(token):
        raise ValueError(f"local Python {field_name} token is malformed")
    return token


def _validate_local_python_process_returncode(returncode: int) -> int:
    """Reject untyped raw process return code values without interpreting them."""
    if not isinstance(returncode, int) or isinstance(returncode, bool):
        raise ValueError("local Python process completion returncode must be an int")
    return returncode


def _local_python_subprocess_child_environment(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
) -> dict[str, str]:
    """Return a child-only environment with deterministic invocation PYTHONPATH."""
    child_environment = dict(os.environ)
    child_environment["PYTHONPATH"] = os.pathsep.join(invocation.python_path_entries)
    return child_environment


def _validate_local_python_raw_text(value: str, *, field_name: str) -> str:
    """Reject untyped raw process text while preserving empty and multiline values."""
    if not isinstance(value, str):
        raise ValueError(f"local Python process completion {field_name} must be text")
    return value


def _validate_contract_revision(value: str, *, field_name: str) -> str:
    """Reject blank or malformed revision labels."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip() or _contains_control_character(value):
        raise ValueError(f"{field_name} is malformed")
    return value


def _local_python_environment_parts_from_fields(
    runner_environment: tuple[RuntimeProbeReplayField, ...],
) -> _LocalPythonEnvironmentParts:
    """Extract strict local-Python path metadata from runner environment fields."""
    _validate_replay_fields(
        runner_environment,
        field_name="runner_environment",
    )
    singleton_values: dict[str, str] = {}
    python_path_entries: list[str] = []

    for replay_field in runner_environment:
        if replay_field.key in _LOCAL_PYTHON_REPEATED_ENVIRONMENT_KEYS:
            if replay_field.key == _LOCAL_PYTHON_PATH_ENTRY_ENVIRONMENT_KEY:
                python_path_entries.append(
                    _validate_local_python_path_metadata(
                        replay_field.value,
                        field_key=replay_field.key,
                    )
                )
            continue

        if replay_field.key in singleton_values:
            raise ValueError(
                f"duplicate singleton runner_environment field {replay_field.key}"
            )
        singleton_values[replay_field.key] = replay_field.value

    repository_root = _required_local_python_singleton_path(
        singleton_values,
        field_key=_LOCAL_PYTHON_REPOSITORY_ROOT_ENVIRONMENT_KEY,
    )
    working_directory = _required_local_python_singleton_path(
        singleton_values,
        field_key=_LOCAL_PYTHON_WORKING_DIRECTORY_ENVIRONMENT_KEY,
    )
    return (repository_root, working_directory, tuple(python_path_entries))


def _required_local_python_singleton_path(
    singleton_values: Mapping[str, str],
    *,
    field_key: str,
) -> str:
    """Return one required singleton path after absolute-path validation."""
    if field_key not in _LOCAL_PYTHON_REQUIRED_SINGLETON_ENVIRONMENT_KEYS:
        raise ValueError("local Python singleton field is not required")
    value = singleton_values.get(field_key)
    if value is None:
        raise ValueError(
            f"missing required singleton runner_environment field {field_key}"
        )
    return _validate_local_python_path_metadata(value, field_key=field_key)


def _validate_local_python_path_metadata(value: str, *, field_key: str) -> str:
    """Reject blank, relative, or malformed local-Python path metadata."""
    return _validate_absolute_path_metadata(
        value,
        field_name=f"runner_environment field {field_key}",
    )


def _validate_absolute_path_metadata(value: str, *, field_name: str) -> str:
    """Reject blank, relative, or malformed path metadata."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} path metadata must be non-empty")
    if value != value.strip() or _contains_control_character(value):
        raise ValueError(f"{field_name} path metadata is malformed")
    if not _is_absolute_path_metadata(value):
        raise ValueError(f"{field_name} path metadata must be absolute")
    return value


def _contains_control_character(value: str) -> bool:
    """Return whether a metadata value contains path-breaking control characters."""
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _is_absolute_path_metadata(value: str) -> bool:
    """Return whether a path string is absolute on supported path syntaxes."""
    return PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()


def _validate_runner_handoff_metadata(
    *,
    runner_contract_revision: str,
    timeout_seconds: int,
    runner_environment: tuple[RuntimeProbeReplayField, ...],
    runner_assumptions: tuple[RuntimeProbeReplayField, ...],
) -> None:
    """Reject incomplete future-runner contract metadata."""
    if not runner_contract_revision.strip():
        raise ValueError("runner_contract_revision must be non-empty")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if not runner_environment:
        raise ValueError("runtime probe runner requests require runner_environment")
    if not runner_assumptions:
        raise ValueError("runtime probe runner requests require runner_assumptions")
    _validate_replay_fields(
        runner_environment,
        field_name="runner_environment",
    )
    _validate_replay_fields(
        runner_assumptions,
        field_name="runner_assumptions",
    )


def _runtime_probe_result_from_attempt(
    attempt: RuntimeProbeExecutionAttempt,
) -> RuntimeProbeResult:
    """Build the externally admitted result contract for one normalized attempt."""
    if attempt.outcome is RuntimeProbeResultOutcome.OBSERVED:
        return RuntimeProbeObservedResult(
            plan_id=attempt.plan_id,
            request_id=attempt.request_id,
            request=attempt.request,
            replay_artifact=attempt.execution_input.replay_artifact,
            normalized_payload=attempt.normalized_payload,
            durable_artifact_reference=attempt.durable_artifact_reference,
        )

    if attempt.outcome in _NON_PROOF_ATTEMPT_OUTCOMES:
        failure_summary = attempt.failure_summary
        if failure_summary is None:
            raise ValueError("non-proof runtime probe attempts require failure_summary")
        return RuntimeProbeNonProofResult(
            plan_id=attempt.plan_id,
            request_id=attempt.request_id,
            request=attempt.request,
            outcome=attempt.outcome,
            failure_summary=failure_summary,
            replay_artifact=attempt.execution_input.replay_artifact,
            failure_detail_fields=attempt.failure_detail_fields,
        )

    raise ValueError("runtime probe execution attempt outcome is not supported")


def _runtime_probe_result_from_runner_request_attempt(
    runner_request: RuntimeProbeRunnerRequest,
    attempt: RuntimeProbeExecutionAttempt,
) -> RuntimeProbeResult:
    """Build a result only after confirming runner-request identity is preserved."""
    result = _runtime_probe_result_from_attempt(attempt)
    if result.plan_id != runner_request.plan_id:
        raise ValueError("runtime probe result plan_id must match runner request")
    if result.request_id != runner_request.request_id:
        raise ValueError("runtime probe result request_id must match runner request")
    if result.request is not runner_request.request:
        raise ValueError("runtime probe result request must be runner request request")
    if result.replay_artifact is not runner_request.replay_artifact:
        raise ValueError(
            "runtime probe result replay_artifact must be runner request "
            "replay_artifact"
        )
    return result


def _validate_observed_attempt_metadata(
    attempt: RuntimeProbeExecutionAttempt,
) -> None:
    """Reject observed attempts that carry only failure or empty proof metadata."""
    if attempt.failure_summary is not None or attempt.failure_detail_fields:
        raise ValueError(
            "observed runtime probe execution attempts cannot carry failure metadata"
        )
    if not attempt.normalized_payload and attempt.durable_artifact_reference is None:
        raise ValueError(
            "observed runtime probe execution attempts require normalized_payload "
            "or durable_artifact_reference"
        )


def _validate_non_proof_attempt_metadata(
    attempt: RuntimeProbeExecutionAttempt,
) -> None:
    """Reject failed attempts that omit failure metadata or carry proof metadata."""
    if (
        not isinstance(attempt.failure_summary, str)
        or not attempt.failure_summary.strip()
    ):
        raise ValueError("non-proof runtime probe attempts require failure_summary")
    if attempt.normalized_payload or attempt.durable_artifact_reference is not None:
        raise ValueError(
            "non-proof runtime probe execution attempts cannot carry proof metadata"
        )


def _validate_replay_fields(
    fields: tuple[RuntimeProbeReplayField, ...],
    *,
    field_name: str,
) -> None:
    """Reject replay fields whose frozen values have been tampered blank."""
    if not isinstance(fields, tuple):
        raise ValueError(f"{field_name} must be a tuple of replay fields")
    for replay_field in fields:
        if not isinstance(replay_field, RuntimeProbeReplayField):
            raise ValueError(f"{field_name} must contain replay fields")
        if not replay_field.key.strip() or not replay_field.value.strip():
            raise ValueError(f"{field_name} must not contain blank fields")


def _validate_optional_reference(reference: str | None, *, field_name: str) -> None:
    """Reject blank optional artifact references."""
    if reference is None:
        return
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError(f"{field_name} must be non-empty when provided")


def _validate_request_plan(plan: RuntimeProbeRequestPlan) -> None:
    """Reject request-plan envelopes that drifted after construction."""
    expected_plan = build_runtime_probe_request_plan(plan.requests)
    if plan.request_ids != expected_plan.request_ids:
        raise ValueError("runtime probe execution plan request_ids must match requests")
    if plan.plan_id != expected_plan.plan_id:
        raise ValueError("runtime probe execution plan_id must match requests")


def _runtime_probe_local_python_invocation_identity(
    invocation: RuntimeProbeLocalPythonSubprocessInvocation,
) -> str:
    """Return a stable identity digest for one local-Python invocation contract."""
    return _runtime_probe_local_python_invocation_identity_from_parts(
        plan_id=invocation.runner_request.plan_id,
        request_id=invocation.runner_request.request_id,
        invocation_contract_revision=invocation.invocation_contract_revision,
        argv=invocation.argv,
        working_directory=invocation.working_directory,
        python_path_entries=invocation.python_path_entries,
        timeout_seconds=invocation.timeout_seconds,
        request_replay_payload_fields=invocation.request_replay_payload_fields,
    )


def _runtime_probe_local_python_invocation_identity_from_parts(
    *,
    plan_id: str,
    request_id: str,
    invocation_contract_revision: str,
    argv: tuple[str, ...],
    working_directory: str,
    python_path_entries: tuple[str, ...],
    timeout_seconds: int,
    request_replay_payload_fields: tuple[RuntimeProbeReplayField, ...],
) -> str:
    """Return the stable local-Python invocation identity for copied metadata."""
    replay_payload_identity = tuple(
        (field.key, field.value) for field in request_replay_payload_fields
    )
    serialized_identity = json.dumps(
        (
            ("plan_id", plan_id),
            ("request_id", request_id),
            (
                "invocation_contract_revision",
                invocation_contract_revision,
            ),
            ("argv", argv),
            ("working_directory", working_directory),
            ("python_path_entries", python_path_entries),
            ("timeout_seconds", timeout_seconds),
            ("request_replay_payload_fields", replay_payload_identity),
        ),
        separators=(",", ":"),
    )
    digest = hashlib.sha256(serialized_identity.encode("utf-8")).hexdigest()
    return f"runtime_probe_local_python_subprocess_invocation:{digest}"


def _runtime_probe_identifier(
    *,
    plan_id: str,
    request_id: str,
    request: RuntimeProbeRequest,
) -> str:
    """Return a stable execution-input identity for one planned probe request."""
    serialized_identity = json.dumps(
        (
            ("plan_id", plan_id),
            ("request_id", request_id),
            (
                "source_site_identity",
                runtime_acquisition._source_site_identity(request.source_site),
            ),
            ("family_label", request.family_label.value),
            ("form_label", request.form_label),
            ("replay_target_seed", request.replay_target_seed),
            ("replay_selector_seed", request.replay_selector_seed),
        ),
        separators=(",", ":"),
    )
    digest = hashlib.sha256(serialized_identity.encode("utf-8")).hexdigest()
    return f"runtime_probe_execution_input:{digest}"


def _replay_inputs_for_request(
    *,
    plan_id: str,
    request_id: str,
    request: RuntimeProbeRequest,
) -> tuple[RuntimeProbeReplayField, ...]:
    """Return replay/debug identity fields copied from one planned request."""
    span = request.source_site.span
    return (
        RuntimeProbeReplayField(key="plan_id", value=plan_id),
        RuntimeProbeReplayField(key="request_id", value=request_id),
        RuntimeProbeReplayField(key="subject_kind", value=request.subject_kind.value),
        RuntimeProbeReplayField(key="subject_id", value=request.subject_id),
        RuntimeProbeReplayField(
            key="source_site_id",
            value=request.source_site.site_id,
        ),
        RuntimeProbeReplayField(
            key="source_file_path",
            value=request.source_site.file_path,
        ),
        RuntimeProbeReplayField(
            key="source_start_line",
            value=str(span.start_line),
        ),
        RuntimeProbeReplayField(
            key="source_start_column",
            value=str(span.start_column),
        ),
        RuntimeProbeReplayField(key="source_end_line", value=str(span.end_line)),
        RuntimeProbeReplayField(
            key="source_end_column",
            value=str(span.end_column),
        ),
        RuntimeProbeReplayField(key="reason_code", value=request.reason_code.value),
        RuntimeProbeReplayField(key="boundary_text", value=request.boundary_text),
        RuntimeProbeReplayField(
            key="family_label",
            value=request.family_label.value,
        ),
        RuntimeProbeReplayField(key="form_label", value=request.form_label),
        RuntimeProbeReplayField(
            key="replay_target_seed",
            value=request.replay_target_seed,
        ),
        RuntimeProbeReplayField(
            key="replay_selector_seed",
            value=request.replay_selector_seed,
        ),
    )


__all__ = [
    "RuntimeProbeDiagnosticRunnerRequestPreparation",
    "RuntimeProbeDispatchingRunner",
    "RuntimeProbeExecutionAttempt",
    "RuntimeProbeExecutionInput",
    "RuntimeProbeExecutionInputBatch",
    "RuntimeProbeFailureNormalizingRunner",
    "RuntimeProbeLocalPythonEnvironmentContext",
    "RuntimeProbeLocalPythonProcessCompletion",
    "RuntimeProbeLocalPythonStdoutProtocolResult",
    "RuntimeProbeLocalPythonSubprocessHandlerConfig",
    "RuntimeProbeLocalPythonSubprocessInvocation",
    "RuntimeProbeLocalPythonWorkerRequestPayload",
    "RuntimeProbeLocalPythonWorkerRequestStdinTransport",
    "RuntimeProbeRunnerHandlerEntry",
    "RuntimeProbeRunnerHandlerKey",
    "RuntimeProbeRunnerAttemptCollection",
    "RuntimeProbeRunnerCallable",
    "RuntimeProbeRunnerRequest",
    "RuntimeProbeRunnerRequestBatch",
    "assemble_runtime_probe_result_batch_from_execution_attempts",
    "assemble_runtime_probe_result_batch_from_runner_request_attempts",
    "collect_runtime_probe_execution_attempts_from_runner_requests",
    "derive_runtime_probe_local_python_environment_context",
    "execute_runtime_probe_local_python_subprocess_invocation",
    "execute_runtime_probe_local_python_subprocess_invocation_attempt",
    "make_dispatching_runtime_probe_runner",
    "make_failure_normalizing_runtime_probe_runner",
    "make_runtime_probe_dynamic_import_local_python_subprocess_runner",
    "make_runtime_probe_reflective_dir_local_python_subprocess_runner",
    "make_runtime_probe_reflective_dir_zero_local_python_subprocess_runner",
    "make_runtime_probe_reflective_getattr_default_local_python_subprocess_runner",
    "make_runtime_probe_reflective_getattr_local_python_subprocess_runner",
    "make_runtime_probe_reflective_hasattr_local_python_subprocess_runner",
    "make_runtime_probe_reflective_vars_local_python_subprocess_runner",
    "make_runtime_probe_reflective_vars_zero_local_python_subprocess_runner",
    "make_runtime_probe_runtime_mutation_delattr_local_python_subprocess_runner",
    "make_runtime_probe_runtime_mutation_globals_zero_local_python_subprocess_runner",
    "make_runtime_probe_runtime_mutation_locals_zero_local_python_subprocess_runner",
    "make_runtime_probe_runtime_mutation_setattr_local_python_subprocess_runner",
    "make_runtime_probe_local_python_subprocess_handler_entry",
    "materialize_runtime_probe_execution_input_batch",
    "materialize_runtime_probe_local_python_process_completion_attempt",
    "materialize_runtime_probe_local_python_process_completion",
    "materialize_runtime_probe_local_python_stdout_protocol_failure_attempt",
    "materialize_runtime_probe_local_python_stdout_protocol_attempt",
    "materialize_runtime_probe_local_python_stdout_protocol_result",
    "materialize_runtime_probe_local_python_subprocess_exception_attempt",
    "materialize_runtime_probe_local_python_subprocess_invocation",
    "materialize_runtime_probe_local_python_worker_request_payload",
    "materialize_runtime_probe_local_python_worker_request_stdin_transport",
    "materialize_runtime_probe_runner_request_batch",
    "parse_runtime_probe_local_python_worker_request_payload",
    "prepare_runtime_probe_runner_requests_for_diagnostic",
    "serialize_runtime_probe_local_python_worker_request_payload",
]

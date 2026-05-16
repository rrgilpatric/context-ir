"""Tool-facing facade tests for semantic repository compilation."""

from __future__ import annotations

import hashlib
import sys
import textwrap
from dataclasses import replace
from pathlib import Path

import pytest

import context_ir
import context_ir.compiler as legacy_compiler
import context_ir.mcp_server as mcp_server
import context_ir.optimizer as legacy_optimizer
import context_ir.parser as legacy_parser
import context_ir.renderer as legacy_renderer
import context_ir.runtime_acquisition as runtime_acquisition
import context_ir.runtime_observation_admission as runtime_observation_admission
import context_ir.runtime_observation_recompile as runtime_observation_recompile
import context_ir.runtime_probe_execution as runtime_probe_execution
import context_ir.runtime_probe_requests as runtime_probe_requests
import context_ir.runtime_probe_results as runtime_probe_results
import context_ir.scorer as legacy_scorer
import context_ir.semantic_types as semantic_types
import context_ir.tool_facade as tool_facade
from context_ir.runtime_observation_recompile import (
    apply_runtime_probe_result_batch_for_diagnostic_and_recompile,
)
from context_ir.runtime_probe_execution import (
    collect_runtime_probe_execution_attempts_from_runner_requests,
    prepare_runtime_probe_runner_requests_for_diagnostic,
)
from context_ir.semantic_diagnostics import diagnose_semantic_miss
from context_ir.semantic_types import (
    CapabilityTier,
    ReferenceContext,
    RepositorySnapshotBasis,
    RuntimeAttachmentLink,
    SelectionBasis,
    SemanticCompileContext,
    SemanticCompileResult,
    SemanticDiagnosticBoundary,
    SemanticDiagnosticBoundaryKind,
    SemanticDiagnosticResult,
    SemanticDiagnosticUnitStatus,
    SemanticMissEvidence,
    SemanticMissKind,
    SemanticOptimizationResult,
    SemanticOptimizationWarning,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticRecompileResult,
    SemanticSelectionRecord,
    SourceSite,
    SourceSpan,
    SyntaxDiagnosticCode,
    SyntaxProgram,
    UnresolvedReasonCode,
)
from context_ir.tool_facade import (
    SemanticContextRequest,
    SemanticContextResponse,
    SemanticDefaultLocalPythonSubprocessRecompileRequest,
    SemanticDefaultLocalPythonSubprocessRecompileResponse,
    SemanticDynamicImportLocalPythonSubprocessRecompileRequest,
    SemanticDynamicImportLocalPythonSubprocessRecompileResponse,
    SemanticRuntimeObservationRecompileRequest,
    SemanticRuntimeObservationRecompileResponse,
    compile_repository_context,
    recompile_repository_context_with_default_local_python_subprocess,
    recompile_repository_context_with_dynamic_import_local_python_subprocess,
    recompile_repository_context_with_runtime_observations,
)


def _estimate_tokens(text: str) -> int:
    """Mirror compile-level token estimation for assembled documents."""
    return max(1, (len(text) + 3) // 4)


def _dynamic_import_runtime_observation() -> (
    runtime_acquisition.DynamicImportRuntimeObservation
):
    """Create one admissible dynamic-import runtime observation for facade tests."""
    return _dynamic_import_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:dynamic-import",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=32,
            ),
            snippet='importlib.import_module("pkg.dynamic")',
        )
    )


def _dynamic_import_runtime_observation_for_site(
    site: SourceSite,
    *,
    imported_module: str = "pkg.dynamic",
) -> runtime_acquisition.DynamicImportRuntimeObservation:
    """Create one admissible dynamic-import runtime observation for ``site``."""
    return runtime_acquisition.DynamicImportRuntimeObservation(
        site=site,
        probe_identifier="probe:dynamic-import",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:dynamic-import:trace",
                attachment_role="trace",
                description="dynamic import trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="imported_module",
                value=imported_module,
            ),
        ),
    )


def _eval_runtime_observation() -> runtime_acquisition.EvalRuntimeObservation:
    """Create one admissible ``eval(source)`` runtime observation for facade tests."""
    return _eval_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:eval",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=12,
            ),
            snippet="eval(source)",
        )
    )


def _eval_runtime_observation_for_site(
    site: SourceSite,
    *,
    evaluation_outcome: str = "returned_value",
    source_text: str = '"runtime-value"',
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.EvalRuntimeObservation:
    """Create one admissible ``eval(source)`` runtime observation for ``site``."""
    durable_reference = durable_payload_reference
    if durable_reference is None:
        durable_reference = f"artifact://eval-result/{site.site_id}.json"
    return runtime_acquisition.EvalRuntimeObservation(
        site=site,
        probe_identifier="probe:eval",
        probe_contract_revision="2026-04-26.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:eval:trace",
                attachment_role="trace",
                description="eval trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        replay_inputs=(
            runtime_acquisition._RuntimeObservationField(
                key="source_shape",
                value="literal_expression",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="source_sha256",
                value=hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            ),
        ),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="evaluation_outcome",
                value=evaluation_outcome,
            ),
            runtime_acquisition._RuntimeObservationField(
                key="result_type",
                value="builtins.str",
            ),
        ),
        durable_payload_reference=durable_reference,
    )


def _exec_runtime_observation() -> runtime_acquisition.ExecRuntimeObservation:
    """Create one admissible ``exec(source)`` runtime observation for facade tests."""
    return _exec_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:exec",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=12,
            ),
            snippet="exec(source)",
        )
    )


def _exec_runtime_observation_for_site(
    site: SourceSite,
    *,
    execution_outcome: str = "completed",
    source_text: str = "pass",
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.ExecRuntimeObservation:
    """Create one admissible ``exec(source)`` runtime observation for ``site``."""
    durable_reference = durable_payload_reference
    if durable_reference is None:
        durable_reference = f"artifact://exec-result/{site.site_id}.json"
    return runtime_acquisition.ExecRuntimeObservation(
        site=site,
        probe_identifier="probe:exec",
        probe_contract_revision="2026-04-27.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:exec:trace",
                attachment_role="trace",
                description="exec trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        replay_inputs=(
            runtime_acquisition._RuntimeObservationField(
                key="source_shape",
                value="literal_statement",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="source_sha256",
                value=hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            ),
        ),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="execution_outcome",
                value=execution_outcome,
            ),
            runtime_acquisition._RuntimeObservationField(
                key="statement_kind",
                value="pass",
            ),
        ),
        durable_payload_reference=durable_reference,
    )


def _hasattr_runtime_observation() -> runtime_acquisition.HasattrRuntimeObservation:
    """Create one admissible ``hasattr`` runtime observation for facade tests."""
    return _hasattr_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:hasattr",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=18,
            ),
            snippet='hasattr(obj, "x")',
        )
    )


def _hasattr_runtime_observation_for_site(
    site: SourceSite,
    *,
    attribute_present: bool = True,
) -> runtime_acquisition.HasattrRuntimeObservation:
    """Create one admissible ``hasattr`` runtime observation for ``site``."""
    return runtime_acquisition.HasattrRuntimeObservation(
        site=site,
        probe_identifier="probe:hasattr",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:hasattr:trace",
                attachment_role="trace",
                description="hasattr trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="attribute_present",
                value="true" if attribute_present else "false",
            ),
        ),
    )


def _getattr_runtime_observation() -> runtime_acquisition.GetattrRuntimeObservation:
    """Create one admissible ``getattr`` runtime observation for facade tests."""
    return _getattr_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:getattr",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=18,
            ),
            snippet='getattr(obj, "x")',
        )
    )


def _getattr_runtime_observation_for_site(
    site: SourceSite,
    *,
    lookup_outcome: str = "returned_value",
) -> runtime_acquisition.GetattrRuntimeObservation:
    """Create one admissible ``getattr`` runtime observation for ``site``."""
    return runtime_acquisition.GetattrRuntimeObservation(
        site=site,
        probe_identifier="probe:getattr",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:getattr:trace",
                attachment_role="trace",
                description="getattr trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value=lookup_outcome,
            ),
        ),
    )


def _vars_runtime_observation() -> runtime_acquisition.VarsRuntimeObservation:
    """Create one admissible ``vars`` runtime observation for facade tests."""
    return _vars_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:vars",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=9,
            ),
            snippet="vars(obj)",
        )
    )


def _vars_runtime_observation_for_site(
    site: SourceSite,
    *,
    lookup_outcome: str = "returned_namespace",
) -> runtime_acquisition.VarsRuntimeObservation:
    """Create one admissible ``vars`` runtime observation for ``site``."""
    return runtime_acquisition.VarsRuntimeObservation(
        site=site,
        probe_identifier="probe:vars",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:vars:trace",
                attachment_role="trace",
                description="vars trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value=lookup_outcome,
            ),
        ),
    )


def _globals_runtime_observation() -> runtime_acquisition.GlobalsRuntimeObservation:
    """Create one admissible ``globals()`` runtime observation for facade tests."""
    return _globals_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:globals",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=9,
            ),
            snippet="globals()",
        )
    )


def _globals_runtime_observation_for_site(
    site: SourceSite,
    *,
    lookup_outcome: str = "returned_namespace",
) -> runtime_acquisition.GlobalsRuntimeObservation:
    """Create one admissible ``globals()`` runtime observation for ``site``."""
    return runtime_acquisition.GlobalsRuntimeObservation(
        site=site,
        probe_identifier="probe:globals",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:globals:trace",
                attachment_role="trace",
                description="globals trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value=lookup_outcome,
            ),
        ),
    )


def _locals_runtime_observation() -> runtime_acquisition.LocalsRuntimeObservation:
    """Create one admissible ``locals()`` runtime observation for facade tests."""
    return _locals_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:locals",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=8,
            ),
            snippet="locals()",
        )
    )


def _locals_runtime_observation_for_site(
    site: SourceSite,
    *,
    lookup_outcome: str = "returned_namespace",
) -> runtime_acquisition.LocalsRuntimeObservation:
    """Create one admissible ``locals()`` runtime observation for ``site``."""
    return runtime_acquisition.LocalsRuntimeObservation(
        site=site,
        probe_identifier="probe:locals",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:locals:trace",
                attachment_role="trace",
                description="locals trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value=lookup_outcome,
            ),
        ),
    )


def _setattr_runtime_observation() -> runtime_acquisition.SetattrRuntimeObservation:
    """Create one admissible ``setattr`` runtime observation for facade tests."""
    return _setattr_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:setattr",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=23,
            ),
            snippet='setattr(obj, "x", value)',
        )
    )


def _setattr_runtime_observation_for_site(
    site: SourceSite,
    *,
    mutation_outcome: str = "returned_none",
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.SetattrRuntimeObservation:
    """Create one admissible ``setattr`` runtime observation for ``site``."""
    durable_reference = durable_payload_reference
    if durable_reference is None:
        durable_reference = f"artifact://passed-value/{site.site_id}.json"
    return runtime_acquisition.SetattrRuntimeObservation(
        site=site,
        probe_identifier="probe:setattr",
        probe_contract_revision="2026-04-21.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:setattr:trace",
                attachment_role="trace",
                description="setattr trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="mutation_outcome",
                value=mutation_outcome,
            ),
        ),
        durable_payload_reference=durable_reference,
    )


def _delattr_runtime_observation() -> runtime_acquisition.DelattrRuntimeObservation:
    """Create one admissible ``delattr`` runtime observation for facade tests."""
    return _delattr_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:delattr",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=18,
            ),
            snippet='delattr(obj, "x")',
        )
    )


def _delattr_runtime_observation_for_site(
    site: SourceSite,
    *,
    mutation_outcome: str = "deleted_attribute",
) -> runtime_acquisition.DelattrRuntimeObservation:
    """Create one admissible ``delattr`` runtime observation for ``site``."""
    return runtime_acquisition.DelattrRuntimeObservation(
        site=site,
        probe_identifier="probe:delattr",
        probe_contract_revision="2026-04-21.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:delattr:trace",
                attachment_role="trace",
                description="delattr trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="mutation_outcome",
                value=mutation_outcome,
            ),
        ),
    )


def _dir_runtime_observation() -> runtime_acquisition.DirRuntimeObservation:
    """Create one admissible ``dir(obj)`` runtime observation for facade tests."""
    return _dir_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:dir",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=8,
            ),
            snippet="dir(obj)",
        )
    )


def _dir_runtime_observation_for_site(
    site: SourceSite,
    *,
    listing_entry_count: int | None = 3,
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.DirRuntimeObservation:
    """Create one admissible ``dir(obj)`` runtime observation for ``site``."""
    normalized_payload: tuple[runtime_acquisition._RuntimeObservationField, ...]
    if listing_entry_count is None:
        normalized_payload = ()
    else:
        normalized_payload = (
            runtime_acquisition._RuntimeObservationField(
                key="listing_entry_count",
                value=str(listing_entry_count),
            ),
        )
    durable_reference = durable_payload_reference
    if durable_reference is None:
        durable_reference = f"artifact://dir-listing/{site.site_id}.json"
    return runtime_acquisition.DirRuntimeObservation(
        site=site,
        probe_identifier="probe:dir",
        probe_contract_revision="2026-04-20.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:dir:trace",
                attachment_role="trace",
                description="dir trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=normalized_payload,
        durable_payload_reference=durable_reference,
    )


def _metaclass_behavior_runtime_observation() -> (
    runtime_acquisition.MetaclassBehaviorRuntimeObservation
):
    """Create one admissible metaclass runtime observation for facade tests."""
    return _metaclass_behavior_runtime_observation_for_site(
        SourceSite(
            site_id="site:main:metaclass",
            file_path="main.py",
            span=SourceSpan(
                start_line=1,
                start_column=0,
                end_line=1,
                end_column=14,
            ),
            snippet="metaclass=Meta",
        )
    )


def _metaclass_behavior_runtime_observation_for_site(
    site: SourceSite,
    *,
    class_creation_outcome: str = "created_class",
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.MetaclassBehaviorRuntimeObservation:
    """Create one admissible metaclass runtime observation for ``site``."""
    durable_reference = durable_payload_reference
    if durable_reference is None:
        durable_reference = f"artifact://metaclass-selection/{site.site_id}.json"
    return runtime_acquisition.MetaclassBehaviorRuntimeObservation(
        site=site,
        probe_identifier="probe:metaclass-behavior",
        probe_contract_revision="2026-04-21.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:metaclass:trace",
                attachment_role="trace",
                description="metaclass trace",
            ),
        ),
        replay_target="main.Example",
        replay_selector="class:main.Example:metaclass",
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="class_creation_outcome",
                value=class_creation_outcome,
            ),
        ),
        durable_payload_reference=durable_reference,
    )


def _write_dynamic_import_program(tmp_path: Path) -> None:
    """Write a fixture with one dynamic-import unsupported boundary."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run(name: str) -> None:
                importlib.import_module(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_local_python_dynamic_import_program(tmp_path: Path) -> None:
    """Write a dynamic-import fixture importable by the worker subprocess."""
    (tmp_path / "plugins").mkdir()
    (tmp_path / "plugins" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "plugins" / "recompile_subprocess.py").write_text(
        "VALUE = 'runtime probe subprocess fixture'\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            import importlib

            def run() -> None:
                importlib.import_module("plugins.recompile_subprocess")
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_local_python_locals_program(tmp_path: Path) -> None:
    """Write a replay target with one attachable locals/0 boundary."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            MODULE_VALUE = object()

            def run() -> object:
                local_value = object()
                namespace = locals()
                assert type(namespace) is dict
                assert namespace["local_value"] is local_value
                assert "MODULE_VALUE" not in namespace
                assert "namespace" not in namespace
                return namespace
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _write_local_python_hasattr_probe_program(tmp_path: Path) -> None:
    """Write the exact hasattr replay-input pilot source."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def probe_attribute(obj: object, name: str) -> bool:
                return hasattr(obj, name)
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _snapshot_basis() -> RepositorySnapshotBasis:
    """Return stable repository snapshot metadata for runner facade tests."""
    return RepositorySnapshotBasis(
        snapshot_kind="git_commit",
        snapshot_id="abc123def456",
        is_dirty_worktree=False,
    )


def _probe_field(
    key: str,
    value: str,
) -> runtime_probe_results.RuntimeProbeReplayField:
    """Return one runtime probe replay field."""
    return runtime_probe_results.RuntimeProbeReplayField(key=key, value=value)


def _runner_runtime_assumptions() -> tuple[
    runtime_probe_results.RuntimeProbeReplayField, ...
]:
    """Return explicit runtime assumptions for subprocess facade tests."""
    return (
        _probe_field("python_version", "3.11"),
        _probe_field("dependency_mode", "offline-fixture"),
    )


def _runner_assumptions() -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return explicit runner assumptions for subprocess facade tests."""
    return (
        _probe_field("network", "disabled"),
        _probe_field("filesystem_mode", "read_only_fixture"),
    )


def _local_python_runner_environment(
    working_directory: Path,
) -> tuple[runtime_probe_results.RuntimeProbeReplayField, ...]:
    """Return local-Python subprocess environment fields for a temp repo."""
    source_root = Path(context_ir.__file__).resolve().parents[1]
    return (
        _probe_field("repository_root", str(working_directory)),
        _probe_field("working_directory", str(working_directory)),
        _probe_field("python_path_entry", str(source_root)),
    )


def _probe_execution_attempt(
    runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
    *,
    normalized_payload: tuple[runtime_probe_results.RuntimeProbeReplayField, ...],
) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
    """Return one observed runner attempt tied to the supplied request."""
    return runtime_probe_execution.RuntimeProbeExecutionAttempt(
        plan_id=runner_request.plan_id,
        request_id=runner_request.request_id,
        request=runner_request.request,
        execution_input=runner_request.execution_input,
        outcome=runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED,
        normalized_payload=normalized_payload,
    )


def _unsupported_id_for(program: SemanticProgram, construct_text: str) -> str:
    """Return the unsupported construct ID for ``construct_text``."""
    return next(
        construct.construct_id
        for construct in program.unsupported_constructs
        if construct.construct_text == construct_text
    )


def _runtime_observation_recompile_facade_fixture(
    tmp_path: Path,
) -> tuple[
    SemanticContextResponse,
    SemanticMissEvidence,
    SemanticDiagnosticResult,
    runtime_probe_requests.RuntimeProbeRequestPlan,
    runtime_probe_requests.RuntimeProbeRequest,
    runtime_acquisition.DynamicImportRuntimeObservation,
    str,
]:
    """Build a prior facade response with one planned runtime observation request."""
    _write_dynamic_import_program(tmp_path)
    previous_response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="dynamic import",
            budget=32,
        )
    )
    unsupported_id = _unsupported_id_for(
        previous_response.program,
        "importlib.import_module(name)",
    )
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence="importlib.import_module(name)",
    )
    diagnostic = diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    assert diagnostic.omitted_unit_ids == (unsupported_id,)
    assert len(diagnostic.planned_runtime_probe_requests) == 1
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    request = diagnostic.planned_runtime_probe_requests[0]
    observation = _dynamic_import_runtime_observation_for_site(request.source_site)
    return (
        previous_response,
        miss_evidence,
        diagnostic,
        plan,
        request,
        observation,
        unsupported_id,
    )


def _dynamic_import_local_python_subprocess_recompile_facade_fixture(
    tmp_path: Path,
) -> tuple[
    SemanticContextResponse,
    SemanticMissEvidence,
    SemanticDiagnosticResult,
    runtime_probe_requests.RuntimeProbeRequestPlan,
    runtime_probe_requests.RuntimeProbeRequest,
    str,
]:
    """Build a prior facade response with one subprocess-runnable request."""
    _write_local_python_dynamic_import_program(tmp_path)
    previous_response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="dynamic import",
            budget=32,
        )
    )
    boundary_text = 'importlib.import_module("plugins.recompile_subprocess")'
    unsupported_id = _unsupported_id_for(previous_response.program, boundary_text)
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence=boundary_text,
    )
    diagnostic = diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    assert diagnostic.omitted_unit_ids == (unsupported_id,)
    assert len(plan.requests) == 1
    request = plan.requests[0]
    assert request.boundary_text == boundary_text
    assert (
        request.family_label is runtime_probe_requests.RuntimeProbeFamily.DYNAMIC_IMPORT
    )
    assert request.form_label == "dynamic_import:importlib.import_module/1"
    assert request.replay_target_seed == "main.run"
    return (
        previous_response,
        miss_evidence,
        diagnostic,
        plan,
        request,
        unsupported_id,
    )


def _default_local_python_subprocess_recompile_facade_fixture(
    tmp_path: Path,
) -> tuple[
    SemanticContextResponse,
    SemanticMissEvidence,
    SemanticDiagnosticResult,
    runtime_probe_requests.RuntimeProbeRequestPlan,
    runtime_probe_requests.RuntimeProbeRequest,
    str,
]:
    """Build a prior facade response with one default-runner request."""
    _write_local_python_locals_program(tmp_path)
    previous_response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="runtime mutation",
            budget=32,
        )
    )
    boundary_text = "locals()"
    unsupported_id = _unsupported_id_for(previous_response.program, boundary_text)
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence=boundary_text,
    )
    diagnostic = diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    assert diagnostic.omitted_unit_ids == (unsupported_id,)
    assert len(plan.requests) == 1
    request = plan.requests[0]
    assert request.boundary_text == boundary_text
    assert (
        request.family_label
        is runtime_probe_requests.RuntimeProbeFamily.RUNTIME_MUTATION
    )
    assert request.form_label == "runtime_mutation:locals/0"
    assert request.replay_target_seed == "main.run"
    return (
        previous_response,
        miss_evidence,
        diagnostic,
        plan,
        request,
        unsupported_id,
    )


def _default_local_python_subprocess_hasattr_facade_fixture(
    tmp_path: Path,
) -> tuple[
    SemanticContextResponse,
    SemanticMissEvidence,
    SemanticDiagnosticResult,
    runtime_probe_requests.RuntimeProbeRequestPlan,
    runtime_probe_requests.RuntimeProbeRequest,
    str,
]:
    """Build a prior facade response with the exact hasattr pilot request."""
    _write_local_python_hasattr_probe_program(tmp_path)
    previous_response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="hasattr probe",
            budget=32,
        )
    )
    boundary_text = "hasattr(obj, name)"
    unsupported_id = _unsupported_id_for(previous_response.program, boundary_text)
    miss_evidence = SemanticMissEvidence(
        kind=SemanticMissKind.ABSENT_SYMBOL,
        evidence=boundary_text,
    )
    diagnostic = diagnose_semantic_miss(
        previous_response.compile_result,
        miss_evidence,
        previous_response.program,
    )
    plan = diagnostic.planned_runtime_probe_request_plan
    assert plan is not None
    assert diagnostic.omitted_unit_ids == (unsupported_id,)
    assert len(plan.requests) == 1
    request = plan.requests[0]
    assert request.subject_id == "unsupported:call:main.py:2:11"
    assert request.boundary_text == boundary_text
    assert (
        request.family_label
        is runtime_probe_requests.RuntimeProbeFamily.REFLECTIVE_BUILTIN
    )
    assert request.form_label == "reflective_builtin:hasattr/2"
    assert request.replay_target_seed == "main.probe_attribute"
    return (
        previous_response,
        miss_evidence,
        diagnostic,
        plan,
        request,
        unsupported_id,
    )


def _boundary_for(
    result: SemanticDiagnosticResult,
    unit_id: str,
) -> SemanticDiagnosticBoundary:
    """Return the diagnostic boundary classification for ``unit_id``."""
    return next(
        boundary
        for boundary in result.boundary_classifications
        if boundary.unit_id == unit_id
    )


def _unplanned_site() -> SourceSite:
    """Return a source site outside the diagnostic request plan."""
    return SourceSite(
        site_id="site:unplanned",
        file_path="main.py",
        span=SourceSpan(
            start_line=99,
            start_column=0,
            end_line=99,
            end_column=12,
        ),
        snippet="missing()",
    )


def test_recompile_repository_context_with_runtime_observations_applies_and_mirrors(
    tmp_path: Path,
) -> None:
    """The facade applies observations, recompiles, and mirrors nested results."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        _plan,
        request,
        observation,
        unsupported_id,
    ) = _runtime_observation_recompile_facade_fixture(tmp_path)

    response = recompile_repository_context_with_runtime_observations(
        SemanticRuntimeObservationRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            runtime_observations=(observation,),
            miss_evidence=miss_evidence,
            delta_budget=160,
        )
    )
    boundary = _boundary_for(response.diagnostic, unsupported_id)
    selected_trace = next(
        selection.trace_summary
        for selection in response.compile_result.optimization.selections
        if selection.unit_id == unsupported_id
    )

    assert isinstance(response, SemanticRuntimeObservationRecompileResponse)
    assert response.observation_application is (
        response.runtime_observation_recompile.observation_application
    )
    assert response.recompile_result is (
        response.runtime_observation_recompile.recompile_result
    )
    assert response.observation_application.diagnostic is diagnostic
    assert response.observation_application.admissions[0].request is request
    assert response.observation_application.admissions[0].observation is observation
    assert response.program is response.observation_application.updated_program
    assert response.program is not previous_response.program
    assert response.compile_result is response.recompile_result.compile_result
    assert response.diagnostic is response.recompile_result.diagnostic
    assert response.compile_budget == previous_response.compile_budget + 160
    assert response.compile_total_tokens == response.compile_result.total_tokens
    assert response.budget_delta == 160
    assert response.newly_selected_unit_ids == (
        response.recompile_result.newly_selected_unit_ids
    )
    assert response.upgraded_unit_ids == response.recompile_result.upgraded_unit_ids
    assert response.diagnostic.planned_runtime_probe_requests == ()
    assert response.diagnostic.planned_runtime_probe_request_plan == (
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )
    assert boundary.status is SemanticDiagnosticUnitStatus.OMITTED
    assert boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert boundary.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert boundary.has_attached_runtime_provenance is True
    assert selected_trace is not None
    assert selected_trace.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert selected_trace.has_attached_runtime_provenance is True
    assert unsupported_id in response.newly_selected_unit_ids


def test_recompile_repository_context_with_empty_observations_preserves_program(
    tmp_path: Path,
) -> None:
    """Empty observations keep the original program and still recompile."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        _plan,
        _request,
        _observation,
        _unsupported_id,
    ) = _runtime_observation_recompile_facade_fixture(tmp_path)

    response = recompile_repository_context_with_runtime_observations(
        SemanticRuntimeObservationRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            runtime_observations=(),
            miss_evidence=miss_evidence,
            delta_budget=96,
        )
    )

    assert response.observation_application.admissions == ()
    assert response.observation_application.updated_program is previous_response.program
    assert response.program is previous_response.program
    assert response.compile_result is not previous_response.compile_result
    assert response.compile_budget == previous_response.compile_budget + 96
    assert response.diagnostic.planned_runtime_probe_requests == (
        diagnostic.planned_runtime_probe_requests
    )
    assert previous_response.program.provenance_records == []


def test_recompile_repository_context_delegates_and_forwards_embed_fn(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade delegates with the previous response and optional embeddings."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        _plan,
        _request,
        observation,
        _unsupported_id,
    ) = _runtime_observation_recompile_facade_fixture(tmp_path)
    calls: list[
        tuple[
            SemanticProgram,
            SemanticDiagnosticResult,
            tuple[runtime_observation_admission.RuntimeObservation, ...],
            SemanticCompileResult,
            SemanticMissEvidence,
            int,
            tool_facade.EmbeddingFunction | None,
        ]
    ] = []

    def embed_fn(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _text in texts]

    fake_observation_application = (
        runtime_observation_admission.RuntimeObservationApplication(
            diagnostic=diagnostic,
            admissions=(),
            updated_program=previous_response.program,
        )
    )
    fake_recompile_result = SemanticRecompileResult(
        compile_result=previous_response.compile_result,
        diagnostic=diagnostic,
        budget_delta=12,
        newly_selected_unit_ids=(),
        upgraded_unit_ids=(),
    )
    fake_result = runtime_observation_recompile.RuntimeObservationRecompileApplication(
        observation_application=fake_observation_application,
        recompile_result=fake_recompile_result,
    )

    def fake_apply(
        program: SemanticProgram,
        received_diagnostic: SemanticDiagnosticResult,
        observations: tuple[runtime_observation_admission.RuntimeObservation, ...],
        previous_result: SemanticCompileResult,
        received_miss_evidence: SemanticMissEvidence,
        delta_budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> runtime_observation_recompile.RuntimeObservationRecompileApplication:
        calls.append(
            (
                program,
                received_diagnostic,
                observations,
                previous_result,
                received_miss_evidence,
                delta_budget,
                embed_fn,
            )
        )
        return fake_result

    monkeypatch.setattr(
        tool_facade,
        "apply_runtime_observations_for_diagnostic_and_recompile",
        fake_apply,
    )

    response = recompile_repository_context_with_runtime_observations(
        SemanticRuntimeObservationRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            runtime_observations=(observation,),
            miss_evidence=miss_evidence,
            delta_budget=12,
            embed_fn=embed_fn,
        )
    )

    assert calls == [
        (
            previous_response.program,
            diagnostic,
            (observation,),
            previous_response.compile_result,
            miss_evidence,
            12,
            embed_fn,
        )
    ]
    assert response.runtime_observation_recompile is fake_result
    assert response.observation_application is fake_observation_application
    assert response.recompile_result is fake_recompile_result


def test_recompile_repository_context_propagates_existing_gates(
    tmp_path: Path,
) -> None:
    """Application and recompile preconditions still reject through the facade."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        _plan,
        request,
        observation,
        _unsupported_id,
    ) = _runtime_observation_recompile_facade_fixture(tmp_path)

    missing_plan = replace(diagnostic, planned_runtime_probe_request_plan=None)
    with pytest.raises(ValueError, match="planned_runtime_probe_request_plan"):
        recompile_repository_context_with_runtime_observations(
            SemanticRuntimeObservationRecompileRequest(
                previous_response=previous_response,
                diagnostic=missing_plan,
                runtime_observations=(observation,),
                miss_evidence=miss_evidence,
                delta_budget=96,
            )
        )

    with pytest.raises(ValueError, match="not present in request plan"):
        recompile_repository_context_with_runtime_observations(
            SemanticRuntimeObservationRecompileRequest(
                previous_response=previous_response,
                diagnostic=diagnostic,
                runtime_observations=(
                    _dynamic_import_runtime_observation_for_site(_unplanned_site()),
                ),
                miss_evidence=miss_evidence,
                delta_budget=96,
            )
        )

    with pytest.raises(ValueError, match="share the same source site"):
        recompile_repository_context_with_runtime_observations(
            SemanticRuntimeObservationRecompileRequest(
                previous_response=previous_response,
                diagnostic=diagnostic,
                runtime_observations=(
                    observation,
                    _exec_runtime_observation_for_site(request.source_site),
                ),
                miss_evidence=miss_evidence,
                delta_budget=96,
            )
        )

    with pytest.raises(ValueError, match="does not match planned request family/form"):
        recompile_repository_context_with_runtime_observations(
            SemanticRuntimeObservationRecompileRequest(
                previous_response=previous_response,
                diagnostic=diagnostic,
                runtime_observations=(
                    _exec_runtime_observation_for_site(request.source_site),
                ),
                miss_evidence=miss_evidence,
                delta_budget=96,
            )
        )

    with pytest.raises(ValueError, match="delta_budget must be >= 0"):
        recompile_repository_context_with_runtime_observations(
            SemanticRuntimeObservationRecompileRequest(
                previous_response=previous_response,
                diagnostic=diagnostic,
                runtime_observations=(observation,),
                miss_evidence=miss_evidence,
                delta_budget=-1,
            )
        )

    previous_without_context = replace(
        previous_response,
        compile_result=replace(previous_response.compile_result, compile_context=None),
    )
    with pytest.raises(ValueError, match="compile_context"):
        recompile_repository_context_with_runtime_observations(
            SemanticRuntimeObservationRecompileRequest(
                previous_response=previous_without_context,
                diagnostic=diagnostic,
                runtime_observations=(),
                miss_evidence=miss_evidence,
                delta_budget=96,
            )
        )


def test_recompile_repository_context_response_rejects_broken_mirrors(
    tmp_path: Path,
) -> None:
    """The recompile facade response enforces object-identity mirror fields."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        _plan,
        _request,
        observation,
        _unsupported_id,
    ) = _runtime_observation_recompile_facade_fixture(tmp_path)
    response = recompile_repository_context_with_runtime_observations(
        SemanticRuntimeObservationRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            runtime_observations=(observation,),
            miss_evidence=miss_evidence,
            delta_budget=160,
        )
    )

    with pytest.raises(ValueError, match="program must mirror"):
        SemanticRuntimeObservationRecompileResponse(
            runtime_observation_recompile=response.runtime_observation_recompile,
            observation_application=response.observation_application,
            recompile_result=response.recompile_result,
            program=previous_response.program,
            compile_result=response.compile_result,
            diagnostic=response.diagnostic,
            compile_total_tokens=response.compile_total_tokens,
            compile_budget=response.compile_budget,
            budget_delta=response.budget_delta,
            newly_selected_unit_ids=response.newly_selected_unit_ids,
            upgraded_unit_ids=response.upgraded_unit_ids,
        )

    with pytest.raises(ValueError, match="compile_budget must mirror"):
        SemanticRuntimeObservationRecompileResponse(
            runtime_observation_recompile=response.runtime_observation_recompile,
            observation_application=response.observation_application,
            recompile_result=response.recompile_result,
            program=response.program,
            compile_result=response.compile_result,
            diagnostic=response.diagnostic,
            compile_total_tokens=response.compile_total_tokens,
            compile_budget=response.compile_budget + 1,
            budget_delta=response.budget_delta,
            newly_selected_unit_ids=response.newly_selected_unit_ids,
            upgraded_unit_ids=response.upgraded_unit_ids,
        )


def test_dynamic_import_local_python_subprocess_recompile_facade_runs_and_mirrors(
    tmp_path: Path,
) -> None:
    """The facade runs subprocess-backed dynamic-import probes and mirrors results."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        plan,
        request,
        unsupported_id,
    ) = _dynamic_import_local_python_subprocess_recompile_facade_fixture(tmp_path)
    repository_snapshot_basis = _snapshot_basis()
    runtime_assumptions = _runner_runtime_assumptions()
    runner_environment = _local_python_runner_environment(tmp_path)
    runner_assumptions = _runner_assumptions()

    response = recompile_repository_context_with_dynamic_import_local_python_subprocess(
        SemanticDynamicImportLocalPythonSubprocessRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            miss_evidence=miss_evidence,
            delta_budget=160,
            python_executable=sys.executable,
            invocation_contract_revision=(
                "runtime-probe-local-python-subprocess:test.1"
            ),
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
            repository_snapshot_basis=repository_snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=runtime_assumptions,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )
    )
    recompile_application = response.result_batch_recompile_application
    preparation = response.runner_request_preparation
    collection = response.runner_attempt_collection
    runner_request = preparation.runner_request_batch.runner_requests[0]
    attempt = collection.attempts[0]
    observed_result = collection.result_batch.results[0]
    admission = response.observation_application.admissions[0]
    boundary = _boundary_for(response.diagnostic, unsupported_id)
    expected_payload = (
        _probe_field("imported_module", "plugins.recompile_subprocess"),
    )
    selected_trace = next(
        selection.trace_summary
        for selection in response.compile_result.optimization.selections
        if selection.unit_id == unsupported_id
    )

    assert isinstance(
        response,
        SemanticDynamicImportLocalPythonSubprocessRecompileResponse,
    )
    assert response.runner_request_preparation is (
        response.dynamic_import_local_python_subprocess_recompile.runner_request_preparation
    )
    assert response.runner_attempt_collection is (
        response.dynamic_import_local_python_subprocess_recompile.runner_attempt_collection
    )
    assert response.result_batch_recompile_application is (
        response.dynamic_import_local_python_subprocess_recompile.result_batch_recompile_application
    )
    assert response.result_batch_admission is (
        recompile_application.result_batch_admission
    )
    assert response.non_proof_results is recompile_application.non_proof_results
    assert (
        response.observation_application
        is recompile_application.observation_application
    )
    assert response.recompile_result is recompile_application.recompile_result
    assert response.program is response.observation_application.updated_program
    assert response.program is not previous_response.program
    assert response.compile_result is response.recompile_result.compile_result
    assert response.diagnostic is response.recompile_result.diagnostic
    assert response.compile_total_tokens == response.compile_result.total_tokens
    assert response.compile_budget == previous_response.compile_budget + 160
    assert response.budget_delta == 160
    assert response.newly_selected_unit_ids == (
        response.recompile_result.newly_selected_unit_ids
    )
    assert response.upgraded_unit_ids == response.recompile_result.upgraded_unit_ids
    assert preparation.diagnostic is diagnostic
    assert preparation.request_plan is plan
    assert preparation.execution_input_batch.request_ids == plan.request_ids
    assert (
        preparation.execution_input_batch.inputs[0].replay_artifact.runtime_assumptions
        is runtime_assumptions
    )
    assert preparation.runner_request_batch.runner_environment is runner_environment
    assert preparation.runner_request_batch.runner_assumptions is runner_assumptions
    assert runner_request.request is request
    assert runner_request.runner_contract_revision == "runtime-probe-runner:test.1"
    assert runner_request.timeout_seconds == 30
    assert collection.runner_request_batch is preparation.runner_request_batch
    assert attempt.request is request
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == expected_payload
    assert attempt.failure_summary is None
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.request is request
    assert observed_result.normalized_payload == expected_payload
    assert observed_result.is_admissible_runtime_backed_proof is True
    assert response.non_proof_results == ()
    assert response.result_batch_admission.non_proof_results == ()
    assert response.observation_application.admissions is (
        response.result_batch_admission.admissions
    )
    assert admission.request is request
    assert admission.request_id == observed_result.request_id
    assert tuple(
        (field.key, field.value) for field in admission.observation.normalized_payload
    ) == (("imported_module", "plugins.recompile_subprocess"),)
    assert response.diagnostic.planned_runtime_probe_requests == ()
    assert response.diagnostic.planned_runtime_probe_request_plan == (
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )
    assert boundary.status is SemanticDiagnosticUnitStatus.OMITTED
    assert boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert boundary.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert boundary.has_attached_runtime_provenance is True
    assert selected_trace is not None
    assert selected_trace.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert selected_trace.has_attached_runtime_provenance is True
    assert unsupported_id in response.newly_selected_unit_ids

    response_kwargs = {
        "dynamic_import_local_python_subprocess_recompile": (
            response.dynamic_import_local_python_subprocess_recompile
        ),
        "runner_request_preparation": response.runner_request_preparation,
        "runner_attempt_collection": response.runner_attempt_collection,
        "result_batch_recompile_application": (
            response.result_batch_recompile_application
        ),
        "result_batch_admission": response.result_batch_admission,
        "non_proof_results": response.non_proof_results,
        "observation_application": response.observation_application,
        "recompile_result": response.recompile_result,
        "program": response.program,
        "compile_result": response.compile_result,
        "diagnostic": response.diagnostic,
        "compile_total_tokens": response.compile_total_tokens,
        "compile_budget": response.compile_budget,
        "budget_delta": response.budget_delta,
        "newly_selected_unit_ids": response.newly_selected_unit_ids,
        "upgraded_unit_ids": response.upgraded_unit_ids,
    }

    with pytest.raises(ValueError, match="result_batch_admission must mirror"):
        SemanticDynamicImportLocalPythonSubprocessRecompileResponse(
            **(
                response_kwargs
                | {
                    "result_batch_admission": (
                        runtime_observation_admission.RuntimeProbeResultBatchAdmission(
                            admissions=(),
                            non_proof_results=response.non_proof_results,
                        )
                    )
                }
            )
        )

    with pytest.raises(ValueError, match="compile_budget must mirror"):
        SemanticDynamicImportLocalPythonSubprocessRecompileResponse(
            **(response_kwargs | {"compile_budget": response.compile_budget + 1})
        )


def test_dynamic_import_local_python_subprocess_recompile_facade_delegates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards every explicit caller input to the internal helper."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        _plan,
        _request,
        _unsupported_id,
    ) = _dynamic_import_local_python_subprocess_recompile_facade_fixture(tmp_path)
    repository_snapshot_basis = _snapshot_basis()
    runtime_assumptions = _runner_runtime_assumptions()
    runner_environment = _local_python_runner_environment(tmp_path)
    runner_assumptions = _runner_assumptions()
    calls: list[tuple[object, ...]] = []
    returned_results: list[
        runtime_observation_recompile.RuntimeProbeRunnerCallableRecompileApplication
    ] = []

    def embed_fn(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _text in texts]

    def fake_apply(
        program: SemanticProgram,
        received_diagnostic: SemanticDiagnosticResult,
        previous_result: SemanticCompileResult,
        received_miss_evidence: SemanticMissEvidence,
        delta_budget: int,
        *,
        python_executable: str,
        invocation_contract_revision: str,
        completion_contract_revision: str,
        repository_snapshot_basis: RepositorySnapshotBasis,
        probe_contract_revision: str,
        runtime_assumptions: tuple[
            runtime_probe_results.RuntimeProbeReplayField,
            ...,
        ],
        runner_contract_revision: str,
        timeout_seconds: int,
        runner_environment: tuple[
            runtime_probe_results.RuntimeProbeReplayField,
            ...,
        ],
        runner_assumptions: tuple[
            runtime_probe_results.RuntimeProbeReplayField,
            ...,
        ],
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> runtime_observation_recompile.RuntimeProbeRunnerCallableRecompileApplication:
        calls.append(
            (
                program,
                received_diagnostic,
                previous_result,
                received_miss_evidence,
                delta_budget,
                python_executable,
                invocation_contract_revision,
                completion_contract_revision,
                repository_snapshot_basis,
                probe_contract_revision,
                runtime_assumptions,
                runner_contract_revision,
                timeout_seconds,
                runner_environment,
                runner_assumptions,
                embed_fn,
            )
        )
        preparation = prepare_runtime_probe_runner_requests_for_diagnostic(
            received_diagnostic,
            repository_snapshot_basis=repository_snapshot_basis,
            probe_contract_revision=probe_contract_revision,
            runtime_assumptions=runtime_assumptions,
            runner_contract_revision=runner_contract_revision,
            timeout_seconds=timeout_seconds,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )

        def runner(
            runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
        ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
            return _probe_execution_attempt(
                runner_request,
                normalized_payload=(
                    _probe_field("imported_module", "plugins.recompile_subprocess"),
                ),
            )

        collection = collect_runtime_probe_execution_attempts_from_runner_requests(
            preparation.runner_request_batch,
            runner,
        )
        result_batch_recompile_application = (
            apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
                program,
                received_diagnostic,
                collection.result_batch,
                previous_result,
                received_miss_evidence,
                delta_budget,
                embed_fn=embed_fn,
            )
        )
        runner_recompile = (
            runtime_observation_recompile.RuntimeProbeRunnerCallableRecompileApplication
        )
        result = runner_recompile(
            runner_request_preparation=preparation,
            runner_attempt_collection=collection,
            result_batch_recompile_application=result_batch_recompile_application,
        )
        returned_results.append(result)
        return result

    monkeypatch.setattr(
        tool_facade,
        "apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile",
        fake_apply,
    )

    response = recompile_repository_context_with_dynamic_import_local_python_subprocess(
        SemanticDynamicImportLocalPythonSubprocessRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            miss_evidence=miss_evidence,
            delta_budget=12,
            python_executable="/path/to/python",
            invocation_contract_revision="runtime-probe-invocation:test.1",
            completion_contract_revision="runtime-probe-completion:test.1",
            repository_snapshot_basis=repository_snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=runtime_assumptions,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=7,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
            embed_fn=embed_fn,
        )
    )

    assert calls == [
        (
            previous_response.program,
            diagnostic,
            previous_response.compile_result,
            miss_evidence,
            12,
            "/path/to/python",
            "runtime-probe-invocation:test.1",
            "runtime-probe-completion:test.1",
            repository_snapshot_basis,
            "runtime-probe-contract:test.1",
            runtime_assumptions,
            "runtime-probe-runner:test.1",
            7,
            runner_environment,
            runner_assumptions,
            embed_fn,
        )
    ]
    assert (
        response.dynamic_import_local_python_subprocess_recompile
        is (returned_results[0])
    )
    assert response.runner_request_preparation is (
        returned_results[0].runner_request_preparation
    )
    assert response.runner_attempt_collection is (
        returned_results[0].runner_attempt_collection
    )
    assert response.result_batch_recompile_application is (
        returned_results[0].result_batch_recompile_application
    )
    assert response.compile_budget == previous_response.compile_budget + 12


def test_default_local_python_subprocess_recompile_facade_runs_locals_and_mirrors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The facade runs the real default subprocess path for locals/0."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        plan,
        request,
        unsupported_id,
    ) = _default_local_python_subprocess_recompile_facade_fixture(tmp_path)
    repository_snapshot_basis = _snapshot_basis()
    runtime_assumptions = _runner_runtime_assumptions()
    runner_environment = _local_python_runner_environment(tmp_path)
    runner_assumptions = _runner_assumptions()
    original_run = runtime_probe_execution.subprocess.run
    subprocess_invocations: list[tuple[str, ...]] = []

    def spying_run(*args: object, **kwargs: object) -> object:
        argv = args[0]
        if isinstance(argv, tuple | list):
            subprocess_invocations.append(tuple(str(part) for part in argv))
        else:
            subprocess_invocations.append((str(argv),))
        return original_run(*args, **kwargs)

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", spying_run)

    response = recompile_repository_context_with_default_local_python_subprocess(
        SemanticDefaultLocalPythonSubprocessRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            miss_evidence=miss_evidence,
            delta_budget=160,
            python_executable=sys.executable,
            invocation_contract_revision=(
                "runtime-probe-local-python-subprocess:test.1"
            ),
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
            repository_snapshot_basis=repository_snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=runtime_assumptions,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )
    )
    recompile_application = response.result_batch_recompile_application
    preparation = response.runner_request_preparation
    collection = response.runner_attempt_collection
    runner_request = preparation.runner_request_batch.runner_requests[0]
    attempt = collection.attempts[0]
    observed_result = collection.result_batch.results[0]
    admission = response.observation_application.admissions[0]
    boundary = _boundary_for(response.diagnostic, unsupported_id)
    expected_payload = (_probe_field("lookup_outcome", "returned_namespace"),)
    selected_trace = next(
        selection.trace_summary
        for selection in response.compile_result.optimization.selections
        if selection.unit_id == unsupported_id
    )

    assert subprocess_invocations == [
        (sys.executable, "-m", "context_ir.runtime_probe_worker"),
    ]
    assert isinstance(
        response,
        SemanticDefaultLocalPythonSubprocessRecompileResponse,
    )
    assert response.runner_request_preparation is (
        response.default_local_python_subprocess_recompile.runner_request_preparation
    )
    assert response.runner_attempt_collection is (
        response.default_local_python_subprocess_recompile.runner_attempt_collection
    )
    assert response.result_batch_recompile_application is (
        response.default_local_python_subprocess_recompile.result_batch_recompile_application
    )
    assert response.result_batch_admission is (
        recompile_application.result_batch_admission
    )
    assert response.non_proof_results is recompile_application.non_proof_results
    assert (
        response.observation_application
        is recompile_application.observation_application
    )
    assert response.recompile_result is recompile_application.recompile_result
    assert response.program is response.observation_application.updated_program
    assert response.program is not previous_response.program
    assert response.compile_result is response.recompile_result.compile_result
    assert response.diagnostic is response.recompile_result.diagnostic
    assert response.compile_total_tokens == response.compile_result.total_tokens
    assert response.compile_budget == previous_response.compile_budget + 160
    assert response.budget_delta == 160
    assert response.newly_selected_unit_ids == (
        response.recompile_result.newly_selected_unit_ids
    )
    assert response.upgraded_unit_ids == response.recompile_result.upgraded_unit_ids
    assert preparation.diagnostic is diagnostic
    assert preparation.request_plan is plan
    assert preparation.execution_input_batch.request_ids == plan.request_ids
    assert (
        preparation.execution_input_batch.inputs[0].replay_artifact.runtime_assumptions
        is runtime_assumptions
    )
    assert preparation.runner_request_batch.runner_environment is runner_environment
    assert preparation.runner_request_batch.runner_assumptions is runner_assumptions
    assert runner_request.request is request
    assert runner_request.runner_contract_revision == "runtime-probe-runner:test.1"
    assert runner_request.timeout_seconds == 30
    assert collection.runner_request_batch is preparation.runner_request_batch
    assert attempt.request is request
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == expected_payload
    assert attempt.failure_summary is None
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.request is request
    assert observed_result.normalized_payload == expected_payload
    assert observed_result.is_admissible_runtime_backed_proof is True
    assert response.non_proof_results == ()
    assert response.result_batch_admission.non_proof_results == ()
    assert response.observation_application.admissions is (
        response.result_batch_admission.admissions
    )
    assert admission.request is request
    assert admission.request_id == observed_result.request_id
    assert tuple(
        (field.key, field.value) for field in admission.observation.normalized_payload
    ) == (("lookup_outcome", "returned_namespace"),)
    assert response.diagnostic.planned_runtime_probe_requests == ()
    assert response.diagnostic.planned_runtime_probe_request_plan == (
        runtime_probe_requests.build_runtime_probe_request_plan(())
    )
    assert boundary.status is SemanticDiagnosticUnitStatus.OMITTED
    assert boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert boundary.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert boundary.has_attached_runtime_provenance is True
    assert selected_trace is not None
    assert selected_trace.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert selected_trace.has_attached_runtime_provenance is True
    assert unsupported_id in response.newly_selected_unit_ids

    response_kwargs = {
        "default_local_python_subprocess_recompile": (
            response.default_local_python_subprocess_recompile
        ),
        "runner_request_preparation": response.runner_request_preparation,
        "runner_attempt_collection": response.runner_attempt_collection,
        "result_batch_recompile_application": (
            response.result_batch_recompile_application
        ),
        "result_batch_admission": response.result_batch_admission,
        "non_proof_results": response.non_proof_results,
        "observation_application": response.observation_application,
        "recompile_result": response.recompile_result,
        "program": response.program,
        "compile_result": response.compile_result,
        "diagnostic": response.diagnostic,
        "compile_total_tokens": response.compile_total_tokens,
        "compile_budget": response.compile_budget,
        "budget_delta": response.budget_delta,
        "newly_selected_unit_ids": response.newly_selected_unit_ids,
        "upgraded_unit_ids": response.upgraded_unit_ids,
    }

    with pytest.raises(ValueError, match="result_batch_admission must mirror"):
        SemanticDefaultLocalPythonSubprocessRecompileResponse(
            **(
                response_kwargs
                | {
                    "result_batch_admission": (
                        runtime_observation_admission.RuntimeProbeResultBatchAdmission(
                            admissions=(),
                            non_proof_results=response.non_proof_results,
                        )
                    )
                }
            )
        )

    with pytest.raises(ValueError, match="compile_budget must mirror"):
        SemanticDefaultLocalPythonSubprocessRecompileResponse(
            **(response_kwargs | {"compile_budget": response.compile_budget + 1})
        )


def test_default_local_python_subprocess_recompile_facade_runs_exact_hasattr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The facade carries exact hasattr replay inputs through default subprocess."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        plan,
        request,
        unsupported_id,
    ) = _default_local_python_subprocess_hasattr_facade_fixture(tmp_path)
    runtime_assumptions = _runner_runtime_assumptions()
    runner_environment = _local_python_runner_environment(tmp_path)
    runner_assumptions = _runner_assumptions()
    original_run = runtime_probe_execution.subprocess.run
    subprocess_invocations: list[tuple[str, ...]] = []

    def spying_run(*args: object, **kwargs: object) -> object:
        argv = args[0]
        if isinstance(argv, tuple | list):
            subprocess_invocations.append(tuple(str(part) for part in argv))
        else:
            subprocess_invocations.append((str(argv),))
        return original_run(*args, **kwargs)

    monkeypatch.setattr(runtime_probe_execution.subprocess, "run", spying_run)

    response = recompile_repository_context_with_default_local_python_subprocess(
        SemanticDefaultLocalPythonSubprocessRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            miss_evidence=miss_evidence,
            delta_budget=160,
            python_executable=sys.executable,
            invocation_contract_revision=(
                "runtime-probe-local-python-subprocess:test.1"
            ),
            completion_contract_revision=(
                "runtime-probe-local-python-completion:test.1"
            ),
            repository_snapshot_basis=_snapshot_basis(),
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=runtime_assumptions,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=30,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )
    )
    preparation = response.runner_request_preparation
    collection = response.runner_attempt_collection
    runner_request = preparation.runner_request_batch.runner_requests[0]
    attempt = collection.attempts[0]
    observed_result = collection.result_batch.results[0]
    admission = response.observation_application.admissions[0]
    boundary = _boundary_for(response.diagnostic, unsupported_id)
    expected_payload = (_probe_field("attribute_present", "true"),)
    expected_replay_inputs = (
        _probe_field("object_type", "builtins.int"),
        _probe_field("attribute_name", "bit_length"),
    )

    assert subprocess_invocations == [
        (sys.executable, "-m", "context_ir.runtime_probe_worker"),
    ]
    assert preparation.request_plan is plan
    assert runner_request.request is request
    assert runner_request.replay_artifact.replay_inputs[-2:] == expected_replay_inputs
    assert attempt.request is request
    assert attempt.outcome is runtime_probe_results.RuntimeProbeResultOutcome.OBSERVED
    assert attempt.normalized_payload == expected_payload
    assert attempt.observed_replay_inputs == ()
    assert isinstance(observed_result, runtime_probe_results.RuntimeProbeObservedResult)
    assert observed_result.request is request
    assert observed_result.normalized_payload == expected_payload
    assert observed_result.replay_artifact.replay_inputs[-2:] == expected_replay_inputs
    assert admission.request is request
    assert tuple(
        (field.key, field.value) for field in admission.observation.normalized_payload
    ) == (("attribute_present", "true"),)
    assert tuple(
        (field.key, field.value) for field in admission.observation.replay_inputs[-2:]
    ) == (("object_type", "builtins.int"), ("attribute_name", "bit_length"))
    assert response.non_proof_results == ()
    assert boundary.boundary_kind is (
        SemanticDiagnosticBoundaryKind.UNSUPPORTED_OPAQUE_WITH_ATTACHED_RUNTIME_SUPPORT
    )
    assert boundary.has_attached_runtime_provenance is True
    assert unsupported_id in response.newly_selected_unit_ids


def test_default_local_python_subprocess_recompile_facade_delegates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards every explicit caller input to the default helper."""
    (
        previous_response,
        miss_evidence,
        diagnostic,
        _plan,
        _request,
        _unsupported_id,
    ) = _default_local_python_subprocess_recompile_facade_fixture(tmp_path)
    repository_snapshot_basis = _snapshot_basis()
    runtime_assumptions = _runner_runtime_assumptions()
    runner_environment = _local_python_runner_environment(tmp_path)
    runner_assumptions = _runner_assumptions()
    calls: list[tuple[object, ...]] = []
    returned_results: list[
        runtime_observation_recompile.RuntimeProbeRunnerCallableRecompileApplication
    ] = []

    def embed_fn(texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _text in texts]

    def fake_apply(
        program: SemanticProgram,
        received_diagnostic: SemanticDiagnosticResult,
        previous_result: SemanticCompileResult,
        received_miss_evidence: SemanticMissEvidence,
        delta_budget: int,
        *,
        python_executable: str,
        invocation_contract_revision: str,
        completion_contract_revision: str,
        repository_snapshot_basis: RepositorySnapshotBasis,
        probe_contract_revision: str,
        runtime_assumptions: tuple[
            runtime_probe_results.RuntimeProbeReplayField,
            ...,
        ],
        runner_contract_revision: str,
        timeout_seconds: int,
        runner_environment: tuple[
            runtime_probe_results.RuntimeProbeReplayField,
            ...,
        ],
        runner_assumptions: tuple[
            runtime_probe_results.RuntimeProbeReplayField,
            ...,
        ],
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> runtime_observation_recompile.RuntimeProbeRunnerCallableRecompileApplication:
        calls.append(
            (
                program,
                received_diagnostic,
                previous_result,
                received_miss_evidence,
                delta_budget,
                python_executable,
                invocation_contract_revision,
                completion_contract_revision,
                repository_snapshot_basis,
                probe_contract_revision,
                runtime_assumptions,
                runner_contract_revision,
                timeout_seconds,
                runner_environment,
                runner_assumptions,
                embed_fn,
            )
        )
        preparation = prepare_runtime_probe_runner_requests_for_diagnostic(
            received_diagnostic,
            repository_snapshot_basis=repository_snapshot_basis,
            probe_contract_revision=probe_contract_revision,
            runtime_assumptions=runtime_assumptions,
            runner_contract_revision=runner_contract_revision,
            timeout_seconds=timeout_seconds,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
        )

        def runner(
            runner_request: runtime_probe_execution.RuntimeProbeRunnerRequest,
        ) -> runtime_probe_execution.RuntimeProbeExecutionAttempt:
            return _probe_execution_attempt(
                runner_request,
                normalized_payload=(
                    _probe_field("lookup_outcome", "returned_namespace"),
                ),
            )

        collection = collect_runtime_probe_execution_attempts_from_runner_requests(
            preparation.runner_request_batch,
            runner,
        )
        result_batch_recompile_application = (
            apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
                program,
                received_diagnostic,
                collection.result_batch,
                previous_result,
                received_miss_evidence,
                delta_budget,
                embed_fn=embed_fn,
            )
        )
        runner_recompile = (
            runtime_observation_recompile.RuntimeProbeRunnerCallableRecompileApplication
        )
        result = runner_recompile(
            runner_request_preparation=preparation,
            runner_attempt_collection=collection,
            result_batch_recompile_application=result_batch_recompile_application,
        )
        returned_results.append(result)
        return result

    monkeypatch.setattr(
        tool_facade,
        "apply_default_local_python_subprocess_for_diagnostic_and_recompile",
        fake_apply,
    )

    response = recompile_repository_context_with_default_local_python_subprocess(
        SemanticDefaultLocalPythonSubprocessRecompileRequest(
            previous_response=previous_response,
            diagnostic=diagnostic,
            miss_evidence=miss_evidence,
            delta_budget=12,
            python_executable="/path/to/python",
            invocation_contract_revision="runtime-probe-invocation:test.1",
            completion_contract_revision="runtime-probe-completion:test.1",
            repository_snapshot_basis=repository_snapshot_basis,
            probe_contract_revision="runtime-probe-contract:test.1",
            runtime_assumptions=runtime_assumptions,
            runner_contract_revision="runtime-probe-runner:test.1",
            timeout_seconds=7,
            runner_environment=runner_environment,
            runner_assumptions=runner_assumptions,
            embed_fn=embed_fn,
        )
    )

    assert calls == [
        (
            previous_response.program,
            diagnostic,
            previous_response.compile_result,
            miss_evidence,
            12,
            "/path/to/python",
            "runtime-probe-invocation:test.1",
            "runtime-probe-completion:test.1",
            repository_snapshot_basis,
            "runtime-probe-contract:test.1",
            runtime_assumptions,
            "runtime-probe-runner:test.1",
            7,
            runner_environment,
            runner_assumptions,
            embed_fn,
        )
    ]
    assert response.default_local_python_subprocess_recompile is (returned_results[0])
    assert response.runner_request_preparation is (
        returned_results[0].runner_request_preparation
    )
    assert response.runner_attempt_collection is (
        returned_results[0].runner_attempt_collection
    )
    assert response.result_batch_recompile_application is (
        returned_results[0].result_batch_recompile_application
    )
    assert response.compile_budget == previous_response.compile_budget + 12


def test_compile_repository_context_returns_typed_response_for_simple_repo(
    tmp_path: Path,
) -> None:
    """The facade returns the semantic program and compile result together."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def run() -> None:
                helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="run helper",
            budget=1000,
        )
    )

    assert isinstance(response, SemanticContextResponse)
    assert isinstance(response.program, SemanticProgram)
    assert isinstance(response.compile_result, SemanticCompileResult)
    assert response.program.repo_root == tmp_path
    assert response.compile_result.compile_context == SemanticCompileContext(
        query="run helper"
    )
    assert response.compile_budget == 1000
    assert response.compile_total_tokens == response.compile_result.total_tokens


def test_compile_repository_context_uses_analyzer_and_semantic_compiler(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade keeps analyzer calls unchanged when runtime data is omitted."""
    calls: list[str] = []
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    selection = SemanticSelectionRecord(
        unit_id="unit:one",
        detail="identity",
        token_count=0,
        basis=SelectionBasis.HEURISTIC_CANDIDATE,
        reason="fake trace",
        edit_score=0.1,
        support_score=0.0,
    )
    warning = SemanticOptimizationWarning(
        code=SemanticOptimizationWarningCode.BUDGET_PRESSURE,
        message="fake warning",
        unit_id="unit:one",
    )
    optimization = SemanticOptimizationResult(
        selections=(selection,),
        omitted_unit_ids=("unit:two",),
        warnings=(warning,),
        total_tokens=0,
        budget=64,
        confidence=0.5,
    )
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nfake",
        optimization=optimization,
        omitted_unit_ids=("unit:two",),
        total_tokens=6,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )

    def injected_embed(texts: list[str]) -> list[list[float]]:
        """Return deterministic vectors for pass-through verification."""
        return [[0.0] for _ in texts]

    def fake_analyze(repo_root: Path | str) -> SemanticProgram:
        calls.append(f"analyze:{repo_root}")
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        calls.append(f"compile:{query}:{budget}")
        assert received_program is program
        assert embed_fn is injected_embed
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=str(tmp_path),
            query="query",
            budget=64,
            embed_fn=injected_embed,
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert response.selection_trace == (selection,)
    assert response.optimization_warnings == (warning,)
    assert response.omitted_unit_ids == ("unit:two",)
    assert calls == [f"analyze:{tmp_path}", "compile:query:64"]


def test_compile_repository_context_forwards_dynamic_import_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards accepted runtime observations to the analyzer seam."""
    observation = _dynamic_import_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nruntime-backed",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.DynamicImportRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        dynamic_import_runtime_observations: tuple[
            runtime_acquisition.DynamicImportRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, dynamic_import_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            dynamic_import_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_builtin_dynamic_import_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching builtin import runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(name: str) -> None:
                __import__(name)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "__import__(name)"
    )
    observation = _dynamic_import_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="dynamic import",
            budget=160,
            dynamic_import_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_dynamic_import_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_eval_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``eval`` observations to the analyzer seam."""
    observation = _eval_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nruntime-backed",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.EvalRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        eval_runtime_observations: tuple[
            runtime_acquisition.EvalRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, eval_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            eval_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_eval_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``eval`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(source: str, globals_ns: dict[str, object]) -> None:
                eval(source)
                eval(source, globals_ns)
                exec(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "eval(source)"
    )
    observation = _eval_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="eval runtime",
            budget=160,
            eval_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_eval_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_exec_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``exec`` observations to the analyzer seam."""
    observation = _exec_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nruntime-backed",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.ExecRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        exec_runtime_observations: tuple[
            runtime_acquisition.ExecRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, exec_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            exec_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_exec_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``exec`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(
                source: str,
                globals_ns: dict[str, object],
                locals_ns: dict[str, object],
            ) -> None:
                exec(source)
                exec(source, globals_ns)
                exec(source, globals_ns, locals_ns)
                eval(source)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "exec(source)"
    )
    observation = _exec_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="exec runtime",
            budget=160,
            exec_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_exec_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_hasattr_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``hasattr`` observations to the analyzer seam."""
    observation = _hasattr_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nruntime-backed",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.HasattrRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        hasattr_runtime_observations: tuple[
            runtime_acquisition.HasattrRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, hasattr_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            hasattr_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_hasattr_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``hasattr`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object, name: str) -> None:
                hasattr(obj, name)
                hasattr(obj)
                vars(obj)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "hasattr(obj, name)"
    )
    observation = _hasattr_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="hasattr runtime",
            budget=160,
            hasattr_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_hasattr_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_getattr_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``getattr`` observations to the analyzer seam."""
    observation = _getattr_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nruntime-backed",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.GetattrRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        getattr_runtime_observations: tuple[
            runtime_acquisition.GetattrRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, getattr_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            getattr_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_getattr_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``getattr`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object, name: str, default: object) -> None:
                getattr(obj, name)
                getattr(obj, name, default)
                getattr()
                hasattr(obj, name)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "getattr(obj, name, default)"
    )
    observation = _getattr_runtime_observation_for_site(
        construct.site,
        lookup_outcome="returned_default_value",
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="getattr runtime",
            budget=160,
            getattr_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_getattr_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_vars_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``vars`` observations to the analyzer seam."""
    observation = _vars_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nruntime-backed",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.VarsRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        vars_runtime_observations: tuple[
            runtime_acquisition.VarsRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, vars_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            vars_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_vars_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``vars`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object) -> None:
                vars(obj)
                vars()
                dir(obj)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "vars(obj)"
    )
    observation = _vars_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="vars runtime",
            budget=160,
            vars_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_vars_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_attaches_vars_runtime_provenance_for_zero_arg_vars(
    tmp_path: Path,
) -> None:
    """The facade attaches runtime-backed proof for the bounded ``vars()`` branch."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object) -> None:
                vars(obj)
                vars()
                dir(obj)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "vars()"
    )
    observation = _vars_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="vars runtime",
            budget=160,
            vars_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_vars_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_globals_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``globals()`` observations to the analyzer seam."""
    observation = _globals_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nglobals runtime",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.GlobalsRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        globals_runtime_observations: tuple[
            runtime_acquisition.GlobalsRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, globals_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            globals_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_globals_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``globals()`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object) -> None:
                globals()
                locals()
                vars()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "globals()"
    )
    observation = _globals_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="globals runtime",
            budget=160,
            globals_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_globals_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_locals_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``locals()`` observations to the analyzer seam."""
    observation = _locals_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nlocals runtime",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.LocalsRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        locals_runtime_observations: tuple[
            runtime_acquisition.LocalsRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, locals_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            locals_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_locals_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``locals()`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object) -> None:
                globals()
                locals()
                vars()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "locals()"
    )
    observation = _locals_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="locals runtime",
            budget=160,
            locals_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_locals_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_setattr_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``setattr`` observations to the analyzer seam."""
    observation = _setattr_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nsetattr runtime",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.SetattrRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        setattr_runtime_observations: tuple[
            runtime_acquisition.SetattrRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, setattr_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            setattr_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_setattr_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``setattr`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object, name: str, value: object) -> None:
                setattr(obj, name, value)
                setattr(obj, name)
                delattr(obj, name)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "setattr(obj, name, value)"
    )
    observation = _setattr_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="setattr runtime",
            budget=160,
            setattr_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_setattr_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_delattr_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``delattr`` observations to the analyzer seam."""
    observation = _delattr_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\ndelattr runtime",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.DelattrRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        delattr_runtime_observations: tuple[
            runtime_acquisition.DelattrRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, delattr_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            delattr_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_delattr_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``delattr`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object, name: str, value: object) -> None:
                delattr(obj, name)
                delattr(obj)
                setattr(obj, name, value)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "delattr(obj, name)"
    )
    observation = _delattr_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="delattr runtime",
            budget=160,
            delattr_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_delattr_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_forwards_dir_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards bounded ``dir`` observations to the analyzer seam."""
    observation = _dir_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\ndir runtime",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.DirRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        dir_runtime_observations: tuple[
            runtime_acquisition.DirRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, dir_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            dir_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_dir_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching ``dir`` runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def run(obj: object) -> None:
                dir(obj)
                dir()
                vars(obj)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    constructs_by_text = {
        construct.construct_text: construct
        for construct in base_program.unsupported_constructs
    }
    observations = (
        _dir_runtime_observation_for_site(constructs_by_text["dir(obj)"].site),
        _dir_runtime_observation_for_site(
            constructs_by_text["dir()"].site,
            listing_entry_count=None,
        ),
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="dir runtime",
            budget=160,
            dir_runtime_observations=observations,
        )
    )
    expected_program = runtime_acquisition.attach_dir_runtime_provenance(
        base_program,
        observations,
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert len(response.program.provenance_records) == 2
    records_by_subject_id = {
        record.subject_id: record for record in response.program.provenance_records
    }
    assert {
        constructs_by_text["dir(obj)"].construct_id,
        constructs_by_text["dir()"].construct_id,
    } == set(records_by_subject_id)
    for record in records_by_subject_id.values():
        assert (
            record.subject_kind
            is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
        )


def test_compile_repository_context_forwards_metaclass_behavior_runtime_observations(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade forwards metaclass observations to the analyzer seam."""
    observation = _metaclass_behavior_runtime_observation()
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nmetaclass runtime",
        optimization=SemanticOptimizationResult(
            selections=(),
            omitted_unit_ids=(),
            warnings=(),
            total_tokens=0,
            budget=64,
            confidence=0.5,
        ),
        omitted_unit_ids=(),
        total_tokens=8,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    analyzer_calls: list[
        tuple[
            Path | str,
            tuple[runtime_acquisition.MetaclassBehaviorRuntimeObservation, ...],
        ]
    ] = []

    def fake_analyze(
        repo_root: Path | str,
        *,
        metaclass_behavior_runtime_observations: tuple[
            runtime_acquisition.MetaclassBehaviorRuntimeObservation, ...
        ] = (),
    ) -> SemanticProgram:
        analyzer_calls.append((repo_root, metaclass_behavior_runtime_observations))
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        assert received_program is program
        assert query == "query"
        assert budget == 64
        assert embed_fn is None
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="query",
            budget=64,
            metaclass_behavior_runtime_observations=(observation,),
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert analyzer_calls == [(tmp_path, (observation,))]


def test_compile_repository_context_attaches_metaclass_behavior_runtime_provenance(
    tmp_path: Path,
) -> None:
    """The facade preserves unsupported truth while attaching metaclass runtime."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            class Base:
                pass

            class Meta(type):
                pass

            class Holder:
                Meta = Meta

            class Example(Base, metaclass=Holder.Meta):
                pass
            """
        ).lstrip(),
        encoding="utf-8",
    )

    base_program = context_ir.analyze_repository(tmp_path)
    construct = next(
        candidate
        for candidate in base_program.unsupported_constructs
        if candidate.construct_text == "metaclass=Holder.Meta"
    )
    observation = _metaclass_behavior_runtime_observation_for_site(construct.site)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="metaclass runtime",
            budget=160,
            metaclass_behavior_runtime_observations=(observation,),
        )
    )
    expected_program = runtime_acquisition.attach_metaclass_behavior_runtime_provenance(
        base_program,
        [observation],
    )

    assert response.program == expected_program
    assert response.unsupported_constructs == tuple(base_program.unsupported_constructs)
    assert response.program.unresolved_frontier == base_program.unresolved_frontier
    assert len(response.program.provenance_records) == 1
    [record] = response.program.provenance_records
    assert record.subject_kind is semantic_types.SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.subject_id == construct.construct_id


def test_compile_repository_context_exposes_uncertainty_and_unsupported_constructs(
    tmp_path: Path,
) -> None:
    """Frontier and unsupported lower-layer surfaces remain explicit."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.helpers import *
            from pkg.helpers import helper

            def run() -> None:
                helper()
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="run missing_call from pkg.helpers import *",
            budget=1000,
        )
    )

    assert response.unresolved_frontier == tuple(response.program.unresolved_frontier)
    assert response.unsupported_constructs == tuple(
        response.program.unsupported_constructs
    )
    assert any(
        access.access_text == "missing_call"
        and access.context is ReferenceContext.CALL
        and access.reason_code is UnresolvedReasonCode.UNRESOLVED_NAME
        for access in response.unresolved_frontier
    )
    assert any(
        construct.construct_text == "from pkg.helpers import *"
        and construct.reason_code is UnresolvedReasonCode.STAR_IMPORT
        for construct in response.unsupported_constructs
    )
    assert "unresolved:" in response.compile_result.document
    assert "unsupported construct" in response.compile_result.document
    assert "text: from pkg.helpers import *" in response.compile_result.document


def test_compile_repository_context_preserves_parse_error_truthfulness(
    tmp_path: Path,
) -> None:
    """Parse-error files stay visible without gaining semantic facts."""
    (tmp_path / "good.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text(
        "from good import VALUE\nclass Broken(\n",
        encoding="utf-8",
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="VALUE",
            budget=1000,
        )
    )

    assert response.syntax_diagnostics == tuple(response.program.syntax.diagnostics)
    assert {"file:good.py", "file:bad.py"}.issubset(
        response.program.syntax.source_files
    )
    assert any(
        diagnostic.code is SyntaxDiagnosticCode.PARSE_ERROR
        and diagnostic.file_id == "file:bad.py"
        for diagnostic in response.syntax_diagnostics
    )
    assert all(
        symbol.file_id != "file:bad.py"
        for symbol in response.program.resolved_symbols.values()
    )
    assert all(
        binding.site.file_path != "bad.py" for binding in response.program.bindings
    )
    assert all(
        reference.site.file_path != "bad.py"
        for reference in response.program.resolved_references
    )
    assert all(
        access.site.file_path != "bad.py" for access in response.unresolved_frontier
    )
    assert all(
        construct.site.file_path != "bad.py"
        for construct in response.unsupported_constructs
    )


def test_compile_repository_context_preserves_budget_honesty(
    tmp_path: Path,
) -> None:
    """Facade totals mirror the underlying compile result and requested budget."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def run() -> None:
                helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="run",
            budget=200,
        )
    )

    assert response.compile_budget == response.compile_result.budget == 200
    assert response.compile_total_tokens == response.compile_result.total_tokens
    assert response.compile_total_tokens == _estimate_tokens(
        response.compile_result.document
    )
    assert response.compile_total_tokens <= response.compile_budget
    assert (
        response.compile_result.optimization.total_tokens
        <= response.compile_total_tokens
    )


def test_compile_repository_context_does_not_call_retired_graph_first_apis(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade does not route through retired graph-first entry points."""
    (tmp_path / "main.py").write_text(
        "def run() -> None:\n    return None\n",
        encoding="utf-8",
    )

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("retired graph-first API was called")

    monkeypatch.setattr(legacy_parser, "parse_file", fail)
    monkeypatch.setattr(legacy_parser, "parse_repository", fail)
    monkeypatch.setattr(legacy_scorer, "score_graph", fail)
    monkeypatch.setattr(legacy_optimizer, "optimize", fail)
    monkeypatch.setattr(legacy_renderer, "render", fail)
    monkeypatch.setattr(legacy_compiler, "compile", fail)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="run",
            budget=200,
        )
    )

    assert isinstance(response, SemanticContextResponse)


def test_tool_facade_does_not_change_package_root_exports() -> None:
    """The facade remains an explicit module API rather than a root export."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)

    new_facade_names = {
        "SemanticDefaultLocalPythonSubprocessRecompileRequest",
        "SemanticDefaultLocalPythonSubprocessRecompileResponse",
        "SemanticDynamicImportLocalPythonSubprocessRecompileRequest",
        "SemanticDynamicImportLocalPythonSubprocessRecompileResponse",
        "recompile_repository_context_with_default_local_python_subprocess",
        "recompile_repository_context_with_dynamic_import_local_python_subprocess",
    }
    facade_names = {
        "EmbeddingFunction",
        "SemanticContextRequest",
        "SemanticContextResponse",
        *new_facade_names,
        "SemanticRuntimeObservationRecompileRequest",
        "SemanticRuntimeObservationRecompileResponse",
        "compile_repository_context",
        "recompile_repository_context_with_runtime_observations",
    }

    assert new_facade_names.issubset(set(tool_facade.__all__))
    assert facade_names.issubset(set(tool_facade.__all__))
    assert facade_names.isdisjoint(context_ir.__all__)
    assert not hasattr(context_ir, "SemanticContextRequest")
    assert not hasattr(context_ir, "SemanticContextResponse")
    assert not hasattr(
        context_ir,
        "SemanticDefaultLocalPythonSubprocessRecompileRequest",
    )
    assert not hasattr(
        context_ir,
        "SemanticDefaultLocalPythonSubprocessRecompileResponse",
    )
    assert not hasattr(
        context_ir,
        "SemanticDynamicImportLocalPythonSubprocessRecompileRequest",
    )
    assert not hasattr(
        context_ir,
        "SemanticDynamicImportLocalPythonSubprocessRecompileResponse",
    )
    assert not hasattr(context_ir, "SemanticRuntimeObservationRecompileRequest")
    assert not hasattr(context_ir, "SemanticRuntimeObservationRecompileResponse")
    assert not hasattr(context_ir, "compile_repository_context")
    assert not hasattr(
        context_ir,
        "recompile_repository_context_with_default_local_python_subprocess",
    )
    assert not hasattr(
        context_ir,
        "recompile_repository_context_with_dynamic_import_local_python_subprocess",
    )
    assert not hasattr(
        context_ir,
        "recompile_repository_context_with_runtime_observations",
    )
    assert tuple(mcp_server.__all__) == (
        "MCP_SERVER",
        "compile_repository_context",
        "run_stdio_server",
    )
    assert new_facade_names.isdisjoint(mcp_server.__all__)
    for facade_name in new_facade_names:
        assert not hasattr(mcp_server, facade_name)

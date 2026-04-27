"""Tool-facing facade tests for semantic repository compilation."""

from __future__ import annotations

import hashlib
import textwrap
from pathlib import Path

import context_ir
import context_ir.compiler as legacy_compiler
import context_ir.optimizer as legacy_optimizer
import context_ir.parser as legacy_parser
import context_ir.renderer as legacy_renderer
import context_ir.runtime_acquisition as runtime_acquisition
import context_ir.scorer as legacy_scorer
import context_ir.semantic_types as semantic_types
import context_ir.tool_facade as tool_facade
from context_ir.semantic_types import (
    ReferenceContext,
    RepositorySnapshotBasis,
    RuntimeAttachmentLink,
    SelectionBasis,
    SemanticCompileContext,
    SemanticCompileResult,
    SemanticOptimizationResult,
    SemanticOptimizationWarning,
    SemanticOptimizationWarningCode,
    SemanticProgram,
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
    compile_repository_context,
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

    facade_names = {
        "EmbeddingFunction",
        "SemanticContextRequest",
        "SemanticContextResponse",
        "compile_repository_context",
    }

    assert facade_names.isdisjoint(context_ir.__all__)
    assert not hasattr(context_ir, "SemanticContextRequest")
    assert not hasattr(context_ir, "SemanticContextResponse")
    assert not hasattr(context_ir, "compile_repository_context")

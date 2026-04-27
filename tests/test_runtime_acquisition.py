"""Tests for runtime-backed provenance attachment infrastructure."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

import context_ir.runtime_acquisition as runtime_acquisition
from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_types import (
    CallSiteFact,
    CapabilityTier,
    DependencyProofKind,
    EvidenceOriginKind,
    ReferenceContext,
    ReplayStatus,
    RepositorySnapshotBasis,
    ResolvedSymbol,
    ResolvedSymbolKind,
    RuntimeAttachmentLink,
    SemanticDependency,
    SemanticDependencyKind,
    SemanticProgram,
    SemanticProvenanceRecord,
    SemanticSubjectKind,
    SourceSite,
    SourceSpan,
    SyntaxProgram,
    UnresolvedAccess,
    UnresolvedReasonCode,
    UnsupportedConstruct,
)


def make_site(site_id: str, path: str = "pkg/runtime.py") -> SourceSite:
    """Create a stable source site for runtime acquisition tests."""
    return SourceSite(
        site_id=site_id,
        file_path=path,
        span=SourceSpan(start_line=1, start_column=0, end_line=1, end_column=12),
        snippet="pass",
    )


def _derived_program(tmp_path: Path) -> SemanticProgram:
    """Run the accepted lower layers through frontier derivation."""
    syntax = extract_syntax(tmp_path)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


def _dynamic_import_runtime_observation(
    site: SourceSite,
    *,
    imported_module: str,
) -> runtime_acquisition.DynamicImportRuntimeObservation:
    """Create one admissible dynamic-import runtime observation for a source site."""
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
                attachment_id=f"attachment:{site.site_id}:trace",
                attachment_role="trace",
                description="dynamic import trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        runtime_assumptions=(
            runtime_acquisition._RuntimeObservationField(
                key="python",
                value="3.11",
            ),
        ),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="imported_module",
                value=imported_module,
            ),
        ),
    )


def _eval_runtime_observation(
    site: SourceSite,
    *,
    evaluation_outcome: str = "returned_value",
    source_shape: str = "literal_expression",
    source_text: str = '"runtime-value"',
    source_sha256: str | None = None,
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.EvalRuntimeObservation:
    """Create one admissible ``eval(source)`` runtime observation."""
    durable_reference = durable_payload_reference
    if durable_reference is None:
        durable_reference = f"artifact://eval-result/{site.site_id}.json"
    source_digest = source_sha256
    if source_digest is None:
        source_digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
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
                attachment_id=f"attachment:{site.site_id}:trace",
                attachment_role="trace",
                description="eval trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        replay_inputs=(
            runtime_acquisition._RuntimeObservationField(
                key="source_shape",
                value=source_shape,
            ),
            runtime_acquisition._RuntimeObservationField(
                key="source_sha256",
                value=source_digest,
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


def _exec_runtime_observation(
    site: SourceSite,
    *,
    execution_outcome: str = "completed",
    source_shape: str = "literal_statement",
    source_text: str = "pass",
    source_sha256: str | None = None,
    statement_kind: str | None = "pass",
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.ExecRuntimeObservation:
    """Create one admissible ``exec(source)`` runtime observation."""
    durable_reference = durable_payload_reference
    if durable_reference is None:
        durable_reference = f"artifact://exec-result/{site.site_id}.json"
    source_digest = source_sha256
    if source_digest is None:
        source_digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    normalized_payload = [
        runtime_acquisition._RuntimeObservationField(
            key="execution_outcome",
            value=execution_outcome,
        ),
    ]
    if statement_kind is not None:
        normalized_payload.append(
            runtime_acquisition._RuntimeObservationField(
                key="statement_kind",
                value=statement_kind,
            )
        )
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
                attachment_id=f"attachment:{site.site_id}:trace",
                attachment_role="trace",
                description="exec trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        replay_inputs=(
            runtime_acquisition._RuntimeObservationField(
                key="source_shape",
                value=source_shape,
            ),
            runtime_acquisition._RuntimeObservationField(
                key="source_sha256",
                value=source_digest,
            ),
        ),
        normalized_payload=tuple(normalized_payload),
        durable_payload_reference=durable_reference,
    )


def _hasattr_runtime_observation(
    site: SourceSite,
    *,
    attribute_present: bool,
) -> runtime_acquisition.HasattrRuntimeObservation:
    """Create one admissible ``hasattr`` runtime observation for a source site."""
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
                attachment_id=f"attachment:{site.site_id}:trace",
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


def _getattr_runtime_observation(
    site: SourceSite,
    *,
    lookup_outcome: str,
) -> runtime_acquisition.GetattrRuntimeObservation:
    """Create one admissible ``getattr`` runtime observation for a source site."""
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
                attachment_id=f"attachment:{site.site_id}:trace",
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


def _vars_runtime_observation(
    site: SourceSite,
    *,
    lookup_outcome: str,
) -> runtime_acquisition.VarsRuntimeObservation:
    """Create one admissible ``vars`` runtime observation for a source site."""
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
                attachment_id=f"attachment:{site.site_id}:trace",
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


def _globals_runtime_observation(
    site: SourceSite,
    *,
    lookup_outcome: str = "returned_namespace",
) -> runtime_acquisition.GlobalsRuntimeObservation:
    """Create one admissible ``globals()`` runtime observation for a source site."""
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
                attachment_id=f"attachment:{site.site_id}:trace",
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


def _locals_runtime_observation(
    site: SourceSite,
    *,
    lookup_outcome: str = "returned_namespace",
) -> runtime_acquisition.LocalsRuntimeObservation:
    """Create one admissible ``locals()`` runtime observation for a source site."""
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
                attachment_id=f"attachment:{site.site_id}:trace",
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


def _setattr_runtime_observation(
    site: SourceSite,
    *,
    mutation_outcome: str = "returned_none",
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.SetattrRuntimeObservation:
    """Create one admissible ``setattr(obj, name, value)`` observation."""
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
                attachment_id=f"attachment:{site.site_id}:trace",
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


def _delattr_runtime_observation(
    site: SourceSite,
    *,
    mutation_outcome: str = "deleted_attribute",
) -> runtime_acquisition.DelattrRuntimeObservation:
    """Create one admissible ``delattr(obj, name)`` observation for a source site."""
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
                attachment_id=f"attachment:{site.site_id}:trace",
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


def _dir_runtime_observation(
    site: SourceSite,
    *,
    listing_entry_count: int | None = 3,
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.DirRuntimeObservation:
    """Create one admissible ``dir(obj)`` runtime observation for a source site."""
    durable_reference = durable_payload_reference
    if durable_reference is None:
        durable_reference = f"artifact://dir-listing/{site.site_id}.json"
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
                attachment_id=f"attachment:{site.site_id}:trace",
                attachment_role="trace",
                description="dir trace",
            ),
        ),
        replay_target="main.run",
        replay_selector="call:main.run",
        normalized_payload=normalized_payload,
        durable_payload_reference=durable_reference,
    )


def _metaclass_behavior_runtime_observation(
    site: SourceSite,
    *,
    class_creation_outcome: str = "created_class",
    durable_payload_reference: str | None = None,
) -> runtime_acquisition.MetaclassBehaviorRuntimeObservation:
    """Create one admissible metaclass runtime observation for a source site."""
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
                attachment_id=f"attachment:{site.site_id}:trace",
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


def make_program(
    existing_records: list[SemanticProvenanceRecord] | None = None,
) -> SemanticProgram:
    """Build a minimal semantic program with attachable runtime subjects."""
    repo_root = Path("/tmp/repo")
    syntax = SyntaxProgram(
        repo_root=repo_root,
        call_sites=[
            CallSiteFact(
                call_site_id="call:runner:init",
                enclosing_scope_id="scope:function:pkg.runtime.run",
                site=make_site("site:call:init"),
                callee_text="helper",
                argument_count=0,
            )
        ],
    )
    runner_symbol = ResolvedSymbol(
        symbol_id="sym:pkg.runtime:Runner",
        kind=ResolvedSymbolKind.CLASS,
        qualified_name="pkg.runtime.Runner",
        file_id="file:pkg/runtime.py",
        definition_site=make_site("site:def:runner"),
        defining_scope_id="scope:module:pkg.runtime",
    )
    helper_symbol = ResolvedSymbol(
        symbol_id="sym:pkg.runtime:helper",
        kind=ResolvedSymbolKind.FUNCTION,
        qualified_name="pkg.runtime.helper",
        file_id="file:pkg/runtime.py",
        definition_site=make_site("site:def:helper"),
        defining_scope_id="scope:module:pkg.runtime",
    )
    dependency = SemanticDependency(
        dependency_id="dep:pkg.runtime:runner-helper",
        source_symbol_id=runner_symbol.symbol_id,
        target_symbol_id=helper_symbol.symbol_id,
        kind=SemanticDependencyKind.CALL,
        proof_kind=DependencyProofKind.CALL_RESOLUTION,
        evidence_site_id="site:call:init",
    )
    unresolved = UnresolvedAccess(
        access_id="frontier:pkg.runtime:missing",
        site=make_site("site:frontier:missing"),
        access_text="missing_dependency",
        context=ReferenceContext.CALL,
        enclosing_scope_id="scope:function:pkg.runtime.run",
        reason_code=UnresolvedReasonCode.UNRESOLVED_NAME,
    )
    unsupported = UnsupportedConstruct(
        construct_id="unsupported:pkg.runtime:exec",
        site=make_site("site:unsupported:exec"),
        construct_text="exec(code)",
        reason_code=UnresolvedReasonCode.EXEC_OR_EVAL,
        enclosing_scope_id="scope:function:pkg.runtime.run",
    )
    return SemanticProgram(
        repo_root=repo_root,
        syntax=syntax,
        resolved_symbols={
            runner_symbol.symbol_id: runner_symbol,
            helper_symbol.symbol_id: helper_symbol,
        },
        proven_dependencies=[dependency],
        unresolved_frontier=[unresolved],
        unsupported_constructs=[unsupported],
        provenance_records=[] if existing_records is None else existing_records,
    )


def make_observation(
    *,
    subject_kind: SemanticSubjectKind = SemanticSubjectKind.SYMBOL,
    subject_id: str = "sym:pkg.runtime:Runner",
    outcome: runtime_acquisition._RuntimeObservationOutcome = (
        runtime_acquisition._RuntimeObservationOutcome.OBSERVED
    ),
    normalized_payload: tuple[runtime_acquisition._RuntimeObservationField, ...] = (
        runtime_acquisition._RuntimeObservationField(
            key="observed_state",
            value="initialized",
        ),
    ),
    durable_payload_reference: str | None = None,
) -> runtime_acquisition._RuntimeObservation:
    """Create one admissible runtime observation for attachment tests."""
    return runtime_acquisition._RuntimeObservation(
        subject_kind=subject_kind,
        subject_id=subject_id,
        outcome=outcome,
        probe_identifier="probe:pkg.runtime:init",
        probe_contract_revision="2026-04-18.1",
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
            is_dirty_worktree=False,
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id="attachment:runtime:stdout",
                attachment_role="stdout",
                description="probe stdout",
            ),
            RuntimeAttachmentLink(
                attachment_id="attachment:runtime:trace",
                attachment_role="trace",
                description="probe trace",
            ),
        ),
        replay_target="pkg.runtime.run",
        replay_selector="call:pkg.runtime.run",
        replay_inputs=(
            runtime_acquisition._RuntimeObservationField(
                key="mode",
                value="safe",
            ),
        ),
        runtime_assumptions=(
            runtime_acquisition._RuntimeObservationField(
                key="python",
                value="3.11",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="platform",
                value="linux",
            ),
        ),
        normalized_payload=normalized_payload,
        durable_payload_reference=durable_payload_reference,
    )


def test_attach_runtime_observations_appends_records_without_mutating_input() -> None:
    """Admissible observations append runtime-backed provenance to a new program."""
    program = make_program()
    symbol_observation = make_observation()
    dependency_observation = make_observation(
        subject_kind=SemanticSubjectKind.DEPENDENCY,
        subject_id="dep:pkg.runtime:runner-helper",
        normalized_payload=(),
        durable_payload_reference="artifact://runtime/trace.json",
    )

    updated_program = runtime_acquisition.attach_runtime_observations(
        program,
        [symbol_observation, dependency_observation],
    )

    assert updated_program is not program
    assert program.provenance_records == []
    assert len(updated_program.provenance_records) == 2
    assert updated_program.provenance_records is not program.provenance_records

    symbol_record, dependency_record = updated_program.provenance_records
    assert symbol_record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert symbol_record.evidence_origin is EvidenceOriginKind.RUNTIME_PROBE_IDENTITY
    assert symbol_record.replay_status is ReplayStatus.REPRODUCIBLE_RUNTIME
    assert symbol_record.subject_kind is SemanticSubjectKind.SYMBOL
    assert symbol_record.subject_id == "sym:pkg.runtime:Runner"
    assert [site.site_id for site in symbol_record.subject_sites] == ["site:def:runner"]
    assert symbol_record.evidence_sites == ()

    symbol_origin_detail = json.loads(symbol_record.origin_detail)
    assert symbol_origin_detail["probe_identifier"] == "probe:pkg.runtime:init"
    assert symbol_origin_detail["probe_contract_revision"] == "2026-04-18.1"
    assert symbol_origin_detail["replay_target"] == "pkg.runtime.run"
    assert symbol_origin_detail["replay_selector"] == "call:pkg.runtime.run"
    assert symbol_origin_detail["replay_inputs"] == {"mode": "safe"}
    assert symbol_origin_detail["runtime_assumptions"] == {
        "platform": "linux",
        "python": "3.11",
    }
    assert symbol_origin_detail["normalized_payload"] == {
        "observed_state": "initialized"
    }

    assert dependency_record.subject_kind is SemanticSubjectKind.DEPENDENCY
    assert dependency_record.subject_id == "dep:pkg.runtime:runner-helper"
    assert {site.site_id for site in dependency_record.subject_sites} == {
        "site:def:runner",
        "site:def:helper",
    }
    assert [site.site_id for site in dependency_record.evidence_sites] == [
        "site:call:init"
    ]

    dependency_origin_detail = json.loads(dependency_record.origin_detail)
    assert dependency_origin_detail["normalized_payload"] == {}
    assert (
        dependency_origin_detail["durable_payload_reference"]
        == "artifact://runtime/trace.json"
    )


def test_attach_runtime_observations_rejects_unknown_subject_id() -> None:
    """Runtime-backed provenance may only target known semantic subject IDs."""
    program = make_program()
    observation = make_observation(subject_id="sym:pkg.runtime:Missing")

    with pytest.raises(ValueError, match="unknown subject_id"):
        runtime_acquisition.attach_runtime_observations(program, [observation])


def test_attach_runtime_observations_rejects_duplicate_generated_record_id() -> None:
    """Generated record IDs may not collide with existing provenance records."""
    program = make_program()
    observation = make_observation()
    first_pass = runtime_acquisition.attach_runtime_observations(program, [observation])
    existing_record = first_pass.provenance_records[0]
    program_with_existing = replace(program, provenance_records=[existing_record])

    with pytest.raises(ValueError, match="record_id already exists"):
        runtime_acquisition.attach_runtime_observations(
            program_with_existing,
            [observation],
        )


@pytest.mark.parametrize(
    ("observation", "error_match"),
    [
        (
            replace(make_observation(), probe_identifier=""),
            "probe_identifier must be non-empty",
        ),
        (
            replace(make_observation(), probe_contract_revision=""),
            "probe_contract_revision must be non-empty",
        ),
        (
            replace(make_observation(), repository_snapshot_basis=None),
            "repository_snapshot_basis must be provided",
        ),
        (
            replace(make_observation(), attachment_links=()),
            "attachment_links must be non-empty",
        ),
        (
            replace(
                make_observation(),
                outcome=runtime_acquisition._RuntimeObservationOutcome.CRASHED,
            ),
            "non-admissible runtime observation outcome",
        ),
        (
            replace(
                make_observation(),
                outcome=runtime_acquisition._RuntimeObservationOutcome.TIMED_OUT,
            ),
            "non-admissible runtime observation outcome",
        ),
        (
            replace(
                make_observation(),
                outcome=(
                    runtime_acquisition._RuntimeObservationOutcome.MISSING_ENVIRONMENT
                ),
            ),
            "non-admissible runtime observation outcome",
        ),
        (
            replace(
                make_observation(),
                normalized_payload=(),
                durable_payload_reference=None,
            ),
            "normalized_payload or durable_payload_reference",
        ),
    ],
)
def test_attach_runtime_observations_rejects_incomplete_inputs(
    observation: runtime_acquisition._RuntimeObservation,
    error_match: str,
) -> None:
    """Incomplete or non-admissible observations are rejected explicitly."""
    program = make_program()

    with pytest.raises(ValueError, match=error_match):
        runtime_acquisition.attach_runtime_observations(program, [observation])


@pytest.mark.parametrize(
    ("subject_kind", "subject_id", "subject_site_id"),
    [
        (
            SemanticSubjectKind.FRONTIER_ITEM,
            "frontier:pkg.runtime:missing",
            "site:frontier:missing",
        ),
        (
            SemanticSubjectKind.UNSUPPORTED_FINDING,
            "unsupported:pkg.runtime:exec",
            "site:unsupported:exec",
        ),
    ],
)
def test_attach_runtime_observations_accepts_frontier_and_unsupported_subjects(
    subject_kind: SemanticSubjectKind,
    subject_id: str,
    subject_site_id: str,
) -> None:
    """Runtime-backed provenance may attach to frontier and unsupported subjects."""
    program = make_program()
    observation = make_observation(
        subject_kind=subject_kind,
        subject_id=subject_id,
    )

    updated_program = runtime_acquisition.attach_runtime_observations(
        program,
        [observation],
    )

    [record] = updated_program.provenance_records

    assert record.subject_kind is subject_kind
    assert record.subject_id == subject_id
    assert [site.site_id for site in record.subject_sites] == [subject_site_id]
    assert record.evidence_sites == ()
    assert updated_program.unresolved_frontier == program.unresolved_frontier
    assert updated_program.unsupported_constructs == program.unsupported_constructs


def test_attach_dynamic_import_runtime_provenance_targets_dynamic_import_boundaries(
    tmp_path: Path,
) -> None:
    """Only existing dynamic-import unsupported constructs gain attachments."""
    (tmp_path / "main.py").write_text(
        """
import importlib
import importlib as loader
from importlib import import_module
from importlib import import_module as load_module

def run(name: str, source: str) -> None:
    importlib.import_module(name)
    import_module(name)
    load_module(name)
    loader.import_module(name)
    __import__(name)
    exec(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _dynamic_import_runtime_observation(
            construct.site,
            imported_module=f"observed:{construct.construct_text}",
        )
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_dynamic_import_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    expected_texts = {
        "importlib.import_module(name)",
        "import_module(name)",
        "load_module(name)",
        "loader.import_module(name)",
        "__import__(name)",
    }
    expected_subject_ids = {
        constructs_by_text[construct_text].construct_id
        for construct_text in expected_texts
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == expected_subject_ids
    assert constructs_by_text["exec(source)"].construct_id not in attached_subject_ids

    for record in updated_program.provenance_records:
        construct = next(
            candidate
            for candidate in program.unsupported_constructs
            if candidate.construct_id == record.subject_id
        )
        assert record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
        assert record.capability_tier is CapabilityTier.RUNTIME_BACKED
        assert record.subject_sites == (construct.site,)


def test_attach_eval_runtime_provenance_targets_only_bounded_eval_source(
    tmp_path: Path,
) -> None:
    """Only the exact ``eval(source)`` boundary gains runtime attachments."""
    (tmp_path / "main.py").write_text(
        """
def helper() -> str:
    return "helper"

def run(source: str, suffix: str, globals_ns: dict[str, object]) -> None:
    eval(source)
    eval(source, globals_ns)
    eval(source=source)
    eval("helper()")
    eval(helper())
    eval(source + suffix)
    exec(source)
    getattr(source, "strip")
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _eval_runtime_observation(construct.site)
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_eval_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {constructs_by_text["eval(source)"].construct_id}
    assert (
        constructs_by_text["eval(source, globals_ns)"].construct_id
        not in attached_subject_ids
    )
    assert (
        constructs_by_text["eval(source=source)"].construct_id
        not in attached_subject_ids
    )
    assert (
        constructs_by_text['eval("helper()")'].construct_id not in attached_subject_ids
    )
    assert constructs_by_text["eval(helper())"].construct_id not in attached_subject_ids
    assert (
        constructs_by_text["eval(source + suffix)"].construct_id
        not in attached_subject_ids
    )
    assert constructs_by_text["exec(source)"].construct_id not in attached_subject_ids
    assert (
        constructs_by_text['getattr(source, "strip")'].construct_id
        not in attached_subject_ids
    )

    [record] = updated_program.provenance_records
    observation = _eval_runtime_observation(constructs_by_text["eval(source)"].site)
    origin_detail = json.loads(record.origin_detail)
    assert record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert record.subject_sites == (constructs_by_text["eval(source)"].site,)
    assert origin_detail["normalized_payload"] == {
        "evaluation_outcome": "returned_value",
        "result_type": "builtins.str",
    }
    assert origin_detail["replay_inputs"] == {
        "source_shape": "literal_expression",
        "source_sha256": hashlib.sha256(b'"runtime-value"').hexdigest(),
    }
    assert (
        origin_detail["durable_payload_reference"]
        == observation.durable_payload_reference
    )


def test_attach_eval_runtime_provenance_ignores_shadowed_names(
    tmp_path: Path,
) -> None:
    """Shadowed ``eval`` names remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def run(loader, source: str) -> None:
    eval = loader
    eval(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    call_site = next(
        candidate
        for candidate in program.syntax.call_sites
        if candidate.callee_text == "eval"
    )
    observation = _eval_runtime_observation(call_site.site)

    updated_program = runtime_acquisition.attach_eval_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_exec_runtime_provenance_targets_only_bounded_exec_source(
    tmp_path: Path,
) -> None:
    """Only the exact ``exec(source)`` boundary gains runtime attachments."""
    (tmp_path / "main.py").write_text(
        """
import builtins

def run(
    source: str,
    suffix: str,
    globals_ns: dict[str, object],
    locals_ns: dict[str, object],
) -> None:
    exec(source)
    exec(source, globals_ns)
    exec(source, globals_ns, locals_ns)
    exec(source=source)
    exec("pass")
    exec(source + suffix)
    builtins.exec(source)
    eval(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _exec_runtime_observation(call_site.site)
        for call_site in program.syntax.call_sites
    ]

    updated_program = runtime_acquisition.attach_exec_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {constructs_by_text["exec(source)"].construct_id}
    assert (
        constructs_by_text["exec(source, globals_ns)"].construct_id
        not in attached_subject_ids
    )
    assert (
        constructs_by_text["exec(source, globals_ns, locals_ns)"].construct_id
        not in attached_subject_ids
    )
    assert (
        constructs_by_text["exec(source=source)"].construct_id
        not in attached_subject_ids
    )
    assert constructs_by_text['exec("pass")'].construct_id not in attached_subject_ids
    assert (
        constructs_by_text["exec(source + suffix)"].construct_id
        not in attached_subject_ids
    )
    assert constructs_by_text["eval(source)"].construct_id not in attached_subject_ids

    [record] = updated_program.provenance_records
    observation = _exec_runtime_observation(constructs_by_text["exec(source)"].site)
    origin_detail = json.loads(record.origin_detail)
    assert record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert record.subject_sites == (constructs_by_text["exec(source)"].site,)
    assert origin_detail["normalized_payload"] == {
        "execution_outcome": "completed",
        "statement_kind": "pass",
    }
    assert origin_detail["replay_inputs"] == {
        "source_shape": "literal_statement",
        "source_sha256": hashlib.sha256(b"pass").hexdigest(),
    }
    assert (
        origin_detail["durable_payload_reference"]
        == observation.durable_payload_reference
    )


def test_attach_exec_runtime_provenance_ignores_shadowed_names(
    tmp_path: Path,
) -> None:
    """Shadowed ``exec`` names remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def run(loader, source: str) -> None:
    exec = loader
    exec(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    call_site = next(
        candidate
        for candidate in program.syntax.call_sites
        if candidate.callee_text == "exec"
    )
    observation = _exec_runtime_observation(call_site.site)

    updated_program = runtime_acquisition.attach_exec_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_hasattr_runtime_provenance_targets_supported_hasattr_boundaries(
    tmp_path: Path,
) -> None:
    """Only existing unshadowed two-argument ``hasattr`` findings gain attachments."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str) -> None:
    hasattr(obj, name)
    hasattr(obj)
    getattr(obj, name)
    vars(obj)
    dir(obj)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _hasattr_runtime_observation(
            construct.site,
            attribute_present=construct.construct_text == "hasattr(obj, name)",
        )
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_hasattr_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {
        constructs_by_text["hasattr(obj, name)"].construct_id
    }
    assert constructs_by_text["hasattr(obj)"].construct_id not in attached_subject_ids
    assert (
        constructs_by_text["getattr(obj, name)"].construct_id
        not in attached_subject_ids
    )
    assert constructs_by_text["vars(obj)"].construct_id not in attached_subject_ids
    assert constructs_by_text["dir(obj)"].construct_id not in attached_subject_ids

    [record] = updated_program.provenance_records
    assert record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert record.subject_sites == (constructs_by_text["hasattr(obj, name)"].site,)


def test_attach_getattr_runtime_provenance_targets_supported_getattr_boundaries(
    tmp_path: Path,
) -> None:
    """Only existing unshadowed two-argument ``getattr`` findings gain attachments."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str, default: object) -> None:
    getattr(obj, name)
    getattr(obj, name, default)
    getattr()
    hasattr(obj, name)
    vars(obj)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _getattr_runtime_observation(
            construct.site,
            lookup_outcome=(
                "returned_value"
                if construct.construct_text == "getattr(obj, name)"
                else "returned_default_value"
            ),
        )
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_getattr_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {
        constructs_by_text["getattr(obj, name)"].construct_id,
        constructs_by_text["getattr(obj, name, default)"].construct_id,
    }
    assert constructs_by_text["getattr()"].construct_id not in attached_subject_ids
    assert (
        constructs_by_text["hasattr(obj, name)"].construct_id
        not in attached_subject_ids
    )
    assert constructs_by_text["vars(obj)"].construct_id not in attached_subject_ids

    records_by_subject_id = {
        record.subject_id: record for record in updated_program.provenance_records
    }
    assert len(records_by_subject_id) == 2
    first_record = records_by_subject_id[
        constructs_by_text["getattr(obj, name)"].construct_id
    ]
    assert first_record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert first_record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert first_record.subject_sites == (
        constructs_by_text["getattr(obj, name)"].site,
    )
    first_origin_detail = json.loads(first_record.origin_detail)
    assert first_origin_detail["normalized_payload"] == {
        "lookup_outcome": "returned_value"
    }

    defaulted_record = records_by_subject_id[
        constructs_by_text["getattr(obj, name, default)"].construct_id
    ]
    assert defaulted_record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert defaulted_record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert defaulted_record.subject_sites == (
        constructs_by_text["getattr(obj, name, default)"].site,
    )
    defaulted_origin_detail = json.loads(defaulted_record.origin_detail)
    assert defaulted_origin_detail["normalized_payload"] == {
        "lookup_outcome": "returned_default_value"
    }


def test_attach_vars_runtime_provenance_targets_supported_vars_boundaries(
    tmp_path: Path,
) -> None:
    """Only existing unshadowed zero/one-argument ``vars`` findings gain attachments."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object) -> None:
    vars(obj)
    vars()
    dir(obj)
    getattr(obj, "name")
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _vars_runtime_observation(
            construct.site,
            lookup_outcome=(
                "raised_type_error"
                if construct.construct_text == "vars(obj)"
                else "returned_namespace"
            ),
        )
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_vars_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {
        constructs_by_text["vars(obj)"].construct_id,
        constructs_by_text["vars()"].construct_id,
    }
    assert constructs_by_text["dir(obj)"].construct_id not in attached_subject_ids
    assert (
        constructs_by_text['getattr(obj, "name")'].construct_id
        not in attached_subject_ids
    )

    records_by_subject_id = {
        record.subject_id: record for record in updated_program.provenance_records
    }
    assert len(records_by_subject_id) == 2

    one_arg_record = records_by_subject_id[constructs_by_text["vars(obj)"].construct_id]
    assert one_arg_record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert one_arg_record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert one_arg_record.subject_sites == (constructs_by_text["vars(obj)"].site,)
    one_arg_origin_detail = json.loads(one_arg_record.origin_detail)
    assert one_arg_origin_detail["normalized_payload"] == {
        "lookup_outcome": "raised_type_error"
    }

    zero_arg_record = records_by_subject_id[constructs_by_text["vars()"].construct_id]
    assert zero_arg_record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert zero_arg_record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert zero_arg_record.subject_sites == (constructs_by_text["vars()"].site,)
    zero_arg_origin_detail = json.loads(zero_arg_record.origin_detail)
    assert zero_arg_origin_detail["normalized_payload"] == {
        "lookup_outcome": "returned_namespace"
    }


def test_attach_globals_runtime_provenance_targets_supported_globals_boundaries(
    tmp_path: Path,
) -> None:
    """Only existing unshadowed simple-name ``globals()`` findings gain attachments."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str, value: object) -> None:
    globals()
    locals()
    vars()
    setattr(obj, name, value)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _globals_runtime_observation(construct.site)
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_globals_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {constructs_by_text["globals()"].construct_id}
    assert constructs_by_text["locals()"].construct_id not in attached_subject_ids
    assert constructs_by_text["vars()"].construct_id not in attached_subject_ids
    assert (
        constructs_by_text["setattr(obj, name, value)"].construct_id
        not in attached_subject_ids
    )

    [record] = updated_program.provenance_records
    assert record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert record.subject_sites == (constructs_by_text["globals()"].site,)
    origin_detail = json.loads(record.origin_detail)
    assert origin_detail["normalized_payload"] == {
        "lookup_outcome": "returned_namespace"
    }


def test_attach_globals_runtime_provenance_allows_additional_payload_fields(
    tmp_path: Path,
) -> None:
    """``globals()`` observations may carry extra payload beyond lookup outcome."""
    (tmp_path / "main.py").write_text(
        """
def run() -> None:
    globals()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "globals()"
    )
    observation = replace(
        _globals_runtime_observation(construct.site),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="lookup_outcome",
                value="returned_namespace",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="namespace_entry_count",
                value="4",
            ),
        ),
    )

    updated_program = runtime_acquisition.attach_globals_runtime_provenance(
        program,
        [observation],
    )

    [record] = updated_program.provenance_records
    origin_detail = json.loads(record.origin_detail)
    assert origin_detail["normalized_payload"] == {
        "lookup_outcome": "returned_namespace",
        "namespace_entry_count": "4",
    }


def test_attach_globals_runtime_provenance_ignores_wrong_arity_forms(
    tmp_path: Path,
) -> None:
    """Wrong-arity ``globals`` calls remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object) -> None:
    globals(obj)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "globals(obj)"
    )
    observation = _globals_runtime_observation(construct.site)

    updated_program = runtime_acquisition.attach_globals_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_globals_runtime_provenance_ignores_shadowed_names(
    tmp_path: Path,
) -> None:
    """Shadowed ``globals`` names remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def run(loader) -> None:
    globals = loader
    globals()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    call_site = next(
        candidate
        for candidate in program.syntax.call_sites
        if candidate.callee_text == "globals"
    )
    observation = _globals_runtime_observation(call_site.site)

    updated_program = runtime_acquisition.attach_globals_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_locals_runtime_provenance_targets_supported_locals_boundaries(
    tmp_path: Path,
) -> None:
    """Only existing unshadowed simple-name ``locals()`` findings gain attachments."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str, value: object) -> None:
    globals()
    locals()
    vars()
    setattr(obj, name, value)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _locals_runtime_observation(construct.site)
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_locals_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {constructs_by_text["locals()"].construct_id}
    assert constructs_by_text["globals()"].construct_id not in attached_subject_ids
    assert constructs_by_text["vars()"].construct_id not in attached_subject_ids
    assert (
        constructs_by_text["setattr(obj, name, value)"].construct_id
        not in attached_subject_ids
    )

    [record] = updated_program.provenance_records
    assert record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert record.subject_sites == (constructs_by_text["locals()"].site,)
    origin_detail = json.loads(record.origin_detail)
    assert origin_detail["normalized_payload"] == {
        "lookup_outcome": "returned_namespace"
    }


def test_attach_locals_runtime_provenance_ignores_wrong_arity_forms(
    tmp_path: Path,
) -> None:
    """Wrong-arity ``locals`` calls remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object) -> None:
    locals(obj)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "locals(obj)"
    )
    observation = _locals_runtime_observation(construct.site)

    updated_program = runtime_acquisition.attach_locals_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_locals_runtime_provenance_ignores_shadowed_names(
    tmp_path: Path,
) -> None:
    """Shadowed ``locals`` names remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def run(loader) -> None:
    locals = loader
    locals()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    call_site = next(
        candidate
        for candidate in program.syntax.call_sites
        if candidate.callee_text == "locals"
    )
    observation = _locals_runtime_observation(call_site.site)

    updated_program = runtime_acquisition.attach_locals_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_setattr_runtime_provenance_targets_supported_setattr_boundaries(
    tmp_path: Path,
) -> None:
    """Only existing unshadowed three-argument ``setattr`` findings gain attachments."""
    (tmp_path / "main.py").write_text(
        """
def run(
    obj: object,
    name: str,
    value: object,
    extra: object,
) -> None:
    setattr(obj, name, value)
    setattr(obj, name)
    setattr(obj, name, value, extra)
    delattr(obj, name)
    globals()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _setattr_runtime_observation(construct.site)
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_setattr_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {
        constructs_by_text["setattr(obj, name, value)"].construct_id
    }
    assert (
        constructs_by_text["setattr(obj, name)"].construct_id
        not in attached_subject_ids
    )
    assert (
        constructs_by_text["setattr(obj, name, value, extra)"].construct_id
        not in attached_subject_ids
    )
    assert (
        constructs_by_text["delattr(obj, name)"].construct_id
        not in attached_subject_ids
    )
    assert constructs_by_text["globals()"].construct_id not in attached_subject_ids

    [record] = updated_program.provenance_records
    assert record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert record.subject_sites == (
        constructs_by_text["setattr(obj, name, value)"].site,
    )
    origin_detail = json.loads(record.origin_detail)
    assert origin_detail["normalized_payload"] == {"mutation_outcome": "returned_none"}
    assert (
        origin_detail["durable_payload_reference"]
        == _setattr_runtime_observation(
            constructs_by_text["setattr(obj, name, value)"].site
        ).durable_payload_reference
    )


def test_attach_setattr_runtime_provenance_allows_additional_payload_fields(
    tmp_path: Path,
) -> None:
    """``setattr`` observations may carry extra payload beyond mutation outcome."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str, value: object) -> None:
    setattr(obj, name, value)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "setattr(obj, name, value)"
    )
    observation = replace(
        _setattr_runtime_observation(construct.site),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="mutation_outcome",
                value="returned_none",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="value_argument_source",
                value="call_argument",
            ),
        ),
    )

    updated_program = runtime_acquisition.attach_setattr_runtime_provenance(
        program,
        [observation],
    )

    [record] = updated_program.provenance_records
    origin_detail = json.loads(record.origin_detail)
    assert origin_detail["normalized_payload"] == {
        "mutation_outcome": "returned_none",
        "value_argument_source": "call_argument",
    }


def test_attach_delattr_runtime_provenance_targets_supported_delattr_boundaries(
    tmp_path: Path,
) -> None:
    """Only existing unshadowed two-argument ``delattr`` findings gain attachments."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str, value: object) -> None:
    delattr(obj, name)
    delattr(obj)
    delattr()
    setattr(obj, name, value)
    globals()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _delattr_runtime_observation(construct.site)
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_delattr_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {
        constructs_by_text["delattr(obj, name)"].construct_id
    }
    assert constructs_by_text["delattr(obj)"].construct_id not in attached_subject_ids
    assert constructs_by_text["delattr()"].construct_id not in attached_subject_ids
    assert (
        constructs_by_text["setattr(obj, name, value)"].construct_id
        not in attached_subject_ids
    )
    assert constructs_by_text["globals()"].construct_id not in attached_subject_ids

    [record] = updated_program.provenance_records
    assert record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert record.subject_sites == (constructs_by_text["delattr(obj, name)"].site,)
    origin_detail = json.loads(record.origin_detail)
    assert origin_detail["normalized_payload"] == {
        "mutation_outcome": "deleted_attribute"
    }


def test_attach_delattr_runtime_provenance_allows_additional_payload_fields(
    tmp_path: Path,
) -> None:
    """``delattr`` observations may carry extra payload beyond mutation outcome."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str) -> None:
    delattr(obj, name)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "delattr(obj, name)"
    )
    observation = replace(
        _delattr_runtime_observation(construct.site),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="mutation_outcome",
                value="deleted_attribute",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="attribute_name_source",
                value="argument",
            ),
        ),
    )

    updated_program = runtime_acquisition.attach_delattr_runtime_provenance(
        program,
        [observation],
    )

    [record] = updated_program.provenance_records
    origin_detail = json.loads(record.origin_detail)
    assert origin_detail["normalized_payload"] == {
        "mutation_outcome": "deleted_attribute",
        "attribute_name_source": "argument",
    }


def test_attach_dir_runtime_provenance_targets_supported_dir_boundaries(
    tmp_path: Path,
) -> None:
    """Only existing unshadowed simple-name ``dir`` findings gain attachments."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object) -> None:
    dir(obj)
    dir()
    vars(obj)
    getattr(obj, "name")
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _dir_runtime_observation(
            construct.site,
            listing_entry_count=None if construct.construct_text == "dir()" else 3,
        )
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_dir_runtime_provenance(
        program,
        observations,
    )
    constructs_by_text = {
        construct.construct_text: construct
        for construct in program.unsupported_constructs
    }
    attached_subject_ids = {
        record.subject_id for record in updated_program.provenance_records
    }
    records_by_subject_id = {
        record.subject_id: record for record in updated_program.provenance_records
    }

    assert updated_program is not program
    assert program.provenance_records == []
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert attached_subject_ids == {
        constructs_by_text["dir(obj)"].construct_id,
        constructs_by_text["dir()"].construct_id,
    }
    assert constructs_by_text["vars(obj)"].construct_id not in attached_subject_ids
    assert (
        constructs_by_text['getattr(obj, "name")'].construct_id
        not in attached_subject_ids
    )

    one_arg_record = records_by_subject_id[constructs_by_text["dir(obj)"].construct_id]
    assert one_arg_record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert one_arg_record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert one_arg_record.subject_sites == (constructs_by_text["dir(obj)"].site,)
    one_arg_origin_detail = json.loads(one_arg_record.origin_detail)
    assert one_arg_origin_detail["normalized_payload"] == {"listing_entry_count": "3"}
    assert (
        one_arg_origin_detail["durable_payload_reference"]
        == _dir_runtime_observation(
            constructs_by_text["dir(obj)"].site
        ).durable_payload_reference
    )

    zero_arg_record = records_by_subject_id[constructs_by_text["dir()"].construct_id]
    assert zero_arg_record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert zero_arg_record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert zero_arg_record.subject_sites == (constructs_by_text["dir()"].site,)
    zero_arg_origin_detail = json.loads(zero_arg_record.origin_detail)
    assert zero_arg_origin_detail["normalized_payload"] == {}
    assert (
        zero_arg_origin_detail["durable_payload_reference"]
        == _dir_runtime_observation(
            constructs_by_text["dir()"].site,
            listing_entry_count=None,
        ).durable_payload_reference
    )


def test_attach_dir_runtime_provenance_ignores_wrong_arity_forms(
    tmp_path: Path,
) -> None:
    """Wrong-arity ``dir`` calls remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, extra: object) -> None:
    dir(obj, extra)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "dir(obj, extra)"
    )
    observation = _dir_runtime_observation(construct.site)

    updated_program = runtime_acquisition.attach_dir_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_dir_runtime_provenance_ignores_shadowed_names(
    tmp_path: Path,
) -> None:
    """Shadowed ``dir`` names remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def run(loader, obj) -> None:
    dir = loader
    dir(obj)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    call_site = next(
        candidate
        for candidate in program.syntax.call_sites
        if candidate.callee_text == "dir"
    )
    observation = _dir_runtime_observation(call_site.site)

    updated_program = runtime_acquisition.attach_dir_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_metaclass_behavior_runtime_provenance_targets_keyword_site(
    tmp_path: Path,
) -> None:
    """Only the preserved metaclass keyword site gains metaclass runtime proof."""
    (tmp_path / "main.py").write_text(
        """
class Base:
    pass

class Meta(type):
    pass

class Holder:
    Meta = Meta

class Example(Base, metaclass=Holder.Meta):
    pass
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    observations = [
        _metaclass_behavior_runtime_observation(construct.site)
        for construct in program.unsupported_constructs
    ]

    updated_program = runtime_acquisition.attach_metaclass_behavior_runtime_provenance(
        program,
        observations,
    )
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "metaclass=Holder.Meta"
    )

    assert updated_program is not program
    assert updated_program.unsupported_constructs == program.unsupported_constructs
    assert updated_program.unresolved_frontier == program.unresolved_frontier
    assert len(updated_program.provenance_records) == 1
    [record] = updated_program.provenance_records
    assert record.subject_kind is SemanticSubjectKind.UNSUPPORTED_FINDING
    assert record.capability_tier is CapabilityTier.RUNTIME_BACKED
    assert record.subject_id == construct.construct_id
    assert record.subject_sites == (construct.site,)
    assert any(
        access.access_text == "Holder.Meta"
        for access in updated_program.unresolved_frontier
    )
    origin_detail = json.loads(record.origin_detail)
    assert origin_detail["normalized_payload"] == {
        "class_creation_outcome": "created_class"
    }
    assert (
        origin_detail["durable_payload_reference"]
        == _metaclass_behavior_runtime_observation(
            construct.site
        ).durable_payload_reference
    )


def test_attach_metaclass_behavior_runtime_provenance_allows_additional_payload_fields(
    tmp_path: Path,
) -> None:
    """Metaclass observations may carry additive normalized payload fields."""
    (tmp_path / "main.py").write_text(
        """
class Base:
    pass

class Meta(type):
    pass

class Example(Base, metaclass=Meta):
    pass
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "metaclass=Meta"
    )
    observation = replace(
        _metaclass_behavior_runtime_observation(construct.site),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="class_creation_outcome",
                value="created_class",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="created_class_qualified_name",
                value="main.Example",
            ),
            runtime_acquisition._RuntimeObservationField(
                key="selected_metaclass_qualified_name",
                value="main.Meta",
            ),
        ),
    )

    updated_program = runtime_acquisition.attach_metaclass_behavior_runtime_provenance(
        program,
        [observation],
    )

    [record] = updated_program.provenance_records
    origin_detail = json.loads(record.origin_detail)
    assert origin_detail["normalized_payload"] == {
        "class_creation_outcome": "created_class",
        "created_class_qualified_name": "main.Example",
        "selected_metaclass_qualified_name": "main.Meta",
    }


def test_attach_metaclass_behavior_runtime_provenance_ignores_nested_attribute_sites(
    tmp_path: Path,
) -> None:
    """Nested metaclass attribute sites remain outside the keyword-surface seam."""
    (tmp_path / "main.py").write_text(
        """
class Base:
    pass

class Meta(type):
    pass

class Holder:
    Meta = Meta

class Example(Base, metaclass=Holder.Meta):
    pass
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    attribute_site = next(
        candidate.site
        for candidate in program.syntax.attribute_sites
        if candidate.base_text == "Holder" and candidate.attribute_name == "Meta"
    )
    observation = _metaclass_behavior_runtime_observation(attribute_site)

    updated_program = runtime_acquisition.attach_metaclass_behavior_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_metaclass_behavior_runtime_provenance_rejects_non_created_class_outcome(
    tmp_path: Path,
) -> None:
    """Metaclass observations must report the successful created-class outcome."""
    (tmp_path / "main.py").write_text(
        """
class Base:
    pass

class Meta(type):
    pass

class Example(Base, metaclass=Meta):
    pass
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "metaclass=Meta"
    )
    observation = _metaclass_behavior_runtime_observation(
        construct.site,
        class_creation_outcome="raised_type_error",
    )

    with pytest.raises(ValueError, match="created_class"):
        runtime_acquisition.attach_metaclass_behavior_runtime_provenance(
            program,
            [observation],
        )


def test_attach_metaclass_behavior_runtime_provenance_rejects_missing_outcome_key(
    tmp_path: Path,
) -> None:
    """Metaclass observations must keep the required discriminator key."""
    (tmp_path / "main.py").write_text(
        """
class Base:
    pass

class Meta(type):
    pass

class Example(Base, metaclass=Meta):
    pass
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "metaclass=Meta"
    )
    observation = replace(
        _metaclass_behavior_runtime_observation(construct.site),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="selected_metaclass_qualified_name",
                value="main.Meta",
            ),
        ),
    )

    with pytest.raises(ValueError, match="class_creation_outcome"):
        runtime_acquisition.attach_metaclass_behavior_runtime_provenance(
            program,
            [observation],
        )


def test_attach_metaclass_behavior_runtime_provenance_rejects_missing_durable_artifact(
    tmp_path: Path,
) -> None:
    """Metaclass observations must carry durable created-class proof."""
    (tmp_path / "main.py").write_text(
        """
class Base:
    pass

class Meta(type):
    pass

class Example(Base, metaclass=Meta):
    pass
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "metaclass=Meta"
    )
    observation = replace(
        _metaclass_behavior_runtime_observation(construct.site),
        durable_payload_reference=None,
    )

    with pytest.raises(ValueError, match="durable_payload_reference"):
        runtime_acquisition.attach_metaclass_behavior_runtime_provenance(
            program,
            [observation],
        )


def test_attach_eval_runtime_provenance_rejects_invalid_evaluation_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``eval`` observations must claim the returned-value branch."""
    (tmp_path / "main.py").write_text(
        """
def run(source: str) -> None:
    eval(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "eval(source)"
    )
    observation = _eval_runtime_observation(
        construct.site,
        evaluation_outcome="raised_syntax_error",
    )

    with pytest.raises(ValueError, match="returned_value"):
        runtime_acquisition.attach_eval_runtime_provenance(
            program,
            [observation],
        )


def test_attach_eval_runtime_provenance_rejects_missing_source_replay_proof(
    tmp_path: Path,
) -> None:
    """Matched ``eval`` observations must carry bounded evaluated-source proof."""
    (tmp_path / "main.py").write_text(
        """
def run(source: str) -> None:
    eval(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "eval(source)"
    )
    observation = replace(
        _eval_runtime_observation(construct.site),
        replay_inputs=(
            runtime_acquisition._RuntimeObservationField(
                key="source_shape",
                value="literal_expression",
            ),
        ),
    )

    with pytest.raises(ValueError, match="source_sha256"):
        runtime_acquisition.attach_eval_runtime_provenance(
            program,
            [observation],
        )


def test_attach_eval_runtime_provenance_rejects_missing_durable_payload_reference(
    tmp_path: Path,
) -> None:
    """Matched ``eval`` observations must carry durable returned-value proof."""
    (tmp_path / "main.py").write_text(
        """
def run(source: str) -> None:
    eval(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "eval(source)"
    )
    observation = replace(
        _eval_runtime_observation(construct.site),
        durable_payload_reference=None,
    )

    with pytest.raises(ValueError, match="durable_payload_reference"):
        runtime_acquisition.attach_eval_runtime_provenance(
            program,
            [observation],
        )


def test_attach_exec_runtime_provenance_rejects_invalid_execution_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``exec`` observations must claim the completed branch."""
    (tmp_path / "main.py").write_text(
        """
def run(source: str) -> None:
    exec(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "exec(source)"
    )
    observation = _exec_runtime_observation(
        construct.site,
        execution_outcome="raised_syntax_error",
    )

    with pytest.raises(ValueError, match="completed"):
        runtime_acquisition.attach_exec_runtime_provenance(
            program,
            [observation],
        )


def test_attach_exec_runtime_provenance_rejects_invalid_statement_kind(
    tmp_path: Path,
) -> None:
    """Matched ``exec`` observations only accept the optional pass-statement summary."""
    (tmp_path / "main.py").write_text(
        """
def run(source: str) -> None:
    exec(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "exec(source)"
    )
    observation = _exec_runtime_observation(
        construct.site,
        statement_kind="import",
    )

    with pytest.raises(ValueError, match="statement_kind"):
        runtime_acquisition.attach_exec_runtime_provenance(
            program,
            [observation],
        )


def test_attach_exec_runtime_provenance_rejects_missing_source_replay_proof(
    tmp_path: Path,
) -> None:
    """Matched ``exec`` observations must carry bounded executed-source proof."""
    (tmp_path / "main.py").write_text(
        """
def run(source: str) -> None:
    exec(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "exec(source)"
    )
    observation = replace(
        _exec_runtime_observation(construct.site),
        replay_inputs=(
            runtime_acquisition._RuntimeObservationField(
                key="source_shape",
                value="literal_statement",
            ),
        ),
    )

    with pytest.raises(ValueError, match="source_sha256"):
        runtime_acquisition.attach_exec_runtime_provenance(
            program,
            [observation],
        )


def test_attach_exec_runtime_provenance_rejects_invalid_source_digest(
    tmp_path: Path,
) -> None:
    """Matched ``exec`` observations must identify executed source by SHA-256."""
    (tmp_path / "main.py").write_text(
        """
def run(source: str) -> None:
    exec(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "exec(source)"
    )
    observation = _exec_runtime_observation(
        construct.site,
        source_sha256="not-a-digest",
    )

    with pytest.raises(ValueError, match="64-character hex digest"):
        runtime_acquisition.attach_exec_runtime_provenance(
            program,
            [observation],
        )


def test_attach_exec_runtime_provenance_rejects_non_pass_source_digest(
    tmp_path: Path,
) -> None:
    """Matched ``exec`` observations must identify exactly ``pass`` as source."""
    (tmp_path / "main.py").write_text(
        """
def run(source: str) -> None:
    exec(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "exec(source)"
    )
    observation = _exec_runtime_observation(
        construct.site,
        source_sha256=hashlib.sha256(b"print(1)").hexdigest(),
    )

    with pytest.raises(ValueError, match="exact executed source 'pass'"):
        runtime_acquisition.attach_exec_runtime_provenance(
            program,
            [observation],
        )


def test_attach_exec_runtime_provenance_rejects_missing_durable_payload_reference(
    tmp_path: Path,
) -> None:
    """Matched ``exec`` observations must carry durable completion proof."""
    (tmp_path / "main.py").write_text(
        """
def run(source: str) -> None:
    exec(source)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "exec(source)"
    )
    observation = replace(
        _exec_runtime_observation(construct.site),
        durable_payload_reference=None,
    )

    with pytest.raises(ValueError, match="durable_payload_reference"):
        runtime_acquisition.attach_exec_runtime_provenance(
            program,
            [observation],
        )


def test_attach_getattr_runtime_provenance_rejects_non_lookup_outcome_payload(
    tmp_path: Path,
) -> None:
    """Matched ``getattr`` observations must carry the bounded lookup outcome."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str) -> None:
    getattr(obj, name)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "getattr(obj, name)"
    )
    observation = replace(
        _getattr_runtime_observation(
            construct.site,
            lookup_outcome="returned_value",
        ),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="observed_value",
                value="some-value",
            ),
        ),
    )

    with pytest.raises(ValueError, match="lookup_outcome"):
        runtime_acquisition.attach_getattr_runtime_provenance(
            program,
            [observation],
        )


def test_attach_getattr_runtime_provenance_rejects_mismatched_defaulted_lookup_outcome(
    tmp_path: Path,
) -> None:
    """Defaulted ``getattr`` observations may not claim the raise-only branch."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str, default: object) -> None:
    getattr(obj, name, default)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "getattr(obj, name, default)"
    )
    observation = _getattr_runtime_observation(
        construct.site,
        lookup_outcome="raised_attribute_error",
    )

    with pytest.raises(ValueError, match="returned_default_value"):
        runtime_acquisition.attach_getattr_runtime_provenance(
            program,
            [observation],
        )


def test_attach_vars_runtime_provenance_rejects_invalid_lookup_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``vars(obj)`` observations must carry the bounded lookup outcome."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object) -> None:
    vars(obj)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "vars(obj)"
    )
    observation = _vars_runtime_observation(
        construct.site,
        lookup_outcome="returned_value",
    )

    with pytest.raises(ValueError, match="returned_namespace"):
        runtime_acquisition.attach_vars_runtime_provenance(
            program,
            [observation],
        )


def test_attach_vars_runtime_provenance_rejects_zero_arg_type_error_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``vars()`` observations may not claim the one-argument error branch."""
    (tmp_path / "main.py").write_text(
        """
def run() -> None:
    vars()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "vars()"
    )
    observation = _vars_runtime_observation(
        construct.site,
        lookup_outcome="raised_type_error",
    )

    with pytest.raises(ValueError, match="returned_namespace"):
        runtime_acquisition.attach_vars_runtime_provenance(
            program,
            [observation],
        )


def test_attach_globals_runtime_provenance_rejects_invalid_lookup_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``globals()`` observations must claim the returned namespace branch."""
    (tmp_path / "main.py").write_text(
        """
def run() -> None:
    globals()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "globals()"
    )
    observation = _globals_runtime_observation(
        construct.site,
        lookup_outcome="raised_type_error",
    )

    with pytest.raises(ValueError, match="returned_namespace"):
        runtime_acquisition.attach_globals_runtime_provenance(
            program,
            [observation],
        )


def test_attach_globals_runtime_provenance_rejects_missing_lookup_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``globals()`` observations must keep the discriminator key."""
    (tmp_path / "main.py").write_text(
        """
def run() -> None:
    globals()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "globals()"
    )
    observation = replace(
        _globals_runtime_observation(construct.site),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="namespace_entry_count",
                value="4",
            ),
        ),
    )

    with pytest.raises(ValueError, match="lookup_outcome"):
        runtime_acquisition.attach_globals_runtime_provenance(
            program,
            [observation],
        )


def test_attach_locals_runtime_provenance_rejects_invalid_lookup_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``locals()`` observations must claim the returned namespace branch."""
    (tmp_path / "main.py").write_text(
        """
def run() -> None:
    locals()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "locals()"
    )
    observation = _locals_runtime_observation(
        construct.site,
        lookup_outcome="raised_type_error",
    )

    with pytest.raises(ValueError, match="returned_namespace"):
        runtime_acquisition.attach_locals_runtime_provenance(
            program,
            [observation],
        )


def test_attach_locals_runtime_provenance_rejects_missing_lookup_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``locals()`` observations must keep the discriminator key."""
    (tmp_path / "main.py").write_text(
        """
def run() -> None:
    locals()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "locals()"
    )
    observation = replace(
        _locals_runtime_observation(construct.site),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="namespace_entry_count",
                value="4",
            ),
        ),
    )

    with pytest.raises(ValueError, match="lookup_outcome"):
        runtime_acquisition.attach_locals_runtime_provenance(
            program,
            [observation],
        )


def test_attach_setattr_runtime_provenance_rejects_invalid_mutation_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``setattr`` observations must claim the returned-``None`` outcome."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str, value: object) -> None:
    setattr(obj, name, value)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "setattr(obj, name, value)"
    )
    observation = _setattr_runtime_observation(
        construct.site,
        mutation_outcome="raised_attribute_error",
    )

    with pytest.raises(ValueError, match="returned_none"):
        runtime_acquisition.attach_setattr_runtime_provenance(
            program,
            [observation],
        )


def test_attach_setattr_runtime_provenance_rejects_missing_mutation_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``setattr`` observations must keep the discriminator key."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str, value: object) -> None:
    setattr(obj, name, value)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "setattr(obj, name, value)"
    )
    observation = replace(
        _setattr_runtime_observation(construct.site),
        normalized_payload=(
            runtime_acquisition._RuntimeObservationField(
                key="attribute_name_source",
                value="argument",
            ),
        ),
    )

    with pytest.raises(ValueError, match="mutation_outcome"):
        runtime_acquisition.attach_setattr_runtime_provenance(
            program,
            [observation],
        )


def test_attach_setattr_runtime_provenance_rejects_missing_durable_payload_reference(
    tmp_path: Path,
) -> None:
    """Matched ``setattr`` observations must carry durable passed-value proof."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str, value: object) -> None:
    setattr(obj, name, value)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "setattr(obj, name, value)"
    )
    observation = replace(
        _setattr_runtime_observation(construct.site),
        durable_payload_reference=None,
    )

    with pytest.raises(ValueError, match="durable_payload_reference"):
        runtime_acquisition.attach_setattr_runtime_provenance(
            program,
            [observation],
        )


def test_attach_setattr_runtime_provenance_ignores_shadowed_names(
    tmp_path: Path,
) -> None:
    """Shadowed ``setattr`` names remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def run(loader, obj, name, value) -> None:
    setattr = loader
    setattr(obj, name, value)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    call_site = next(
        candidate
        for candidate in program.syntax.call_sites
        if candidate.callee_text == "setattr"
    )
    observation = _setattr_runtime_observation(call_site.site)

    updated_program = runtime_acquisition.attach_setattr_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_delattr_runtime_provenance_rejects_invalid_mutation_outcome(
    tmp_path: Path,
) -> None:
    """Matched ``delattr`` observations must claim deleted-attribute outcome."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object, name: str) -> None:
    delattr(obj, name)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "delattr(obj, name)"
    )
    observation = _delattr_runtime_observation(
        construct.site,
        mutation_outcome="raised_attribute_error",
    )

    with pytest.raises(ValueError, match="deleted_attribute"):
        runtime_acquisition.attach_delattr_runtime_provenance(
            program,
            [observation],
        )


def test_attach_delattr_runtime_provenance_ignores_shadowed_names(
    tmp_path: Path,
) -> None:
    """Shadowed ``delattr`` names remain outside the attachable builtin seam."""
    (tmp_path / "main.py").write_text(
        """
def helper() -> None:
    return None

def run(loader) -> None:
    delattr = loader
    delattr()
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    call_site = next(
        candidate
        for candidate in program.syntax.call_sites
        if candidate.callee_text == "delattr"
    )
    observation = _delattr_runtime_observation(call_site.site)

    updated_program = runtime_acquisition.attach_delattr_runtime_provenance(
        program,
        [observation],
    )

    assert updated_program is program
    assert updated_program.provenance_records == []


def test_attach_dir_runtime_provenance_rejects_missing_durable_payload_reference(
    tmp_path: Path,
) -> None:
    """Matched ``dir(obj)`` observations must carry durable listing proof."""
    (tmp_path / "main.py").write_text(
        """
def run(obj: object) -> None:
    dir(obj)
""".lstrip(),
        encoding="utf-8",
    )

    program = _derived_program(tmp_path)
    construct = next(
        candidate
        for candidate in program.unsupported_constructs
        if candidate.construct_text == "dir(obj)"
    )
    observation = replace(
        _dir_runtime_observation(construct.site),
        durable_payload_reference=None,
    )

    with pytest.raises(ValueError, match="durable_payload_reference"):
        runtime_acquisition.attach_dir_runtime_provenance(
            program,
            [observation],
        )

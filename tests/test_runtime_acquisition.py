"""Tests for runtime-backed provenance attachment infrastructure."""

from __future__ import annotations

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

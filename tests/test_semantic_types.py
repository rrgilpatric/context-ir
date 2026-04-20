"""Contract tests for the semantic-first baseline types."""

from pathlib import Path

import pytest

import context_ir
from context_ir import (
    CapabilityTier,
    DownstreamVisibility,
    EvidenceOriginKind,
    ReplayStatus,
    RepositorySnapshotBasis,
    RuntimeAttachmentLink,
    SelectionBasis,
    SelectionDirective,
    SemanticDiagnosticBoundary,
    SemanticDiagnosticBoundaryKind,
    SemanticDiagnosticUnitStatus,
    SemanticOptimizationWarning,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticProvenanceRecord,
    SemanticSelectionRecord,
    SemanticSubjectKind,
    SemanticUnitTraceSummary,
    SourceSite,
    SourceSpan,
    SupportedDecorator,
    SupportedSubsetBoundary,
    SyntaxProgram,
    UnresolvedAccess,
    UnresolvedReasonCode,
    UnsupportedConstruct,
    analyze_repository,
)
from context_ir.semantic_types import (
    DataclassField,
    DataclassModel,
    DecoratorFact,
    DecoratorSupport,
    DependencyProofKind,
    DiagnosticSeverity,
    ImportTargetKind,
    ParameterFact,
    ParameterKind,
    ReferenceContext,
    ResolvedImport,
    ResolvedSymbol,
    ResolvedSymbolKind,
    ResolverDiagnostic,
    SemanticDependency,
    SemanticDependencyKind,
    SyntaxDiagnostic,
    SyntaxDiagnosticCode,
)


def make_site(site_id: str, path: str = "pkg/models.py") -> SourceSite:
    """Create a stable source site for contract tests."""
    return SourceSite(
        site_id=site_id,
        file_path=path,
        span=SourceSpan(start_line=1, start_column=0, end_line=1, end_column=12),
        snippet="@dataclass",
    )


def test_public_semantic_contracts_are_constructible() -> None:
    """Top-level semantic contracts can be imported and assembled."""
    syntax = SyntaxProgram(repo_root=Path("/tmp/repo"))
    program = SemanticProgram(
        repo_root=Path("/tmp/repo"),
        syntax=syntax,
    )

    assert isinstance(program, SemanticProgram)
    assert isinstance(program.syntax, SyntaxProgram)
    assert program.supported_subset.supported_decorators == (
        SupportedDecorator.DATACLASS,
    )
    assert program.syntax.metaclass_keywords == []
    assert program.resolved_imports == []
    assert program.dataclass_models == []
    assert program.dataclass_fields == []
    assert program.proven_dependencies == []
    assert program.unresolved_frontier == []
    assert program.provenance_records == []


def test_package_root_exports_semantic_baseline_surface() -> None:
    """The package root exposes the semantic-first baseline symbols."""
    expected_public_names = {
        "CapabilityTier",
        "DownstreamVisibility",
        "EvidenceOriginKind",
        "ReplayStatus",
        "RepositorySnapshotBasis",
        "SelectionBasis",
        "SelectionDirective",
        "SemanticDiagnosticBoundary",
        "SemanticDiagnosticBoundaryKind",
        "SemanticDiagnosticUnitStatus",
        "SemanticProvenanceRecord",
        "SemanticDependency",
        "SemanticProgram",
        "SemanticSubjectKind",
        "SemanticUnitTraceSummary",
        "RuntimeAttachmentLink",
        "SourceSite",
        "SourceSpan",
        "SupportedDecorator",
        "SupportedSubsetBoundary",
        "SyntaxProgram",
        "UnresolvedAccess",
        "UnresolvedReasonCode",
        "UnsupportedConstruct",
        "analyze_repository",
    }

    assert expected_public_names.issubset(set(context_ir.__all__))

    for public_name in expected_public_names:
        assert hasattr(context_ir, public_name)


def test_package_root_does_not_reexport_held_old_stack_contracts() -> None:
    """The package root does not normalize held old-stack contracts."""
    forbidden_public_names = {"CompileContext", "diagnose", "recompile"}

    assert forbidden_public_names.isdisjoint(set(context_ir.__all__))

    for public_name in forbidden_public_names:
        assert not hasattr(context_ir, public_name)


def test_proven_dependency_and_heuristic_candidate_are_distinct_contracts() -> None:
    """Proven dependencies stay separate from downstream heuristic candidates."""
    source_symbol = ResolvedSymbol(
        symbol_id="sym:pkg.models:User",
        kind=ResolvedSymbolKind.CLASS,
        qualified_name="pkg.models.User",
        file_id="file:pkg/models.py",
        definition_site=make_site("site:def:user"),
        defining_scope_id="scope:module:pkg.models",
    )
    target_symbol = ResolvedSymbol(
        symbol_id="sym:pkg.datatypes:Record",
        kind=ResolvedSymbolKind.CLASS,
        qualified_name="pkg.datatypes.Record",
        file_id="file:pkg/datatypes.py",
        definition_site=make_site("site:def:record", path="pkg/datatypes.py"),
        defining_scope_id="scope:module:pkg.datatypes",
    )
    dependency = SemanticDependency(
        dependency_id="dep:1",
        source_symbol_id=source_symbol.symbol_id,
        target_symbol_id=target_symbol.symbol_id,
        kind=SemanticDependencyKind.INHERITANCE,
        proof_kind=DependencyProofKind.BASE_CLASS_RESOLUTION,
        evidence_site_id="site:base:User",
    )
    directive = SelectionDirective(
        directive_id="select:1",
        basis=SelectionBasis.HEURISTIC_CANDIDATE,
        symbol_id=target_symbol.symbol_id,
        detail="rank for retrieval only",
    )

    assert dependency.source_symbol_id == source_symbol.symbol_id
    assert dependency.target_symbol_id == target_symbol.symbol_id
    assert dependency.proof_status.value == "proven"
    assert directive.basis is SelectionBasis.HEURISTIC_CANDIDATE
    assert type(dependency) is not type(directive)


def test_unresolved_and_unsupported_surfaces_require_reason_and_site() -> None:
    """Unknown and unsupported outputs carry stable site context and reason codes."""
    unresolved = UnresolvedAccess(
        access_id="frontier:attr:1",
        site=make_site("site:attr:1"),
        access_text="model.dynamic_attr",
        context=ReferenceContext.ATTRIBUTE_ACCESS,
        enclosing_scope_id="scope:function:load_user",
        reason_code=UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE,
        detail="attribute not declared in supported subset",
    )
    unsupported = UnsupportedConstruct(
        construct_id="unsupported:exec:1",
        site=make_site("site:exec:1"),
        construct_text="exec(code)",
        reason_code=UnresolvedReasonCode.EXEC_OR_EVAL,
        detail="runtime code execution is out of scope",
        enclosing_scope_id="scope:function:build",
    )

    assert unresolved.reason_code is UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    assert unresolved.site.site_id == "site:attr:1"
    assert unresolved.site.span.start_line == 1
    assert unresolved.proof_status.value == "unknown"
    assert unsupported.reason_code is UnresolvedReasonCode.EXEC_OR_EVAL
    assert unsupported.site.file_path == "pkg/models.py"
    assert unsupported.proof_status.value == "unsupported"


def test_dataclass_is_explicit_supported_decorator_surface() -> None:
    """The baseline represents @dataclass as a supported decorator fact."""
    decorator = DecoratorFact(
        decorator_id="decorator:dataclass:1",
        owner_definition_id="def:pkg.models:User",
        site=make_site("site:decorator:1"),
        expression_text="@dataclass",
        support=DecoratorSupport.SUPPORTED,
        supported_decorator=SupportedDecorator.DATACLASS,
        resolved_qualified_name="dataclasses.dataclass",
    )

    assert decorator.support is DecoratorSupport.SUPPORTED
    assert decorator.supported_decorator is SupportedDecorator.DATACLASS
    assert decorator.resolved_qualified_name == "dataclasses.dataclass"


def test_resolved_import_and_dataclass_object_facts_are_constructible() -> None:
    """Resolver object-model facts can be constructed with strict invariants."""
    resolved_import = ResolvedImport(
        import_id="import:1",
        binding_symbol_id="import:1",
        bound_name="dataclass",
        scope_id="def:pkg.models",
        site=make_site("site:import:1"),
        target_kind=ImportTargetKind.EXTERNAL,
        target_qualified_name="dataclasses.dataclass",
    )
    dataclass_model = DataclassModel(
        model_id="dataclass:def:pkg.models:User",
        class_symbol_id="def:pkg.models:User",
        decorator_reference_id="reference:decorator:1",
        decorator_site=make_site("site:decorator:1"),
    )
    dataclass_field = DataclassField(
        field_id="dataclass_field:assign:1",
        class_symbol_id="def:pkg.models:User",
        field_symbol_id="assign:1",
        name="name",
        site=make_site("site:field:1"),
        annotation_text="str",
        has_default=True,
        default_value_text="'user'",
    )

    assert resolved_import.target_kind is ImportTargetKind.EXTERNAL
    assert resolved_import.target_qualified_name == "dataclasses.dataclass"
    assert dataclass_model.decorator_target_qualified_name == "dataclasses.dataclass"
    assert dataclass_field.annotation_text == "str"


def test_supported_subset_boundary_surfaces_unknown_handling() -> None:
    """The initial subset boundary explicitly records supported and unknown cases."""
    boundary = SupportedSubsetBoundary()

    assert SupportedDecorator.DATACLASS in boundary.supported_decorators
    assert (
        UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS
        in boundary.unknown_without_proof
    )
    assert UnresolvedReasonCode.REFLECTIVE_BUILTIN in boundary.unknown_without_proof
    assert UnresolvedReasonCode.STAR_IMPORT in boundary.unknown_without_proof
    assert UnresolvedReasonCode.OPAQUE_DECORATOR in boundary.unknown_without_proof
    assert boundary.subset_name == "python-static-core-v1"


def test_semantic_program_accepts_explicit_provenance_records() -> None:
    """The widened semantic contract can carry later tier provenance records."""
    syntax = SyntaxProgram(repo_root=Path("/tmp/repo"))
    runtime_snapshot = RepositorySnapshotBasis(
        snapshot_kind="git_commit",
        snapshot_id="abc123def456",
    )
    runtime_attachments = (
        RuntimeAttachmentLink(
            attachment_id="attachment:runner:stdout",
            attachment_role="stdout",
            description="probe stdout",
        ),
        RuntimeAttachmentLink(
            attachment_id="attachment:runner:trace",
            attachment_role="trace",
            description="probe event trace",
        ),
    )
    records = [
        SemanticProvenanceRecord(
            record_id="prov:symbol:static:1",
            subject_kind=SemanticSubjectKind.SYMBOL,
            subject_id="def:pkg.models:User",
            capability_tier=CapabilityTier.STATICALLY_PROVED,
            evidence_origin=EvidenceOriginKind.STATIC_DERIVATION_RULE,
            origin_detail="call_resolution",
            replay_status=ReplayStatus.DETERMINISTIC_STATIC,
            subject_sites=(make_site("site:def:user"),),
            evidence_sites=(make_site("site:def:user:evidence"),),
        ),
        SemanticProvenanceRecord(
            record_id="prov:symbol:runtime:1",
            subject_kind=SemanticSubjectKind.SYMBOL,
            subject_id="sym:pkg.service:Runner",
            capability_tier=CapabilityTier.RUNTIME_BACKED,
            evidence_origin=EvidenceOriginKind.RUNTIME_PROBE_IDENTITY,
            origin_detail="probe:runner:init",
            replay_status=ReplayStatus.REPRODUCIBLE_RUNTIME,
            repository_snapshot_basis=runtime_snapshot,
            attachment_links=runtime_attachments,
            subject_sites=(make_site("site:runner"),),
            evidence_sites=(make_site("site:runner:probe"),),
        ),
        SemanticProvenanceRecord(
            record_id="prov:frontier:1",
            subject_kind=SemanticSubjectKind.FRONTIER_ITEM,
            subject_id="frontier:call:1",
            capability_tier=CapabilityTier.HEURISTIC_FRONTIER,
            evidence_origin=EvidenceOriginKind.HEURISTIC_RULE,
            origin_detail="frontier_ranker_v1",
            replay_status=ReplayStatus.NON_PROOF_HEURISTIC,
            subject_sites=(make_site("site:frontier"),),
            evidence_sites=(make_site("site:frontier:evidence"),),
            downstream_visibility=(
                DownstreamVisibility.COMPILE,
                DownstreamVisibility.DIAGNOSE,
            ),
        ),
        SemanticProvenanceRecord(
            record_id="prov:unsupported:1",
            subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
            subject_id="unsupported:exec:1",
            capability_tier=CapabilityTier.UNSUPPORTED_OPAQUE,
            evidence_origin=EvidenceOriginKind.UNSUPPORTED_REASON_CODE,
            origin_detail="exec_or_eval",
            replay_status=ReplayStatus.OPAQUE_BOUNDARY,
            subject_sites=(make_site("site:unsupported"),),
            evidence_sites=(make_site("site:unsupported:evidence"),),
        ),
    ]
    program = SemanticProgram(
        repo_root=Path("/tmp/repo"),
        syntax=syntax,
        provenance_records=records,
    )

    assert program.provenance_records == records
    assert program.provenance_records[1].repository_snapshot_basis == runtime_snapshot
    assert program.provenance_records[1].attachment_links == runtime_attachments
    assert {record.capability_tier for record in records} == {
        CapabilityTier.STATICALLY_PROVED,
        CapabilityTier.RUNTIME_BACKED,
        CapabilityTier.HEURISTIC_FRONTIER,
        CapabilityTier.UNSUPPORTED_OPAQUE,
    }


def test_selection_and_warning_trace_summary_stays_typed_and_aligned() -> None:
    """Selection and warning traces can carry explicit tier-aware summaries."""
    trace_summary = SemanticUnitTraceSummary(
        subject_id="def:pkg.models:User",
        subject_kind=SemanticSubjectKind.SYMBOL,
        primary_capability_tier=CapabilityTier.STATICALLY_PROVED,
        primary_evidence_origin=EvidenceOriginKind.STATIC_DERIVATION_RULE,
        primary_replay_status=ReplayStatus.DETERMINISTIC_STATIC,
        attached_runtime_provenance_record_ids=("prov:symbol:runtime:1",),
    )
    selection = SemanticSelectionRecord(
        unit_id="def:pkg.models:User",
        detail="summary",
        token_count=12,
        basis=SelectionBasis.HEURISTIC_CANDIDATE,
        reason="selected for query",
        edit_score=0.6,
        support_score=0.3,
        trace_summary=trace_summary,
    )
    warning = SemanticOptimizationWarning(
        code=SemanticOptimizationWarningCode.BUDGET_PRESSURE,
        message="selected with downgraded detail",
        unit_id="def:pkg.models:User",
        trace_summary=trace_summary,
    )

    assert selection.trace_summary == trace_summary
    assert warning.trace_summary == trace_summary
    assert trace_summary.has_attached_runtime_provenance is True


@pytest.mark.parametrize(
    ("primary_evidence_origin", "primary_replay_status"),
    [
        (
            EvidenceOriginKind.HEURISTIC_RULE,
            ReplayStatus.DETERMINISTIC_STATIC,
        ),
        (
            EvidenceOriginKind.STATIC_DERIVATION_RULE,
            ReplayStatus.NON_PROOF_HEURISTIC,
        ),
    ],
)
def test_semantic_unit_trace_summary_rejects_misaligned_primary_contract_values(
    primary_evidence_origin: EvidenceOriginKind,
    primary_replay_status: ReplayStatus,
) -> None:
    """Trace summaries must honor the same tier-origin-replay mapping as records."""
    with pytest.raises(ValueError, match="primary_capability_tier contract"):
        SemanticUnitTraceSummary(
            subject_id="def:pkg.models:User",
            subject_kind=SemanticSubjectKind.SYMBOL,
            primary_capability_tier=CapabilityTier.STATICALLY_PROVED,
            primary_evidence_origin=primary_evidence_origin,
            primary_replay_status=primary_replay_status,
        )


def test_trace_summary_rejects_invalid_subject_kind_primary_tier() -> None:
    """Trace summaries reject subject-kind and primary-tier mismatches."""
    with pytest.raises(ValueError, match="primary_capability_tier contract"):
        SemanticUnitTraceSummary(
            subject_id="frontier:call:invalid",
            subject_kind=SemanticSubjectKind.FRONTIER_ITEM,
            primary_capability_tier=CapabilityTier.STATICALLY_PROVED,
            primary_evidence_origin=EvidenceOriginKind.STATIC_DERIVATION_RULE,
            primary_replay_status=ReplayStatus.DETERMINISTIC_STATIC,
        )


def test_semantic_unit_trace_summary_keeps_runtime_provenance_additive() -> None:
    """Runtime-backed record IDs stay additive instead of becoming primary truth."""
    trace_summary = SemanticUnitTraceSummary(
        subject_id="def:pkg.models:User",
        subject_kind=SemanticSubjectKind.SYMBOL,
        primary_capability_tier=CapabilityTier.STATICALLY_PROVED,
        primary_evidence_origin=EvidenceOriginKind.STATIC_DERIVATION_RULE,
        primary_replay_status=ReplayStatus.DETERMINISTIC_STATIC,
        attached_runtime_provenance_record_ids=("prov:symbol:runtime:1",),
    )

    assert trace_summary.has_attached_runtime_provenance is True

    with pytest.raises(ValueError, match="may not be runtime-backed"):
        SemanticUnitTraceSummary(
            subject_id="def:pkg.models:User",
            subject_kind=SemanticSubjectKind.SYMBOL,
            primary_capability_tier=CapabilityTier.RUNTIME_BACKED,
            primary_evidence_origin=EvidenceOriginKind.RUNTIME_PROBE_IDENTITY,
            primary_replay_status=ReplayStatus.REPRODUCIBLE_RUNTIME,
            attached_runtime_provenance_record_ids=("prov:symbol:runtime:1",),
        )


def test_semantic_diagnostic_boundaries_stay_typed_and_aligned() -> None:
    """Diagnostic boundary records expose typed tier/runtime classifications."""
    trace_summary = SemanticUnitTraceSummary(
        subject_id="frontier:call:1",
        subject_kind=SemanticSubjectKind.FRONTIER_ITEM,
        primary_capability_tier=CapabilityTier.HEURISTIC_FRONTIER,
        primary_evidence_origin=EvidenceOriginKind.HEURISTIC_RULE,
        primary_replay_status=ReplayStatus.NON_PROOF_HEURISTIC,
        attached_runtime_provenance_record_ids=("prov:frontier:runtime:1",),
    )
    boundary = SemanticDiagnosticBoundary(
        unit_id="frontier:call:1",
        status=SemanticDiagnosticUnitStatus.TOO_SHALLOW,
        boundary_kind=(
            SemanticDiagnosticBoundaryKind.HEURISTIC_FRONTIER_WITH_ATTACHED_RUNTIME_SUPPORT
        ),
        primary_capability_tier=CapabilityTier.HEURISTIC_FRONTIER,
        has_attached_runtime_provenance=True,
        trace_summary=trace_summary,
    )
    result = context_ir.SemanticDiagnosticResult(
        grounded_unit_ids=("frontier:call:1",),
        omitted_unit_ids=(),
        too_shallow_unit_ids=("frontier:call:1",),
        sufficiently_represented_unit_ids=(),
        recommended_expansions=("frontier:call:1",),
        reason="Frontier runtime-supported boundary was too shallow.",
        boundary_classifications=(boundary,),
    )

    assert result.boundary_classifications == (boundary,)
    assert boundary.needs_runtime_backed_support is False


def test_semantic_provenance_record_rejects_misaligned_contract_values() -> None:
    """Tier, replay, and subject-kind invariants stay explicit in the schema."""
    with pytest.raises(ValueError, match="capability_tier contract"):
        SemanticProvenanceRecord(
            record_id="prov:frontier:invalid",
            subject_kind=SemanticSubjectKind.FRONTIER_ITEM,
            subject_id="frontier:call:invalid",
            capability_tier=CapabilityTier.STATICALLY_PROVED,
            evidence_origin=EvidenceOriginKind.STATIC_DERIVATION_RULE,
            origin_detail="call_resolution",
            replay_status=ReplayStatus.DETERMINISTIC_STATIC,
            subject_sites=(make_site("site:frontier:invalid"),),
        )


@pytest.mark.parametrize(
    ("subject_kind", "subject_id"),
    [
        (
            SemanticSubjectKind.FRONTIER_ITEM,
            "frontier:call:runtime",
        ),
        (
            SemanticSubjectKind.UNSUPPORTED_FINDING,
            "unsupported:exec:runtime",
        ),
    ],
)
def test_runtime_backed_provenance_accepts_frontier_and_unsupported_subjects(
    subject_kind: SemanticSubjectKind,
    subject_id: str,
) -> None:
    """Runtime-backed provenance may attach to frontier and unsupported subjects."""
    record = SemanticProvenanceRecord(
        record_id=f"prov:{subject_kind.value}:runtime",
        subject_kind=subject_kind,
        subject_id=subject_id,
        capability_tier=CapabilityTier.RUNTIME_BACKED,
        evidence_origin=EvidenceOriginKind.RUNTIME_PROBE_IDENTITY,
        origin_detail="probe:runtime:subject",
        replay_status=ReplayStatus.REPRODUCIBLE_RUNTIME,
        repository_snapshot_basis=RepositorySnapshotBasis(
            snapshot_kind="git_commit",
            snapshot_id="abc123def456",
        ),
        attachment_links=(
            RuntimeAttachmentLink(
                attachment_id=f"attachment:{subject_kind.value}:stdout",
                attachment_role="stdout",
            ),
        ),
        subject_sites=(make_site(f"site:{subject_kind.value}:subject"),),
    )

    assert record.subject_kind is subject_kind
    assert record.subject_id == subject_id
    assert record.capability_tier is CapabilityTier.RUNTIME_BACKED


def test_runtime_backed_provenance_requires_snapshot_basis_and_attachments() -> None:
    """Runtime-backed records must carry admissibility metadata."""
    runtime_attachment = RuntimeAttachmentLink(
        attachment_id="attachment:runtime:stdout",
        attachment_role="stdout",
    )
    runtime_snapshot = RepositorySnapshotBasis(
        snapshot_kind="git_commit",
        snapshot_id="abc123def456",
        is_dirty_worktree=True,
    )

    with pytest.raises(ValueError, match="repository_snapshot_basis"):
        SemanticProvenanceRecord(
            record_id="prov:runtime:missing-snapshot",
            subject_kind=SemanticSubjectKind.SYMBOL,
            subject_id="sym:pkg.runtime:Runner",
            capability_tier=CapabilityTier.RUNTIME_BACKED,
            evidence_origin=EvidenceOriginKind.RUNTIME_PROBE_IDENTITY,
            origin_detail="probe:runner:init",
            replay_status=ReplayStatus.REPRODUCIBLE_RUNTIME,
            attachment_links=(runtime_attachment,),
            evidence_sites=(make_site("site:runtime:probe"),),
        )

    with pytest.raises(ValueError, match="attachment_links"):
        SemanticProvenanceRecord(
            record_id="prov:runtime:missing-attachment",
            subject_kind=SemanticSubjectKind.SYMBOL,
            subject_id="sym:pkg.runtime:Runner",
            capability_tier=CapabilityTier.RUNTIME_BACKED,
            evidence_origin=EvidenceOriginKind.RUNTIME_PROBE_IDENTITY,
            origin_detail="probe:runner:init",
            replay_status=ReplayStatus.REPRODUCIBLE_RUNTIME,
            repository_snapshot_basis=runtime_snapshot,
            evidence_sites=(make_site("site:runtime:probe"),),
        )


def test_non_runtime_provenance_rejects_runtime_only_metadata() -> None:
    """Non-runtime tiers may not carry runtime-backed admissibility metadata."""
    runtime_snapshot = RepositorySnapshotBasis(
        snapshot_kind="git_commit",
        snapshot_id="abc123def456",
    )

    with pytest.raises(ValueError, match="only valid for runtime-backed provenance"):
        SemanticProvenanceRecord(
            record_id="prov:static:runtime-only-metadata",
            subject_kind=SemanticSubjectKind.SYMBOL,
            subject_id="def:pkg.models:User",
            capability_tier=CapabilityTier.STATICALLY_PROVED,
            evidence_origin=EvidenceOriginKind.STATIC_DERIVATION_RULE,
            origin_detail="call_resolution",
            replay_status=ReplayStatus.DETERMINISTIC_STATIC,
            repository_snapshot_basis=runtime_snapshot,
            subject_sites=(make_site("site:def:user"),),
        )


def test_syntax_program_diagnostics_surface_parse_failures() -> None:
    """SyntaxProgram can carry explicit parse-failure diagnostics."""
    diagnostic = SyntaxDiagnostic(
        diagnostic_id="syntax:pkg/models.py:parse_error",
        file_id="file:pkg/models.py",
        site=make_site("site:syntax:1"),
        code=SyntaxDiagnosticCode.PARSE_ERROR,
        message="invalid syntax",
    )
    syntax = SyntaxProgram(repo_root=Path("/tmp/repo"), diagnostics=[diagnostic])

    assert syntax.diagnostics == [diagnostic]
    assert syntax.diagnostics[0].code is SyntaxDiagnosticCode.PARSE_ERROR


def test_syntax_program_can_carry_parameter_facts() -> None:
    """SyntaxProgram retains syntax-only parameter facts for later binding."""
    parameter = ParameterFact(
        parameter_id="parameter:def:pkg/models.py:pkg.models.make:0",
        owner_definition_id="def:pkg/models.py:pkg.models.make",
        name="value",
        kind=ParameterKind.POSITIONAL_OR_KEYWORD,
        ordinal=0,
        site=make_site("site:param:1"),
        annotation_text="int",
        has_default=True,
        default_value_text="1",
    )
    syntax = SyntaxProgram(repo_root=Path("/tmp/repo"), parameters=[parameter])

    assert syntax.parameters == [parameter]
    assert syntax.parameters[0].kind is ParameterKind.POSITIONAL_OR_KEYWORD
    assert syntax.parameters[0].default_value_text == "1"


def test_semantic_program_keeps_diagnostics_separate_from_frontier() -> None:
    """Diagnostics remain a distinct surface from unresolved frontier items."""
    syntax = SyntaxProgram(repo_root=Path("/tmp/repo"))
    unresolved = UnresolvedAccess(
        access_id="frontier:name:1",
        site=make_site("site:name:1"),
        access_text="unknown_name",
        context=ReferenceContext.LOAD,
        enclosing_scope_id="scope:function:run",
        reason_code=UnresolvedReasonCode.UNRESOLVED_NAME,
    )
    diagnostic = ResolverDiagnostic(
        diagnostic_id="diag:1",
        site=make_site("site:diag:1"),
        severity=DiagnosticSeverity.WARNING,
        reason_code=UnresolvedReasonCode.UNRESOLVED_NAME,
        message="Could not resolve unknown_name",
    )
    program = SemanticProgram(
        repo_root=Path("/tmp/repo"),
        syntax=syntax,
        unresolved_frontier=[unresolved],
        diagnostics=[diagnostic],
    )

    assert program.unresolved_frontier == [unresolved]
    assert program.diagnostics == [diagnostic]


def test_analyze_repository_returns_semantic_program(tmp_path: Path) -> None:
    """The public analysis API returns a semantic program."""
    (tmp_path / "example.py").write_text("VALUE = 1\n", encoding="utf-8")

    program = analyze_repository(tmp_path)

    assert isinstance(program, SemanticProgram)
    assert program.repo_root == tmp_path

"""Eval oracle loading and selector resolution."""

from __future__ import annotations

import ast
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar, cast

from context_ir.analyzer import analyze_repository
from context_ir.runtime_acquisition import (
    DynamicImportRuntimeObservation,
    HasattrRuntimeObservation,
    _RuntimeObservationField,
    attach_dynamic_import_runtime_provenance,
    attach_hasattr_runtime_provenance,
)
from context_ir.semantic_types import (
    CallSiteFact,
    CapabilityTier,
    DownstreamVisibility,
    EvidenceOriginKind,
    ReferenceContext,
    ReplayStatus,
    RepositorySnapshotBasis,
    ResolvedSymbol,
    ResolvedSymbolKind,
    RuntimeAttachmentLink,
    SemanticProgram,
    SemanticSubjectKind,
    SemanticUnitTraceSummary,
    SourceSite,
    SourceSpan,
    UnresolvedAccess,
    UnresolvedReasonCode,
    UnsupportedConstruct,
)

OracleRole = Literal["edit", "support"]
OracleMinDetail = Literal["identity", "summary", "source"]
ResolutionStatus = Literal["resolved", "unresolved", "ambiguous"]
_CandidateT = TypeVar(
    "_CandidateT",
    ResolvedSymbol,
    UnresolvedAccess,
    UnsupportedConstruct,
)

_ALLOWED_MIN_DETAIL = frozenset({"identity", "summary", "source"})
_ALLOWED_ROLES = frozenset({"edit", "support"})
_ALLOWED_TASK_FIELDS = frozenset({"task_id", "fixture_id", "expected_selectors"})
_ALLOWED_SYMBOL_SELECTOR_FIELDS = frozenset(
    {
        "kind",
        "qualified_name",
        "role",
        "min_detail",
        "symbol_kind",
        "rationale",
        "expected_primary_capability_tier",
        "expect_attached_runtime_provenance",
    }
)
_ALLOWED_FRONTIER_SELECTOR_FIELDS = frozenset(
    {
        "kind",
        "file_path",
        "access_text",
        "context",
        "reason_code",
        "min_detail",
        "enclosing_qualified_name",
        "source_snippet",
        "rationale",
        "expected_primary_capability_tier",
        "expect_attached_runtime_provenance",
    }
)
_ALLOWED_UNSUPPORTED_SELECTOR_FIELDS = frozenset(
    {
        "kind",
        "file_path",
        "construct_text",
        "reason_code",
        "min_detail",
        "enclosing_qualified_name",
        "source_snippet",
        "rationale",
        "expected_primary_capability_tier",
        "expect_attached_runtime_provenance",
    }
)
_FORBIDDEN_GENERATED_ID_FIELDS = frozenset(
    {
        "access_id",
        "access_ids",
        "construct_id",
        "construct_ids",
        "resolved_unit_id",
        "resolved_unit_ids",
        "semantic_unit_id",
        "semantic_unit_ids",
        "symbol_id",
        "symbol_ids",
        "unit_id",
        "unit_ids",
    }
)
_PRIMARY_TRACE_DEFAULTS: dict[
    SemanticSubjectKind, tuple[CapabilityTier, EvidenceOriginKind, ReplayStatus]
] = {
    SemanticSubjectKind.SYMBOL: (
        CapabilityTier.STATICALLY_PROVED,
        EvidenceOriginKind.STATIC_DERIVATION_RULE,
        ReplayStatus.DETERMINISTIC_STATIC,
    ),
    SemanticSubjectKind.FRONTIER_ITEM: (
        CapabilityTier.HEURISTIC_FRONTIER,
        EvidenceOriginKind.HEURISTIC_RULE,
        ReplayStatus.NON_PROOF_HEURISTIC,
    ),
    SemanticSubjectKind.UNSUPPORTED_FINDING: (
        CapabilityTier.UNSUPPORTED_OPAQUE,
        EvidenceOriginKind.UNSUPPORTED_REASON_CODE,
        ReplayStatus.OPAQUE_BOUNDARY,
    ),
}
_RUNTIME_OBSERVATION_FILENAME = "eval_runtime_observations.json"
_DYNAMIC_IMPORT_RUNTIME_OBSERVATION_FILENAME = _RUNTIME_OBSERVATION_FILENAME
_HASATTR_RUNTIME_OBSERVATION_FILENAME = _RUNTIME_OBSERVATION_FILENAME
_ALLOWED_RUNTIME_OBSERVATION_DOCUMENT_FIELDS = frozenset(
    {
        "schema_version",
        "dynamic_import_runtime_observations",
        "hasattr_runtime_observations",
    }
)
_ALLOWED_DYNAMIC_IMPORT_OBSERVATION_FIELDS = frozenset(
    {
        "file_path",
        "start_line",
        "start_column",
        "end_line",
        "end_column",
        "source_snippet",
        "probe_identifier",
        "probe_contract_revision",
        "repository_snapshot_basis",
        "attachment_links",
        "replay_target",
        "replay_selector",
        "replay_inputs",
        "runtime_assumptions",
        "normalized_payload",
        "durable_payload_reference",
    }
)
_ALLOWED_HASATTR_OBSERVATION_FIELDS = _ALLOWED_DYNAMIC_IMPORT_OBSERVATION_FIELDS
_ALLOWED_REPOSITORY_SNAPSHOT_BASIS_FIELDS = frozenset(
    {"snapshot_kind", "snapshot_id", "is_dirty_worktree"}
)
_ALLOWED_RUNTIME_ATTACHMENT_LINK_FIELDS = frozenset(
    {"attachment_id", "attachment_role", "description"}
)
_ALLOWED_RUNTIME_FIELD_FIELDS = frozenset({"key", "value"})


class EvalOracleSchemaError(ValueError):
    """Raised when a durable eval task record violates the oracle schema."""


class EvalOracleResolutionError(RuntimeError):
    """Raised when one or more oracle selectors do not resolve exactly once."""

    def __init__(
        self,
        message: str,
        failures: tuple[ResolvedOracleSelector, ...],
    ) -> None:
        """Initialize the error with the failed selector records."""
        super().__init__(message)
        self.failures = failures


@dataclass(frozen=True)
class SymbolOracleSelector:
    """Durable selector for a resolved semantic symbol."""

    kind: Literal["symbol"]
    qualified_name: str
    role: OracleRole
    min_detail: OracleMinDetail
    symbol_kind: ResolvedSymbolKind | None = None
    rationale: str | None = None
    expected_primary_capability_tier: CapabilityTier | None = None
    expect_attached_runtime_provenance: bool | None = None


@dataclass(frozen=True)
class FrontierOracleSelector:
    """Durable selector for an unresolved frontier access."""

    kind: Literal["frontier"]
    file_path: str
    access_text: str
    context: ReferenceContext
    reason_code: UnresolvedReasonCode
    min_detail: OracleMinDetail
    enclosing_qualified_name: str | None = None
    source_snippet: str | None = None
    rationale: str | None = None
    expected_primary_capability_tier: CapabilityTier | None = None
    expect_attached_runtime_provenance: bool | None = None


@dataclass(frozen=True)
class UnsupportedOracleSelector:
    """Durable selector for an unsupported semantic construct."""

    kind: Literal["unsupported"]
    file_path: str
    construct_text: str
    reason_code: UnresolvedReasonCode
    min_detail: OracleMinDetail
    enclosing_qualified_name: str | None = None
    source_snippet: str | None = None
    rationale: str | None = None
    expected_primary_capability_tier: CapabilityTier | None = None
    expect_attached_runtime_provenance: bool | None = None


OracleSelector = (
    SymbolOracleSelector | FrontierOracleSelector | UnsupportedOracleSelector
)


@dataclass(frozen=True)
class EvalOracleTask:
    """Durable eval oracle task loaded from a repository JSON asset."""

    task_id: str
    fixture_id: str
    expected_selectors: tuple[OracleSelector, ...]


@dataclass(frozen=True)
class ResolvedOracleSelector:
    """Runtime resolution result for one durable oracle selector."""

    selector: OracleSelector
    resolution_status: ResolutionStatus
    resolved_unit_id: str | None
    resolved_file_path: str | None
    resolved_span: SourceSpan | None
    failure_reason: str | None
    candidate_count: int
    candidate_summaries: tuple[str, ...]
    primary_capability_tier: CapabilityTier | None = None
    primary_evidence_origin: EvidenceOriginKind | None = None
    primary_replay_status: ReplayStatus | None = None
    has_attached_runtime_provenance: bool | None = None
    attached_runtime_provenance_record_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvalOracleSetup:
    """Resolved eval oracle task setup tied to one analyzed semantic program."""

    task: EvalOracleTask
    semantic_program: SemanticProgram
    resolved_selectors: tuple[ResolvedOracleSelector, ...]


def load_eval_oracle_task(task_path: Path | str) -> EvalOracleTask:
    """Load a durable eval oracle task JSON file into typed selectors."""
    path = Path(task_path)
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise EvalOracleSchemaError(f"invalid task JSON in {path}: {error}") from error
    _reject_generated_id_fields(raw, path="$")
    record = _expect_object(raw, path="$")
    _validate_allowed_fields(record, _ALLOWED_TASK_FIELDS, path="$")
    task_id = _required_string(record, "task_id", path="$")
    fixture_id = _required_string(record, "fixture_id", path="$")
    selector_records = _required_list(record, "expected_selectors", path="$")
    selectors = tuple(
        _parse_selector(selector_record, path=f"$.expected_selectors[{index}]")
        for index, selector_record in enumerate(selector_records)
    )
    if not selectors:
        raise EvalOracleSchemaError("task must contain at least one expected selector")
    return EvalOracleTask(
        task_id=task_id,
        fixture_id=fixture_id,
        expected_selectors=selectors,
    )


def setup_eval_oracle_task(
    task_path: Path | str,
    repo_root: Path | str | None = None,
) -> EvalOracleSetup:
    """Load and resolve an eval oracle task against its fixture repository."""
    task = load_eval_oracle_task(task_path)
    root = (
        Path(repo_root)
        if repo_root is not None
        else _default_fixture_root(
            Path(task_path),
            task.fixture_id,
        )
    )
    program = analyze_repository(root)
    dynamic_import_runtime_observations = (
        load_fixture_dynamic_import_runtime_observations(
            root,
            semantic_program=program,
        )
    )
    if dynamic_import_runtime_observations:
        program = attach_dynamic_import_runtime_provenance(
            program,
            dynamic_import_runtime_observations,
        )
    hasattr_runtime_observations = load_fixture_hasattr_runtime_observations(
        root,
        semantic_program=program,
    )
    if hasattr_runtime_observations:
        program = attach_hasattr_runtime_provenance(
            program,
            hasattr_runtime_observations,
        )
    return _resolved_eval_oracle_setup(task, program)


def resolve_eval_oracle_task(
    task: EvalOracleTask,
    repo_root: Path | str,
) -> EvalOracleSetup:
    """Resolve every durable selector through ``analyze_repository``."""
    program = analyze_repository(Path(repo_root))
    return _resolved_eval_oracle_setup(task, program)


def load_fixture_dynamic_import_runtime_observations(
    repo_root: Path | str,
    *,
    semantic_program: SemanticProgram | None = None,
) -> tuple[DynamicImportRuntimeObservation, ...]:
    """Load fixture-local dynamic-import runtime observations when present."""
    root = Path(repo_root)
    observation_path = root / _DYNAMIC_IMPORT_RUNTIME_OBSERVATION_FILENAME
    if not observation_path.is_file():
        return ()

    try:
        raw: object = json.loads(observation_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise EvalOracleSchemaError(
            f"invalid dynamic-import runtime observation JSON in "
            f"{observation_path}: {error}"
        ) from error
    _reject_generated_id_fields(raw, path="$")
    record = _expect_object(raw, path="$")
    _validate_allowed_fields(
        record,
        _ALLOWED_RUNTIME_OBSERVATION_DOCUMENT_FIELDS,
        path="$",
    )
    schema_version = _required_string(record, "schema_version", path="$")
    if schema_version != "v1":
        raise EvalOracleSchemaError("$.schema_version must be 'v1'")
    observation_records = _optional_list(
        record,
        "dynamic_import_runtime_observations",
        path="$",
    )
    if observation_records is None:
        return ()
    if not observation_records:
        raise EvalOracleSchemaError(
            "dynamic-import runtime observation file must contain at least one "
            "observation"
        )

    program = (
        semantic_program if semantic_program is not None else analyze_repository(root)
    )
    site_index = _dynamic_import_observation_site_index(program)
    return tuple(
        _parse_dynamic_import_runtime_observation(
            observation_record,
            path=f"$.dynamic_import_runtime_observations[{index}]",
            site_index=site_index,
        )
        for index, observation_record in enumerate(observation_records)
    )


def load_fixture_hasattr_runtime_observations(
    repo_root: Path | str,
    *,
    semantic_program: SemanticProgram | None = None,
) -> tuple[HasattrRuntimeObservation, ...]:
    """Load fixture-local ``hasattr`` runtime observations when present."""
    root = Path(repo_root)
    observation_path = root / _HASATTR_RUNTIME_OBSERVATION_FILENAME
    if not observation_path.is_file():
        return ()

    try:
        raw: object = json.loads(observation_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise EvalOracleSchemaError(
            f"invalid hasattr runtime observation JSON in {observation_path}: {error}"
        ) from error
    _reject_generated_id_fields(raw, path="$")
    record = _expect_object(raw, path="$")
    _validate_allowed_fields(
        record,
        _ALLOWED_RUNTIME_OBSERVATION_DOCUMENT_FIELDS,
        path="$",
    )
    schema_version = _required_string(record, "schema_version", path="$")
    if schema_version != "v1":
        raise EvalOracleSchemaError("$.schema_version must be 'v1'")
    observation_records = _optional_list(
        record,
        "hasattr_runtime_observations",
        path="$",
    )
    if observation_records is None:
        return ()
    if not observation_records:
        raise EvalOracleSchemaError(
            "hasattr runtime observation file must contain at least one observation"
        )

    program = (
        semantic_program if semantic_program is not None else analyze_repository(root)
    )
    site_index = _hasattr_observation_site_index(program)
    return tuple(
        _parse_hasattr_runtime_observation(
            observation_record,
            path=f"$.hasattr_runtime_observations[{index}]",
            site_index=site_index,
        )
        for index, observation_record in enumerate(observation_records)
    )


def _resolved_eval_oracle_setup(
    task: EvalOracleTask,
    program: SemanticProgram,
) -> EvalOracleSetup:
    """Resolve one oracle task against an already analyzed semantic program."""
    resolved_selectors = tuple(
        _resolve_selector(selector=selector, program=program)
        for selector in task.expected_selectors
    )
    failures = tuple(
        resolved_selector
        for resolved_selector in resolved_selectors
        if resolved_selector.resolution_status != "resolved"
    )
    if failures:
        raise EvalOracleResolutionError(
            _resolution_failure_message(task.task_id, failures),
            failures,
        )
    return EvalOracleSetup(
        task=task,
        semantic_program=program,
        resolved_selectors=resolved_selectors,
    )


def _default_fixture_root(task_path: Path, fixture_id: str) -> Path:
    """Return the conventional fixture root for a task asset path."""
    return task_path.parent.parent / "fixtures" / fixture_id


def _dynamic_import_observation_site_index(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], SourceSite]:
    """Index eligible dynamic-import source sites by file/span identity."""
    site_index: dict[tuple[str, int, int, int, int], SourceSite] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.DYNAMIC_IMPORT:
            continue
        identity = _source_site_identity(construct.site)
        if identity in site_index:
            raise EvalOracleSchemaError(
                "multiple dynamic-import unsupported constructs share the same "
                "source site"
            )
        site_index[identity] = construct.site
    return site_index


def _hasattr_observation_site_index(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], SourceSite]:
    """Index eligible ``hasattr(obj, name)`` source sites by file/span identity."""
    call_sites_by_unsupported_id = {
        f"unsupported:{call_site.call_site_id}": call_site
        for call_site in program.syntax.call_sites
    }
    site_index: dict[tuple[str, int, int, int, int], SourceSite] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
            continue
        call_site = call_sites_by_unsupported_id.get(construct.construct_id)
        if call_site is None or not _is_eligible_hasattr_call_site(call_site):
            continue
        identity = _source_site_identity(construct.site)
        if identity in site_index:
            raise EvalOracleSchemaError(
                "multiple hasattr unsupported constructs share the same source site"
            )
        site_index[identity] = construct.site
    return site_index


def _is_eligible_hasattr_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is the fixture-loadable ``hasattr`` form."""
    if call_site.argument_count != 2:
        return False
    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(expression, ast.Name) and expression.id == "hasattr"


def _parse_dynamic_import_runtime_observation(
    raw: object,
    *,
    path: str,
    site_index: dict[tuple[str, int, int, int, int], SourceSite],
) -> DynamicImportRuntimeObservation:
    """Parse one fixture-local dynamic-import runtime observation record."""
    record = _expect_object(raw, path=path)
    _validate_allowed_fields(
        record,
        _ALLOWED_DYNAMIC_IMPORT_OBSERVATION_FIELDS,
        path=path,
    )
    site = _matched_dynamic_import_observation_site(
        file_path=_required_string(record, "file_path", path=path),
        start_line=_required_positive_int(record, "start_line", path=path),
        start_column=_required_non_negative_int(record, "start_column", path=path),
        end_line=_required_positive_int(record, "end_line", path=path),
        end_column=_required_non_negative_int(record, "end_column", path=path),
        source_snippet=_optional_string(record, "source_snippet", path=path),
        site_index=site_index,
        path=path,
    )
    return DynamicImportRuntimeObservation(
        site=site,
        probe_identifier=_required_string(record, "probe_identifier", path=path),
        probe_contract_revision=_required_string(
            record,
            "probe_contract_revision",
            path=path,
        ),
        repository_snapshot_basis=_required_repository_snapshot_basis(
            record,
            path=path,
        ),
        attachment_links=_required_runtime_attachment_links(record, path=path),
        replay_target=_required_string(record, "replay_target", path=path),
        replay_selector=_required_string(record, "replay_selector", path=path),
        replay_inputs=_optional_runtime_fields(record, "replay_inputs", path=path),
        runtime_assumptions=_optional_runtime_fields(
            record,
            "runtime_assumptions",
            path=path,
        ),
        normalized_payload=_required_runtime_fields(
            record,
            "normalized_payload",
            path=path,
        ),
        durable_payload_reference=_optional_string(
            record,
            "durable_payload_reference",
            path=path,
        ),
    )


def _parse_hasattr_runtime_observation(
    raw: object,
    *,
    path: str,
    site_index: dict[tuple[str, int, int, int, int], SourceSite],
) -> HasattrRuntimeObservation:
    """Parse one fixture-local ``hasattr`` runtime observation record."""
    record = _expect_object(raw, path=path)
    _validate_allowed_fields(
        record,
        _ALLOWED_HASATTR_OBSERVATION_FIELDS,
        path=path,
    )
    site = _matched_hasattr_observation_site(
        file_path=_required_string(record, "file_path", path=path),
        start_line=_required_positive_int(record, "start_line", path=path),
        start_column=_required_non_negative_int(record, "start_column", path=path),
        end_line=_required_positive_int(record, "end_line", path=path),
        end_column=_required_non_negative_int(record, "end_column", path=path),
        source_snippet=_optional_string(record, "source_snippet", path=path),
        site_index=site_index,
        path=path,
    )
    return HasattrRuntimeObservation(
        site=site,
        probe_identifier=_required_string(record, "probe_identifier", path=path),
        probe_contract_revision=_required_string(
            record,
            "probe_contract_revision",
            path=path,
        ),
        repository_snapshot_basis=_required_repository_snapshot_basis(
            record,
            path=path,
        ),
        attachment_links=_required_runtime_attachment_links(record, path=path),
        replay_target=_required_string(record, "replay_target", path=path),
        replay_selector=_required_string(record, "replay_selector", path=path),
        replay_inputs=_optional_runtime_fields(record, "replay_inputs", path=path),
        runtime_assumptions=_optional_runtime_fields(
            record,
            "runtime_assumptions",
            path=path,
        ),
        normalized_payload=_required_runtime_fields(
            record,
            "normalized_payload",
            path=path,
        ),
        durable_payload_reference=_optional_string(
            record,
            "durable_payload_reference",
            path=path,
        ),
    )


def _matched_dynamic_import_observation_site(
    *,
    file_path: str,
    start_line: int,
    start_column: int,
    end_line: int,
    end_column: int,
    source_snippet: str | None,
    site_index: dict[tuple[str, int, int, int, int], SourceSite],
    path: str,
) -> SourceSite:
    """Return the analyzed source site matching one fixture observation record."""
    identity = (file_path, start_line, start_column, end_line, end_column)
    site = site_index.get(identity)
    if site is None:
        raise EvalOracleSchemaError(
            f"{path} does not match any analyzed dynamic-import source site"
        )
    if source_snippet is not None and site.snippet != source_snippet:
        raise EvalOracleSchemaError(
            f"{path}.source_snippet does not match the analyzed source site"
        )
    return site


def _matched_hasattr_observation_site(
    *,
    file_path: str,
    start_line: int,
    start_column: int,
    end_line: int,
    end_column: int,
    source_snippet: str | None,
    site_index: dict[tuple[str, int, int, int, int], SourceSite],
    path: str,
) -> SourceSite:
    """Return the analyzed source site matching one ``hasattr`` observation."""
    identity = (file_path, start_line, start_column, end_line, end_column)
    site = site_index.get(identity)
    if site is None:
        raise EvalOracleSchemaError(
            f"{path} does not match any analyzed eligible hasattr source site"
        )
    if source_snippet is not None and site.snippet != source_snippet:
        raise EvalOracleSchemaError(
            f"{path}.source_snippet does not match the analyzed source site"
        )
    return site


def _required_repository_snapshot_basis(
    record: dict[str, object],
    *,
    path: str,
) -> RepositorySnapshotBasis:
    """Parse one required repository snapshot basis object."""
    basis_record = _required_object(record, "repository_snapshot_basis", path=path)
    _validate_allowed_fields(
        basis_record,
        _ALLOWED_REPOSITORY_SNAPSHOT_BASIS_FIELDS,
        path=f"{path}.repository_snapshot_basis",
    )
    return RepositorySnapshotBasis(
        snapshot_kind=_required_string(
            basis_record,
            "snapshot_kind",
            path=f"{path}.repository_snapshot_basis",
        ),
        snapshot_id=_required_string(
            basis_record,
            "snapshot_id",
            path=f"{path}.repository_snapshot_basis",
        ),
        is_dirty_worktree=_optional_bool(
            basis_record,
            "is_dirty_worktree",
            path=f"{path}.repository_snapshot_basis",
        )
        or False,
    )


def _required_runtime_attachment_links(
    record: dict[str, object],
    *,
    path: str,
) -> tuple[RuntimeAttachmentLink, ...]:
    """Parse required runtime attachment link metadata."""
    link_records = _required_list(record, "attachment_links", path=path)
    return tuple(
        _runtime_attachment_link(
            link_record,
            path=f"{path}.attachment_links[{index}]",
        )
        for index, link_record in enumerate(link_records)
    )


def _runtime_attachment_link(
    raw: object,
    *,
    path: str,
) -> RuntimeAttachmentLink:
    """Parse one runtime attachment link object."""
    record = _expect_object(raw, path=path)
    _validate_allowed_fields(
        record,
        _ALLOWED_RUNTIME_ATTACHMENT_LINK_FIELDS,
        path=path,
    )
    return RuntimeAttachmentLink(
        attachment_id=_required_string(record, "attachment_id", path=path),
        attachment_role=_required_string(record, "attachment_role", path=path),
        description=_optional_string(record, "description", path=path),
    )


def _required_runtime_fields(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> tuple[_RuntimeObservationField, ...]:
    """Parse one required non-empty runtime field collection."""
    field_records = _required_list(record, key, path=path)
    if not field_records:
        raise EvalOracleSchemaError(f"{path}.{key} must contain at least one field")
    return tuple(
        _runtime_observation_field(
            field_record,
            path=f"{path}.{key}[{index}]",
        )
        for index, field_record in enumerate(field_records)
    )


def _optional_runtime_fields(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> tuple[_RuntimeObservationField, ...]:
    """Parse an optional runtime field collection."""
    field_records = _optional_list(record, key, path=path)
    if field_records is None:
        return ()
    return tuple(
        _runtime_observation_field(
            field_record,
            path=f"{path}.{key}[{index}]",
        )
        for index, field_record in enumerate(field_records)
    )


def _runtime_observation_field(
    raw: object,
    *,
    path: str,
) -> _RuntimeObservationField:
    """Parse one key/value runtime observation field entry."""
    record = _expect_object(raw, path=path)
    _validate_allowed_fields(record, _ALLOWED_RUNTIME_FIELD_FIELDS, path=path)
    return _RuntimeObservationField(
        key=_required_string(record, "key", path=path),
        value=_required_string(record, "value", path=path),
    )


def _source_site_identity(site: SourceSite) -> tuple[str, int, int, int, int]:
    """Return the stable file/span identity for one analyzed source site."""
    span = site.span
    return (
        site.file_path,
        span.start_line,
        span.start_column,
        span.end_line,
        span.end_column,
    )


def _parse_selector(raw: object, *, path: str) -> OracleSelector:
    """Parse one selector JSON object into its typed dataclass."""
    record = _expect_object(raw, path=path)
    kind = _required_string(record, "kind", path=path)
    if kind == "symbol":
        return _parse_symbol_selector(record, path=path)
    if kind == "frontier":
        return _parse_frontier_selector(record, path=path)
    if kind == "unsupported":
        return _parse_unsupported_selector(record, path=path)
    raise EvalOracleSchemaError(f"{path}.kind must be symbol, frontier, or unsupported")


def _parse_symbol_selector(
    record: dict[str, object],
    *,
    path: str,
) -> SymbolOracleSelector:
    """Parse a symbol selector object."""
    _validate_allowed_fields(record, _ALLOWED_SYMBOL_SELECTOR_FIELDS, path=path)
    return SymbolOracleSelector(
        kind="symbol",
        qualified_name=_required_string(record, "qualified_name", path=path),
        role=_parse_role(_required_string(record, "role", path=path), path=path),
        min_detail=_parse_min_detail(
            _required_string(record, "min_detail", path=path),
            path=path,
        ),
        symbol_kind=_optional_resolved_symbol_kind(record, path=path),
        rationale=_optional_string(record, "rationale", path=path),
        expected_primary_capability_tier=_optional_expected_primary_capability_tier(
            record,
            path=path,
        ),
        expect_attached_runtime_provenance=_optional_bool(
            record,
            "expect_attached_runtime_provenance",
            path=path,
        ),
    )


def _parse_frontier_selector(
    record: dict[str, object],
    *,
    path: str,
) -> FrontierOracleSelector:
    """Parse a frontier selector object."""
    _validate_allowed_fields(record, _ALLOWED_FRONTIER_SELECTOR_FIELDS, path=path)
    return FrontierOracleSelector(
        kind="frontier",
        file_path=_required_string(record, "file_path", path=path),
        access_text=_required_string(record, "access_text", path=path),
        context=_parse_reference_context(
            _required_string(record, "context", path=path),
            path=f"{path}.context",
        ),
        reason_code=_parse_reason_code(
            _required_string(record, "reason_code", path=path),
            path=f"{path}.reason_code",
        ),
        min_detail=_parse_min_detail(
            _required_string(record, "min_detail", path=path),
            path=path,
        ),
        enclosing_qualified_name=_optional_string(
            record,
            "enclosing_qualified_name",
            path=path,
        ),
        source_snippet=_optional_string(record, "source_snippet", path=path),
        rationale=_optional_string(record, "rationale", path=path),
        expected_primary_capability_tier=_optional_expected_primary_capability_tier(
            record,
            path=path,
        ),
        expect_attached_runtime_provenance=_optional_bool(
            record,
            "expect_attached_runtime_provenance",
            path=path,
        ),
    )


def _parse_unsupported_selector(
    record: dict[str, object],
    *,
    path: str,
) -> UnsupportedOracleSelector:
    """Parse an unsupported selector object."""
    _validate_allowed_fields(record, _ALLOWED_UNSUPPORTED_SELECTOR_FIELDS, path=path)
    return UnsupportedOracleSelector(
        kind="unsupported",
        file_path=_required_string(record, "file_path", path=path),
        construct_text=_required_string(record, "construct_text", path=path),
        reason_code=_parse_reason_code(
            _required_string(record, "reason_code", path=path),
            path=f"{path}.reason_code",
        ),
        min_detail=_parse_min_detail(
            _required_string(record, "min_detail", path=path),
            path=path,
        ),
        enclosing_qualified_name=_optional_string(
            record,
            "enclosing_qualified_name",
            path=path,
        ),
        source_snippet=_optional_string(record, "source_snippet", path=path),
        rationale=_optional_string(record, "rationale", path=path),
        expected_primary_capability_tier=_optional_expected_primary_capability_tier(
            record,
            path=path,
        ),
        expect_attached_runtime_provenance=_optional_bool(
            record,
            "expect_attached_runtime_provenance",
            path=path,
        ),
    )


def _resolve_selector(
    *,
    selector: OracleSelector,
    program: SemanticProgram,
) -> ResolvedOracleSelector:
    """Resolve one typed selector against the analyzed semantic program."""
    if isinstance(selector, SymbolOracleSelector):
        return _resolve_symbol_selector(selector=selector, program=program)
    if isinstance(selector, FrontierOracleSelector):
        return _resolve_frontier_selector(selector=selector, program=program)
    return _resolve_unsupported_selector(selector=selector, program=program)


def _resolve_symbol_selector(
    *,
    selector: SymbolOracleSelector,
    program: SemanticProgram,
) -> ResolvedOracleSelector:
    """Resolve a symbol selector to exactly one resolved symbol."""
    candidates = tuple(
        symbol
        for symbol in program.resolved_symbols.values()
        if symbol.qualified_name == selector.qualified_name
        and (selector.symbol_kind is None or symbol.kind is selector.symbol_kind)
    )
    return _resolved_record_from_candidates(
        selector=selector,
        candidates=candidates,
        unit_id=lambda symbol: symbol.symbol_id,
        site=lambda symbol: symbol.definition_site,
        summary=_symbol_candidate_summary,
        program=program,
    )


def _resolve_frontier_selector(
    *,
    selector: FrontierOracleSelector,
    program: SemanticProgram,
) -> ResolvedOracleSelector:
    """Resolve a frontier selector to exactly one unresolved access."""
    candidates = tuple(
        access
        for access in program.unresolved_frontier
        if access.site.file_path == selector.file_path
        and access.access_text == selector.access_text
        and access.context is selector.context
        and access.reason_code is selector.reason_code
        and _matches_enclosing_qualified_name(
            selector.enclosing_qualified_name,
            access.enclosing_scope_id,
            program,
        )
        and _matches_source_snippet(selector.source_snippet, access.site)
    )
    return _resolved_record_from_candidates(
        selector=selector,
        candidates=candidates,
        unit_id=lambda access: access.access_id,
        site=lambda access: access.site,
        summary=_frontier_candidate_summary,
        program=program,
    )


def _resolve_unsupported_selector(
    *,
    selector: UnsupportedOracleSelector,
    program: SemanticProgram,
) -> ResolvedOracleSelector:
    """Resolve an unsupported selector to exactly one unsupported construct."""
    candidates = tuple(
        construct
        for construct in program.unsupported_constructs
        if construct.site.file_path == selector.file_path
        and construct.construct_text == selector.construct_text
        and construct.reason_code is selector.reason_code
        and _matches_enclosing_qualified_name(
            selector.enclosing_qualified_name,
            construct.enclosing_scope_id,
            program,
        )
        and _matches_source_snippet(selector.source_snippet, construct.site)
    )
    return _resolved_record_from_candidates(
        selector=selector,
        candidates=candidates,
        unit_id=lambda construct: construct.construct_id,
        site=lambda construct: construct.site,
        summary=_unsupported_candidate_summary,
        program=program,
    )


def _resolved_record_from_candidates(
    *,
    selector: OracleSelector,
    candidates: tuple[_CandidateT, ...],
    unit_id: Callable[[_CandidateT], str],
    site: Callable[[_CandidateT], SourceSite],
    summary: Callable[[_CandidateT], str],
    program: SemanticProgram,
) -> ResolvedOracleSelector:
    """Build the standard resolution record from a candidate list."""
    if len(candidates) == 1:
        candidate = candidates[0]
        candidate_site = site(candidate)
        trace_summary = _selector_trace_summary(
            selector=selector,
            subject_id=unit_id(candidate),
            program=program,
        )
        return ResolvedOracleSelector(
            selector=selector,
            resolution_status="resolved",
            resolved_unit_id=unit_id(candidate),
            resolved_file_path=candidate_site.file_path,
            resolved_span=candidate_site.span,
            failure_reason=None,
            candidate_count=1,
            candidate_summaries=(),
            primary_capability_tier=trace_summary.primary_capability_tier,
            primary_evidence_origin=trace_summary.primary_evidence_origin,
            primary_replay_status=trace_summary.primary_replay_status,
            has_attached_runtime_provenance=(
                trace_summary.has_attached_runtime_provenance
            ),
            attached_runtime_provenance_record_ids=(
                trace_summary.attached_runtime_provenance_record_ids
            ),
        )
    if len(candidates) > 1:
        return ResolvedOracleSelector(
            selector=selector,
            resolution_status="ambiguous",
            resolved_unit_id=None,
            resolved_file_path=None,
            resolved_span=None,
            failure_reason=f"selector matched {len(candidates)} candidates",
            candidate_count=len(candidates),
            candidate_summaries=tuple(summary(candidate) for candidate in candidates),
        )
    return ResolvedOracleSelector(
        selector=selector,
        resolution_status="unresolved",
        resolved_unit_id=None,
        resolved_file_path=None,
        resolved_span=None,
        failure_reason="selector matched no candidates",
        candidate_count=0,
        candidate_summaries=(),
    )


def _matches_enclosing_qualified_name(
    expected_qualified_name: str | None,
    enclosing_scope_id: str | None,
    program: SemanticProgram,
) -> bool:
    """Return whether an enclosing scope matches an optional qualified selector."""
    if expected_qualified_name is None:
        return True
    if enclosing_scope_id is None:
        return False
    symbol = program.resolved_symbols.get(enclosing_scope_id)
    return symbol is not None and symbol.qualified_name == expected_qualified_name


def _matches_source_snippet(
    expected_source_snippet: str | None,
    site: SourceSite,
) -> bool:
    """Return whether a source site matches an optional source snippet."""
    if expected_source_snippet is None:
        return True
    return site.snippet is not None and site.snippet.strip() == expected_source_snippet


def _symbol_candidate_summary(symbol: ResolvedSymbol) -> str:
    """Return a diagnostic summary for one symbol candidate."""
    return (
        f"{symbol.symbol_id} {symbol.kind.value} {symbol.qualified_name} "
        f"{_site_summary(symbol.definition_site)}"
    )


def _frontier_candidate_summary(access: UnresolvedAccess) -> str:
    """Return a diagnostic summary for one frontier candidate."""
    return (
        f"{access.access_id} {access.context.value} {access.access_text} "
        f"{access.reason_code.value} {_site_summary(access.site)}"
    )


def _unsupported_candidate_summary(construct: UnsupportedConstruct) -> str:
    """Return a diagnostic summary for one unsupported candidate."""
    return (
        f"{construct.construct_id} {construct.construct_text} "
        f"{construct.reason_code.value} {_site_summary(construct.site)}"
    )


def _site_summary(site: SourceSite) -> str:
    """Return a compact source location summary."""
    span = site.span
    return (
        f"{site.file_path}:{span.start_line}:{span.start_column}-"
        f"{span.end_line}:{span.end_column}"
    )


def _resolution_failure_message(
    task_id: str,
    failures: tuple[ResolvedOracleSelector, ...],
) -> str:
    """Return a clear setup failure message for unresolved selectors."""
    details = "; ".join(
        f"{failure.resolution_status} selector with "
        f"{failure.candidate_count} candidates: {failure.failure_reason}"
        for failure in failures
    )
    return f"eval oracle task {task_id!r} failed selector setup: {details}"


def _reject_generated_id_fields(value: object, *, path: str) -> None:
    """Reject generated semantic unit identifiers in durable task JSON."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise EvalOracleSchemaError(f"{path} contains a non-string key")
            child_path = f"{path}.{key}"
            if key in _FORBIDDEN_GENERATED_ID_FIELDS:
                raise EvalOracleSchemaError(
                    f"{child_path} is a generated runtime identifier field"
                )
            _reject_generated_id_fields(child, path=child_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_generated_id_fields(item, path=f"{path}[{index}]")


def _expect_object(value: object, *, path: str) -> dict[str, object]:
    """Return ``value`` as an object record or raise a schema error."""
    if not isinstance(value, dict):
        raise EvalOracleSchemaError(f"{path} must be an object")
    record: dict[str, object] = {}
    for key, child in value.items():
        if not isinstance(key, str):
            raise EvalOracleSchemaError(f"{path} contains a non-string key")
        record[key] = child
    return record


def _validate_allowed_fields(
    record: dict[str, object],
    allowed_fields: frozenset[str],
    *,
    path: str,
) -> None:
    """Reject fields outside the schema contract for one object record."""
    unknown_fields = sorted(set(record) - allowed_fields)
    if unknown_fields:
        field_list = ", ".join(sorted(allowed_fields))
        raise EvalOracleSchemaError(
            f"{path} contains unknown field {unknown_fields[0]!r}; "
            f"allowed fields: {field_list}"
        )


def _required_list(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> list[object]:
    """Return a required list field from a schema object."""
    value = record.get(key)
    if not isinstance(value, list):
        raise EvalOracleSchemaError(f"{path}.{key} must be a list")
    return value


def _optional_list(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> list[object] | None:
    """Return an optional list field from a schema object."""
    value = record.get(key)
    if value is None:
        return None
    if not isinstance(value, list):
        raise EvalOracleSchemaError(f"{path}.{key} must be a list")
    return value


def _required_object(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> dict[str, object]:
    """Return a required object field from a schema object."""
    return _expect_object(record.get(key), path=f"{path}.{key}")


def _required_string(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> str:
    """Return a required non-empty string field from a schema object."""
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise EvalOracleSchemaError(f"{path}.{key} must be a non-empty string")
    return value


def _required_positive_int(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> int:
    """Return a required positive integer field from a schema object."""
    value = record.get(key)
    if type(value) is not int or value <= 0:
        raise EvalOracleSchemaError(f"{path}.{key} must be a positive integer")
    return value


def _required_non_negative_int(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> int:
    """Return a required non-negative integer field from a schema object."""
    value = record.get(key)
    if type(value) is not int or value < 0:
        raise EvalOracleSchemaError(f"{path}.{key} must be a non-negative integer")
    return value


def _optional_string(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> str | None:
    """Return an optional string field from a schema object."""
    value = record.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise EvalOracleSchemaError(f"{path}.{key} must be a non-empty string")
    return value


def _parse_role(value: str, *, path: str) -> OracleRole:
    """Parse an oracle role string."""
    if value not in _ALLOWED_ROLES:
        raise EvalOracleSchemaError(f"{path}.role must be edit or support")
    return cast(OracleRole, value)


def _parse_min_detail(value: str, *, path: str) -> OracleMinDetail:
    """Parse a minimum detail string."""
    if value not in _ALLOWED_MIN_DETAIL:
        raise EvalOracleSchemaError(
            f"{path}.min_detail must be identity, summary, or source"
        )
    return cast(OracleMinDetail, value)


def _optional_expected_primary_capability_tier(
    record: dict[str, object],
    *,
    path: str,
) -> CapabilityTier | None:
    """Parse an optional expected primary capability tier."""
    value = _optional_string(record, "expected_primary_capability_tier", path=path)
    if value is None:
        return None
    try:
        tier = CapabilityTier(value)
    except ValueError as error:
        raise EvalOracleSchemaError(
            f"{path}.expected_primary_capability_tier is not supported"
        ) from error
    if tier is CapabilityTier.RUNTIME_BACKED:
        raise EvalOracleSchemaError(
            f"{path}.expected_primary_capability_tier must be statically_proved, "
            "heuristic/frontier, or unsupported/opaque"
        )
    return tier


def _optional_bool(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> bool | None:
    """Return an optional boolean field from a schema object."""
    value = record.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise EvalOracleSchemaError(f"{path}.{key} must be a boolean")
    return value


def _optional_resolved_symbol_kind(
    record: dict[str, object],
    *,
    path: str,
) -> ResolvedSymbolKind | None:
    """Parse an optional resolved symbol kind string."""
    value = _optional_string(record, "symbol_kind", path=path)
    if value is None:
        return None
    try:
        return ResolvedSymbolKind(value)
    except ValueError as error:
        raise EvalOracleSchemaError(f"{path}.symbol_kind is not supported") from error


def _selector_trace_summary(
    *,
    selector: OracleSelector,
    subject_id: str,
    program: SemanticProgram,
) -> SemanticUnitTraceSummary:
    """Return the compile-visible trace summary for one resolved selector subject."""
    subject_kind = _selector_subject_kind(selector)
    ordered_records = tuple(
        sorted(
            (
                record
                for record in program.provenance_records
                if record.subject_kind is subject_kind
                and record.subject_id == subject_id
                and DownstreamVisibility.COMPILE in record.downstream_visibility
            ),
            key=lambda record: record.record_id,
        )
    )
    primary_record = next(
        (
            record
            for record in ordered_records
            if record.capability_tier is not CapabilityTier.RUNTIME_BACKED
        ),
        None,
    )
    if primary_record is None:
        (
            primary_capability_tier,
            primary_evidence_origin,
            primary_replay_status,
        ) = _PRIMARY_TRACE_DEFAULTS[subject_kind]
    else:
        primary_capability_tier = primary_record.capability_tier
        primary_evidence_origin = primary_record.evidence_origin
        primary_replay_status = primary_record.replay_status
    return SemanticUnitTraceSummary(
        subject_id=subject_id,
        subject_kind=subject_kind,
        primary_capability_tier=primary_capability_tier,
        primary_evidence_origin=primary_evidence_origin,
        primary_replay_status=primary_replay_status,
        attached_runtime_provenance_record_ids=tuple(
            record.record_id
            for record in ordered_records
            if record.capability_tier is CapabilityTier.RUNTIME_BACKED
        ),
    )


def _selector_subject_kind(selector: OracleSelector) -> SemanticSubjectKind:
    """Return the semantic subject kind implied by one durable selector."""
    if selector.kind == "symbol":
        return SemanticSubjectKind.SYMBOL
    if selector.kind == "frontier":
        return SemanticSubjectKind.FRONTIER_ITEM
    return SemanticSubjectKind.UNSUPPORTED_FINDING


def _parse_reference_context(value: str, *, path: str) -> ReferenceContext:
    """Parse a reference context string."""
    try:
        return ReferenceContext(value)
    except ValueError as error:
        raise EvalOracleSchemaError(f"{path} is not a supported context") from error


def _parse_reason_code(value: str, *, path: str) -> UnresolvedReasonCode:
    """Parse an unresolved reason code string."""
    try:
        return UnresolvedReasonCode(value)
    except ValueError as error:
        raise EvalOracleSchemaError(f"{path} is not a supported reason code") from error

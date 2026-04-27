"""Runtime-backed provenance attachment for already-admissible observations."""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from enum import Enum

from context_ir.semantic_types import (
    CallSiteFact,
    CapabilityTier,
    EvidenceOriginKind,
    MetaclassKeywordFact,
    ReplayStatus,
    RepositorySnapshotBasis,
    RuntimeAttachmentLink,
    SemanticDependency,
    SemanticProgram,
    SemanticProvenanceRecord,
    SemanticSubjectKind,
    SourceSite,
    UnresolvedAccess,
    UnresolvedReasonCode,
    UnsupportedConstruct,
)


@dataclass(frozen=True)
class _RuntimeObservationField:
    """Normalized runtime observation metadata entry."""

    key: str
    value: str

    def __post_init__(self) -> None:
        """Reject incomplete normalized metadata entries."""
        if not self.key.strip():
            raise ValueError("runtime observation field key must be non-empty")
        if not self.value.strip():
            raise ValueError("runtime observation field value must be non-empty")


class _RuntimeObservationOutcome(Enum):
    """Outcomes recorded for one already-collected runtime observation."""

    OBSERVED = "observed"
    CRASHED = "crashed"
    TIMED_OUT = "timed_out"
    MISSING_ENVIRONMENT = "missing_environment"


_GETATTR_LOOKUP_OUTCOMES_BY_ARGUMENT_COUNT = {
    2: frozenset(
        {
            "returned_value",
            "raised_attribute_error",
        }
    ),
    3: frozenset(
        {
            "returned_value",
            "returned_default_value",
        }
    ),
}

_VARS_LOOKUP_OUTCOMES_BY_ARGUMENT_COUNT = {
    0: frozenset(
        {
            "returned_namespace",
        }
    ),
    1: frozenset(
        {
            "returned_namespace",
            "raised_type_error",
        }
    ),
}

_EXEC_PASS_SOURCE_SHA256 = hashlib.sha256(b"pass").hexdigest()


@dataclass(frozen=True)
class _RuntimeObservation:
    """Internal typed contract for runtime observations eligible for attachment."""

    subject_kind: SemanticSubjectKind
    subject_id: str
    outcome: _RuntimeObservationOutcome
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis | None
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class DynamicImportRuntimeObservation:
    """Admissible runtime observation for one dynamic-import boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class EvalRuntimeObservation:
    """Admissible runtime observation for one bounded ``eval(source)`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class ExecRuntimeObservation:
    """Admissible runtime observation for one bounded ``exec(source)`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class HasattrRuntimeObservation:
    """Admissible runtime observation for one ``hasattr(obj, name)`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class GetattrRuntimeObservation:
    """Admissible runtime observation for one ``getattr(obj, name)`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class DirRuntimeObservation:
    """Admissible runtime observation for one attachable ``dir`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class VarsRuntimeObservation:
    """Admissible runtime observation for one attachable ``vars`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class GlobalsRuntimeObservation:
    """Admissible runtime observation for one attachable ``globals()`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class LocalsRuntimeObservation:
    """Admissible runtime observation for one attachable ``locals()`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class SetattrRuntimeObservation:
    """Admissible runtime observation for one attachable ``setattr`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class DelattrRuntimeObservation:
    """Admissible runtime observation for one attachable ``delattr`` boundary."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


@dataclass(frozen=True)
class MetaclassBehaviorRuntimeObservation:
    """Admissible runtime observation for one attachable metaclass keyword site."""

    site: SourceSite
    probe_identifier: str
    probe_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    attachment_links: tuple[RuntimeAttachmentLink, ...]
    replay_target: str
    replay_selector: str
    replay_inputs: tuple[_RuntimeObservationField, ...] = ()
    runtime_assumptions: tuple[_RuntimeObservationField, ...] = ()
    normalized_payload: tuple[_RuntimeObservationField, ...] = ()
    durable_payload_reference: str | None = None


def attach_runtime_observations(
    program: SemanticProgram,
    observations: Sequence[_RuntimeObservation],
) -> SemanticProgram:
    """Attach admissible runtime-backed provenance to a new semantic program."""
    site_index = _build_site_index(program)
    existing_record_ids = {record.record_id for record in program.provenance_records}
    generated_record_ids: set[str] = set()
    new_records: list[SemanticProvenanceRecord] = []

    for observation in observations:
        _validate_observation(observation)
        subject_sites, evidence_sites = _resolve_observation_sites(
            program=program,
            observation=observation,
            site_index=site_index,
        )
        origin_detail = _build_origin_detail(observation)
        record_id = _build_record_id(
            subject_kind=observation.subject_kind,
            subject_id=observation.subject_id,
            origin_detail=origin_detail,
        )
        if record_id in existing_record_ids:
            raise ValueError(
                "generated runtime-backed provenance record_id already exists in "
                "program.provenance_records"
            )
        if record_id in generated_record_ids:
            raise ValueError(
                "generated runtime-backed provenance record_id is duplicated "
                "within observations"
            )
        generated_record_ids.add(record_id)
        new_records.append(
            SemanticProvenanceRecord(
                record_id=record_id,
                subject_kind=observation.subject_kind,
                subject_id=observation.subject_id,
                capability_tier=CapabilityTier.RUNTIME_BACKED,
                evidence_origin=EvidenceOriginKind.RUNTIME_PROBE_IDENTITY,
                origin_detail=origin_detail,
                replay_status=ReplayStatus.REPRODUCIBLE_RUNTIME,
                repository_snapshot_basis=observation.repository_snapshot_basis,
                attachment_links=observation.attachment_links,
                subject_sites=subject_sites,
                evidence_sites=evidence_sites,
            )
        )

    return replace(
        program,
        provenance_records=[*program.provenance_records, *new_records],
    )


def attach_dynamic_import_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[DynamicImportRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible dynamic-import boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_dynamic_import_constructs(program)
    matched_observations = [
        _runtime_observation_from_dynamic_import_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_eval_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[EvalRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``eval(source)`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_eval_constructs(program)
    matched_observations = [
        _runtime_observation_from_eval_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_exec_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[ExecRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``exec(source)`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_exec_constructs(program)
    matched_observations = [
        _runtime_observation_from_exec_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_hasattr_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[HasattrRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``hasattr`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_hasattr_constructs(program)
    matched_observations = [
        _runtime_observation_from_hasattr_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_getattr_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[GetattrRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``getattr`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_getattr_constructs(program)
    matched_observations: list[_RuntimeObservation] = []
    for observation in observations:
        matched_construct = eligible_constructs.get(
            _source_site_identity(observation.site)
        )
        if matched_construct is None:
            continue
        construct, call_argument_count = matched_construct
        matched_observations.append(
            _runtime_observation_from_getattr_observation(
                construct=construct,
                call_argument_count=call_argument_count,
                observation=observation,
            )
        )
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_vars_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[VarsRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``vars`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_vars_constructs(program)
    matched_observations: list[_RuntimeObservation] = []
    for observation in observations:
        matched_construct = eligible_constructs.get(
            _source_site_identity(observation.site)
        )
        if matched_construct is None:
            continue
        construct, call_argument_count = matched_construct
        matched_observations.append(
            _runtime_observation_from_vars_observation(
                construct=construct,
                call_argument_count=call_argument_count,
                observation=observation,
            )
        )
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_globals_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[GlobalsRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``globals()`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_globals_constructs(program)
    matched_observations = [
        _runtime_observation_from_globals_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_setattr_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[SetattrRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``setattr`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_setattr_constructs(program)
    matched_observations = [
        _runtime_observation_from_setattr_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_locals_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[LocalsRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``locals()`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_locals_constructs(program)
    matched_observations = [
        _runtime_observation_from_locals_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_delattr_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[DelattrRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``delattr`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_delattr_constructs(program)
    matched_observations = [
        _runtime_observation_from_delattr_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_dir_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[DirRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible ``dir`` boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_dir_constructs(program)
    matched_observations = [
        _runtime_observation_from_dir_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def attach_metaclass_behavior_runtime_provenance(
    program: SemanticProgram,
    observations: Sequence[MetaclassBehaviorRuntimeObservation],
) -> SemanticProgram:
    """Attach runtime-backed provenance to eligible metaclass keyword boundaries."""
    if not observations:
        return program

    eligible_constructs = _eligible_metaclass_behavior_constructs(program)
    matched_observations = [
        _runtime_observation_from_metaclass_behavior_observation(
            construct=construct,
            observation=observation,
        )
        for observation in observations
        if (
            construct := eligible_constructs.get(
                _source_site_identity(observation.site)
            )
        )
        is not None
    ]
    if not matched_observations:
        return program
    return attach_runtime_observations(program, matched_observations)


def _validate_observation(observation: _RuntimeObservation) -> None:
    """Reject incomplete or non-admissible runtime observations."""
    if not observation.subject_id.strip():
        raise ValueError("subject_id must be non-empty")
    if not observation.probe_identifier.strip():
        raise ValueError("probe_identifier must be non-empty")
    if not observation.probe_contract_revision.strip():
        raise ValueError("probe_contract_revision must be non-empty")
    if observation.repository_snapshot_basis is None:
        raise ValueError("repository_snapshot_basis must be provided")
    if not observation.attachment_links:
        raise ValueError("attachment_links must be non-empty")
    if not observation.replay_target.strip():
        raise ValueError("replay_target must be non-empty")
    if not observation.replay_selector.strip():
        raise ValueError("replay_selector must be non-empty")
    if observation.outcome is not _RuntimeObservationOutcome.OBSERVED:
        raise ValueError(
            "non-admissible runtime observation outcome cannot be attached as "
            "runtime-backed proof"
        )
    if len(observation.attachment_links) != len(
        {link.attachment_id for link in observation.attachment_links}
    ):
        raise ValueError("attachment_links attachment_id values must be unique")
    if (
        not observation.normalized_payload
        and observation.durable_payload_reference is None
    ):
        raise ValueError(
            "runtime observations require normalized_payload or "
            "durable_payload_reference"
        )
    if observation.durable_payload_reference is not None and not (
        observation.durable_payload_reference.strip()
    ):
        raise ValueError("durable_payload_reference must be non-empty when provided")

    _normalized_field_mapping(
        observation.replay_inputs,
        field_name="replay_inputs",
    )
    _normalized_field_mapping(
        observation.runtime_assumptions,
        field_name="runtime_assumptions",
    )
    _normalized_field_mapping(
        observation.normalized_payload,
        field_name="normalized_payload",
    )


def _resolve_observation_sites(
    program: SemanticProgram,
    observation: _RuntimeObservation,
    site_index: dict[str, SourceSite],
) -> tuple[tuple[SourceSite, ...], tuple[SourceSite, ...]]:
    """Resolve subject and evidence sites for one runtime observation."""
    if observation.subject_kind is SemanticSubjectKind.SYMBOL:
        symbol = program.resolved_symbols.get(observation.subject_id)
        if symbol is None:
            raise ValueError(
                f"unknown subject_id for subject_kind=SYMBOL: {observation.subject_id}"
            )
        return (symbol.definition_site,), ()

    if observation.subject_kind is SemanticSubjectKind.DEPENDENCY:
        dependency = _find_dependency(program, observation.subject_id)
        if dependency is None:
            raise ValueError(
                "unknown subject_id for subject_kind=DEPENDENCY: "
                f"{observation.subject_id}"
            )
        return _dependency_sites(program, dependency, site_index)

    if observation.subject_kind is SemanticSubjectKind.FRONTIER_ITEM:
        frontier_item = _find_frontier_item(program, observation.subject_id)
        if frontier_item is None:
            raise ValueError(
                "unknown subject_id for subject_kind=FRONTIER_ITEM: "
                f"{observation.subject_id}"
            )
        return (frontier_item.site,), ()

    unsupported_construct = _find_unsupported_construct(program, observation.subject_id)
    if unsupported_construct is None:
        raise ValueError(
            "unknown subject_id for subject_kind=UNSUPPORTED_FINDING: "
            f"{observation.subject_id}"
        )
    return (unsupported_construct.site,), ()


def _build_origin_detail(observation: _RuntimeObservation) -> str:
    """Serialize normalized runtime-backed provenance metadata deterministically."""
    origin_payload: dict[str, object] = {
        "probe_identifier": observation.probe_identifier.strip(),
        "probe_contract_revision": observation.probe_contract_revision.strip(),
        "replay_target": observation.replay_target.strip(),
        "replay_selector": observation.replay_selector.strip(),
        "replay_inputs": _normalized_field_mapping(
            observation.replay_inputs,
            field_name="replay_inputs",
        ),
        "runtime_assumptions": _normalized_field_mapping(
            observation.runtime_assumptions,
            field_name="runtime_assumptions",
        ),
        "normalized_payload": _normalized_field_mapping(
            observation.normalized_payload,
            field_name="normalized_payload",
        ),
    }
    if observation.durable_payload_reference is not None:
        origin_payload["durable_payload_reference"] = (
            observation.durable_payload_reference.strip()
        )
    return json.dumps(origin_payload, sort_keys=True, separators=(",", ":"))


def _build_record_id(
    subject_kind: SemanticSubjectKind,
    subject_id: str,
    origin_detail: str,
) -> str:
    """Derive a stable record ID from subject identity and runtime metadata."""
    digest_source = "\n".join((subject_kind.value, subject_id, origin_detail))
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:24]
    return f"prov:runtime:{subject_kind.value}:{digest}"


def _dependency_sites(
    program: SemanticProgram,
    dependency: SemanticDependency,
    site_index: dict[str, SourceSite],
) -> tuple[tuple[SourceSite, ...], tuple[SourceSite, ...]]:
    """Resolve subject and evidence sites for a dependency-backed observation."""
    source_symbol = program.resolved_symbols.get(dependency.source_symbol_id)
    if source_symbol is None:
        raise ValueError(
            "dependency source_symbol_id is missing from resolved_symbols: "
            f"{dependency.source_symbol_id}"
        )
    target_symbol = program.resolved_symbols.get(dependency.target_symbol_id)
    if target_symbol is None:
        raise ValueError(
            "dependency target_symbol_id is missing from resolved_symbols: "
            f"{dependency.target_symbol_id}"
        )

    subject_sites = _dedupe_sites(
        (source_symbol.definition_site, target_symbol.definition_site)
    )
    if dependency.evidence_site_id is None:
        return subject_sites, ()

    evidence_site = site_index.get(dependency.evidence_site_id)
    if evidence_site is None:
        return subject_sites, ()
    return subject_sites, (evidence_site,)


def _normalized_field_mapping(
    fields: tuple[_RuntimeObservationField, ...],
    field_name: str,
) -> dict[str, str]:
    """Normalize one metadata field collection into a deterministic mapping."""
    normalized: dict[str, str] = {}
    for field in fields:
        key = field.key.strip()
        if key in normalized:
            raise ValueError(f"{field_name} keys must be unique")
        normalized[key] = field.value.strip()
    return normalized


def _build_site_index(program: SemanticProgram) -> dict[str, SourceSite]:
    """Index known source sites by site ID for evidence-site attachment."""
    return {site.site_id: site for site in _iter_program_sites(program)}


def _eligible_dynamic_import_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible dynamic-import boundaries by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.DYNAMIC_IMPORT:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_dynamic_import_call_site(
            call_site.callee_text
        ):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible dynamic-import constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _eligible_hasattr_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible ``hasattr(obj, name)`` unsupported constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_hasattr_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible hasattr constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _eligible_eval_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible ``eval(source)`` unsupported constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.EXEC_OR_EVAL:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_eval_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible eval constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _eligible_exec_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible ``exec(source)`` unsupported constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.EXEC_OR_EVAL:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_exec_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible exec constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _eligible_getattr_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], tuple[UnsupportedConstruct, int]]:
    """Index eligible ``getattr(obj, name)`` unsupported constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[
        tuple[str, int, int, int, int], tuple[UnsupportedConstruct, int]
    ] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_getattr_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible getattr constructs share the same source site"
            )
        eligible_constructs[source_identity] = (construct, call_site.argument_count)
    return eligible_constructs


def _eligible_vars_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], tuple[UnsupportedConstruct, int]]:
    """Index eligible ``vars`` unsupported constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[
        tuple[str, int, int, int, int], tuple[UnsupportedConstruct, int]
    ] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_vars_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible vars constructs share the same source site"
            )
        eligible_constructs[source_identity] = (construct, call_site.argument_count)
    return eligible_constructs


def _eligible_globals_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible ``globals()`` unsupported constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_globals_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible globals constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _eligible_locals_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible ``locals()`` unsupported constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_locals_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible locals constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _eligible_delattr_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible ``delattr(obj, name)`` constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_delattr_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible delattr constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _eligible_setattr_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible ``setattr(obj, name, value)`` constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.RUNTIME_MUTATION:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_setattr_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible setattr constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _eligible_dir_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible ``dir`` unsupported constructs by source site."""
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.REFLECTIVE_BUILTIN:
            continue
        call_site = _call_site_for_unsupported_construct(
            construct=construct,
            call_sites_by_id=call_sites_by_id,
        )
        if call_site is None or not _is_supported_dir_call_site(call_site):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible dir constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _eligible_metaclass_behavior_constructs(
    program: SemanticProgram,
) -> dict[tuple[str, int, int, int, int], UnsupportedConstruct]:
    """Index eligible metaclass keyword constructs by preserved keyword site."""
    metaclass_keywords_by_id = {
        metaclass_keyword.metaclass_keyword_id: metaclass_keyword
        for metaclass_keyword in program.syntax.metaclass_keywords
    }
    eligible_constructs: dict[tuple[str, int, int, int, int], UnsupportedConstruct] = {}
    for construct in program.unsupported_constructs:
        if construct.reason_code is not UnresolvedReasonCode.METACLASS_BEHAVIOR:
            continue
        metaclass_keyword = _metaclass_keyword_for_unsupported_construct(
            construct=construct,
            metaclass_keywords_by_id=metaclass_keywords_by_id,
        )
        if metaclass_keyword is None:
            continue
        if construct.construct_text != metaclass_keyword.keyword_text:
            continue
        if _source_site_identity(construct.site) != _source_site_identity(
            metaclass_keyword.site
        ):
            continue
        source_identity = _source_site_identity(construct.site)
        if source_identity in eligible_constructs:
            raise ValueError(
                "multiple eligible metaclass constructs share the same source site"
            )
        eligible_constructs[source_identity] = construct
    return eligible_constructs


def _call_site_for_unsupported_construct(
    *,
    construct: UnsupportedConstruct,
    call_sites_by_id: dict[str, CallSiteFact],
) -> CallSiteFact | None:
    """Return the originating call site for one unsupported call construct."""
    if not construct.construct_id.startswith("unsupported:"):
        return None
    call_site_id = construct.construct_id.removeprefix("unsupported:")
    return call_sites_by_id.get(call_site_id)


def _metaclass_keyword_for_unsupported_construct(
    *,
    construct: UnsupportedConstruct,
    metaclass_keywords_by_id: dict[str, MetaclassKeywordFact],
) -> MetaclassKeywordFact | None:
    """Return the originating metaclass keyword for one unsupported construct."""
    if not construct.construct_id.startswith("unsupported:"):
        return None
    metaclass_keyword_id = construct.construct_id.removeprefix("unsupported:")
    return metaclass_keywords_by_id.get(metaclass_keyword_id)


def _is_supported_dynamic_import_call_site(callee_text: str) -> bool:
    """Return whether ``callee_text`` is currently an attachable dynamic import."""
    try:
        expression = ast.parse(callee_text, mode="eval").body
    except SyntaxError:
        return False

    if isinstance(expression, ast.Name):
        return True

    attribute_names = _attribute_chain_names(expression)
    return attribute_names == ("import_module",)


def _is_supported_hasattr_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is the accepted attachable ``hasattr`` form."""
    if call_site.argument_count != 2:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(expression, ast.Name) and expression.id == "hasattr"


def _is_supported_eval_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is the accepted attachable ``eval`` form."""
    if call_site.argument_count != 1:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    if not (isinstance(expression, ast.Name) and expression.id == "eval"):
        return False

    snippet = call_site.site.snippet
    if snippet is None:
        return False
    try:
        call_expression = ast.parse(snippet.strip(), mode="eval").body
    except SyntaxError:
        return False
    return (
        isinstance(call_expression, ast.Call)
        and isinstance(call_expression.func, ast.Name)
        and call_expression.func.id == "eval"
        and len(call_expression.args) == 1
        and not call_expression.keywords
        and isinstance(call_expression.args[0], ast.Name)
        and call_expression.args[0].id == "source"
    )


def _is_supported_exec_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is the accepted attachable ``exec`` form."""
    if call_site.argument_count != 1:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    if not (isinstance(expression, ast.Name) and expression.id == "exec"):
        return False

    snippet = call_site.site.snippet
    if snippet is None:
        return False
    try:
        call_expression = ast.parse(snippet.strip(), mode="eval").body
    except SyntaxError:
        return False
    return (
        isinstance(call_expression, ast.Call)
        and isinstance(call_expression.func, ast.Name)
        and call_expression.func.id == "exec"
        and len(call_expression.args) == 1
        and not call_expression.keywords
        and isinstance(call_expression.args[0], ast.Name)
        and call_expression.args[0].id == "source"
    )


def _is_supported_getattr_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is the accepted attachable ``getattr`` form."""
    if call_site.argument_count not in {2, 3}:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(expression, ast.Name) and expression.id == "getattr"


def _is_supported_vars_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is an accepted attachable ``vars`` form."""
    if call_site.argument_count not in {0, 1}:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(expression, ast.Name) and expression.id == "vars"


def _is_supported_globals_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is the accepted attachable ``globals()`` form."""
    if call_site.argument_count != 0:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(expression, ast.Name) and expression.id == "globals"


def _is_supported_locals_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is the accepted attachable ``locals()`` form."""
    if call_site.argument_count != 0:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(expression, ast.Name) and expression.id == "locals"


def _is_supported_setattr_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is the accepted attachable ``setattr`` form."""
    if call_site.argument_count != 3:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(expression, ast.Name) and expression.id == "setattr"


def _is_supported_delattr_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is the accepted attachable ``delattr`` form."""
    if call_site.argument_count != 2:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(expression, ast.Name) and expression.id == "delattr"


def _is_supported_dir_call_site(call_site: CallSiteFact) -> bool:
    """Return whether ``call_site`` is an accepted attachable ``dir`` form."""
    if call_site.argument_count not in {0, 1}:
        return False

    try:
        expression = ast.parse(call_site.callee_text, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(expression, ast.Name) and expression.id == "dir"


def _attribute_chain_names(expression: ast.AST) -> tuple[str, ...] | None:
    """Return dotted attribute names for a simple rooted chain."""
    if not isinstance(expression, ast.Attribute):
        return None

    attribute_names: list[str] = []
    current: ast.AST = expression
    while isinstance(current, ast.Attribute):
        attribute_names.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    attribute_names.reverse()
    return tuple(attribute_names)


def _runtime_observation_from_dynamic_import_observation(
    *,
    construct: UnsupportedConstruct,
    observation: DynamicImportRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched dynamic-import observation into the generic contract."""
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_hasattr_observation(
    *,
    construct: UnsupportedConstruct,
    observation: HasattrRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``hasattr`` observation into the generic contract."""
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_eval_observation(
    *,
    construct: UnsupportedConstruct,
    observation: EvalRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``eval`` observation into the generic contract."""
    _validate_eval_evaluation_outcome(observation.normalized_payload)
    _validate_eval_replay_inputs(observation.replay_inputs)
    _validate_eval_durable_payload_reference(observation)
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_exec_observation(
    *,
    construct: UnsupportedConstruct,
    observation: ExecRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``exec`` observation into the generic contract."""
    _validate_exec_execution_outcome(observation.normalized_payload)
    _validate_exec_replay_inputs(observation.replay_inputs)
    _validate_exec_durable_payload_reference(observation)
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_getattr_observation(
    *,
    construct: UnsupportedConstruct,
    call_argument_count: int,
    observation: GetattrRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``getattr`` observation into the generic contract."""
    _validate_getattr_lookup_outcome(
        observation.normalized_payload,
        call_argument_count=call_argument_count,
    )
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_vars_observation(
    *,
    construct: UnsupportedConstruct,
    call_argument_count: int,
    observation: VarsRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``vars`` observation into the generic contract."""
    _validate_vars_lookup_outcome(
        observation.normalized_payload,
        call_argument_count=call_argument_count,
    )
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_globals_observation(
    *,
    construct: UnsupportedConstruct,
    observation: GlobalsRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``globals()`` observation into the generic contract."""
    _validate_globals_lookup_outcome(observation.normalized_payload)
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_locals_observation(
    *,
    construct: UnsupportedConstruct,
    observation: LocalsRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``locals()`` observation into the generic contract."""
    _validate_locals_lookup_outcome(observation.normalized_payload)
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_delattr_observation(
    *,
    construct: UnsupportedConstruct,
    observation: DelattrRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``delattr`` observation into the generic contract."""
    _validate_delattr_mutation_outcome(observation.normalized_payload)
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_setattr_observation(
    *,
    construct: UnsupportedConstruct,
    observation: SetattrRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``setattr`` observation into the generic contract."""
    _validate_setattr_mutation_outcome(observation.normalized_payload)
    _validate_setattr_durable_payload_reference(observation)
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_dir_observation(
    *,
    construct: UnsupportedConstruct,
    observation: DirRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched ``dir`` observation into the generic contract."""
    _validate_dir_durable_payload_reference(observation)
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _runtime_observation_from_metaclass_behavior_observation(
    *,
    construct: UnsupportedConstruct,
    observation: MetaclassBehaviorRuntimeObservation,
) -> _RuntimeObservation:
    """Translate one matched metaclass observation into the generic contract."""
    _validate_metaclass_behavior_class_creation_outcome(observation.normalized_payload)
    _validate_metaclass_behavior_durable_payload_reference(observation)
    return _RuntimeObservation(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        outcome=_RuntimeObservationOutcome.OBSERVED,
        probe_identifier=observation.probe_identifier,
        probe_contract_revision=observation.probe_contract_revision,
        repository_snapshot_basis=observation.repository_snapshot_basis,
        attachment_links=observation.attachment_links,
        replay_target=observation.replay_target,
        replay_selector=observation.replay_selector,
        replay_inputs=observation.replay_inputs,
        runtime_assumptions=observation.runtime_assumptions,
        normalized_payload=observation.normalized_payload,
        durable_payload_reference=observation.durable_payload_reference,
    )


def _validate_getattr_lookup_outcome(
    normalized_payload: tuple[_RuntimeObservationField, ...],
    *,
    call_argument_count: int,
) -> None:
    """Require the bounded ``getattr`` runtime payload for this slice."""
    payload = _normalized_field_mapping(
        normalized_payload,
        field_name="normalized_payload",
    )
    if set(payload) != {"lookup_outcome"}:
        raise ValueError(
            "getattr runtime observations require normalized_payload.lookup_outcome"
        )

    lookup_outcome = payload["lookup_outcome"]
    allowed_outcomes = _GETATTR_LOOKUP_OUTCOMES_BY_ARGUMENT_COUNT.get(
        call_argument_count
    )
    if allowed_outcomes is None:
        raise ValueError(
            "getattr runtime observations require an eligible call-site arity"
        )
    if lookup_outcome not in allowed_outcomes:
        allowed_outcomes_text = " or ".join(
            f"'{outcome}'" for outcome in sorted(allowed_outcomes)
        )
        raise ValueError(
            "getattr runtime observations require lookup_outcome to be "
            f"{allowed_outcomes_text}"
        )


def _validate_vars_lookup_outcome(
    normalized_payload: tuple[_RuntimeObservationField, ...],
    *,
    call_argument_count: int,
) -> None:
    """Require the bounded ``vars`` runtime payload for this slice."""
    payload = _normalized_field_mapping(
        normalized_payload,
        field_name="normalized_payload",
    )
    if set(payload) != {"lookup_outcome"}:
        raise ValueError(
            "vars runtime observations require normalized_payload.lookup_outcome"
        )

    lookup_outcome = payload["lookup_outcome"]
    allowed_outcomes = _VARS_LOOKUP_OUTCOMES_BY_ARGUMENT_COUNT.get(call_argument_count)
    if allowed_outcomes is None:
        raise ValueError(
            "vars runtime observations require an eligible call-site arity"
        )
    if lookup_outcome not in allowed_outcomes:
        allowed_outcomes_text = " or ".join(
            f"'{outcome}'" for outcome in sorted(allowed_outcomes)
        )
        raise ValueError(
            "vars runtime observations require lookup_outcome to be "
            f"{allowed_outcomes_text}"
        )


def _validate_eval_evaluation_outcome(
    normalized_payload: tuple[_RuntimeObservationField, ...],
) -> None:
    """Require the bounded ``eval`` runtime payload for this slice."""
    payload = _normalized_field_mapping(
        normalized_payload,
        field_name="normalized_payload",
    )
    evaluation_outcome = payload.get("evaluation_outcome")
    if evaluation_outcome is None:
        raise ValueError(
            "eval runtime observations require normalized_payload.evaluation_outcome"
        )
    if evaluation_outcome != "returned_value":
        raise ValueError(
            "eval runtime observations require evaluation_outcome to be "
            "'returned_value'"
        )


def _validate_eval_replay_inputs(
    replay_inputs: tuple[_RuntimeObservationField, ...],
) -> None:
    """Require bounded evaluated-source replay proof for ``eval`` observations."""
    inputs = _normalized_field_mapping(
        replay_inputs,
        field_name="replay_inputs",
    )
    source_shape = inputs.get("source_shape")
    if source_shape is None:
        raise ValueError("eval runtime observations require replay_inputs.source_shape")
    if source_shape != "literal_expression":
        raise ValueError(
            "eval runtime observations require source_shape to be 'literal_expression'"
        )

    source_sha256 = inputs.get("source_sha256")
    if source_sha256 is None:
        raise ValueError(
            "eval runtime observations require replay_inputs.source_sha256"
        )
    if not _is_sha256_digest(source_sha256):
        raise ValueError(
            "eval runtime observations require source_sha256 to be a "
            "64-character hex digest"
        )


def _validate_eval_durable_payload_reference(
    observation: EvalRuntimeObservation,
) -> None:
    """Require durable returned-value proof for the bounded ``eval`` seam."""
    durable_payload_reference = observation.durable_payload_reference
    if durable_payload_reference is None or not durable_payload_reference.strip():
        raise ValueError("eval runtime observations require durable_payload_reference")


def _validate_exec_execution_outcome(
    normalized_payload: tuple[_RuntimeObservationField, ...],
) -> None:
    """Require the bounded ``exec`` runtime payload for this slice."""
    payload = _normalized_field_mapping(
        normalized_payload,
        field_name="normalized_payload",
    )
    execution_outcome = payload.get("execution_outcome")
    if execution_outcome is None:
        raise ValueError(
            "exec runtime observations require normalized_payload.execution_outcome"
        )
    if execution_outcome != "completed":
        raise ValueError(
            "exec runtime observations require execution_outcome to be 'completed'"
        )
    statement_kind = payload.get("statement_kind")
    if statement_kind is not None and statement_kind != "pass":
        raise ValueError(
            "exec runtime observations require statement_kind to be 'pass' when "
            "provided"
        )


def _validate_exec_replay_inputs(
    replay_inputs: tuple[_RuntimeObservationField, ...],
) -> None:
    """Require bounded executed-source replay proof for ``exec`` observations."""
    inputs = _normalized_field_mapping(
        replay_inputs,
        field_name="replay_inputs",
    )
    source_shape = inputs.get("source_shape")
    if source_shape is None:
        raise ValueError("exec runtime observations require replay_inputs.source_shape")
    if source_shape != "literal_statement":
        raise ValueError(
            "exec runtime observations require source_shape to be 'literal_statement'"
        )

    source_sha256 = inputs.get("source_sha256")
    if source_sha256 is None:
        raise ValueError(
            "exec runtime observations require replay_inputs.source_sha256"
        )
    if not _is_sha256_digest(source_sha256):
        raise ValueError(
            "exec runtime observations require source_sha256 to be a "
            "64-character hex digest"
        )
    if source_sha256 != _EXEC_PASS_SOURCE_SHA256:
        raise ValueError(
            "exec runtime observations require source_sha256 to identify "
            "exact executed source 'pass'"
        )


def _validate_exec_durable_payload_reference(
    observation: ExecRuntimeObservation,
) -> None:
    """Require durable completion proof for the bounded ``exec`` seam."""
    durable_payload_reference = observation.durable_payload_reference
    if durable_payload_reference is None or not durable_payload_reference.strip():
        raise ValueError("exec runtime observations require durable_payload_reference")


def _validate_globals_lookup_outcome(
    normalized_payload: tuple[_RuntimeObservationField, ...],
) -> None:
    """Require the bounded ``globals()`` runtime payload for this slice."""
    payload = _normalized_field_mapping(
        normalized_payload,
        field_name="normalized_payload",
    )
    lookup_outcome = payload.get("lookup_outcome")
    if lookup_outcome is None:
        raise ValueError(
            "globals runtime observations require normalized_payload.lookup_outcome"
        )
    if lookup_outcome != "returned_namespace":
        raise ValueError(
            "globals runtime observations require lookup_outcome to be "
            "'returned_namespace'"
        )


def _validate_locals_lookup_outcome(
    normalized_payload: tuple[_RuntimeObservationField, ...],
) -> None:
    """Require the bounded ``locals()`` runtime payload for this slice."""
    payload = _normalized_field_mapping(
        normalized_payload,
        field_name="normalized_payload",
    )
    lookup_outcome = payload.get("lookup_outcome")
    if lookup_outcome is None:
        raise ValueError(
            "locals runtime observations require normalized_payload.lookup_outcome"
        )
    if lookup_outcome != "returned_namespace":
        raise ValueError(
            "locals runtime observations require lookup_outcome to be "
            "'returned_namespace'"
        )


def _validate_setattr_mutation_outcome(
    normalized_payload: tuple[_RuntimeObservationField, ...],
) -> None:
    """Require the bounded ``setattr`` runtime payload for this slice."""
    payload = _normalized_field_mapping(
        normalized_payload,
        field_name="normalized_payload",
    )
    mutation_outcome = payload.get("mutation_outcome")
    if mutation_outcome is None:
        raise ValueError(
            "setattr runtime observations require normalized_payload.mutation_outcome"
        )
    if mutation_outcome != "returned_none":
        raise ValueError(
            "setattr runtime observations require mutation_outcome to be "
            "'returned_none'"
        )


def _validate_setattr_durable_payload_reference(
    observation: SetattrRuntimeObservation,
) -> None:
    """Require durable passed-value proof for the bounded ``setattr`` seam."""
    durable_payload_reference = observation.durable_payload_reference
    if durable_payload_reference is None or not durable_payload_reference.strip():
        raise ValueError(
            "setattr runtime observations require durable_payload_reference"
        )


def _validate_delattr_mutation_outcome(
    normalized_payload: tuple[_RuntimeObservationField, ...],
) -> None:
    """Require the bounded ``delattr`` runtime payload for this slice."""
    payload = _normalized_field_mapping(
        normalized_payload,
        field_name="normalized_payload",
    )
    mutation_outcome = payload.get("mutation_outcome")
    if mutation_outcome is None:
        raise ValueError(
            "delattr runtime observations require normalized_payload.mutation_outcome"
        )
    if mutation_outcome != "deleted_attribute":
        raise ValueError(
            "delattr runtime observations require mutation_outcome to be "
            "'deleted_attribute'"
        )


def _validate_dir_durable_payload_reference(
    observation: DirRuntimeObservation,
) -> None:
    """Require durable directory-listing proof for the bounded ``dir`` seam."""
    durable_payload_reference = observation.durable_payload_reference
    if durable_payload_reference is None or not durable_payload_reference.strip():
        raise ValueError("dir runtime observations require durable_payload_reference")


def _validate_metaclass_behavior_class_creation_outcome(
    normalized_payload: tuple[_RuntimeObservationField, ...],
) -> None:
    """Require the bounded metaclass runtime payload for this slice."""
    payload = _normalized_field_mapping(
        normalized_payload,
        field_name="normalized_payload",
    )
    class_creation_outcome = payload.get("class_creation_outcome")
    if class_creation_outcome is None:
        raise ValueError(
            "metaclass behavior runtime observations require "
            "normalized_payload.class_creation_outcome"
        )
    if class_creation_outcome != "created_class":
        raise ValueError(
            "metaclass behavior runtime observations require "
            "class_creation_outcome to be 'created_class'"
        )


def _validate_metaclass_behavior_durable_payload_reference(
    observation: MetaclassBehaviorRuntimeObservation,
) -> None:
    """Require durable created-class proof for the bounded metaclass seam."""
    durable_payload_reference = observation.durable_payload_reference
    if durable_payload_reference is None or not durable_payload_reference.strip():
        raise ValueError(
            "metaclass behavior runtime observations require durable_payload_reference"
        )


def _is_sha256_digest(value: str) -> bool:
    """Return whether ``value`` is a SHA-256 hex digest."""
    stripped = value.strip()
    if len(stripped) != 64:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in stripped)


def _source_site_identity(site: SourceSite) -> tuple[str, int, int, int, int]:
    """Return the stable source identity used for runtime-attachment matching."""
    span = site.span
    return (
        site.file_path,
        span.start_line,
        span.start_column,
        span.end_line,
        span.end_column,
    )


def _iter_program_sites(program: SemanticProgram) -> Iterable[SourceSite]:
    """Yield source sites already present on the semantic program."""
    for syntax_diagnostic in program.syntax.diagnostics:
        yield syntax_diagnostic.site
    for definition in program.syntax.definitions:
        yield definition.site
    for parameter in program.syntax.parameters:
        yield parameter.site
    for imported in program.syntax.imports:
        yield imported.site
    for decorator in program.syntax.decorators:
        yield decorator.site
    for base_expression in program.syntax.base_expressions:
        yield base_expression.site
    for assignment in program.syntax.assignments:
        yield assignment.site
    for call_site in program.syntax.call_sites:
        yield call_site.site
    for attribute_site in program.syntax.attribute_sites:
        yield attribute_site.site
    for symbol in program.resolved_symbols.values():
        yield symbol.definition_site
    for binding in program.bindings:
        yield binding.site
    for resolved_import in program.resolved_imports:
        yield resolved_import.site
    for dataclass_model in program.dataclass_models:
        yield dataclass_model.decorator_site
    for dataclass_field in program.dataclass_fields:
        yield dataclass_field.site
    for resolved_reference in program.resolved_references:
        yield resolved_reference.site
    for frontier_item in program.unresolved_frontier:
        yield frontier_item.site
    for unsupported_construct in program.unsupported_constructs:
        yield unsupported_construct.site
    for resolver_diagnostic in program.diagnostics:
        yield resolver_diagnostic.site
    for provenance_record in program.provenance_records:
        yield from provenance_record.subject_sites
        yield from provenance_record.evidence_sites


def _dedupe_sites(sites: tuple[SourceSite, ...]) -> tuple[SourceSite, ...]:
    """Preserve site order while removing duplicate site IDs."""
    deduped: list[SourceSite] = []
    seen_site_ids: set[str] = set()
    for site in sites:
        if site.site_id in seen_site_ids:
            continue
        seen_site_ids.add(site.site_id)
        deduped.append(site)
    return tuple(deduped)


def _find_dependency(
    program: SemanticProgram,
    dependency_id: str,
) -> SemanticDependency | None:
    """Return the dependency with ``dependency_id`` when present."""
    for dependency in program.proven_dependencies:
        if dependency.dependency_id == dependency_id:
            return dependency
    return None


def _find_frontier_item(
    program: SemanticProgram,
    access_id: str,
) -> UnresolvedAccess | None:
    """Return the unresolved frontier item with ``access_id`` when present."""
    for frontier_item in program.unresolved_frontier:
        if frontier_item.access_id == access_id:
            return frontier_item
    return None


def _find_unsupported_construct(
    program: SemanticProgram,
    construct_id: str,
) -> UnsupportedConstruct | None:
    """Return the unsupported construct with ``construct_id`` when present."""
    for unsupported_construct in program.unsupported_constructs:
        if unsupported_construct.construct_id == construct_id:
            return unsupported_construct
    return None


__all__ = [
    "DelattrRuntimeObservation",
    "DynamicImportRuntimeObservation",
    "DirRuntimeObservation",
    "EvalRuntimeObservation",
    "ExecRuntimeObservation",
    "GetattrRuntimeObservation",
    "GlobalsRuntimeObservation",
    "HasattrRuntimeObservation",
    "LocalsRuntimeObservation",
    "MetaclassBehaviorRuntimeObservation",
    "SetattrRuntimeObservation",
    "VarsRuntimeObservation",
    "attach_delattr_runtime_provenance",
    "attach_dynamic_import_runtime_provenance",
    "attach_dir_runtime_provenance",
    "attach_eval_runtime_provenance",
    "attach_exec_runtime_provenance",
    "attach_getattr_runtime_provenance",
    "attach_globals_runtime_provenance",
    "attach_hasattr_runtime_provenance",
    "attach_locals_runtime_provenance",
    "attach_metaclass_behavior_runtime_provenance",
    "attach_setattr_runtime_provenance",
    "attach_vars_runtime_provenance",
    "attach_runtime_observations",
]

"""Static discovery of compact eval runtime evidence records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from context_ir.semantic_types import (
    CapabilityTier,
    SemanticEvalRuntimeEvidence,
    SemanticEvalRuntimeEvidenceField,
    SourceSite,
    SourceSpan,
    UnresolvedReasonCode,
)

_OBSERVATION_FILENAME = "eval_runtime_observations.json"
_OBSERVATION_LIST_SUFFIX = "_runtime_observations"


class EvalEvidenceError(ValueError):
    """Raised when eval evidence assets cannot form a closed catalog."""


@dataclass(frozen=True)
class EvalRuntimeEvidencePayloadField:
    """One normalized payload key/value pair from runtime evidence."""

    key: str
    value: str

    def __post_init__(self) -> None:
        """Reject incomplete payload fields."""
        if not self.key:
            raise EvalEvidenceError("normalized_payload key must be non-empty")
        if not self.value:
            raise EvalEvidenceError(
                f"normalized_payload.{self.key} value must be non-empty"
            )


@dataclass(frozen=True)
class EvalRuntimeEvidence:
    """Compact internal record for one eval fixture runtime observation."""

    evidence_id: str
    runtime_family: str
    fixture_id: str
    task_ids: tuple[str, ...]
    run_spec_ids: tuple[str, ...]
    artifact_path: str
    source_file_path: str
    source_start_line: int
    source_start_column: int
    construct_text: str
    reason_code: UnresolvedReasonCode
    expected_primary_capability_tier: CapabilityTier
    expect_attached_runtime_provenance: bool
    normalized_payload: tuple[EvalRuntimeEvidencePayloadField, ...]
    durable_payload_reference: str

    def __post_init__(self) -> None:
        """Reject incomplete evidence records."""
        if not self.evidence_id:
            raise EvalEvidenceError("evidence_id must be non-empty")
        if not self.runtime_family:
            raise EvalEvidenceError("runtime_family must be non-empty")
        if not self.fixture_id:
            raise EvalEvidenceError("fixture_id must be non-empty")
        if not self.task_ids:
            raise EvalEvidenceError("task_ids must be non-empty")
        if not self.run_spec_ids:
            raise EvalEvidenceError("run_spec_ids must be non-empty")
        if not self.artifact_path:
            raise EvalEvidenceError("artifact_path must be non-empty")
        if not self.source_file_path:
            raise EvalEvidenceError("source_file_path must be non-empty")
        if self.source_start_line <= 0:
            raise EvalEvidenceError("source_start_line must be positive")
        if self.source_start_column <= 0:
            raise EvalEvidenceError("source_start_column must be positive")
        if not self.construct_text:
            raise EvalEvidenceError("construct_text must be non-empty")
        if not self.normalized_payload:
            raise EvalEvidenceError("normalized_payload must be non-empty")
        if not self.durable_payload_reference:
            raise EvalEvidenceError("durable_payload_reference must be non-empty")
        _validate_unique_payload_keys(
            self.normalized_payload,
            path=f"{self.evidence_id}.normalized_payload",
        )

    def normalized_payload_mapping(self) -> dict[str, str]:
        """Return normalized payload fields keyed by payload name."""
        return {field.key: field.value for field in self.normalized_payload}


@dataclass(frozen=True)
class EvalRuntimeEvidenceCatalog:
    """Deterministically ordered internal eval runtime evidence catalog."""

    records: tuple[EvalRuntimeEvidence, ...]

    def __post_init__(self) -> None:
        """Reject duplicate evidence identifiers."""
        seen_ids: set[str] = set()
        for record in self.records:
            if record.evidence_id in seen_ids:
                raise EvalEvidenceError(f"duplicate evidence_id '{record.evidence_id}'")
            seen_ids.add(record.evidence_id)

    def by_evidence_id(self) -> dict[str, EvalRuntimeEvidence]:
        """Return evidence records keyed by stable evidence identifier."""
        return {record.evidence_id: record for record in self.records}


@dataclass(frozen=True)
class _UnsupportedSelectorRecord:
    selector_path: str
    file_path: str
    construct_text: str
    source_snippet: str | None
    reason_code: UnresolvedReasonCode
    expected_primary_capability_tier: CapabilityTier | None
    expect_attached_runtime_provenance: bool | None


@dataclass(frozen=True)
class _TaskRecord:
    task_id: str
    fixture_id: str
    task_path: str
    unsupported_selectors: tuple[_UnsupportedSelectorRecord, ...]


@dataclass(frozen=True)
class _ObservationRecord:
    runtime_family: str
    fixture_id: str
    artifact_path: str
    file_path: str
    start_line: int
    start_column: int
    source_snippet: str
    normalized_payload: tuple[EvalRuntimeEvidencePayloadField, ...]
    durable_payload_reference: str


def discover_eval_runtime_evidence(repo_root: Path | str) -> EvalRuntimeEvidenceCatalog:
    """Discover compact eval runtime evidence records from repo JSON assets."""
    root = Path(repo_root)
    tasks_by_fixture_id = _load_tasks_by_fixture_id(root)
    run_spec_ids_by_task_path = _load_run_spec_ids_by_task_path(root)
    observations = _load_fixture_runtime_observations(root)
    records: list[EvalRuntimeEvidence] = []
    seen_evidence_ids: set[str] = set()

    for observation in observations:
        task = tasks_by_fixture_id.get(observation.fixture_id)
        if task is None:
            raise EvalEvidenceError(
                f"missing task for observation fixture '{observation.fixture_id}'"
            )

        selector = _matching_unsupported_selector(task, observation)
        expected_primary_capability_tier = _runtime_evidence_capability_tier(selector)
        expect_attached_runtime_provenance = _runtime_evidence_provenance_expectation(
            selector
        )
        run_spec_ids = run_spec_ids_by_task_path.get(task.task_path, ())
        if not run_spec_ids:
            raise EvalEvidenceError(
                "missing run spec reference for task "
                f"'{task.task_id}' at {task.task_path}"
            )

        evidence_id = _build_evidence_id(observation)
        if evidence_id in seen_evidence_ids:
            raise EvalEvidenceError(f"duplicate evidence_id '{evidence_id}'")
        seen_evidence_ids.add(evidence_id)

        records.append(
            EvalRuntimeEvidence(
                evidence_id=evidence_id,
                runtime_family=observation.runtime_family,
                fixture_id=observation.fixture_id,
                task_ids=(task.task_id,),
                run_spec_ids=run_spec_ids,
                artifact_path=observation.artifact_path,
                source_file_path=observation.file_path,
                source_start_line=observation.start_line,
                source_start_column=observation.start_column,
                construct_text=selector.construct_text,
                reason_code=selector.reason_code,
                expected_primary_capability_tier=expected_primary_capability_tier,
                expect_attached_runtime_provenance=expect_attached_runtime_provenance,
                normalized_payload=observation.normalized_payload,
                durable_payload_reference=observation.durable_payload_reference,
            )
        )

    return EvalRuntimeEvidenceCatalog(
        records=tuple(sorted(records, key=lambda record: record.evidence_id))
    )


def render_eval_runtime_evidence(evidence: EvalRuntimeEvidence) -> str:
    """Render one compact eval runtime evidence line for diagnostics."""
    payload = ",".join(
        f"{field.key}={field.value}" for field in evidence.normalized_payload
    )
    return (
        "eval_evidence: "
        f"{evidence.fixture_id} unsupported {evidence.construct_text}; "
        f"primary={evidence.expected_primary_capability_tier.value}; "
        f"runtime=additive; payload={payload}"
    )


def discover_semantic_eval_runtime_evidence(
    repo_root: Path | str,
) -> tuple[SemanticEvalRuntimeEvidence, ...]:
    """Discover compact eval runtime evidence as semantic support units."""
    catalog = discover_eval_runtime_evidence(repo_root)
    return tuple(_semantic_evidence_unit(record) for record in catalog.records)


def _semantic_evidence_unit(
    evidence: EvalRuntimeEvidence,
) -> SemanticEvalRuntimeEvidence:
    """Convert one catalog record into an internal semantic support unit."""
    unit_id = f"eval_evidence:{evidence.evidence_id}"
    source_file_path = (
        PurePosixPath("evals")
        / "fixtures"
        / evidence.fixture_id
        / evidence.source_file_path
    ).as_posix()
    start_column = evidence.source_start_column
    end_column = start_column + len(evidence.construct_text)
    return SemanticEvalRuntimeEvidence(
        unit_id=unit_id,
        evidence_id=evidence.evidence_id,
        runtime_family=evidence.runtime_family,
        fixture_id=evidence.fixture_id,
        task_ids=evidence.task_ids,
        run_spec_ids=evidence.run_spec_ids,
        artifact_path=evidence.artifact_path,
        site=SourceSite(
            site_id=f"site:{unit_id}",
            file_path=source_file_path,
            span=SourceSpan(
                start_line=evidence.source_start_line,
                start_column=start_column,
                end_line=evidence.source_start_line,
                end_column=end_column,
            ),
            snippet=evidence.construct_text,
        ),
        construct_text=evidence.construct_text,
        reason_code=evidence.reason_code,
        primary_capability_tier=evidence.expected_primary_capability_tier,
        expect_attached_runtime_provenance=(
            evidence.expect_attached_runtime_provenance
        ),
        normalized_payload=tuple(
            SemanticEvalRuntimeEvidenceField(key=field.key, value=field.value)
            for field in evidence.normalized_payload
        ),
        durable_payload_reference=evidence.durable_payload_reference,
    )


def _load_tasks_by_fixture_id(root: Path) -> dict[str, _TaskRecord]:
    tasks_dir = root / "evals" / "tasks"
    tasks_by_fixture_id: dict[str, _TaskRecord] = {}
    for task_path in sorted(tasks_dir.glob("*.json")):
        task = _load_task_record(task_path, root)
        if task.fixture_id in tasks_by_fixture_id:
            raise EvalEvidenceError(f"duplicate task fixture_id '{task.fixture_id}'")
        tasks_by_fixture_id[task.fixture_id] = task
    return tasks_by_fixture_id


def _load_task_record(task_path: Path, root: Path) -> _TaskRecord:
    record = _load_json_object(task_path, artifact_kind="task")
    task_id = _required_string(record, "task_id", path="$")
    fixture_id = _required_string(record, "fixture_id", path="$")
    selector_records = _required_list(record, "expected_selectors", path="$")
    unsupported_selectors = tuple(
        _parse_unsupported_selector(
            selector_record,
            path=f"$.expected_selectors[{index}]",
        )
        for index, selector_record in enumerate(selector_records)
        if _selector_kind(selector_record, path=f"$.expected_selectors[{index}]")
        == "unsupported"
    )
    return _TaskRecord(
        task_id=task_id,
        fixture_id=fixture_id,
        task_path=_repo_relative_path(task_path, root),
        unsupported_selectors=unsupported_selectors,
    )


def _parse_unsupported_selector(
    raw: object,
    *,
    path: str,
) -> _UnsupportedSelectorRecord:
    record = _expect_object(raw, path=path)
    file_path = _required_repo_relative_path(record, "file_path", path=path)
    construct_text = _required_string(record, "construct_text", path=path)
    source_snippet = _optional_string(record, "source_snippet", path=path)
    reason_code = _parse_reason_code(
        _required_string(record, "reason_code", path=path),
        path=f"{path}.reason_code",
    )
    expected_primary_capability_tier = _optional_capability_tier(
        record,
        "expected_primary_capability_tier",
        path=f"{path}.expected_primary_capability_tier",
    )
    expect_attached_runtime_provenance = _optional_bool(
        record,
        "expect_attached_runtime_provenance",
        path=f"{path}.expect_attached_runtime_provenance",
    )
    return _UnsupportedSelectorRecord(
        selector_path=path,
        file_path=file_path,
        construct_text=construct_text,
        source_snippet=source_snippet,
        reason_code=reason_code,
        expected_primary_capability_tier=expected_primary_capability_tier,
        expect_attached_runtime_provenance=expect_attached_runtime_provenance,
    )


def _selector_kind(raw: object, *, path: str) -> str:
    record = _expect_object(raw, path=path)
    return _required_string(record, "kind", path=path)


def _load_run_spec_ids_by_task_path(root: Path) -> dict[str, tuple[str, ...]]:
    run_specs_dir = root / "evals" / "run_specs"
    run_spec_ids_by_task_path: dict[str, set[str]] = {}
    for run_spec_path in sorted(run_specs_dir.glob("*.json")):
        record = _load_json_object(run_spec_path, artifact_kind="run spec")
        plan_id = _required_string(record, "plan_id", path="$")
        case_records = _required_list(record, "cases", path="$")
        for index, case_record in enumerate(case_records):
            case = _expect_object(case_record, path=f"$.cases[{index}]")
            task_path = _required_repo_relative_path(
                case,
                "task_path",
                path=f"$.cases[{index}]",
            )
            run_spec_ids_by_task_path.setdefault(task_path, set()).add(plan_id)

    return {
        task_path: tuple(sorted(run_spec_ids))
        for task_path, run_spec_ids in run_spec_ids_by_task_path.items()
    }


def _load_fixture_runtime_observations(root: Path) -> tuple[_ObservationRecord, ...]:
    fixtures_dir = root / "evals" / "fixtures"
    observations: list[_ObservationRecord] = []
    for observation_path in sorted(fixtures_dir.glob(f"*/{_OBSERVATION_FILENAME}")):
        fixture_id = observation_path.parent.name
        artifact_path = _repo_relative_path(observation_path, root)
        document = _load_json_object(observation_path, artifact_kind="observation")
        schema_version = _required_string(document, "schema_version", path="$")
        if schema_version != "v1":
            raise EvalEvidenceError("$.schema_version must be 'v1'")

        observation_keys = sorted(
            key
            for key in document
            if key != "schema_version" and key.endswith(_OBSERVATION_LIST_SUFFIX)
        )
        if not observation_keys:
            raise EvalEvidenceError(
                f"{artifact_path} must contain a runtime observation list"
            )
        for observation_key in observation_keys:
            runtime_family = observation_key[: -len(_OBSERVATION_LIST_SUFFIX)]
            observation_records = _required_list(document, observation_key, path="$")
            if not observation_records:
                raise EvalEvidenceError(
                    f"$.{observation_key} must contain at least one observation"
                )
            for index, observation_record in enumerate(observation_records):
                observations.append(
                    _parse_observation_record(
                        observation_record,
                        fixture_id=fixture_id,
                        runtime_family=runtime_family,
                        artifact_path=artifact_path,
                        path=f"$.{observation_key}[{index}]",
                    )
                )

    return tuple(observations)


def _parse_observation_record(
    raw: object,
    *,
    fixture_id: str,
    runtime_family: str,
    artifact_path: str,
    path: str,
) -> _ObservationRecord:
    record = _expect_object(raw, path=path)
    return _ObservationRecord(
        runtime_family=runtime_family,
        fixture_id=fixture_id,
        artifact_path=artifact_path,
        file_path=_required_repo_relative_path(record, "file_path", path=path),
        start_line=_required_positive_int(record, "start_line", path=path),
        start_column=_required_positive_int(record, "start_column", path=path),
        source_snippet=_required_string(record, "source_snippet", path=path),
        normalized_payload=_parse_payload_fields(
            _required_list(record, "normalized_payload", path=path),
            path=f"{path}.normalized_payload",
        ),
        durable_payload_reference=_required_string(
            record,
            "durable_payload_reference",
            path=path,
        ),
    )


def _parse_payload_fields(
    raw_fields: list[object],
    *,
    path: str,
) -> tuple[EvalRuntimeEvidencePayloadField, ...]:
    if not raw_fields:
        raise EvalEvidenceError(f"{path} must contain at least one field")
    fields = tuple(
        _parse_payload_field(raw_field, path=f"{path}[{index}]")
        for index, raw_field in enumerate(raw_fields)
    )
    _validate_unique_payload_keys(fields, path=path)
    return fields


def _parse_payload_field(
    raw: object,
    *,
    path: str,
) -> EvalRuntimeEvidencePayloadField:
    record = _expect_object(raw, path=path)
    try:
        return EvalRuntimeEvidencePayloadField(
            key=_required_string(record, "key", path=path),
            value=_required_string(record, "value", path=path),
        )
    except EvalEvidenceError as error:
        raise EvalEvidenceError(
            f"malformed normalized_payload at {path}: {error}"
        ) from error


def _validate_unique_payload_keys(
    fields: tuple[EvalRuntimeEvidencePayloadField, ...],
    *,
    path: str,
) -> None:
    seen_keys: set[str] = set()
    for field in fields:
        if field.key in seen_keys:
            raise EvalEvidenceError(
                f"duplicate normalized_payload key '{field.key}' at {path}"
            )
        seen_keys.add(field.key)


def _matching_unsupported_selector(
    task: _TaskRecord,
    observation: _ObservationRecord,
) -> _UnsupportedSelectorRecord:
    matches = tuple(
        selector
        for selector in task.unsupported_selectors
        if _selector_matches_observation(selector, observation)
    )
    if not matches:
        raise EvalEvidenceError(
            "missing matching unsupported selector for "
            f"{observation.fixture_id} {observation.file_path} "
            f"{observation.source_snippet!r}"
        )
    if len(matches) > 1:
        raise EvalEvidenceError(
            "ambiguous matching unsupported selector for "
            f"{observation.fixture_id} {observation.file_path} "
            f"{observation.source_snippet!r}"
        )
    return matches[0]


def _selector_matches_observation(
    selector: _UnsupportedSelectorRecord,
    observation: _ObservationRecord,
) -> bool:
    if selector.file_path != observation.file_path:
        return False
    if selector.construct_text != observation.source_snippet:
        return False
    return (
        selector.source_snippet is None
        or selector.source_snippet == observation.source_snippet
    )


def _runtime_evidence_capability_tier(
    selector: _UnsupportedSelectorRecord,
) -> CapabilityTier:
    tier = selector.expected_primary_capability_tier
    if tier is None:
        raise EvalEvidenceError(
            f"{selector.selector_path}.expected_primary_capability_tier "
            "must be present for matched runtime evidence"
        )
    if tier is not CapabilityTier.UNSUPPORTED_OPAQUE:
        raise EvalEvidenceError(
            f"{selector.selector_path}.expected_primary_capability_tier "
            "must be 'unsupported/opaque'"
        )
    return tier


def _runtime_evidence_provenance_expectation(
    selector: _UnsupportedSelectorRecord,
) -> bool:
    expectation = selector.expect_attached_runtime_provenance
    if expectation is not True:
        raise EvalEvidenceError(
            f"{selector.selector_path}.expect_attached_runtime_provenance "
            "must be true for matched runtime evidence"
        )
    return expectation


def _build_evidence_id(observation: _ObservationRecord) -> str:
    return (
        f"{observation.fixture_id}:{observation.runtime_family}:"
        f"{observation.file_path}:{observation.start_line}:"
        f"{observation.start_column}"
    )


def _load_json_object(path: Path, *, artifact_kind: str) -> dict[str, object]:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise EvalEvidenceError(
            f"invalid {artifact_kind} JSON in {path}: {error}"
        ) from error
    return _expect_object(raw, path="$")


def _expect_object(raw: object, *, path: str) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise EvalEvidenceError(f"{path} must be an object")
    return cast(dict[str, object], raw)


def _required_list(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> list[object]:
    value = record.get(key)
    if not isinstance(value, list):
        raise EvalEvidenceError(f"{path}.{key} must be a list")
    return cast(list[object], value)


def _required_string(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise EvalEvidenceError(f"{path}.{key} must be a non-empty string")
    return value


def _optional_string(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> str | None:
    value = record.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise EvalEvidenceError(f"{path}.{key} must be a non-empty string")
    return value


def _required_repo_relative_path(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> str:
    value = _required_string(record, key, path=path)
    relative_path = PurePosixPath(value)
    if relative_path.is_absolute():
        raise EvalEvidenceError(f"{path}.{key} must be repo-relative")
    if ".." in relative_path.parts:
        raise EvalEvidenceError(f"{path}.{key} must not escape the repository root")
    return relative_path.as_posix()


def _optional_bool(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> bool | None:
    value = record.get(key)
    if value is None:
        return None
    if type(value) is not bool:
        raise EvalEvidenceError(f"{path} must be a boolean")
    return value


def _required_positive_int(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> int:
    value = record.get(key)
    if type(value) is not int or value <= 0:
        raise EvalEvidenceError(f"{path}.{key} must be a positive integer")
    return value


def _parse_reason_code(raw: str, *, path: str) -> UnresolvedReasonCode:
    try:
        return UnresolvedReasonCode(raw)
    except ValueError as error:
        raise EvalEvidenceError(f"{path} must be a known reason code") from error


def _optional_capability_tier(
    record: dict[str, object],
    key: str,
    *,
    path: str,
) -> CapabilityTier | None:
    raw = record.get(key)
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw:
        raise EvalEvidenceError(f"{path} must be a non-empty string")
    return _parse_capability_tier(raw, path=path)


def _parse_capability_tier(raw: str, *, path: str) -> CapabilityTier:
    try:
        return CapabilityTier(raw)
    except ValueError as error:
        raise EvalEvidenceError(f"{path} must be a known capability tier") from error


def _repo_relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


__all__ = [
    "EvalEvidenceError",
    "EvalRuntimeEvidence",
    "EvalRuntimeEvidenceCatalog",
    "EvalRuntimeEvidencePayloadField",
    "discover_eval_runtime_evidence",
    "discover_semantic_eval_runtime_evidence",
    "render_eval_runtime_evidence",
]

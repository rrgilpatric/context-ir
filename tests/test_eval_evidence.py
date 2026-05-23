"""Static eval runtime evidence catalog tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_ir.eval_evidence import (
    EvalEvidenceError,
    EvalRuntimeEvidence,
    discover_eval_runtime_evidence,
    discover_semantic_eval_runtime_evidence,
    render_eval_runtime_evidence,
)
from context_ir.semantic_types import CapabilityTier, UnresolvedReasonCode

REPO_ROOT = Path(__file__).resolve().parents[1]


def _evidence_by_fixture(
    records: tuple[EvalRuntimeEvidence, ...],
    fixture_id: str,
) -> EvalRuntimeEvidence:
    """Return the single evidence record for one fixture."""
    matches = [record for record in records if record.fixture_id == fixture_id]
    assert len(matches) == 1
    return matches[0]


def _payload(record: EvalRuntimeEvidence) -> dict[str, str]:
    """Return normalized payload fields as a mapping."""
    return record.normalized_payload_mapping()


def _write_json(path: Path, record: dict[str, object]) -> None:
    """Write one compact JSON fixture asset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


def _base_selector() -> dict[str, object]:
    """Return a minimal unsupported task selector."""
    return {
        "kind": "unsupported",
        "file_path": "main.py",
        "construct_text": "marker()",
        "reason_code": "reflective_builtin",
        "min_detail": "identity",
        "source_snippet": "marker()",
        "expected_primary_capability_tier": "unsupported/opaque",
        "expect_attached_runtime_provenance": True,
    }


def _base_task(
    *,
    selectors: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Return a minimal task record with one unsupported selector."""
    expected_selectors = selectors if selectors is not None else [_base_selector()]
    return {
        "task_id": "demo_task",
        "fixture_id": "demo_fixture",
        "expected_selectors": expected_selectors,
    }


def _base_observation(
    *,
    normalized_payload: list[dict[str, object]] | None = None,
    start_line: int = 1,
    start_column: int = 1,
    source_snippet: str = "marker()",
) -> dict[str, object]:
    """Return a minimal runtime observation record."""
    return {
        "file_path": "main.py",
        "start_line": start_line,
        "start_column": start_column,
        "source_snippet": source_snippet,
        "normalized_payload": normalized_payload
        if normalized_payload is not None
        else [{"key": "observed", "value": "true"}],
        "durable_payload_reference": "artifact://demo/observation.json",
    }


def _base_observation_document(
    observations: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Return a minimal runtime observation document."""
    return {
        "schema_version": "v1",
        "hasattr_runtime_observations": (
            observations if observations is not None else [_base_observation()]
        ),
    }


def _base_run_spec() -> dict[str, object]:
    """Return a minimal run spec record that references the demo task."""
    return {
        "plan_id": "demo_matrix",
        "cases": [
            {
                "case_id": "demo_case",
                "task_path": "evals/tasks/demo_task.json",
                "query": "demo",
                "budgets": [1],
                "providers": ["context_ir"],
            }
        ],
    }


def _write_minimal_repo(
    tmp_path: Path,
    *,
    task: dict[str, object] | None = None,
    observation_document: dict[str, object] | None = None,
    run_spec: dict[str, object] | None = None,
) -> Path:
    """Write a minimal eval asset set for catalog discovery."""
    observation_path = (
        tmp_path
        / "evals"
        / "fixtures"
        / "demo_fixture"
        / "eval_runtime_observations.json"
    )
    _write_json(
        observation_path,
        (
            observation_document
            if observation_document is not None
            else _base_observation_document()
        ),
    )
    if task is not None:
        _write_json(tmp_path / "evals" / "tasks" / "demo_task.json", task)
    if run_spec is not None:
        _write_json(tmp_path / "evals" / "run_specs" / "demo_matrix.json", run_spec)
    return tmp_path


def test_catalog_discovers_current_fixture_runtime_evidence() -> None:
    """The current eval assets produce the expected compact evidence catalog."""
    catalog = discover_eval_runtime_evidence(REPO_ROOT)

    assert len(catalog.records) == 29
    assert [record.evidence_id for record in catalog.records] == sorted(
        record.evidence_id for record in catalog.records
    )
    evidence_by_id = catalog.by_evidence_id()
    assert len(evidence_by_id) == 29
    assert "oracle_signal_getattr_literal_probe:getattr:main.py:2:11" in evidence_by_id
    assert "oracle_signal_hasattr_literal_probe:hasattr:main.py:2:11" in evidence_by_id
    assert (
        "oracle_signal_dynamic_import_root_literal_probe:dynamic_import:main.py:5:13"
        in evidence_by_id
    )
    assert {record.expected_primary_capability_tier for record in catalog.records} == {
        CapabilityTier.UNSUPPORTED_OPAQUE
    }
    assert all(record.expect_attached_runtime_provenance for record in catalog.records)


def test_catalog_includes_hasattr_probe_runtime_evidence() -> None:
    """The hasattr probe evidence preserves unsupported primary truth."""
    catalog = discover_eval_runtime_evidence(REPO_ROOT)

    evidence = _evidence_by_fixture(catalog.records, "oracle_signal_hasattr_probe")

    assert evidence.runtime_family == "hasattr"
    assert evidence.task_ids == ("oracle_signal_hasattr_probe",)
    assert "oracle_signal_hasattr_probe_matrix" in evidence.run_spec_ids
    assert (
        evidence.artifact_path
        == "evals/fixtures/oracle_signal_hasattr_probe/eval_runtime_observations.json"
    )
    assert evidence.construct_text == "hasattr(obj, name)"
    assert evidence.reason_code is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert (
        evidence.expected_primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    )
    assert evidence.expect_attached_runtime_provenance is True
    assert _payload(evidence)["attribute_present"] == "true"
    assert (
        evidence.durable_payload_reference
        == "artifact://hasattr/int-bit-length-observation.json"
    )


def test_catalog_includes_hasattr_literal_probe_runtime_evidence() -> None:
    """The direct-literal hasattr probe stays additive and unsupported."""
    catalog = discover_eval_runtime_evidence(REPO_ROOT)

    evidence = _evidence_by_fixture(
        catalog.records,
        "oracle_signal_hasattr_literal_probe",
    )

    assert evidence.runtime_family == "hasattr"
    assert evidence.task_ids == ("oracle_signal_hasattr_literal_probe",)
    assert "oracle_signal_hasattr_literal_probe_matrix" in evidence.run_spec_ids
    assert (
        evidence.artifact_path == "evals/fixtures/oracle_signal_hasattr_literal_probe/"
        "eval_runtime_observations.json"
    )
    assert evidence.construct_text == 'hasattr(obj, "bit_length")'
    assert evidence.reason_code is UnresolvedReasonCode.REFLECTIVE_BUILTIN
    assert (
        evidence.expected_primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    )
    assert evidence.expect_attached_runtime_provenance is True
    assert _payload(evidence) == {"attribute_present": "true"}
    assert (
        evidence.durable_payload_reference
        == "artifact://hasattr/literal-int-bit-length-observation.json"
    )


def test_catalog_includes_non_hasattr_eval_probe_runtime_evidence() -> None:
    """The eval probe contributes compact additive runtime payload evidence."""
    catalog = discover_eval_runtime_evidence(REPO_ROOT)

    evidence = _evidence_by_fixture(catalog.records, "oracle_signal_eval_probe")

    assert evidence.runtime_family == "eval"
    assert evidence.construct_text == "eval(source)"
    assert evidence.reason_code is UnresolvedReasonCode.EXEC_OR_EVAL
    assert evidence.run_spec_ids == ("oracle_signal_eval_probe_matrix",)
    assert _payload(evidence)["evaluation_outcome"] == "returned_value"
    assert _payload(evidence)["result_type"] == "builtins.str"


def test_render_eval_runtime_evidence_is_compact() -> None:
    """The local render helper summarizes primary and additive runtime facts."""
    catalog = discover_eval_runtime_evidence(REPO_ROOT)
    evidence = _evidence_by_fixture(catalog.records, "oracle_signal_hasattr_probe")

    assert render_eval_runtime_evidence(evidence) == (
        "eval_evidence: oracle_signal_hasattr_probe unsupported "
        "hasattr(obj, name); primary=unsupported/opaque; runtime=additive; "
        "payload=attribute_present=true"
    )


def test_semantic_eval_runtime_evidence_units_preserve_payload_surface() -> None:
    """Catalog records can become internal semantic support units."""
    [evidence] = [
        unit
        for unit in discover_semantic_eval_runtime_evidence(REPO_ROOT)
        if unit.fixture_id == "oracle_signal_hasattr_probe"
    ]

    assert evidence.unit_id.startswith(
        "eval_evidence:oracle_signal_hasattr_probe:hasattr:"
    )
    assert evidence.site.file_path == (
        "evals/fixtures/oracle_signal_hasattr_probe/main.py"
    )
    assert evidence.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert evidence.expect_attached_runtime_provenance is True
    assert evidence.normalized_payload_mapping()["attribute_present"] == "true"


def test_missing_task_for_observation_fixture_fails_closed(tmp_path: Path) -> None:
    """An observation fixture without exactly one task is rejected."""
    repo_root = _write_minimal_repo(tmp_path, run_spec=_base_run_spec())

    with pytest.raises(
        EvalEvidenceError,
        match="missing task for observation fixture 'demo_fixture'",
    ):
        discover_eval_runtime_evidence(repo_root)


def test_missing_matching_unsupported_selector_fails_closed(tmp_path: Path) -> None:
    """An observation must join to one unsupported selector in its task."""
    selector = _base_selector()
    selector["construct_text"] = "other()"
    selector["source_snippet"] = "other()"
    repo_root = _write_minimal_repo(
        tmp_path,
        task=_base_task(selectors=[selector]),
        run_spec=_base_run_spec(),
    )

    with pytest.raises(
        EvalEvidenceError,
        match="missing matching unsupported selector",
    ):
        discover_eval_runtime_evidence(repo_root)


def test_ambiguous_matching_unsupported_selector_fails_closed(tmp_path: Path) -> None:
    """Multiple matching unsupported selectors are rejected."""
    repo_root = _write_minimal_repo(
        tmp_path,
        task=_base_task(selectors=[_base_selector(), _base_selector()]),
        run_spec=_base_run_spec(),
    )

    with pytest.raises(
        EvalEvidenceError,
        match="ambiguous matching unsupported selector",
    ):
        discover_eval_runtime_evidence(repo_root)


def test_missing_run_spec_reference_fails_closed(tmp_path: Path) -> None:
    """Runtime evidence must be traceable to at least one run spec."""
    repo_root = _write_minimal_repo(tmp_path, task=_base_task())

    with pytest.raises(EvalEvidenceError, match="missing run spec reference"):
        discover_eval_runtime_evidence(repo_root)


def test_duplicate_evidence_id_fails_closed(tmp_path: Path) -> None:
    """Duplicate observation sites would create duplicate evidence IDs."""
    repo_root = _write_minimal_repo(
        tmp_path,
        task=_base_task(),
        observation_document=_base_observation_document(
            observations=[_base_observation(), _base_observation()]
        ),
        run_spec=_base_run_spec(),
    )

    with pytest.raises(EvalEvidenceError, match="duplicate evidence_id"):
        discover_eval_runtime_evidence(repo_root)


@pytest.mark.parametrize(
    "normalized_payload, expected_message",
    [
        ([{"key": "observed"}], "malformed normalized_payload"),
        (
            [
                {"key": "observed", "value": "true"},
                {"key": "observed", "value": "true"},
            ],
            "duplicate normalized_payload key 'observed'",
        ),
    ],
)
def test_malformed_or_duplicate_payload_keys_fail_closed(
    tmp_path: Path,
    normalized_payload: list[dict[str, object]],
    expected_message: str,
) -> None:
    """Normalized payload records must be well formed and uniquely keyed."""
    repo_root = _write_minimal_repo(
        tmp_path,
        task=_base_task(),
        observation_document=_base_observation_document(
            observations=[_base_observation(normalized_payload=normalized_payload)]
        ),
        run_spec=_base_run_spec(),
    )

    with pytest.raises(EvalEvidenceError, match=expected_message):
        discover_eval_runtime_evidence(repo_root)

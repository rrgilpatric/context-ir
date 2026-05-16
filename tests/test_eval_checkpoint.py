"""Internal runtime-evidence checkpoint command tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_checkpoint as eval_checkpoint
import context_ir.semantic_types as semantic_types
from context_ir.eval_providers import (
    CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TASK_IDS = (
    "oracle_signal_locals_probe",
    "oracle_signal_globals_probe",
    "oracle_signal_vars_zero_probe",
    "oracle_signal_dir_zero_probe",
    "oracle_signal_exec_probe",
    "oracle_signal_eval_probe",
    "oracle_signal_metaclass_behavior_probe",
)
EXPECTED_PAYLOADS = {
    "oracle_signal_locals_probe": (("lookup_outcome", "returned_namespace"),),
    "oracle_signal_globals_probe": (("lookup_outcome", "returned_namespace"),),
    "oracle_signal_vars_zero_probe": (("lookup_outcome", "returned_namespace"),),
    "oracle_signal_dir_zero_probe": (("listing_entry_count", "0"),),
    "oracle_signal_exec_probe": (
        ("execution_outcome", "completed"),
        ("statement_kind", "pass"),
    ),
    "oracle_signal_eval_probe": (
        ("evaluation_outcome", "returned_value"),
        ("result_type", "builtins.str"),
    ),
    "oracle_signal_metaclass_behavior_probe": (
        ("class_creation_outcome", "created_class"),
        ("created_class_qualified_name", "main.Example"),
        ("selected_metaclass_qualified_name", "main.Meta"),
    ),
}


def _json_object(path: Path) -> dict[str, object]:
    """Load one JSON object from a test artifact."""
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return cast(dict[str, object], loaded)


def _jsonl_objects(path: Path) -> list[dict[str, object]]:
    """Load compact JSONL test artifact rows."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        loaded = json.loads(line)
        assert isinstance(loaded, dict)
        rows.append(cast(dict[str, object], loaded))
    return rows


def test_execute_eval_checkpoint_writes_internal_runtime_artifacts(
    tmp_path: Path,
) -> None:
    """The checkpoint command writes a generated default-subprocess bundle."""
    output_dir = tmp_path / "checkpoint"

    artifact = eval_checkpoint.execute_eval_checkpoint(output_dir)

    assert isinstance(artifact, eval_checkpoint.EvalCheckpointArtifact)
    assert artifact.paths.output_dir == output_dir
    assert artifact.paths.run_spec_path == output_dir / "run_spec.json"
    assert artifact.paths.ledger_path == output_dir / "ledger.jsonl"
    assert artifact.paths.report_path == output_dir / "report.md"
    assert artifact.paths.manifest_path == output_dir / "manifest.json"
    assert artifact.paths.checkpoint_path == output_dir / "checkpoint.md"
    assert artifact.paths.run_spec_path.exists()
    assert artifact.paths.ledger_path.exists()
    assert artifact.paths.report_path.exists()
    assert artifact.paths.manifest_path.exists()
    assert artifact.paths.checkpoint_path.exists()
    assert not artifact.paths.run_spec_path.is_relative_to(
        REPO_ROOT / "evals" / "run_specs"
    )

    run_spec = _json_object(artifact.paths.run_spec_path)
    case_records = cast(list[dict[str, object]], run_spec["cases"])
    assert run_spec["plan_id"] == "internal_runtime_evidence_checkpoint"
    assert len(case_records) == len(EXPECTED_TASK_IDS)
    assert tuple(
        cast(str, case_record["task_path"]) for case_record in case_records
    ) == tuple(f"evals/tasks/{task_id}.json" for task_id in EXPECTED_TASK_IDS)
    assert {
        tuple(cast(list[int], case_record["budgets"])) for case_record in case_records
    } == {(100,)}
    assert {
        tuple(cast(list[str], case_record["providers"])) for case_record in case_records
    } == {(CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER,)}

    ledger_records = _jsonl_objects(artifact.paths.ledger_path)
    assert len(ledger_records) == len(EXPECTED_TASK_IDS)
    assert tuple(record["task_id"] for record in ledger_records) == EXPECTED_TASK_IDS
    assert {record["provider_name"] for record in ledger_records} == {
        CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    }
    assert {record["budget"] for record in ledger_records} == {100}

    evidence_by_task_id = {row.task_id: row for row in artifact.evidence_rows}
    assert tuple(evidence_by_task_id) == EXPECTED_TASK_IDS
    assert {
        task_id: row.normalized_payload for task_id, row in evidence_by_task_id.items()
    } == EXPECTED_PAYLOADS

    manifest = _json_object(artifact.paths.manifest_path)
    assert manifest["plan_id"] == "internal_runtime_evidence_checkpoint"
    assert manifest["record_count"] == len(EXPECTED_TASK_IDS)
    assert set(cast(list[str], manifest["task_ids"])) == set(EXPECTED_TASK_IDS)
    assert manifest["provider_names"] == [
        CONTEXT_IR_DEFAULT_LOCAL_PYTHON_SUBPROCESS_PROVIDER
    ]
    assert manifest["budgets"] == [100]
    assert manifest["budget_violation_run_ids"] == []

    checkpoint_markdown = artifact.paths.checkpoint_path.read_text(encoding="utf-8")
    assert "not a public benchmark, benchmark result, or product claim" in (
        checkpoint_markdown
    )
    assert "| Generated run spec |" in checkpoint_markdown
    assert "| Raw ledger |" in checkpoint_markdown
    assert "| Eval report |" in checkpoint_markdown
    assert "| Manifest |" in checkpoint_markdown
    assert "| Checkpoint |" in checkpoint_markdown
    for task_id, payload in EXPECTED_PAYLOADS.items():
        assert task_id in checkpoint_markdown
        assert _payload_json(payload) in checkpoint_markdown
    assert "This checkpoint only exercises the exact" in checkpoint_markdown
    assert "does not widen support" in checkpoint_markdown


def test_execute_eval_checkpoint_fails_closed_when_artifacts_exist(
    tmp_path: Path,
) -> None:
    """Existing target artifacts are rejected before ledger append can occur."""
    output_dir = tmp_path / "checkpoint"
    output_dir.mkdir()
    existing_ledger = output_dir / "ledger.jsonl"
    existing_ledger.write_text("stale\n", encoding="utf-8")

    with pytest.raises(
        eval_checkpoint.EvalCheckpointError,
        match="checkpoint target artifact files already exist",
    ):
        eval_checkpoint.execute_eval_checkpoint(output_dir)

    assert existing_ledger.read_text(encoding="utf-8") == "stale\n"
    assert not (output_dir / "run_spec.json").exists()
    assert not (output_dir / "checkpoint.md").exists()


def test_eval_checkpoint_stays_internal_and_avoids_public_claim_surfaces() -> None:
    """Checkpoint generation remains internal and avoids public surfaces."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "EvalCheckpointArtifact" not in context_ir.__all__
    assert "execute_eval_checkpoint" not in context_ir.__all__
    assert not hasattr(context_ir, "EvalCheckpointArtifact")
    assert not hasattr(context_ir, "execute_eval_checkpoint")
    assert not hasattr(eval_checkpoint, "publish_eval_checkpoint")
    assert not hasattr(eval_checkpoint, "render_public_claims")
    assert not hasattr(eval_checkpoint, "write_public_benchmark_report")

    assert set(eval_checkpoint.EvalCheckpointPaths.__dataclass_fields__) == {
        "output_dir",
        "run_spec_path",
        "ledger_path",
        "report_path",
        "manifest_path",
        "checkpoint_path",
    }
    assert set(eval_checkpoint.EvalCheckpointEvidenceRow.__dataclass_fields__) == {
        "task_id",
        "provider_name",
        "budget",
        "normalized_payload",
    }
    assert set(eval_checkpoint.EvalCheckpointArtifact.__dataclass_fields__) == {
        "paths",
        "bundle",
        "evidence_rows",
    }


def _payload_json(payload: tuple[tuple[str, str], ...]) -> str:
    """Return compact normalized payload JSON matching checkpoint Markdown."""
    return json.dumps(
        {key: value for key, value in payload},
        separators=(",", ":"),
        sort_keys=True,
    )

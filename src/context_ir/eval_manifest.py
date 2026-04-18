"""Deterministic internal manifest composition for one eval pipeline run."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from context_ir.eval_pipeline import EvalPipelineArtifact


@dataclass(frozen=True)
class EvalManifestCaseCount:
    """Per-case record-count summary retained in one eval run manifest."""

    case_id: str
    record_count: int


@dataclass(frozen=True)
class EvalRunManifest:
    """Typed deterministic manifest for one completed internal eval pipeline run."""

    spec_path: Path
    ledger_path: Path
    report_path: Path
    plan_id: str
    record_count: int
    written_run_ids: tuple[str, ...]
    case_record_counts: tuple[EvalManifestCaseCount, ...]
    task_ids: tuple[str, ...]
    provider_names: tuple[str, ...]
    budgets: tuple[int, ...]
    budget_violation_run_ids: tuple[str, ...]


def build_eval_run_manifest(
    spec_path: Path | str,
    pipeline_artifact: EvalPipelineArtifact,
) -> EvalRunManifest:
    """Build one narrow manifest from an accepted pipeline artifact."""
    execution_result = pipeline_artifact.execution_result
    report_artifact = pipeline_artifact.report_artifact
    summary = report_artifact.summary

    if report_artifact.source_ledger_path != execution_result.output_path:
        raise ValueError("pipeline artifact ledger path is internally inconsistent")
    if summary.record_count != execution_result.record_count:
        raise ValueError("pipeline artifact record counts are internally inconsistent")

    return EvalRunManifest(
        spec_path=Path(spec_path),
        ledger_path=execution_result.output_path,
        report_path=pipeline_artifact.report_output_path,
        plan_id=execution_result.plan_id,
        record_count=execution_result.record_count,
        written_run_ids=execution_result.written_run_ids,
        case_record_counts=tuple(
            EvalManifestCaseCount(
                case_id=case_count.case_id,
                record_count=case_count.record_count,
            )
            for case_count in execution_result.case_record_counts
        ),
        task_ids=summary.task_ids,
        provider_names=summary.provider_names,
        budgets=summary.budgets,
        budget_violation_run_ids=summary.budget_violation_run_ids,
    )


def eval_run_manifest_to_json(manifest: EvalRunManifest) -> dict[str, object]:
    """Serialize one manifest into a deterministic JSON-safe object."""
    return {
        "spec_path": manifest.spec_path.as_posix(),
        "ledger_path": manifest.ledger_path.as_posix(),
        "report_path": manifest.report_path.as_posix(),
        "plan_id": manifest.plan_id,
        "record_count": manifest.record_count,
        "written_run_ids": list(manifest.written_run_ids),
        "case_record_counts": [
            _case_count_to_json(case_count)
            for case_count in manifest.case_record_counts
        ],
        "task_ids": list(manifest.task_ids),
        "provider_names": list(manifest.provider_names),
        "budgets": list(manifest.budgets),
        "budget_violation_run_ids": list(manifest.budget_violation_run_ids),
    }


def write_eval_run_manifest_json(
    manifest: EvalRunManifest,
    output_path: Path | str,
) -> Path:
    """Write one manifest JSON artifact to the caller-provided path."""
    destination_path = Path(output_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    payload = eval_run_manifest_to_json(manifest)
    destination_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination_path


def _case_count_to_json(case_count: EvalManifestCaseCount) -> dict[str, object]:
    """Return the JSON-safe representation for one case-count summary."""
    return {
        "case_id": case_count.case_id,
        "record_count": case_count.record_count,
    }


__all__ = [
    "EvalManifestCaseCount",
    "EvalRunManifest",
    "build_eval_run_manifest",
    "eval_run_manifest_to_json",
    "write_eval_run_manifest_json",
]

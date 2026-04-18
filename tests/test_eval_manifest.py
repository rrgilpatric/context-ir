"""Deterministic internal eval manifest tests."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import context_ir
import context_ir.eval_manifest as eval_manifest
import context_ir.eval_pipeline as eval_pipeline
import context_ir.semantic_types as semantic_types

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_SPEC_PATH = REPO_ROOT / "evals" / "run_specs" / "oracle_smoke_matrix.json"


def _execute_smoke_pipeline(
    ledger_path: Path,
    report_path: Path,
) -> eval_pipeline.EvalPipelineArtifact:
    """Execute the accepted smoke run spec through the internal pipeline."""
    return eval_pipeline.execute_eval_pipeline(
        RUN_SPEC_PATH,
        ledger_path,
        report_path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )


def test_build_eval_run_manifest_creates_typed_artifact_from_smoke_pipeline(
    tmp_path: Path,
) -> None:
    """A smoke pipeline artifact composes into one narrow typed manifest."""
    pipeline_artifact = _execute_smoke_pipeline(
        tmp_path / "ledgers" / "smoke.jsonl",
        tmp_path / "reports" / "smoke.md",
    )

    manifest = eval_manifest.build_eval_run_manifest(RUN_SPEC_PATH, pipeline_artifact)
    payload = eval_manifest.eval_run_manifest_to_json(manifest)

    assert isinstance(manifest, eval_manifest.EvalRunManifest)
    assert manifest.spec_path == RUN_SPEC_PATH
    assert manifest.ledger_path == pipeline_artifact.execution_result.output_path
    assert manifest.report_path == pipeline_artifact.report_output_path
    assert manifest.plan_id == pipeline_artifact.execution_result.plan_id
    assert manifest.record_count == pipeline_artifact.execution_result.record_count
    assert (
        manifest.written_run_ids == pipeline_artifact.execution_result.written_run_ids
    )
    assert manifest.case_record_counts == tuple(
        eval_manifest.EvalManifestCaseCount(
            case_id=case_count.case_id,
            record_count=case_count.record_count,
        )
        for case_count in pipeline_artifact.execution_result.case_record_counts
    )
    assert manifest.task_ids == pipeline_artifact.report_artifact.summary.task_ids
    assert (
        manifest.provider_names
        == pipeline_artifact.report_artifact.summary.provider_names
    )
    assert manifest.budgets == pipeline_artifact.report_artifact.summary.budgets
    assert (
        manifest.budget_violation_run_ids
        == pipeline_artifact.report_artifact.summary.budget_violation_run_ids
    )
    assert set(payload) == {
        "spec_path",
        "ledger_path",
        "report_path",
        "plan_id",
        "record_count",
        "written_run_ids",
        "case_record_counts",
        "task_ids",
        "provider_names",
        "budgets",
        "budget_violation_run_ids",
    }
    assert "records" not in payload
    assert "markdown_report" not in payload
    assert "provider_aggregates" not in payload
    assert "task_budget_results" not in payload


def test_write_eval_run_manifest_json_writes_nested_caller_path_and_round_trips(
    tmp_path: Path,
) -> None:
    """Writing a manifest creates nested parents and preserves JSON-safe content."""
    pipeline_artifact = _execute_smoke_pipeline(
        tmp_path / "ledgers" / "smoke.jsonl",
        tmp_path / "reports" / "smoke.md",
    )
    manifest = eval_manifest.build_eval_run_manifest(RUN_SPEC_PATH, pipeline_artifact)
    output_path = tmp_path / "artifacts" / "manifests" / "smoke.json"

    assert not output_path.parent.exists()

    written_path = eval_manifest.write_eval_run_manifest_json(manifest, output_path)
    payload = eval_manifest.eval_run_manifest_to_json(manifest)

    assert written_path == output_path
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_independent_smoke_pipelines_produce_equivalent_manifest_content(
    tmp_path: Path,
) -> None:
    """Independent smoke pipelines differ only by caller-selected artifact paths."""
    first_manifest = eval_manifest.build_eval_run_manifest(
        RUN_SPEC_PATH,
        _execute_smoke_pipeline(
            tmp_path / "first" / "ledger.jsonl",
            tmp_path / "first" / "report.md",
        ),
    )
    second_manifest = eval_manifest.build_eval_run_manifest(
        RUN_SPEC_PATH,
        _execute_smoke_pipeline(
            tmp_path / "second" / "ledger.jsonl",
            tmp_path / "second" / "report.md",
        ),
    )

    normalized_first = replace(
        first_manifest,
        ledger_path=Path("ledger.jsonl"),
        report_path=Path("report.md"),
    )
    normalized_second = replace(
        second_manifest,
        ledger_path=Path("ledger.jsonl"),
        report_path=Path("report.md"),
    )

    assert normalized_first == normalized_second


def test_manifest_build_and_write_do_not_mutate_pipeline_artifact(
    tmp_path: Path,
) -> None:
    """Manifest composition leaves the accepted pipeline artifact unchanged."""
    pipeline_artifact = _execute_smoke_pipeline(
        tmp_path / "ledger.jsonl",
        tmp_path / "report.md",
    )
    artifact_before = copy.deepcopy(pipeline_artifact)

    manifest = eval_manifest.build_eval_run_manifest(RUN_SPEC_PATH, pipeline_artifact)
    eval_manifest.write_eval_run_manifest_json(
        manifest,
        tmp_path / "nested" / "manifest.json",
    )

    assert pipeline_artifact == artifact_before


def test_eval_manifest_stays_internal_and_avoids_public_claim_surfaces() -> None:
    """Manifest composition remains internal and does not add public surfaces."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "EvalManifestCaseCount" not in context_ir.__all__
    assert "EvalRunManifest" not in context_ir.__all__
    assert "build_eval_run_manifest" not in context_ir.__all__
    assert "eval_run_manifest_to_json" not in context_ir.__all__
    assert "write_eval_run_manifest_json" not in context_ir.__all__
    assert not hasattr(context_ir, "EvalManifestCaseCount")
    assert not hasattr(context_ir, "EvalRunManifest")
    assert not hasattr(context_ir, "build_eval_run_manifest")
    assert not hasattr(context_ir, "eval_run_manifest_to_json")
    assert not hasattr(context_ir, "write_eval_run_manifest_json")
    assert not hasattr(eval_manifest, "publish_eval_manifest")
    assert not hasattr(eval_manifest, "render_public_claims")
    assert not hasattr(eval_manifest, "write_public_benchmark_report")

    assert set(eval_manifest.EvalManifestCaseCount.__dataclass_fields__) == {
        "case_id",
        "record_count",
    }
    assert set(eval_manifest.EvalRunManifest.__dataclass_fields__) == {
        "spec_path",
        "ledger_path",
        "report_path",
        "plan_id",
        "record_count",
        "written_run_ids",
        "case_record_counts",
        "task_ids",
        "provider_names",
        "budgets",
        "budget_violation_run_ids",
    }

    forbidden_fields = {
        "public_claims",
        "claim_gate",
        "benchmark_summary",
        "provider_aggregates",
        "task_budget_results",
        "markdown_report",
        "ledger_records",
        "generated_at",
    }
    manifest_fields = set(eval_manifest.EvalRunManifest.__dataclass_fields__)

    assert forbidden_fields.isdisjoint(manifest_fields)

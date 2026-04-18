"""Deterministic internal eval pipeline composition tests."""

from __future__ import annotations

import copy
from pathlib import Path

import context_ir
import context_ir.eval_pipeline as eval_pipeline
import context_ir.eval_report as eval_report
import context_ir.eval_runs as eval_runs
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


def test_execute_eval_pipeline_supports_nested_caller_paths_and_writes_exact_report(
    tmp_path: Path,
) -> None:
    """The internal pipeline composes one smoke run into honest typed artifacts."""
    ledger_path = tmp_path / "ledgers" / "nested" / "smoke.jsonl"
    report_path = tmp_path / "reports" / "nested" / "smoke.md"

    assert not ledger_path.parent.exists()
    assert not report_path.parent.exists()

    artifact = _execute_smoke_pipeline(ledger_path, report_path)

    assert isinstance(artifact, eval_pipeline.EvalPipelineArtifact)
    assert isinstance(artifact.execution_result, eval_runs.EvalRunExecutionResult)
    assert isinstance(artifact.report_artifact, eval_report.EvalReportArtifact)
    assert artifact.execution_result.output_path == ledger_path
    assert artifact.report_artifact.source_ledger_path == ledger_path
    assert artifact.report_output_path == report_path
    assert report_path.read_text(encoding="utf-8") == (
        artifact.report_artifact.markdown_report
    )
    assert report_path.read_bytes() == artifact.report_artifact.markdown_report.encode(
        "utf-8"
    )


def test_execute_eval_pipeline_is_deterministic_for_independent_smoke_runs(
    tmp_path: Path,
) -> None:
    """Independent smoke executions compose into equivalent deterministic results."""
    first_artifact = _execute_smoke_pipeline(
        tmp_path / "first.jsonl",
        tmp_path / "first.md",
    )
    second_artifact = _execute_smoke_pipeline(
        tmp_path / "second.jsonl",
        tmp_path / "second.md",
    )

    assert (
        first_artifact.execution_result.plan_id
        == second_artifact.execution_result.plan_id
    )
    assert (
        first_artifact.execution_result.record_count
        == second_artifact.execution_result.record_count
    )
    assert (
        first_artifact.execution_result.written_run_ids
        == second_artifact.execution_result.written_run_ids
    )
    assert (
        first_artifact.execution_result.case_record_counts
        == second_artifact.execution_result.case_record_counts
    )
    assert (
        first_artifact.report_artifact.summary
        == second_artifact.report_artifact.summary
    )
    assert (
        first_artifact.report_artifact.markdown_report
        == second_artifact.report_artifact.markdown_report
    )
    assert (tmp_path / "first.md").read_text(encoding="utf-8") == (
        tmp_path / "second.md"
    ).read_text(encoding="utf-8")


def test_execute_eval_pipeline_does_not_mutate_returned_artifact_after_followup_reads(
    tmp_path: Path,
) -> None:
    """Follow-up reads leave the frozen typed pipeline artifact unchanged."""
    artifact = _execute_smoke_pipeline(
        tmp_path / "smoke.jsonl",
        tmp_path / "smoke.md",
    )
    artifact_before = copy.deepcopy(artifact)

    artifact.report_output_path.read_text(encoding="utf-8")
    artifact.report_output_path.read_bytes()

    assert artifact == artifact_before


def test_eval_pipeline_stays_internal_and_avoids_public_claim_surfaces() -> None:
    """Pipeline composition remains internal and does not add public surfaces."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "EvalPipelineArtifact" not in context_ir.__all__
    assert "execute_eval_pipeline" not in context_ir.__all__
    assert not hasattr(context_ir, "EvalPipelineArtifact")
    assert not hasattr(context_ir, "execute_eval_pipeline")
    assert not hasattr(eval_pipeline, "publish_eval_pipeline")
    assert not hasattr(eval_pipeline, "render_public_claims")
    assert not hasattr(eval_pipeline, "write_public_benchmark_report")

    forbidden_fields = {
        "public_claims",
        "claim_gate",
        "benchmark_summary",
        "report_directory",
        "generated_at",
        "git_commit",
    }
    pipeline_fields = set(eval_pipeline.EvalPipelineArtifact.__dataclass_fields__)

    assert forbidden_fields.isdisjoint(pipeline_fields)

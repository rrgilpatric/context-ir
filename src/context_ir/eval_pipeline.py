"""Deterministic internal eval pipeline composition."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from context_ir.eval_report import (
    EvalReportArtifact,
    build_eval_report,
    write_eval_report_markdown,
)
from context_ir.eval_runs import EvalRunExecutionResult, execute_eval_run_spec


@dataclass(frozen=True)
class EvalPipelineArtifact:
    """Typed deterministic workflow artifact for one eval pipeline execution."""

    execution_result: EvalRunExecutionResult
    report_artifact: EvalReportArtifact
    report_output_path: Path


def execute_eval_pipeline(
    spec_path: Path | str,
    ledger_output_path: Path | str,
    report_output_path: Path | str,
    *,
    git_commit: str,
    python_version: str,
    package_version: str,
    spec_version: str = "v1",
) -> EvalPipelineArtifact:
    """Execute one deterministic eval workflow into caller-provided artifacts."""
    execution_result = execute_eval_run_spec(
        spec_path,
        ledger_output_path,
        git_commit=git_commit,
        python_version=python_version,
        package_version=package_version,
        spec_version=spec_version,
    )
    report_artifact = build_eval_report(execution_result.output_path)
    written_report_path = write_eval_report_markdown(
        report_artifact,
        report_output_path,
    )
    return EvalPipelineArtifact(
        execution_result=execution_result,
        report_artifact=report_artifact,
        report_output_path=written_report_path,
    )


__all__ = [
    "EvalPipelineArtifact",
    "execute_eval_pipeline",
]

"""Deterministic internal bundle-directory orchestration for one eval execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from context_ir.eval_manifest import (
    EvalRunManifest,
    build_eval_run_manifest,
    write_eval_run_manifest_json,
)
from context_ir.eval_pipeline import EvalPipelineArtifact, execute_eval_pipeline

_LEDGER_FILENAME = "ledger.jsonl"
_REPORT_FILENAME = "report.md"
_MANIFEST_FILENAME = "manifest.json"


@dataclass(frozen=True)
class EvalBundlePaths:
    """Deterministic artifact paths for one internal eval bundle directory."""

    bundle_dir: Path
    ledger_path: Path
    report_path: Path
    manifest_path: Path


@dataclass(frozen=True)
class EvalBundleArtifact:
    """Typed deterministic artifact bundle for one completed eval execution."""

    paths: EvalBundlePaths
    pipeline_artifact: EvalPipelineArtifact
    manifest: EvalRunManifest


def execute_eval_bundle(
    spec_path: Path | str,
    bundle_dir: Path | str,
    *,
    git_commit: str,
    python_version: str,
    package_version: str,
    spec_version: str = "v1",
) -> EvalBundleArtifact:
    """Execute one eval pipeline into a deterministic caller-provided bundle."""
    spec_file_path = Path(spec_path)
    paths = _build_bundle_paths(bundle_dir)

    pipeline_artifact = execute_eval_pipeline(
        spec_file_path,
        paths.ledger_path,
        paths.report_path,
        git_commit=git_commit,
        python_version=python_version,
        package_version=package_version,
        spec_version=spec_version,
    )
    manifest = build_eval_run_manifest(spec_file_path, pipeline_artifact)
    written_manifest_path = write_eval_run_manifest_json(manifest, paths.manifest_path)

    if pipeline_artifact.execution_result.output_path != paths.ledger_path:
        raise ValueError("bundle ledger path does not match pipeline output path")
    if pipeline_artifact.report_output_path != paths.report_path:
        raise ValueError("bundle report path does not match pipeline output path")
    if manifest.spec_path != spec_file_path:
        raise ValueError("bundle manifest spec path does not match input spec path")
    if manifest.ledger_path != paths.ledger_path:
        raise ValueError("bundle manifest ledger path does not match bundle path")
    if manifest.report_path != paths.report_path:
        raise ValueError("bundle manifest report path does not match bundle path")
    if written_manifest_path != paths.manifest_path:
        raise ValueError("bundle manifest writer returned an unexpected path")

    return EvalBundleArtifact(
        paths=paths,
        pipeline_artifact=pipeline_artifact,
        manifest=manifest,
    )


def _build_bundle_paths(bundle_dir: Path | str) -> EvalBundlePaths:
    """Return deterministic internal artifact paths for one bundle directory."""
    bundle_directory = Path(bundle_dir)
    return EvalBundlePaths(
        bundle_dir=bundle_directory,
        ledger_path=bundle_directory / _LEDGER_FILENAME,
        report_path=bundle_directory / _REPORT_FILENAME,
        manifest_path=bundle_directory / _MANIFEST_FILENAME,
    )


__all__ = [
    "EvalBundleArtifact",
    "EvalBundlePaths",
    "execute_eval_bundle",
]

"""Deterministic internal eval bundle tests."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import context_ir
import context_ir.eval_bundle as eval_bundle
import context_ir.eval_manifest as eval_manifest
import context_ir.eval_pipeline as eval_pipeline
import context_ir.semantic_types as semantic_types

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_SPEC_PATH = REPO_ROOT / "evals" / "run_specs" / "oracle_smoke_matrix.json"


def _execute_smoke_bundle(bundle_dir: Path) -> eval_bundle.EvalBundleArtifact:
    """Execute the accepted smoke run spec into one deterministic bundle."""
    return eval_bundle.execute_eval_bundle(
        RUN_SPEC_PATH,
        bundle_dir,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )


def test_execute_eval_bundle_writes_nested_bundle_with_deterministic_paths(
    tmp_path: Path,
) -> None:
    """A smoke eval execution composes into one deterministic nested bundle."""
    bundle_dir = tmp_path / "artifacts" / "nested" / "smoke_bundle"

    assert not bundle_dir.exists()

    bundle = _execute_smoke_bundle(bundle_dir)

    assert isinstance(bundle, eval_bundle.EvalBundleArtifact)
    assert isinstance(bundle.paths, eval_bundle.EvalBundlePaths)
    assert isinstance(bundle.pipeline_artifact, eval_pipeline.EvalPipelineArtifact)
    assert isinstance(bundle.manifest, eval_manifest.EvalRunManifest)
    assert bundle.paths.bundle_dir == bundle_dir
    assert bundle.paths.ledger_path == bundle_dir / "ledger.jsonl"
    assert bundle.paths.report_path == bundle_dir / "report.md"
    assert bundle.paths.manifest_path == bundle_dir / "manifest.json"
    assert bundle.paths.bundle_dir.exists()
    assert bundle.paths.ledger_path.exists()
    assert bundle.paths.report_path.exists()
    assert bundle.paths.manifest_path.exists()
    assert (
        bundle.paths.ledger_path
        == bundle.pipeline_artifact.execution_result.output_path
    )
    assert bundle.paths.report_path == bundle.pipeline_artifact.report_output_path
    assert bundle.manifest == eval_manifest.build_eval_run_manifest(
        RUN_SPEC_PATH,
        bundle.pipeline_artifact,
    )
    assert bundle.manifest.spec_path == RUN_SPEC_PATH
    assert bundle.manifest.ledger_path == bundle.paths.ledger_path
    assert bundle.manifest.report_path == bundle.paths.report_path
    assert bundle.paths.report_path.read_bytes() == (
        bundle.pipeline_artifact.report_artifact.markdown_report.encode("utf-8")
    )


def test_execute_eval_bundle_manifest_json_round_trips_to_manifest_payload(
    tmp_path: Path,
) -> None:
    """The bundle manifest file matches the accepted manifest JSON payload exactly."""
    bundle = _execute_smoke_bundle(tmp_path / "bundle")
    payload = eval_manifest.eval_run_manifest_to_json(bundle.manifest)

    assert json.loads(bundle.paths.manifest_path.read_text(encoding="utf-8")) == payload


def test_independent_smoke_bundles_produce_equivalent_manifest_content(
    tmp_path: Path,
) -> None:
    """Independent bundles differ only by caller-selected absolute artifact paths."""
    first_bundle = _execute_smoke_bundle(tmp_path / "first" / "bundle")
    second_bundle = _execute_smoke_bundle(tmp_path / "second" / "bundle")

    normalized_first = replace(
        first_bundle.manifest,
        ledger_path=Path("ledger.jsonl"),
        report_path=Path("report.md"),
    )
    normalized_second = replace(
        second_bundle.manifest,
        ledger_path=Path("ledger.jsonl"),
        report_path=Path("report.md"),
    )

    assert normalized_first == normalized_second


def test_execute_eval_bundle_does_not_mutate_returned_artifacts_after_reads(
    tmp_path: Path,
) -> None:
    """Follow-up reads leave the returned frozen bundle artifacts unchanged."""
    bundle = _execute_smoke_bundle(tmp_path / "bundle")
    pipeline_before = copy.deepcopy(bundle.pipeline_artifact)
    manifest_before = copy.deepcopy(bundle.manifest)

    bundle.paths.ledger_path.read_text(encoding="utf-8")
    bundle.paths.report_path.read_text(encoding="utf-8")
    json.loads(bundle.paths.manifest_path.read_text(encoding="utf-8"))

    assert bundle.pipeline_artifact == pipeline_before
    assert bundle.manifest == manifest_before


def test_eval_bundle_stays_internal_and_avoids_public_claim_surfaces() -> None:
    """Bundle orchestration remains internal and does not add public surfaces."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "EvalBundlePaths" not in context_ir.__all__
    assert "EvalBundleArtifact" not in context_ir.__all__
    assert "execute_eval_bundle" not in context_ir.__all__
    assert not hasattr(context_ir, "EvalBundlePaths")
    assert not hasattr(context_ir, "EvalBundleArtifact")
    assert not hasattr(context_ir, "execute_eval_bundle")
    assert not hasattr(eval_bundle, "publish_eval_bundle")
    assert not hasattr(eval_bundle, "render_public_claims")
    assert not hasattr(eval_bundle, "discover_eval_bundles")

    assert set(eval_bundle.EvalBundlePaths.__dataclass_fields__) == {
        "bundle_dir",
        "ledger_path",
        "report_path",
        "manifest_path",
    }
    assert set(eval_bundle.EvalBundleArtifact.__dataclass_fields__) == {
        "paths",
        "pipeline_artifact",
        "manifest",
    }

    forbidden_fields = {
        "public_claims",
        "claim_gate",
        "benchmark_summary",
        "bundle_index",
        "generated_at",
        "git_commit",
    }

    assert forbidden_fields.isdisjoint(eval_bundle.EvalBundlePaths.__dataclass_fields__)
    assert forbidden_fields.isdisjoint(
        eval_bundle.EvalBundleArtifact.__dataclass_fields__
    )

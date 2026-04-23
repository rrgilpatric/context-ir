"""Deterministic internal eval report artifact tests."""

from __future__ import annotations

import copy
from pathlib import Path

import context_ir
import context_ir.eval_report as eval_report
import context_ir.eval_runs as eval_runs
import context_ir.eval_summary as eval_summary
import context_ir.semantic_types as semantic_types

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_SPEC_PATH = REPO_ROOT / "evals" / "run_specs" / "oracle_smoke_matrix.json"


def _execute_smoke_ledger(path: Path) -> Path:
    """Execute the accepted smoke run spec into one temporary ledger path."""
    eval_runs.execute_eval_run_spec(
        RUN_SPEC_PATH,
        path,
        git_commit="abc1234",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )
    return path


def test_build_eval_report_creates_typed_artifact_from_smoke_ledger(
    tmp_path: Path,
) -> None:
    """A smoke ledger composes into one typed deterministic report artifact."""
    ledger_path = _execute_smoke_ledger(tmp_path / "smoke.jsonl")

    report = eval_report.build_eval_report(ledger_path)

    assert isinstance(report, eval_report.EvalReportArtifact)
    assert report.source_ledger_path == ledger_path
    assert isinstance(report.summary, eval_summary.EvalLedgerSummary)
    assert report.summary == eval_summary.build_eval_ledger_summary(
        eval_summary.load_eval_ledger(ledger_path)
    )
    assert report.markdown_report == eval_summary.render_eval_ledger_summary(
        report.summary
    )
    assert "## Capability-Tier Accounting" in report.markdown_report


def test_write_eval_report_markdown_writes_exact_artifact_markdown(
    tmp_path: Path,
) -> None:
    """Writing a report persists the exact deterministic Markdown body."""
    report = eval_report.build_eval_report(
        _execute_smoke_ledger(tmp_path / "smoke.jsonl")
    )
    output_path = tmp_path / "report.md"

    written_path = eval_report.write_eval_report_markdown(report, output_path)

    assert written_path == output_path
    assert output_path.read_text(encoding="utf-8") == report.markdown_report


def test_build_eval_report_is_deterministic_for_independent_smoke_ledgers(
    tmp_path: Path,
) -> None:
    """Independent accepted smoke ledgers compose into identical report bodies."""
    first_report = eval_report.build_eval_report(
        _execute_smoke_ledger(tmp_path / "first.jsonl")
    )
    second_report = eval_report.build_eval_report(
        _execute_smoke_ledger(tmp_path / "second.jsonl")
    )

    assert first_report.source_ledger_path == tmp_path / "first.jsonl"
    assert second_report.source_ledger_path == tmp_path / "second.jsonl"
    assert first_report.summary == second_report.summary
    assert first_report.markdown_report == second_report.markdown_report


def test_write_eval_report_markdown_does_not_mutate_report_artifact(
    tmp_path: Path,
) -> None:
    """Writing a report leaves the typed report artifact unchanged."""
    report = eval_report.build_eval_report(
        _execute_smoke_ledger(tmp_path / "smoke.jsonl")
    )
    report_before = copy.deepcopy(report)

    eval_report.write_eval_report_markdown(report, tmp_path / "report.md")

    assert report == report_before


def test_eval_report_stays_internal_and_avoids_public_claim_surfaces() -> None:
    """Report composition remains internal and does not add public surfaces."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "EvalReportArtifact" not in context_ir.__all__
    assert "build_eval_report" not in context_ir.__all__
    assert "write_eval_report_markdown" not in context_ir.__all__
    assert not hasattr(context_ir, "EvalReportArtifact")
    assert not hasattr(context_ir, "build_eval_report")
    assert not hasattr(context_ir, "write_eval_report_markdown")
    assert not hasattr(eval_report, "publish_eval_report")
    assert not hasattr(eval_report, "render_public_claims")
    assert not hasattr(eval_report, "discover_eval_reports")

    forbidden_fields = {
        "public_claims",
        "claim_gate",
        "readme_path",
        "eval_md_path",
        "report_directory",
        "generated_at",
        "git_commit",
    }
    report_fields = set(eval_report.EvalReportArtifact.__dataclass_fields__)

    assert forbidden_fields.isdisjoint(report_fields)

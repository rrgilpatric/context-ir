"""Deterministic internal eval report artifact tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import context_ir
import context_ir.eval_report as eval_report
import context_ir.eval_runs as eval_runs
import context_ir.eval_summary as eval_summary
import context_ir.semantic_types as semantic_types

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_SPEC_PATH = REPO_ROOT / "evals" / "run_specs" / "oracle_smoke_matrix.json"
GETATTR_DEFAULT_RUN_SPEC_PATH = (
    REPO_ROOT
    / "evals"
    / "run_specs"
    / "oracle_signal_getattr_default_probe_matrix.json"
)
GETATTR_DEFAULT_VALUE_RUN_SPEC_PATH = (
    REPO_ROOT
    / "evals"
    / "run_specs"
    / "oracle_signal_getattr_default_value_probe_matrix.json"
)


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


def _write_runtime_outcome_ledger(path: Path) -> Path:
    """Write one compact ledger with both defaulted getattr outcomes."""
    records = [
        _runtime_outcome_record(
            run_id="run-default",
            lookup_outcome="returned_default_value",
        ),
        _runtime_outcome_record(
            run_id="run-value",
            lookup_outcome="returned_value",
        ),
    ]
    path.write_text(
        "\n".join(
            json.dumps(record, separators=(",", ":"), sort_keys=True)
            for record in records
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _execute_defaulted_getattr_branch_ledger(path: Path) -> Path:
    """Execute both accepted defaulted getattr branch specs into one ledger."""
    for run_spec_path in (
        GETATTR_DEFAULT_RUN_SPEC_PATH,
        GETATTR_DEFAULT_VALUE_RUN_SPEC_PATH,
    ):
        eval_runs.execute_eval_run_spec(
            run_spec_path,
            path,
            git_commit="abc1234",
            python_version="3.11.9",
            package_version=context_ir.__version__,
        )
    return path


def _runtime_outcome_record(
    *,
    run_id: str,
    lookup_outcome: str,
) -> dict[str, object]:
    """Return one minimal ledger row with normalized runtime outcome data."""
    return {
        "run_id": run_id,
        "task_id": "task_alpha",
        "provider_name": "provider_alpha",
        "budget": 100,
        "provider_metadata": {"selected_units": []},
        "resolved_selectors": [],
        "runtime_provenance_records": [
            {
                "record_id": f"prov:runtime:unsupported:{run_id}",
                "normalized_payload": {"lookup_outcome": lookup_outcome},
            }
        ],
        "metrics": {
            "budget_compliant": True,
            "aggregate_score": 0.5,
            "edit_coverage": 0.5,
            "support_coverage": 0.5,
            "representation_adequacy": 0.5,
            "uncertainty_honesty": 0.5,
            "noise_efficiency": 0.5,
        },
    }


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
    assert "### Selected Units by Provider" in report.markdown_report
    assert (
        "### Selected Units by Provider and Actual Primary Tier"
        in report.markdown_report
    )
    assert "## Runtime Outcome Accounting" in report.markdown_report


def test_build_eval_report_surfaces_runtime_outcome_accounting(
    tmp_path: Path,
) -> None:
    """Reports expose separate normalized runtime outcome counts."""
    ledger_path = _write_runtime_outcome_ledger(tmp_path / "runtime_outcomes.jsonl")

    report = eval_report.build_eval_report(ledger_path)

    assert tuple(
        (
            aggregate.payload_key,
            aggregate.payload_value,
            aggregate.runtime_provenance_count,
        )
        for aggregate in report.summary.runtime_outcome_aggregates
    ) == (
        ("lookup_outcome", "returned_default_value", 1),
        ("lookup_outcome", "returned_value", 1),
    )
    assert "| lookup_outcome | returned_default_value | 1 |" in report.markdown_report
    assert "| lookup_outcome | returned_value | 1 |" in report.markdown_report


def test_eval_report_distinguishes_defaulted_getattr_branch_outcomes(
    tmp_path: Path,
) -> None:
    """A report over both defaulted getattr branches keeps branch outcomes separate."""
    ledger_path = _execute_defaulted_getattr_branch_ledger(
        tmp_path / "defaulted_getattr_branches.jsonl"
    )

    report = eval_report.build_eval_report(ledger_path)

    assert tuple(
        (
            aggregate.payload_key,
            aggregate.payload_value,
            aggregate.runtime_provenance_count,
        )
        for aggregate in report.summary.runtime_outcome_aggregates
        if aggregate.payload_key == "lookup_outcome"
    ) == (
        ("lookup_outcome", "returned_default_value", 3),
        ("lookup_outcome", "returned_value", 3),
    )
    assert "| lookup_outcome | returned_default_value | 3 |" in report.markdown_report
    assert "| lookup_outcome | returned_value | 3 |" in report.markdown_report


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

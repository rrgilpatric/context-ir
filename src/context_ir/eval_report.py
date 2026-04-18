"""Internal deterministic eval report composition for one raw ledger."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from context_ir.eval_summary import (
    EvalLedgerSummary,
    build_eval_ledger_summary,
    load_eval_ledger,
    render_eval_ledger_summary,
)


@dataclass(frozen=True)
class EvalReportArtifact:
    """Typed deterministic Markdown report artifact for one eval ledger."""

    source_ledger_path: Path
    summary: EvalLedgerSummary
    markdown_report: str


def build_eval_report(ledger_path: Path | str) -> EvalReportArtifact:
    """Compose one accepted raw ledger into a typed deterministic report."""
    ledger = load_eval_ledger(ledger_path)
    summary = build_eval_ledger_summary(ledger)
    markdown_report = render_eval_ledger_summary(summary)
    return EvalReportArtifact(
        source_ledger_path=ledger.source_path,
        summary=summary,
        markdown_report=markdown_report,
    )


def write_eval_report_markdown(
    report: EvalReportArtifact,
    output_path: Path | str,
) -> Path:
    """Write the exact deterministic Markdown body to a caller path."""
    destination_path = Path(output_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(report.markdown_report, encoding="utf-8")
    return destination_path

from pkg.collector import collect_signal_rows
from pkg.digest import render_assignment_digest
from pkg.labels import build_priority_labels


def run_signal_smoke_b(query: str) -> str:
    rows = collect_signal_rows(query)
    labels = build_priority_labels(rows)
    digest = render_assignment_digest(rows, labels)
    gap_registry.record_assignment_note(digest)
    return digest

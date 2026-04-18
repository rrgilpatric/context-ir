def render_assignment_digest(rows: list[str], labels: list[str]) -> str:
    row_text = " / ".join(rows)
    label_text = ", ".join(labels)
    return f"assignment digest: {row_text} [{label_text}]"

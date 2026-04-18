def build_priority_labels(rows: list[str]) -> list[str]:
    labels = [f"priority:{index + 1}" for index, _ in enumerate(rows)]
    if not labels:
        return ["priority:none"]
    return labels

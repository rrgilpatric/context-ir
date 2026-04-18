def build_execution_plan(query: str) -> list[str]:
    cleaned_query = query.strip() or "signal smoke"
    return [
        f"collect signal for {cleaned_query}",
        "draft execution plan",
        "confirm preview",
    ]

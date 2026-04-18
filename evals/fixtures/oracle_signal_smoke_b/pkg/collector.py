def collect_signal_rows(query: str) -> list[str]:
    cleaned_query = query.strip() or "signal digest"
    first_row = f"assignment signal for {cleaned_query}"
    second_row = "priority labels stay deterministic"
    third_row = "digest note stays visible"
    return [first_row, second_row, third_row]

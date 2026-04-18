def resolve_owner_alias(query: str) -> str:
    normalized_query = query.lower()
    if "owner" in normalized_query or "alias" in normalized_query:
        return "ops-handoff"
    return "review-handoff"

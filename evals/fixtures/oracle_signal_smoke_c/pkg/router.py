from pkg.registry import resolve_owner_alias


def build_handoff_route(query: str) -> list[str]:
    owner_alias = resolve_owner_alias(query)
    route = [f"owner:{owner_alias}", "keep route summary aligned"]
    handoff_tracker.record_missing_note(route)
    return route

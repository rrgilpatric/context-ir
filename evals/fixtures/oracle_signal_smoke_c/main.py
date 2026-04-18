from pkg.router import build_handoff_route
from pkg.summary import render_route_summary


def run_signal_smoke_c(query: str) -> str:
    handoff_query = query.strip() or "missing handoff note"
    route = build_handoff_route(handoff_query)
    return render_route_summary(route)

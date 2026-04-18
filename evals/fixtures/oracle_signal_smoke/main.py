from pkg.planner import build_execution_plan
from pkg.presenter import *
from pkg.presenter import render_patch_preview


def run_signal_smoke(query: str) -> str:
    plan = build_execution_plan(query)
    preview = render_patch_preview(plan)
    record_missing_step(plan)
    return preview

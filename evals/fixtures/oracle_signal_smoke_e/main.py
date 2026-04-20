from pkg.service import MemberSignalCompiler


def run_signal_smoke_e(query: str) -> str:
    compiler = MemberSignalCompiler()
    return compiler.compile_member_digest(query)

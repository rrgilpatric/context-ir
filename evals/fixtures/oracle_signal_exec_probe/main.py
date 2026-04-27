def probe_exec_source() -> str:
    source = "pass"
    exec(source)
    return "completed"


def render_probe_digest() -> str:
    value = probe_exec_source()
    return f"exec:{value}"

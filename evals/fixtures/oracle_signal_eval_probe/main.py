def probe_eval_source() -> str:
    source = '"eval-probe-value"'
    return eval(source)


def render_probe_digest() -> str:
    value = probe_eval_source()
    return f"eval:{value}"

def probe_literal_attribute(obj: object) -> bool:
    return hasattr(obj, "bit_length")


def render_probe_digest() -> str:
    status = "ready" if probe_literal_attribute(1) else "missing"
    return f"hasattr_literal:{status}"

def probe_attribute(obj: object, name: str) -> bool:
    return hasattr(obj, name)


def render_probe_digest() -> str:
    status = "ready" if probe_attribute(1, "bit_length") else "missing"
    return f"hasattr:{status}"

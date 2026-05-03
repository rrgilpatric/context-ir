def probe_attribute(obj: object, name: str) -> bool:
    return hasattr(obj, name)


def render_probe_digest() -> str:
    status = (
        "present" if probe_attribute(1, "definitely_missing_attribute") else "missing"
    )
    return f"hasattr_false:{status}"

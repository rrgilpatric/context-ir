def probe_attribute(obj: object, name: str, default: object) -> object:
    return getattr(obj, name, default)


def render_probe_digest() -> str:
    fallback = object()
    status = (
        "default"
        if probe_attribute(1, "missing_attribute", fallback) is fallback
        else "value"
    )
    return f"getattr-default:{status}"

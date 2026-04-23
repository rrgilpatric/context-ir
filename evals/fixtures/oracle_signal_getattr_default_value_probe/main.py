def probe_attribute(obj: object, name: str, default: object) -> object:
    return getattr(obj, name, default)


def render_probe_digest() -> str:
    fallback = object()
    value = probe_attribute(1, "bit_length", fallback)
    status = "value" if value is not fallback else "default"
    return f"getattr-default-value:{status}"

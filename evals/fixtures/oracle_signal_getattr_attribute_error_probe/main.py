def probe_attribute(obj: object, name: str) -> object:
    return getattr(obj, name)


def render_probe_digest() -> str:
    try:
        probe_attribute(1, "definitely_missing_attribute")
    except AttributeError:
        status = "raised_attribute_error"
    else:
        status = "returned_value"
    return f"getattr_attribute_error:{status}"

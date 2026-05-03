def probe_namespace(obj: object) -> dict[str, object]:
    return vars(obj)


def render_probe_digest() -> str:
    try:
        probe_namespace(1)
    except TypeError:
        status = "raised_type_error"
    else:
        status = "returned_namespace"
    return f"vars_type_error:{status}"

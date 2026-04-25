def probe_local_namespace() -> dict[str, object]:
    return vars()


def render_probe_digest() -> str:
    namespace = probe_local_namespace()
    return f"vars:{len(namespace)}"

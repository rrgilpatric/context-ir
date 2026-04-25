def probe_local_namespace() -> dict[str, object]:
    marker = "locals"
    return locals()


def render_probe_digest() -> str:
    namespace = probe_local_namespace()
    return f"locals:{namespace['marker']}:{len(namespace)}"

def probe_global_namespace() -> dict[str, object]:
    return globals()


def render_probe_digest() -> str:
    namespace = probe_global_namespace()
    return f"globals:{len(namespace)}"

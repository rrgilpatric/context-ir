def probe_directory(obj: object) -> list[str]:
    return dir(obj)


def render_probe_digest() -> str:
    names = probe_directory(1)
    return f"dir:{len(names)}"

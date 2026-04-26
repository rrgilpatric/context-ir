def probe_directory() -> list[str]:
    return dir()


def render_probe_digest() -> str:
    names = probe_directory()
    return f"dir:{len(names)}"

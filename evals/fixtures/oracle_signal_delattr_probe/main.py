class ProbeTarget:
    def __init__(self) -> None:
        self.flag = "ready"


def probe_delete_attribute(obj: object, name: str) -> None:
    delattr(obj, name)


def render_probe_digest() -> str:
    target = ProbeTarget()
    probe_delete_attribute(target, "flag")
    return "delattr:deleted"

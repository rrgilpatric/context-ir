class ProbeTarget:
    def __init__(self) -> None:
        self.flag = "ready"


def probe_delete_literal_attribute(obj: object) -> None:
    delattr(obj, "flag")


def render_probe_digest() -> str:
    target = ProbeTarget()
    probe_delete_literal_attribute(target)
    return "delattr_literal:deleted"

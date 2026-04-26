class ProbeTarget:
    def __init__(self) -> None:
        self.flag: object = "initial"


def probe_set_attribute(obj: object, name: str, value: object) -> None:
    setattr(obj, name, value)


def render_probe_digest() -> str:
    target = ProbeTarget()
    probe_set_attribute(target, "flag", "ready")
    return f"setattr:{target.flag}"

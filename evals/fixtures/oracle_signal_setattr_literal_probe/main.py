class ProbeTarget:
    def __init__(self) -> None:
        self.flag: object = "initial"


def probe_set_literal_attribute(obj: object, value: object) -> None:
    setattr(obj, "flag", value)


def render_probe_digest() -> str:
    target = ProbeTarget()
    probe_set_literal_attribute(target, "ready")
    return f"setattr_literal:{target.flag}"

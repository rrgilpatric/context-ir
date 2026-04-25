class ProbeRecord:
    def __init__(self, label: str) -> None:
        self.label = label


def probe_namespace(obj: object) -> dict[str, object]:
    return vars(obj)


def render_probe_digest() -> str:
    namespace = probe_namespace(ProbeRecord("ready"))
    return f"vars:{namespace['label']}"

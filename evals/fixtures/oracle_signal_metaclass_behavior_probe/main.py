class Base:
    pass


class Meta(type):
    pass


class Example(Base, metaclass=Meta):
    pass


def render_probe_digest() -> str:
    return f"metaclass:{Example.__name__}:{type(Example).__name__}"

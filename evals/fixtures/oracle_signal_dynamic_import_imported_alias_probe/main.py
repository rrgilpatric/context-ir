from importlib import import_module as load_module


def load_weather_plugin() -> str:
    name = "plugins.weather"
    module = load_module(name)
    return module.render_card()


def render_probe_digest() -> str:
    digest = load_weather_plugin()
    return f"probe:{digest}"

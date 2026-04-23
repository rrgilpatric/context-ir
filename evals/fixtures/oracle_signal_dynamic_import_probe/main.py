from importlib import import_module


def load_weather_plugin() -> str:
    module = import_module("plugins.weather")
    return module.render_card()


def render_probe_digest() -> str:
    digest = load_weather_plugin()
    return f"probe:{digest}"

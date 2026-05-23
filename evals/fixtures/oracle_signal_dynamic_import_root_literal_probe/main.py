import importlib


def load_weather_plugin() -> str:
    module = importlib.import_module("plugins.weather")
    return module.render_card()


def render_probe_digest() -> str:
    digest = load_weather_plugin()
    return f"probe:{digest}"

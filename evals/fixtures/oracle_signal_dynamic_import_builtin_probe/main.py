import sys


def load_weather_plugin() -> str:
    name = "plugins.weather"
    __import__(name)
    module = sys.modules[name]
    return module.render_card()


def render_probe_digest() -> str:
    digest = load_weather_plugin()
    return f"probe:{digest}"

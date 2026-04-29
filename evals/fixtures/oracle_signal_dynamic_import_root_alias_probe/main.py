import importlib as loader


def load_weather_plugin() -> str:
    name = "plugins.weather"
    module = loader.import_module(name)
    return module.render_card()


def render_probe_digest() -> str:
    digest = load_weather_plugin()
    return f"probe:{digest}"

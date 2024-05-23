from os.path import dirname, abspath, join

from dynaconf import Dynaconf

current_dir = dirname(abspath(__file__))

class SingletonSettings:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SingletonSettings, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "settings"):
            current_dir = dirname(abspath(__file__))
            self.settings = Dynaconf(
                envvar_prefix=False,
                merge_enabled=True,
                settings_files=[join(current_dir, f) for f in [
                    "test_generation_prompt.toml",
                    "language_extensions.toml", ]]
            )


def get_settings():
    return SingletonSettings().settings

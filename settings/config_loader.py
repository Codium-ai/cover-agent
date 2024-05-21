from dynaconf import Dynaconf

global_settings = Dynaconf(
    envvar_prefix=False,
    merge_enabled=True,
settings_files=["settings/config.toml"]
)

def get_settings():
    return global_settings

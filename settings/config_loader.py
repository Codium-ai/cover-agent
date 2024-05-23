from dynaconf import Dynaconf

global_settings = Dynaconf(
    envvar_prefix=False,
    merge_enabled=True,
settings_files=["settings/test_generation_prompt.toml"]
)

def get_settings():
    return global_settings
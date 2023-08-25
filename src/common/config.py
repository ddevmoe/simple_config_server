import os


_PREFIX = 'SCS'


def resolve_config_value(name: str, default=None) -> str | None:
    full_name = f'{_PREFIX}_{name}'
    value = os.environ.get(full_name, default)
    return value


HTTP_PORT = int(resolve_config_value('HTTP_PORT', 8080))
LOCAL_FOLDER_LOADER_PATH = resolve_config_value('LOCAL_CONFIG_FOLDER_PATH', './configs')

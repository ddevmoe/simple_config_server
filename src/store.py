from collections import defaultdict

from src.common import errors
from src.common.models import EnvConfig
from src.loaders import LoaderBase


class ConfigStore:
    def __init__(self, content_loader: LoaderBase):
        self._loader = content_loader
        self._configs: dict[str, dict[str, EnvConfig]] = {}

    async def get_config(self, name: str, env: str) -> dict:
        try:
            config = self._configs[name]
        except KeyError:
            raise errors.ConfigNotFoundError(name) from None

        try:
            env_config = config[env]
        except KeyError:
            raise errors.EnvNotFoundError(name, env) from None

        return env_config.content

    async def reload(self, name: str):
        config = await self._loader.load(name)
        self._configs[config.name] = config.envs

    async def reload_all(self):
        # Completely rewrites the store
        configs = await self._loader.load_all()

        result: dict[str, dict[str, EnvConfig]] = defaultdict(dict)
        for config in configs:
            result[config.name] = config.envs

        self._configs = dict(result)

from src.common import errors
from src.common.models import Config, EnvConfig
from src.parser import ConfigParser
from src.readers import ReaderBase


class ConfigStore:
    def __init__(self, reader: ReaderBase, parser: ConfigParser):
        self._reader = reader
        self._parser = parser
        self._configs: dict[str, Config] = {}

    # TODO: Method is sync, remove async def
    async def get_config(self, name: str) -> Config | None:
        config = self._configs.get(name)
        return config
        try:
            config = self._configs[name]
        except KeyError:
            raise errors.ConfigNotFoundError(name) from None

        try:
            env_config = config.envs[env]
        except KeyError:
            raise errors.EnvNotFoundError(name, env) from None

        return env_config

    def get_available_configs(self) -> list[str]:
        return list(self._configs)

    async def reload(self, name: str):
        unparsed_config = await self._reader.read(name)
        config = self._parser.parse_config(unparsed_config, self._configs.values())
        self._configs[config.name] = config

    async def reload_all(self):
        # Completely rewrites the store
        unparsed_configs = await self._reader.read_all()
        parsed_configs = self._parser.parse_configs(unparsed_configs, [])

        configs = {
            config.name: config
            for config in parsed_configs
        }
        self._configs = configs

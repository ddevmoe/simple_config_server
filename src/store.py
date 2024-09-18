from src.common.models import Config
from src.parser import ConfigParser
from src.readers import ReaderBase


class ConfigStore:
    def __init__(self, reader: ReaderBase, parser: ConfigParser):
        self._reader = reader
        self._parser = parser
        self._configs: dict[str, Config] = {}

    def get_config(self, name: str) -> Config | None:
        config = self._configs.get(name)
        return config

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

import glob
import json
from pathlib import Path

from src.common.errors import ConfigNotFoundError
from src.common.models import Config
from src.parser import ConfigParser
from .loader_base import LoaderBase


class LocalFolderLoader(LoaderBase):
    def __init__(self, parser: ConfigParser, folder_path: str):
        super().__init__(parser)
        self._path = folder_path.rstrip('/')

    def _load_from_path(self, path: str) -> Config:
        with open(path) as of:
            content: dict = json.load(of)

        file_name = Path(path).stem
        config = self._parser.parse_config(file_name, content)
        return config

    async def load(self, name: str) -> Config:
        file_path = glob.glob(f'{self._path}/{name}.json')
        if not file_path:
            raise ConfigNotFoundError(name)

        config = self._load_from_path(file_path[0])
        return config

    async def load_all(self) -> list[Config]:
        configs: list[Config] = []
        file_paths = glob.glob(f'{self._path}/**.json')
        for path in file_paths:
            config = self._load_from_path(path)
            configs.append(config)

        return configs

import glob
from abc import ABC, abstractmethod
from pathlib import Path

from src.common.errors import ConfigNotFoundError
from src.common.models import UnparsedConfig

from .deserializers import DeserializerBase


class ReaderBase(ABC):
    """
    Defines the interface of all `Reader` implementations.

    A `Reader` class provides an interface to a specific kind of resource that contains unparsed configuration
    files.
    """

    def __init__(self):
        ...

    @abstractmethod
    async def read(self, name: str) -> UnparsedConfig:
        ...

    @abstractmethod
    async def read_all(self) -> list[UnparsedConfig]:
        ...


class LocalFolderReader(ReaderBase):
    def __init__(self, deserializer: DeserializerBase, folder_path: str):
        super().__init__()
        self._path = folder_path.rstrip('/')
        self._deserializer = deserializer

    def _load_from_path(self, path: str) -> UnparsedConfig:
        with open(path) as of:
            content = self._deserializer.deserialize(of.read())

        file_name = Path(path).stem
        config = UnparsedConfig(file_name, content)
        return config

    async def read(self, name: str) -> UnparsedConfig:
        file_path = glob.glob(f'{self._path}/{name}.json')
        if not file_path:
            raise ConfigNotFoundError(name)

        config = self._load_from_path(file_path[0])
        return config

    async def read_all(self) -> list[UnparsedConfig]:
        configs: list[UnparsedConfig] = []
        file_paths = glob.glob(f'{self._path}/**.json')
        for path in file_paths:
            config = self._load_from_path(path)
            configs.append(config)

        return configs

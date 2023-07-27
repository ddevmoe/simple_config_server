from abc import ABC, abstractmethod

from src.common.models import Config
from src.parser import ConfigParser


class LoaderBase(ABC):
    def __init__(self, parser: ConfigParser):
        self._parser = parser

    @abstractmethod
    async def load(self, name: str) -> Config:
        ...

    @abstractmethod
    async def load_all(self) -> list[Config]:
        ...

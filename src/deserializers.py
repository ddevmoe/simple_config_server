import json
from abc import ABC, abstractmethod

from src.common.errors import SimpleConfigServerErrorBase


class DeserializerError(SimpleConfigServerErrorBase):
    def __init__(self, deserializer: str, message: str):
        self.deserializer = deserializer
        super().__init__(message)


class DeserializerBase(ABC):
    """
    Provides an interface that resolves `bytes` to `dict`s.
    Allows for decoupling of `Reader` implementations from content types, and enables an easy interface with various content types (json, yaml, toml, etc.).
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def deserialize(self, content: bytes | str) -> dict:
        ...


class JsonDeserializer(DeserializerBase):
    """
    Deserializes JSON compatible data
    """

    def __init__(self):
        super().__init__('json-deserializer')

    def deserialize(self, content: bytes) -> dict:
        value = json.loads(content)

        if not isinstance(value, dict):
            raise DeserializerError(self.name, f'Provided content could not be resolved to `dict` compatible type')

        return value

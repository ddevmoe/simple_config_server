from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel


@dataclass
class Location:
    BROKEN_PLACEHOLDER = '-x->'
    FILE_REF_PLACEHOLDER = '->'

    path: Iterable[str]

    def __str__(self) -> str:
        pretty_path = (
            '.'.join(self.path)
            .replace(f'.{self.BROKEN_PLACEHOLDER}.', f' {self.BROKEN_PLACEHOLDER} ')
            .replace(f'.{self.FILE_REF_PLACEHOLDER}.', f' {self.FILE_REF_PLACEHOLDER} ')
        )
        return pretty_path


class Problem(BaseModel):
    message: str
    location: Location

    def __str__(self) -> str:
        pretty_message = f'{{{self.location}}}: {self.message}'
        return pretty_message


@dataclass
class UnparsedConfig:
    name: str
    content: dict


class EnvConfig(BaseModel):
    """Represents a complete configuration of specific value"""
    name: str
    env: str
    content: dict
    problems: list[Problem]

    @property
    def has_problems(self) -> bool:
        return bool(self.problems)


class Config(BaseModel):
    """Holds all environments of a config"""
    name: str
    default_env: EnvConfig
    envs: dict[str, EnvConfig]
    problems: list[Problem]

    @property
    def has_problems(self) -> bool:
        return bool(self.problems)

    def get_env(self, env: str) -> EnvConfig | None:
        return self.envs.get(env)

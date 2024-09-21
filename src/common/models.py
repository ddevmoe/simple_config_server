from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel, Field


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
    """Represents a complete configuration of specific env"""

    name: str
    env: str
    content: dict
    problems: list[Problem] = Field(default_factory=list)

    @property
    def has_problems(self) -> bool:
        return bool(self.problems)

    def __repr__(self) -> str:
        result = f'{self.name}[{self.env}]'

        if self.has_problems:
            result += f'!({len(self.problems)})'

        return result


class Config(BaseModel):
    """Holds all environments of a config"""

    name: str
    default_env: EnvConfig
    envs: dict[str, EnvConfig]
    problems: list[Problem] = Field(default_factory=list)

    @property
    def has_problems(self) -> bool:
        return bool(self.problems)

    def __repr__(self) -> str:
        result = self.name

        env_reprs = [
            (
                f'{config_env.env}!({len(config_env.problems)})'
                if config_env.has_problems
                else config_env.env
            )
            for config_env in [self.default_env, *self.envs.values()]
        ]

        result = f'{self.name}[{",".join(env_reprs)}]'
        if self.has_problems:
            result += f'!({len(self.problems)})'

        return result

    def get_env(self, env: str) -> EnvConfig | None:
        return self.envs.get(env)

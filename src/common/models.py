from dataclasses import dataclass


@dataclass
class UnparsedConfig:
    name: str
    content: dict


@dataclass
class EnvConfig:
    name: str
    env: str
    content: dict


@dataclass
class Config:
    name: str
    envs: dict[str, EnvConfig]

from collections import defaultdict
from copy import deepcopy
from typing import Annotated, Iterable

from pydantic import BaseModel, Field, ValidationError

from src import merger, reference_resolver
from src.common import config
from src.common.models import (
    Config,
    Location,
    Problem,
    EnvConfig,
    UnparsedConfig,
)


class _ShardSchema(BaseModel):
    envs: Annotated[
        list[str],
        Field(pattern=config.VALID_ENV_PATTERN),
    ]
    content: dict


class _PreparsedConfig(BaseModel):
    default: dict
    shards: list[_ShardSchema]


class ConfigParseResult(BaseModel):
    config: Config | None
    problems: list[Problem]


class ConfigParser:
    def _parse_config_model_problems(self, validation_error: ValidationError) -> list[Problem]:
        errors = validation_error.errors(include_url=False)

        problems: list[Problem] = []
        for error in errors:
            location = Location([str(key) for key in error['loc']])
            problem = Problem(message=error["msg"], location=location)
            problems.append(problem)

        return problems

    def _generate_config(self, unparsed_config: UnparsedConfig) -> Config:
        """
        Convert `UnparsedConfig` instance to `Config`
        """

        try:
            preparsed_config = _PreparsedConfig(**unparsed_config.content)
        except ValidationError as validation_error:
            problems = self._parse_config_model_problems(validation_error)
            default_env = EnvConfig(name=unparsed_config.name, env='default', content={}, problems=[])
            return Config(name=unparsed_config.name, default_env=default_env, envs={}, problems=problems)

        content_by_env: dict[str, dict] = defaultdict(lambda: deepcopy(preparsed_config.default))

        problems_by_env: dict[str, list[Problem]] = defaultdict(list)
        for shard_index, shard in enumerate(preparsed_config.shards):
            for env in shard.envs:
                try:
                    merged = merger.merge(content_by_env[env], shard.content)
                    content_by_env[env] = merged
                except merger.MergeUnequalTypesError as merge_error:
                    # Append location of the merge error in the unparsed config (including shard index)
                    location = Location(['shards', str(shard_index), *merge_error.path])
                    problem = Problem(message=str(merge_error), location=location)
                    problems_by_env[env].append(problem)

        built_env_configs = {
            env: EnvConfig(name=unparsed_config.name, env=env, content=content, problems=problems_by_env[env])
            for env, content in content_by_env.items()
        }

        default_env = EnvConfig(name=unparsed_config.name, env='default', content=preparsed_config.default, problems=[])
        parsed_config = Config(name=unparsed_config.name, default_env=default_env, envs=built_env_configs, problems=[])
        return parsed_config

    def parse_configs(self, unparsed_configs: list[UnparsedConfig], existing_configs: Iterable[Config]) -> list[Config]:
        """
        Converts an `UnparsedConfig` instance to a `Config` instance and resolves
        references to other config files
        """

        parsed_configs = [self._generate_config(config) for config in unparsed_configs]

        # Take out configs from `existing_configs` if they are being replaced by the newly provided configs
        new_config_names = {config.name for config in parsed_configs}
        non_replaced_configs = [config for config in existing_configs if config.name not in new_config_names]
        current_configs = parsed_configs + non_replaced_configs

        resolved_configs = reference_resolver.resolve_references(current_configs)
        return resolved_configs

    def parse_config(self, unparsed_config: UnparsedConfig, existing_configs: Iterable[Config]) -> Config:
        """
        Converts an `UnparsedConfig` instance to a `Config` instance and resolves
        references to other config files
        """

        parsed_configs = self.parse_configs([unparsed_config], existing_configs)
        config = next(config for config in parsed_configs if config.name == unparsed_config.name)
        return config

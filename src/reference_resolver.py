"""
This reference resolution method uses recursion and nested traversal to resolve config references.

Another solution that might be more efficient (yet more complicated to implement / operate?) is to build a config reference
graph and start the resolution from the leaves (configs that do not reference others), thus saving the "nested traversal" inefficiency.
"""

import re
from dataclasses import dataclass
from typing import Any, TypeVar

from src.common.errors import SimpleConfigServerErrorBase
from src.common.models import Config, EnvConfig


T = TypeVar('T')

CONFIG_REFERENCE_PATTERN = '^\\${[0-9A-Za-z._-]+}$'


class SelfReferencingConfigurationError(SimpleConfigServerErrorBase):
    MESSAGE = 'Configuration must not reference itself'

    def __init__(self, config_name: str, env: str, reference_location: list[str]):
        super().__init__(self.MESSAGE)
        self.config_name = config_name
        self.env = env
        self.reference_location = reference_location

    def __str__(self) -> str:
        pretty_reference_location = '.'.join(self.reference_location)
        return f'Config "{self.config_name}" under env "{self.env}" is referencing itself at "{pretty_reference_location}"'


class ReferencingNonExistentConfigurationError(SimpleConfigServerErrorBase):
    MESSAGE = 'A configuration reference points to a nonexistent configuration'

    def __init__(self, config_name: str, env: str, reference_location: list[str], referenced_config_name: str):
        super().__init__(self.MESSAGE)
        self.config_name = config_name
        self.env = env
        self.reference_location = reference_location
        self.referenced_config_name = referenced_config_name

    def __str__(self) -> str:
        pretty_reference_location = '.'.join(self.reference_location)
        return f'Config "{self.config_name}" under env "{self.env}" contains a reference at "{pretty_reference_location}" to config "{self.referenced_config_name}" but it does not exist'


@dataclass
class ConfigReference:
    config_name: str
    env: str
    reference_target: list[str]


def is_value_a_reference(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    matched_reference_pattern = re.match(CONFIG_REFERENCE_PATTERN, value)
    return bool(matched_reference_pattern)


def build_config_reference(env: str, value: str) -> ConfigReference:
    reference_parts = value.strip('${}').split('.')
    config_name = reference_parts[0]
    reference_path = reference_parts[1:]
    return ConfigReference(config_name, env, reference_path)


def _get_nested_dictionary_value(dict_for_traversal: dict, path: list[str]) -> Any:
    value = dict_for_traversal
    for key in path:
        value = value[key]
    return value


def resolve_config_env_value(
    root_path: list[str],
    value: T,
    current_config: EnvConfig,
    config_by_name: dict[str, Config]
) -> T:
    if isinstance(value, dict):
        resolved_value = {}
        for key, traversed_value in value.items():
            nested_path = [*root_path, key]
            resolved_traversed_value = resolve_config_env_value(nested_path, traversed_value, current_config, config_by_name)
            resolved_value[key] = resolved_traversed_value
        return resolved_value  # type: ignore

    if not isinstance(value, str):
        return value

    if not is_value_a_reference(value):
        return value

    reference = build_config_reference(current_config.env, value)
    if reference.config_name == current_config.name:
        raise SelfReferencingConfigurationError(current_config.name, current_config.env, root_path)

    if reference.config_name not in config_by_name:
        raise ReferencingNonExistentConfigurationError(current_config.name, current_config.env, root_path, reference.config_name)

    referenced_config = config_by_name[reference.config_name]
    if not current_config.env in referenced_config.envs:
        pass  # TODO: Display warning for taking value from env default?

    referenced_env = referenced_config.envs.get(current_config.env) or referenced_config.envs['default']
    referenced_value = _get_nested_dictionary_value(referenced_env.content, reference.reference_target)

    # The referenced value might be a dictionary that contains more references (or be a reference itself), we make sure
    # to fully resolve them too.
    resolved_referenced_value = resolve_config_env_value(root_path, referenced_value, current_config, config_by_name)
    return resolved_referenced_value


def resolve_config(config: Config, config_by_name: dict[str, Config]) -> Config:
    resolved_envs: dict[str, EnvConfig] = {}
    for env_config in config.envs.values():
        resolved_content = resolve_config_env_value([], env_config.content, env_config, config_by_name)
        resolved_env = EnvConfig(env_config.name, env_config.env, resolved_content)
        resolved_envs[env_config.env] = resolved_env

    resolved_config = Config(config.name, resolved_envs)
    return resolved_config


def resolve_references(configs: list[Config]) -> list[Config]:
    config_by_name = {config.name: config for config in configs}

    resolved_configs: list[Config] = []
    for config in configs:
        resolved_config = resolve_config(config, config_by_name)
        resolved_configs.append(resolved_config)

    return resolved_configs

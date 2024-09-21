import re
from dataclasses import dataclass
from typing import Any, TypeVar

from src.common.models import Config, EnvConfig, Location, Problem


T = TypeVar('T')

CONFIG_REFERENCE_PATTERN = '^\\$\\{(?:[0-9A-Za-z_-]+)(?:\\.[0-9A-Za-z_-]+)*\\}$'
REFERENCE_RESOLUTION_ERROR_MESSAGE = 'UNRESOLVED_REFERENCE'


class _NonexistentKeyError(Exception):
    """
    Used internally by this module to accurately determine the location of a missing key reference
    """

    def __init__(self, missing_key_path: list[str]):
        self.missing_key_path = missing_key_path

    def __str__(self) -> str:
        pretty_path = '.'.join(self.missing_key_path[:-1])
        return f'{pretty_path} -x-> {self.missing_key_path[-1]}'


@dataclass
class ConfigReference:
    target_config_name: str
    env: str
    target_reference_path: list[str]


def is_value_a_reference(value: Any) -> bool:
    # TODO: Deal with invalid references (i.e. "${configname.some...key}")?
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
    """Returns value at `path` in dict `dict_for_traversal`"""
    value = dict_for_traversal
    for key in path:
        if not isinstance(value, dict) or key not in value:
            traversed_path = path[:path.index(key) + 1]
            raise _NonexistentKeyError(traversed_path)
        value = value[key]
    return value


def _resolve_config_env_value(
    root_path: list[str],
    value: Any,
    current_config: EnvConfig,
    config_by_name: dict[str, Config],
) -> Any:
    """
    `value`s that are neither a reference nor a dict are returned immediately,

    `dict`s have their values recuresively iterated.

    Detected references are resolved to their targets.
    """

    if isinstance(value, dict):
        resolved_value = {}
        for key, traversed_value in value.items():
            nested_path = [*root_path, key]
            resolved_traversed_value = _resolve_config_env_value(nested_path, traversed_value, current_config, config_by_name)
            resolved_value[key] = resolved_traversed_value
        return resolved_value

    if not isinstance(value, str):
        return value

    if not is_value_a_reference(value):
        return value

    reference = build_config_reference(current_config.env, value)
    if reference.target_config_name == current_config.name:
        current_config.problems.append(Problem(
            message='circular reference',
            location=Location([current_config.name, *root_path, Location.BROKEN_PLACEHOLDER, reference.target_config_name]),
        ))
        return f'{REFERENCE_RESOLUTION_ERROR_MESSAGE} ({value})'

    if reference.target_config_name not in config_by_name:
        current_config.problems.append(Problem(
            message='referencing a nonexistent config',
            location=Location([current_config.name, *root_path, Location.BROKEN_PLACEHOLDER, reference.target_config_name]),
        ))
        return f'{REFERENCE_RESOLUTION_ERROR_MESSAGE} ({value})'

    referenced_config = config_by_name[reference.target_config_name]
    if referenced_config.has_problems:
        current_config.problems.append(Problem(
            message='cannot reference a config with unresolved problems',
            location=Location([current_config.name, *root_path, Location.BROKEN_PLACEHOLDER, reference.target_config_name]),
        ))
        return f'{REFERENCE_RESOLUTION_ERROR_MESSAGE} ({value})'

    referenced_env = referenced_config.envs.get(current_config.env) or referenced_config.default_env
    try:
        # If the reference has no path we assign the targeted content
        if not reference.target_reference_path:
            referenced_value = referenced_env.content
        else:
            referenced_value = _get_nested_dictionary_value(referenced_env.content, reference.target_reference_path)
    except _NonexistentKeyError as error:
        current_config.problems.append(Problem(
            message='referencing a nonexistent key',
            location=Location([
                current_config.name,
                *root_path,
                Location.FILE_REF_PLACEHOLDER,
                f'{referenced_env.name}[{referenced_env.env}]',
                *error.missing_key_path[:-1],
                Location.BROKEN_PLACEHOLDER,
                error.missing_key_path[-1],
            ]),
        ))
        return f'{REFERENCE_RESOLUTION_ERROR_MESSAGE} ({value})'

    # The referenced value might be a dict that contains more references (or be a reference itself), we make sure
    # to fully resolve them too.
    resolved_referenced_value = _resolve_config_env_value(root_path, referenced_value, current_config, config_by_name)
    return resolved_referenced_value


def _resolve_config_references(config: Config, config_by_name: dict[str, Config]) -> Config:
    resolved_envs: dict[str, EnvConfig] = {}
    for env_config in config.envs.values():
        # Skip envs with problems to avoid clutter, as new problems are likely to emerge from existing problems
        if env_config.has_problems:
            resolved_envs[env_config.env] = env_config
            continue

        resolved_content: dict = _resolve_config_env_value([], env_config.content, env_config, config_by_name)

        resolved_env = env_config.model_copy(update={'content': resolved_content})
        resolved_envs[env_config.env] = resolved_env

    # Resolve default env explicitly as it isn't in `config.envs.values()`
    resolved_default_env_content: dict = _resolve_config_env_value([], config.default_env.content, config.default_env, config_by_name)
    resolved_default_env = config.default_env.model_copy(update={'content': resolved_default_env_content})

    resolved_config = config.model_copy(update={'default_env': resolved_default_env, 'envs': resolved_envs})
    return resolved_config


def resolve_references(configs: list[Config]) -> list[Config]:
    config_by_name = {config.name: config for config in configs}

    resolved_configs: list[Config] = []
    for config in configs:
        resolved_config = _resolve_config_references(config, config_by_name)
        resolved_configs.append(resolved_config)

    return resolved_configs

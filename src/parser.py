from collections import defaultdict
from copy import deepcopy
from typing import Iterable

from src import merger
from src import reference_resolver
from src.common.models import Config, EnvConfig, UnparsedConfig


class ConfigParser:
    def _generate_config(self, unparsed_config: UnparsedConfig) -> Config:
        """
        Converts an `UnparsedConfig` instance to a `Config` instance
        """

        defaults: dict = unparsed_config.content.get('default', {})
        shards: list[dict] = unparsed_config.content.get('shards', [])

        content_by_env: dict[str, dict] = defaultdict(lambda: deepcopy(defaults))
        content_by_env['default'] = defaults

        for shard in shards:
            shard_envs = shard['envs']
            shard_content = shard['content']
            for env in shard_envs:
                merged = merger.merge(content_by_env[env], shard_content)
                content_by_env[env] = merged

        built_configs: dict[str, EnvConfig] = {}
        for env, content in content_by_env.items():
            env_config = EnvConfig(unparsed_config.name, env, content)
            built_configs[env] = env_config

        parsed_config = Config(unparsed_config.name, built_configs)
        return parsed_config

    def parse_configs(self, unparsed_configs: list[UnparsedConfig], existing_configs: Iterable[Config]) -> list[Config]:
        parsed_configs = [self._generate_config(config) for config in unparsed_configs]

        # Take out configs from `existing_configs` if they are being replaced by the newly provided configs
        new_config_names = {config.name for config in parsed_configs}
        non_replaced_configs = [config for config in existing_configs if config.name not in new_config_names]
        current_configs = parsed_configs + non_replaced_configs

        resolved_configs = reference_resolver.resolve_references(current_configs)
        return resolved_configs

    def parse_config(self, unparsed_config: UnparsedConfig, existing_configs: Iterable[Config]):
        """
        Converts an `UnparsedConfig` instance to a `Config` instance and resolving
        references to other config files, if provided via `` parameter
        """

        parsed_configs = self.parse_configs([unparsed_config], existing_configs)
        config = next(config for config in parsed_configs if config.name == unparsed_config.name)
        return config

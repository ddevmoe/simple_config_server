from collections import defaultdict
from copy import deepcopy

from src import merger
from src.common.models import Config, EnvConfig


class ConfigParser:
    def parse_config(self, config_name: str, data: dict) -> Config:
        defaults = data.get('default', {})
        raw_shards = data.get('shards', [])

        content_by_env: dict[str, dict] = defaultdict(lambda: deepcopy(defaults))
        content_by_env['default'] = defaults

        for shard in raw_shards:
            shard_envs = shard['envs']
            shard_content = shard['content']
            for env in shard_envs:
                merged = merger.merge(content_by_env[env], shard_content)
                content_by_env[env] = merged

        built_configs: dict[str, EnvConfig] = {}
        for env, content in content_by_env.items():
            env_config = EnvConfig(config_name, env, content)
            built_configs[env] = env_config

        parsed_config = Config(config_name, built_configs)
        return parsed_config

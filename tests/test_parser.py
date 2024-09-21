from unittest import TestCase

from src.common.models import Config, EnvConfig, UnparsedConfig
from src.parser import ConfigParser

class TestParser(TestCase):
    def test_parse_config__no_envs_returns_default_config(self):
        # Arrange
        config_name = 'config1'
        unparsed_config = UnparsedConfig(
            name=config_name,
            content={
                'default': {'key1': 'value1'},
                'shards': [],
            },
        )
        expected = Config(
            name=config_name,
            default_env=EnvConfig(name=config_name, env='default', content={'key1': 'value1'}),
            envs={},
        )
        parser = ConfigParser()

        # Act
        actual = parser.parse_config(unparsed_config, existing_configs=[])

        # Assert
        self.assertEqual(actual, expected)

    def test_parse_config__one_env__returns_both_env_and_default(self):
        # Arrange
        config_name = 'config1'
        unparsed_config = UnparsedConfig(
            name=config_name,
            content={
                'default': {'key1': 'value1'},
                'shards': [
                    {
                        'envs': ['env1'],
                        'content': {},
                    },
                ],
            },
        )
        expected = Config(
            name=config_name,
            default_env=EnvConfig(name=config_name, env='default', content={'key1': 'value1'}),
            envs={'env1': EnvConfig(name=config_name, env='env1', content={'key1': 'value1'})},
        )
        parser = ConfigParser()

        # Act
        actual = parser.parse_config(unparsed_config, [])

        # Assert
        self.assertEqual(actual, expected)

    def test_parse_config__one_shard__two_envs__returns_all_envs(self):
        # Arrange
        config_name = 'config1'
        unparsed_config = UnparsedConfig(
            name=config_name,
            content={
                'default': {'key1': 'value1'},
                'shards': [
                    {
                        'envs': ['env1', 'env2'],
                        'content': {},
                    },
                ],
            },
        )
        expected = Config(
            name=config_name,
            default_env=EnvConfig(name=config_name, env='default', content={'key1': 'value1'}),
            envs={
                'env1': EnvConfig(name=config_name, env='env1', content={'key1': 'value1'}),
                'env2': EnvConfig(name=config_name, env='env2', content={'key1': 'value1'}),
            },
        )
        parser = ConfigParser()

        # Act
        actual = parser.parse_config(unparsed_config, [])

        # Assert

        self.assertEqual(actual, expected)

    def test_parse_config__one_env__only_env_is_overriden(self):
        # Arrange
        config_name = 'config1'
        unparsed_config = UnparsedConfig(
            name=config_name,
            content={
                'default': {'key1': 'value1'},
                'shards': [
                    {
                        'envs': ['env1'],
                        'content': {'key1': 'overridden'},
                    },
                ],
            },
        )
        expected = Config(
            name=config_name,
            default_env=EnvConfig(name=config_name, env='default', content={'key1': 'value1'}),
            envs={'env1': EnvConfig(name=config_name, env='env1', content={'key1': 'overridden'})},
        )
        parser = ConfigParser()

        # Act
        actual = parser.parse_config(unparsed_config, [])

        # Assert
        self.assertEqual(actual, expected)

    def test_parse_config__one_shard_with_two_envs__each_env_is_overriden(self):
        # Arrange
        config_name = 'config1'
        unparsed_config = UnparsedConfig(
            name=config_name,
            content={
                'default': {'key1': 'value1'},
                'shards': [
                    {
                        'envs': ['env1', 'env2'],
                        'content': {'key1': 'overridden'},
                    },
                ],
            },
        )
        expected = Config(
            name=config_name,
            default_env=EnvConfig(name=config_name, env='default', content={'key1': 'value1'}),
            envs={
                'env1': EnvConfig(name=config_name, env='env1', content={'key1': 'overridden'}),
                'env2': EnvConfig(name=config_name, env='env2', content={'key1': 'overridden'}),
            },
        )
        parser = ConfigParser()

        # Act
        actual = parser.parse_config(unparsed_config, [])

        # Assert
        self.assertEqual(actual, expected)

    def test_parse_config__two_shards_with_same_env__shards_are_merged_correctly(self):
        # Arrange
        config_name = 'config1'
        unparsed_config = UnparsedConfig(
            name=config_name,
            content={
                'default': {'key1': 'value1'},
                'shards': [
                    {
                        'envs': ['env1'],
                        'content': {'key1': 'overridden'},
                    },
                    {
                        'envs': ['env1'],
                        'content': {'key2': 'from_shard2'}
                    },
                ],
            },
        )
        expected = Config(
            name=config_name,
            default_env=EnvConfig(name=config_name, env='default', content={'key1': 'value1'}),
            envs={'env1': EnvConfig(name=config_name, env='env1', content={'key1': 'overridden', 'key2': 'from_shard2'})},
        )
        parser = ConfigParser()

        # Act
        actual = parser.parse_config(unparsed_config, [])

        # Assert
        self.assertEqual(actual, expected)

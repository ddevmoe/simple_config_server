from copy import deepcopy
from unittest import TestCase

from src import reference_resolver
from src.common.models import Config, EnvConfig

class TestReferenceResolver(TestCase):
    def test_resolve_references(self):
        # Arrange
        referenced_config = Config(
            'referenced_config',
            {'default': EnvConfig('referenced_config', 'default', {'referenced_key': 'referenced_value'})},
        )

        referencing_config = Config(
            'referencing_config',
            {
                'default': EnvConfig(
                    'referencing_config',
                    'default',
                    {
                        'key1': 'value1',
                        'referencing_key': '${referenced_config.referenced_key}',
                    },
                ),
            },
        )

        expected_resolved_config = Config(
            'referencing_config',
            {
                'default': EnvConfig(
                    'referencing_config',
                    'default',
                    {
                        'key1': 'value1',
                        'referencing_key': 'referenced_value',
                    },
                ),
            },
        )

        expected_result = [referenced_config, expected_resolved_config]

        # Act
        result = reference_resolver.resolve_references([referenced_config, referencing_config])

        # Assert
        self.assertEqual(result, expected_result)

    #####
    def test_resolve_references__original_configs_are_unchanged(self):
        # Arrange
        referenced_config = Config(
            'referenced_config',
            {'default': EnvConfig('referenced_config', 'default', {'referenced_key': 'referenced_value'})},
        )

        referencing_config = Config(
            'referencing_config',
            {
                'default': EnvConfig(
                    'referencing_config',
                    'default',
                    {
                        'key1': 'value1',
                        'referencing_key': '${referenced_config.referenced_key}',
                    },
                ),
            },
        )

        original_configs = [deepcopy(referenced_config), deepcopy(referencing_config)]

        # Act
        _result = reference_resolver.resolve_references([referenced_config, referencing_config])

        # Assert
        self.assertEqual(
            [referenced_config, referencing_config],
            original_configs,
            'Expected reference resolution to keep the original configs unchanged'
        )

    def test_resolve_references__single_config__config_is_unchanged(self):
        # Arrange
        config = Config(
            'config_name',
            {'default': EnvConfig('config_name', 'default', {'key1': 'value1'})},
        )
        original_config = deepcopy(config)

        expected_result = [config]

        # Act
        result = reference_resolver.resolve_references([config])

        # Assert
        self.assertEqual(result, expected_result)

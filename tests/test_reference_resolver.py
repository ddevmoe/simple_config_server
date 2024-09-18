from copy import deepcopy
from unittest import TestCase


from src import reference_resolver
from src.common.models import Config, EnvConfig


class TestReferenceDetection(TestCase):
    def _assert_valid(self, reference: str, description: str):
        self.assertTrue(
            reference_resolver.is_value_a_reference(reference),
            f'expected {description} to be valid',
        )

    def test_reference_detection__valid_values__true(self):
        self._assert_valid('${filename}', 'filename only')
        self._assert_valid('${filename.key1}', 'reference to a key')
        self._assert_valid('${filename.key1.key2}', 'reference to a nested key')

    def _assert_invalid(self, reference: str, description: str):
        self.assertFalse(
            reference_resolver.is_value_a_reference(reference),
            f'expected {description} to be invalid',
        )

    def test_reference_detection__invalid_values__false(self):
        # Trailing Dots
        self._assert_invalid('${config_name.}', 'trailing single dot at end')
        self._assert_invalid('${.config_name}', 'trailing single dot at start')
        self._assert_invalid('${config_name.key1.}', 'trailing dot at end with key')
        self._assert_invalid('${.config_name.key1}', 'trailing dot at start with key')
        self._assert_invalid('${config_name.key1..}', 'trailing double dots at end')

        # Multiple Dots
        self._assert_invalid('${config_name..key1}', 'double dots after filename')
        self._assert_invalid('${config_name.key1..key2}', 'double dots after key')

        # Missing Characters
        self._assert_invalid('$config_name', 'missing braces filename only')
        self._assert_invalid('$config_name.key1', 'missing braces single key')
        self._assert_invalid('$config_name.key1.key2', 'missing braces nested key')
        self._assert_invalid('{config_name}', 'missing dollar filename only')
        self._assert_invalid('{config_name.key1}', 'missing dollar single key')
        self._assert_invalid('{config_name.key1.key2}', 'missing dollar nested key')
        self._assert_invalid('$config_name}', 'missing left brace filename only')
        self._assert_invalid('$config_name.key1}', 'missing left brace single key')
        self._assert_invalid('$config_name.key1.key2}', 'missing left brace nested key')
        self._assert_invalid('${config_name', 'missing right brace filename only')
        self._assert_invalid('${config_name.key1', 'missing right brace single key')
        self._assert_invalid('${config_name.key1.key2', 'missing right brace nested key')


class TestReferenceResolution(TestCase):
    def test_resolve_references(self):
        # Arrange
        referenced_config = Config(
            name='referenced_config',
            envs={'default': EnvConfig('referenced_config', 'default', {'referenced_key': 'referenced_value'})},
        )

        referencing_config = Config(
            name='referencing_config',
            envs={
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
            name='referencing_config',
            envs={
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

    def test_resolve_references__original_configs_are_unchanged(self):
        # Arrange
        referenced_config = Config(
            name='referenced_config',
            envs={'default': EnvConfig('referenced_config', 'default', {'referenced_key': 'referenced_value'})},
        )

        referencing_config = Config(
            name='referencing_config',
            envs={
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
            name='config_name',
            envs={'default': EnvConfig('config_name', 'default', {'key1': 'value1'})},
        )
        original_config = deepcopy(config)

        expected_result = [config]

        # Act
        result = reference_resolver.resolve_references([config])

        # Assert
        self.assertEqual(result, expected_result)

    def test_resolve_references__referencing_nonexistent_env__resolves_values_from_default(self):
        """
        When referencing from an env that doesn't exist in the target config,
        values should be resolved using the default env
        """

        # Arrange
        referenced_config = Config(
            name='referenced_config',
            envs={'default': EnvConfig('referenced_config', 'default', {'referenced_key': 'referenced_value'})},
        )

        referencing_config = Config(
            name='referencing_config',
            envs={
                'default': EnvConfig(
                    name='referencing_config',
                    env='default',
                    content={},
                ),
                'env1': EnvConfig(
                    name='referencing_config',
                    env='env1',
                    content={'referencing_key': '${referenced_config.referenced_key}'},
                ),
            },
        )

        expected_resolved_config = Config(
            name='referencing_config',
            envs={
                'default': EnvConfig(
                    name='referencing_config',
                    env='default',
                    content={},
                ),
                'env1': EnvConfig(
                    name='referencing_config',
                    env='env1',
                    content={'referencing_key': 'referenced_value'},
                ),
            },
        )

        expected_result = [referenced_config, expected_resolved_config]

        # Act
        result = reference_resolver.resolve_references([referenced_config, referencing_config])

        # Assert
        self.assertEqual(result, expected_result)

    def test_resolve_references__nested_references__resolve_successfuly(self):
        # Arrange
        leaf = Config(
            name='leaf',
            envs={'default': EnvConfig('leaf', 'default', {'leaf_key': 'leaf_value'})},
        )

        middle = Config(
            name='middle',
            envs={'default': EnvConfig('middle', 'default', {'middle_key': '${leaf.leaf_key}'})},
        )
        expected_middle = Config(
            name='middle',
            envs={'default': EnvConfig('middle', 'default', {'middle_key': 'leaf_value'})},
        )

        top = Config(
            name='top',
            envs={'default': EnvConfig('top', 'default', {'top_key': '${middle.middle_key}'})},
        )
        expected_top = Config(
            name='top',
            envs={'default': EnvConfig('top', 'default', {'top_key': 'leaf_value'})},
        )

        expected_result = [leaf, expected_middle, expected_top]

        # Act
        result = reference_resolver.resolve_references([leaf, middle, top])

        # Assert
        self.assertEqual(result, expected_result)

    def test_resolve_references__referenced_config_contains_other_references__references_resolve_successfuly(self):
        # Arrange
        leaf = Config(
            name='leaf',
            envs={'default': EnvConfig('leaf', 'default', {'leaf_key': 'leaf_value'})},
        )

        middle = Config(
            name='middle',
            envs={
                'default': EnvConfig(
                    name='middle',
                    env='default',
                    content={'middle_referenced_key': 'middle_referenced_value', 'middle_referencing_key': '${leaf.leaf_key}'},
                ),
            },
        )
        expected_middle = Config(
            name='middle',
            envs={
                'default': EnvConfig(
                    name='middle',
                    env='default',
                    content={'middle_referenced_key': 'middle_referenced_value', 'middle_referencing_key': 'leaf_value'},
                ),
            },
        )

        top = Config(
            name='top',
            envs={'default': EnvConfig('top', 'default', {'top_key': '${middle.middle_referenced_key}'})},
        )
        expected_top = Config(
            name='top',
            envs={'default': EnvConfig('top', 'default', {'top_key': 'middle_referenced_value'})},
        )

        expected_result = [leaf, expected_middle, expected_top]

        # Act
        result = reference_resolver.resolve_references([leaf, middle, top])

        # Assert
        self.assertEqual(result, expected_result)


class TestReferenceResolutionErrorHandline(TestCase):
    def test_resolve_references__self_referencing_config__raises_error(self):
        # Arrange
        self_referencing_config = Config(
            name='self_referencing_config',
            envs={'default': EnvConfig('self_referencing_config', 'default', {'referenced_key': '${self_referencing_config.referenced_key}'})},
        )

        # Act + Assert
        with self.assertRaises(reference_resolver.SelfReferencingConfigurationError, msg='Expected self referencing config to raise an error'):
            _result = reference_resolver.resolve_references([self_referencing_config])

    def test_resolve_references__referencing_nonexistent_config__raises_error(self):
        # Arrange
        referencing_config = Config(
            name='referencing_config',
            envs={'default': EnvConfig('referencing_config', 'default', {'referenced_key': '${nonexistent.referenced_key}'})},
        )

        # Act + Assert
        with self.assertRaises(reference_resolver.ReferencingNonexistentConfigurationError, msg='Expected nonexistent config reference to raise an error'):
            _result = reference_resolver.resolve_references([referencing_config])

    def test_resolve_references__referencing_nonexistent_key__raises_error(self):
        # Arrange
        referenced_config = Config(
            name='referenced_config',
            envs={
                'default': EnvConfig(
                    name='referenced_config',
                    env='default',
                    content={'logs': {'handlers': {'console': {'color': 'neon-pink'}}}},
                ),
            },
        )

        referencing_config = Config(
            name='referencing_config',
            envs={
                'default': EnvConfig(
                    name='referencing_config',
                    env='default',
                    content={'referencing_key': '${referenced_config.logs.handlers.console.nonexistent_key}'},
                ),
            },
        )

        # Act + Assert
        with self.assertRaises(
            reference_resolver.ReferencingNonexistentKeyError,
            msg='Expected referencing a nonexistent key to raise an error',
        ) as mock:
            _result = reference_resolver.resolve_references([referenced_config, referencing_config])

        self.assertEqual(mock.exception.referencing_config_name, referencing_config.name)
        self.assertEqual(mock.exception.env, 'default')
        self.assertEqual(mock.exception.referencing_key, ['referencing_key'])
        self.assertEqual(mock.exception.referenced_config_name, referenced_config.name)
        self.assertEqual(mock.exception.missing_referenced_key_path, ['logs', 'handlers', 'console', 'nonexistent_key'])

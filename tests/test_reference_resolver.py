from copy import deepcopy
from unittest import TestCase


from src import reference_resolver
from src.common.models import Config, EnvConfig, Location, Problem


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
    def test_resolve_references__references_in_default_env(self):
        # Arrange
        referenced_config = Config(
            name='referenced_config',
            default_env=EnvConfig(name='referenced_config', env='default', content={'referenced_key': 'referenced_value'}),
            envs={},
        )

        referencing_config = Config(
            name='referencing_config',
            default_env=EnvConfig(
                name='referencing_config',
                env='default',
                content={
                    'key1': 'value1',
                    'referencing_key': '${referenced_config.referenced_key}',
                },
            ),
            envs={},
        )

        expected_resolved_config = Config(
            name='referencing_config',
            default_env=EnvConfig(
                name='referencing_config',
                env='default',
                content={
                    'key1': 'value1',
                    'referencing_key': 'referenced_value',
                },
            ),
            envs={},
        )

        expected_result = [referenced_config, expected_resolved_config]

        # Act
        result = reference_resolver.resolve_references([referenced_config, referencing_config])

        # Assert
        self.assertEqual(result, expected_result)

    def test_resolve_references__references_in_specific_env(self):
        # Arrange
        referenced_config = Config(
            name='referenced_config',
            default_env=EnvConfig(name='referenced_config', env='default', content={'referenced_key': 'referenced_value'}),
            envs={}, # TODO: Add env1 here to test references resolution on something that isn't the default env
        )

        referencing_config = Config(
            name='referencing_config',
            default_env=EnvConfig(name='referencing_config', env='default', content={'somekey': 'somevalue'}),
            envs={
                'env1': EnvConfig(
                    name='referencing_config',
                    env='env1',
                    content={
                        'key1': 'value1',
                        'referencing_key': '${referenced_config.referenced_key}',
                    },
                ),
            },
        )

        expected_resolved_config = Config(
            name='referencing_config',
            default_env=EnvConfig(name='referencing_config', env='default', content={'somekey': 'somevalue'}),
            envs={
                'env1': EnvConfig(
                    name='referencing_config',
                    env='env1',
                    content={
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
            default_env=EnvConfig(name='referenced_config', env='default', content={'some_key': 'some_value'}),
            envs={'env1': EnvConfig(name='referenced_config', env='env1', content={'referenced_key': 'referenced_value'})},
        )

        referencing_config = Config(
            name='referencing_config',
            default_env=EnvConfig(name='referencing_config', env='default', content={'other_key': 'other_value'}),
            envs={
                'env1': EnvConfig(
                    name='referencing_config',
                    env='env1',
                    content={
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
            default_env=EnvConfig(name='config_name', env='default', content={'default_key1': 'default_value1'}),
            envs={'env1': EnvConfig(name='config_name', env='env1', content={'key1': 'value1'})},
        )
        expected_result = [deepcopy(config)]

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
            default_env=EnvConfig(name='referenced_config', env='default', content={'referenced_key': 'referenced_value'}),
            envs={},
        )

        referencing_config = Config(
            name='referencing_config',
            default_env=EnvConfig(name='referencing_config', env='default', content={}),
            envs={
                'env1': EnvConfig(
                    name='referencing_config',
                    env='env1',
                    content={'referencing_key': '${referenced_config.referenced_key}'},
                ),
            },
        )

        expected_resolved_config = Config(
            name='referencing_config',
            default_env=EnvConfig(name='referencing_config', env='default', content={}),
            envs={
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
            default_env=EnvConfig(name='leaf', env='default', content={'leaf_key': 'leaf_value'}),
            envs={},
        )

        middle = Config(
            name='middle',
            default_env=EnvConfig(name='middle', env='default', content={'middle_key': '${leaf.leaf_key}'}),
            envs={},
        )
        expected_middle = Config(
            name='middle',
            default_env=EnvConfig(name='middle', env='default', content={'middle_key': 'leaf_value'}),
            envs={},
        )

        top = Config(
            name='top',
            default_env=EnvConfig(name='top', env='default', content={'top_key': '${middle.middle_key}'}),
            envs={},
        )
        expected_top = Config(
            name='top',
            default_env=EnvConfig(name='top', env='default', content={'top_key': 'leaf_value'}),
            envs={},
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
            default_env=EnvConfig(name='leaf', env='default', content={'leaf_key': 'leaf_value'}),
            envs={},
        )

        middle = Config(
            name='middle',
            default_env=EnvConfig(
                name='middle',
                env='default',
                content={'middle_referenced_key': 'middle_referenced_value', 'middle_referencing_key': '${leaf.leaf_key}'},
            ),
            envs={},
        )
        expected_middle = Config(
            name='middle',
            default_env=EnvConfig(
                name='middle',
                env='default',
                content={'middle_referenced_key': 'middle_referenced_value', 'middle_referencing_key': 'leaf_value'},
            ),
            envs={},
        )

        top = Config(
            name='top',
            default_env=EnvConfig(name='top', env='default', content={'top_key': '${middle.middle_referenced_key}'}),
            envs={},
        )
        expected_top = Config(
            name='top',
            default_env=EnvConfig(name='top', env='default', content={'top_key': 'middle_referenced_value'}),
            envs={},
        )

        expected_result = [leaf, expected_middle, expected_top]

        # Act
        result = reference_resolver.resolve_references([leaf, middle, top])

        # Assert
        self.assertEqual(result, expected_result)


class TestReferenceResolutionProblems(TestCase):
    def _extract_problems(self, configs: list[Config]) -> list[Problem]:
        """Extracts problems from a config and it's envs"""
        problems: list[Problem] = []
        for config in configs:
            problems.extend(config.problems)
            problems.extend(config.default_env.problems)
            env_problems = [
                problem
                for env_config in config.envs.values()
                for problem in env_config.problems
            ]
            problems.extend(env_problems)

        return problems

    def test_resolve_references__self_referencing_config__is_problem(self):
        # Arrange
        self_referencing_config = Config(
            name='self_referencing_config',
            default_env=EnvConfig(name='self_referencing_config', env='default', content={'referenced_key': '${self_referencing_config.referenced_key}'}),
            envs={},
        )
        expected_problems = [
            Problem(
                message='circular reference',
                location=Location([
                    'self_referencing_config',
                    'referenced_key',
                    Location.BROKEN_PLACEHOLDER,
                    'self_referencing_config',
                ]),
            ),
        ]

        # Act
        result = reference_resolver.resolve_references([self_referencing_config])
        actual_problems = self._extract_problems(result)

        # Assert
        self.assertEqual(actual_problems, expected_problems, 'Expected self referencing config to create a problem')

    def test_resolve_references__referencing_nonexistent_config__is_problem(self):
        # Arrange
        referencing_config = Config(
            name='referencing_config',
            default_env=EnvConfig(name='referencing_config', env='default', content={'referenced_key': '${nonexistent.referenced_key}'}),
            envs={},
        )
        expected_problems = [
            Problem(
                message='referencing a nonexistent config',
                location=Location([
                    'referencing_config',
                    'referenced_key',
                    Location.BROKEN_PLACEHOLDER,
                    'nonexistent',
                ]),
            ),
        ]

        # Act
        result = reference_resolver.resolve_references([referencing_config])
        actual_problems = self._extract_problems(result)

        # Assert
        self.assertEqual(actual_problems, expected_problems, msg='Expected nonexistent config reference to raise an error')

    def test_resolve_references__referencing_nonexistent_key__is_problem(self):
        # Arrange
        referenced_config = Config(
            name='referenced_config',
            default_env=EnvConfig(
                name='referenced_config',
                env='default',
                content={'logs': {'handlers': {'console': {'color': 'neon-pink'}}}},
            ),
            envs={},
        )

        referencing_config = Config(
            name='referencing_config',
            default_env=EnvConfig(
                name='referencing_config',
                env='default',
                content={'referencing_key': '${referenced_config.logs.handlers.console.nonexistent_key}'},
            ),
            envs={},
        )
        expected_problems = [
            Problem(
                message='referencing a nonexistent key',
                location=Location([
                    'referencing_config',
                    'referencing_key',
                    Location.FILE_REF_PLACEHOLDER,
                    'referenced_config[default]',
                    'logs',
                    'handlers',
                    'console',
                    Location.BROKEN_PLACEHOLDER,
                    'nonexistent_key',
                ]),
            ),
        ]

        # Act
        result = reference_resolver.resolve_references([referenced_config, referencing_config])
        actual_problems = self._extract_problems(result)

        # Assert
        self.assertEqual(actual_problems, expected_problems, msg='Expected referencing a nonexistent key to raise an error')

from unittest import TestCase

from src import merger


class TestMerger(TestCase):
    def test_merger__latest_mapping_overrides_previous(self):
        # Arrange
        d1 = {'key': 'value1'}
        d2 = {'key': 'value2'}
        expected = {'key': 'value2'}

        # Act
        actual = merger.merge(d1, d2)

        # Assert
        self.assertEqual(actual, expected, 'Expected latest mapping to override previous ones')

    def test_merger__multiple_overrides__only_latest_is_kept(self):
        # Arrange
        d1 = {'key': 'value1'}
        d2 = {'key': 'value2'}
        d3 = {'key': 'value3'}
        expected = {'key': 'value3'}

        # Act
        actual = merger.merge(d1, d2, d3)

        # Assert
        self.assertEqual(actual, expected, 'Expected latest mapping to override previous ones')

    def test_merger__single_mapping__unchanged(self):
        # Arrange
        d1 = {'key': 'value1'}
        expected = {'key': 'value1'}

        # Act
        actual = merger.merge(d1)

        # Assert
        self.assertEqual(actual, expected, 'Expected single mapping to remain unchanged')

    def test_merger__original_mapping_unmodified(self):
        # Arrange
        d1 = {'key': 'value1'}
        d2 = {'key': 'value2'}
        expected = d1.copy()

        # Act
        _ = merger.merge(d1, d2)

        # Assert
        self.assertEqual(d1, expected, 'Expected original mapping to remain unmodified')

    def test_merger__nested_mappings_are_merged(self):
        # Arrange
        d1 = {'key': {'nested1': 'value1'}}
        d2 = {'key': {'nested2': 'value2'}}
        expected = {'key': {'nested1': 'value1', 'nested2': 'value2'}}

        # Act
        actual = merger.merge(d1, d2)

        # Assert
        self.assertEqual(actual, expected, 'Expected nested mappings to be merged')

    def test_merger__nested_mapping_key__is_overriden(self):
        # Arrange
        d1 = {'key': {'nested_mapping': {'nested_key': 'value1'}}}
        d2 = {'key': {'nested_mapping': {'nested_key': 'value2'}}}
        expected = {'key': {'nested_mapping': {'nested_key': 'value2'}}}

        # Act
        actual = merger.merge(d1, d2)

        # Assert
        self.assertEqual(actual, expected, 'Expected nested mapping key to be overriden')

    def test_merger__lists_are_concatenated(self):
        # Arrange
        d1 = {'items': [1, 2]}
        d2 = {'items': [3, 4]}
        expected = {'items': [1, 2, 3, 4]}

        # Act
        actual = merger.merge(d1, d2)

        # Assert
        self.assertEqual(actual, expected, 'Expected lists to be concatenated')

    def test_merger__different_type_of_values__same_path__raises_error(self):
        # Arrange
        d1 = {'key': 'value'}
        d2 = {'key': 1}

        # Act + Assert
        with self.assertRaises(merger.UnequalTypeError) as _error:
            _ = merger.merge(d1, d2)

    def test_merger__different_type_of_values__same_nested_path__raises_error_with_correct_path(self):
        # Arrange
        d1 = {'key': {'nested_key': 'value'}}
        d2 = {'key': {'nested_key': 1}}
        expected_base_type = 'str'
        expected_extra_type = 'int'
        expected_path = ['key', 'nested_key']

        # Act + Assert
        try:
            _ = merger.merge(d1, d2)
        except merger.UnequalTypeError as error:
            self.assertEqual(error.path, expected_path, 'Expected error to contain fauly path')
            self.assertEqual(error.base_type, expected_base_type)
            self.assertEqual(error.extra_type, expected_extra_type)

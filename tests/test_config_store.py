from unittest import IsolatedAsyncioTestCase

from src.common.models import Config, EnvConfig, UnparsedConfig
from src.parser import ConfigParser
from src.readers import ReaderBase
from src.store import ConfigStore


class MockReader(ReaderBase):
    def __init__(self):
        self._read_return_value: UnparsedConfig | None = None
        self._load_all_return_value: list[UnparsedConfig] | None = None
        super().__init__()

    def set_read_return_value(self, value: UnparsedConfig):
        self._read_return_value = value

    def set_read_all_return_value(self, value: list[UnparsedConfig]):
        self._load_all_return_value = value

    async def read(self, name: str) -> UnparsedConfig:
        if self._read_return_value is None:
            raise ValueError('Nothing broke, the mock was probably misused. No value was set before calling to `read`')

        return self._read_return_value

    async def read_all(self) -> list[UnparsedConfig]:
        if self._load_all_return_value is None:
            raise ValueError('Nothing broke, the mock was probably misused. No value was set before calling to `read_all`')

        return self._load_all_return_value


class TestConfigStore(IsolatedAsyncioTestCase):
    async def test_store__returns_config(self):
        # Arrange
        config_name = 'config1'
        unparsed_configs = [
            UnparsedConfig(
                name=config_name,
                content={
                    'default': {},
                    'shards': [
                        {
                            'envs': ['env1'],
                            'content': {'key': 'value'},
                        },
                    ],
                },
            ),
        ]
        expected = Config(
            name=config_name,
            default_env=EnvConfig(name=config_name, env='default', content={}),
            envs={'env1': EnvConfig(name=config_name, env='env1', content={'key': 'value'})},
        )

        parser = ConfigParser()
        reader = MockReader()
        reader.set_read_all_return_value(unparsed_configs)

        store = ConfigStore(reader, parser)

        # Act
        await store.reload_all()
        actual = store.get_config(config_name)

        # Assert
        self.assertEqual(actual, expected)

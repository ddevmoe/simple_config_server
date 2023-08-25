from src.common.errors import SimpleConfigServerErrorBase


class MergeError(SimpleConfigServerErrorBase):
    def __init__(self, message: str, key: str, path: list[str]):
        super().__init__(message)
        self.key = key
        self.path = path


class MergeUnequalTypesError(MergeError):
    MESSAGE = 'Failed merging given key since values\' types are unequal'

    def __init__(
        self,
        base_type: str,
        extra_type: str,
        key: str,
        path: list[str],
    ):
        super().__init__(self.MESSAGE, key, path)
        self.base_type = base_type
        self.extra_type = extra_type

    @property
    def pretty_path(self) -> str:
        return '.'.join(self.path)

    def __str__(self) -> str:
        return f'{self.message} - {self.pretty_path} -> {self.base_type}(base) != {self.extra_type}(extra)'

    def __repr__(self) -> str:
        return str(self)


def _merge(base: dict, extra: dict, path: list[str]) -> dict:
    for key, value in extra.items():
        if key not in base:
            base[key] = value
            continue

        base_value = base[key]

        if type(value) != type(base_value):
            raise MergeUnequalTypesError(
                type(base_value).__name__,
                type(value).__name__,
                key,
                [*path, key],
            )

        if isinstance(value, list):
            base[key] = base_value + value

        elif isinstance(value, dict):
            _merge(base_value, value, [*path, key])

        else:
            base[key] = value


def merge(*mappings: dict) -> dict:
    result = {}
    for mapping in mappings:
        _merge(result, mapping, [])

    return result

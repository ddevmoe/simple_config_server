class MergeError(Exception):
    def __init__(self, key: str, path: list[str]):
        self.key = key
        self.path = path


class UnequalTypeError(MergeError):
    def __init__(
        self,
        base_type: str,
        extra_type: str,
        key: str,
        path: list[str],
    ):
        super().__init__(key, path)
        self.base_type = base_type
        self.extra_type = extra_type

    def __str__(self) -> str:
        pretty_path = '.'.join(self.path)
        return f'{pretty_path} -> {self.base_type}(base) != {self.extra_type}(extra)'

    def __repr__(self) -> str:
        return str(self)


def _merge(base: dict, extra: dict, path: list[str]) -> dict:
    for key, value in extra.items():
        if key not in base:
            base[key] = value
            continue

        base_value = base[key]

        if type(value) != type(base_value):
            raise UnequalTypeError(
                type(base_value),
                type(value),
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

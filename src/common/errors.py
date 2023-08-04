class SimpleConfigServerErrorBase(Exception):
    def __init__(self, message: str):
        self.message = message


class ConfigNotFoundError(SimpleConfigServerErrorBase):
    MESSAGE = 'Config not found'

    def __init__(self, name: str):
        super().__init__(self.MESSAGE)
        self.name = name

    def __str__(self) -> str:
        return f'Config "{self.name}" was not found'


class EnvNotFoundError(SimpleConfigServerErrorBase):
    MESSAGE = 'Config env not found'

    def __init__(self, name: str, env: str):
        super().__init__(self.MESSAGE)
        self.name = name
        self.env = env

    def __str__(self) -> str:
        return f'Env "{self.env}" of config "{self.name}" was not found'

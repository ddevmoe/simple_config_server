from .models import Config, EnvConfig


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


class ConfigProblemsError(SimpleConfigServerErrorBase):
    MESSAGE = 'Config contains problems'

    def __init__(self, config: Config):
        super().__init__(self.MESSAGE)
        self.config = config

    def __str__(self) -> str:
        pretty_problems = '\n'.join(str(problem) for problem in self.config.problems)
        return f'{self.config.name} is invalid since it has {len(self.config.problems):,} problems:\n{pretty_problems}'


class EnvConfigProblemsError(SimpleConfigServerErrorBase):
    MESSAGE = 'Config env contains problems'

    def __init__(self, env_config: EnvConfig):
        super().__init__(self.MESSAGE)
        self.env_config = env_config

    def __str__(self) -> str:
        pretty_problems = '\n'.join(str(problem) for problem in self.env_config.problems)
        return f'{self.env_config.name}[{self.env_config.env}] is invalid since it has {len(self.env_config.problems):,} problems:\n{pretty_problems}'

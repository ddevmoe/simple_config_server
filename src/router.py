from typing import Annotated

from fastapi import APIRouter, FastAPI, Request, responses, status, Path

from src.common import errors
from src.bootstraper import bootstrap
from src.store import ConfigStore


store: ConfigStore = None  # type: ignore
router = APIRouter()


#region Custom Error Handling


def register_error_handlers(app: FastAPI):
    @app.exception_handler(errors.ConfigNotFoundError)
    def handle_config_not_found_error(_request: Request, error: errors.ConfigNotFoundError):
        return responses.JSONResponse(
            {
                'name': error.name,
                'message': error.message,
                'detailed_message': str(error),
                'status_code': status.HTTP_404_NOT_FOUND,
            },
            status_code=status.HTTP_404_NOT_FOUND
        )
    


    @app.exception_handler(errors.EnvNotFoundError)
    def handle_config_env_not_found_error(_request: Request, error: errors.EnvNotFoundError):
        return responses.JSONResponse(
            {
                'message': error.message,
                'detailed_message': str(error),
                'status_code': status.HTTP_404_NOT_FOUND,
                'name': error.name,
                'env': error.env,
            },
            status_code=status.HTTP_404_NOT_FOUND
        )

    @app.exception_handler(errors.ConfigProblemsError)
    def handle_config_problems_error(_request: Request, error: errors.ConfigProblemsError):
        return responses.JSONResponse(
            {
                'message': error.message,
                'detailed_message': str(error),
                'status_code': status.HTTP_422_UNPROCESSABLE_ENTITY,
                'name': error.config.name,
                'problems': [str(problem) for problem in error.config.problems],
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(errors.EnvConfigProblemsError)
    def handle_env_config_problems_error(_request: Request, error: errors.EnvConfigProblemsError):
        return responses.JSONResponse(
            {
                'message': error.message,
                'detailed_message': str(error),
                'status_code': status.HTTP_422_UNPROCESSABLE_ENTITY,
                'name': error.env_config.name,
                'env': error.env_config.env,
                'problems': [str(problem) for problem in error.env_config.problems],
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

#endregion


@router.on_event('startup')
async def initialize():
    global store
    store = bootstrap()
    await store.reload_all()


@router.get('/available_configs')
def get_available_configs():
    available_config_names = store.get_available_configs()
    return available_config_names


@router.get('/config/{name}/{env}')
def get_config(
    name: Annotated[str, Path(..., pattern='^[a-zA-Z_-]+$')],
    env: Annotated[str, Path(..., pattern='^[a-zA-Z_-]+$')],
) -> responses.JSONResponse:
    config = store.get_config(name)

    if not config:
        raise errors.ConfigNotFoundError(name)

    if config.has_problems:
        raise errors.ConfigProblemsError(config)

    env_config = config.get_env(env)
    if not env_config:
        raise errors.EnvNotFoundError(name, env)

    if env_config.has_problems:
        raise errors.EnvConfigProblemsError(env_config)

    return responses.JSONResponse(env_config.content)


@router.put('/reload/{name}', description='Reload specific configuration by name')
async def reload_config(name: Annotated[str, Path(..., pattern='^[a-zA-Z_-]+$')]):
    await store.reload(name)
    return responses.JSONResponse(
        {
            'message': 'Loaded successcully',
            'status_code': status.HTTP_201_CREATED,
        },
        status_code=status.HTTP_201_CREATED,
    )


@router.put('/reload_all', description='Reload all configurations')
async def reload_all_configs() -> responses.JSONResponse:
    await store.reload_all()
    return responses.JSONResponse(
        {
            'message': 'Reloaded all configurations successfully',
            'status_code': status.HTTP_201_CREATED,
        },
        status_code=status.HTTP_201_CREATED,
    )

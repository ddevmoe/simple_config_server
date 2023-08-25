from typing import Annotated

from fastapi import APIRouter, responses, status, Path

from src.bootstraper import bootstrap
from src.store import ConfigStore


store: ConfigStore = None


router = APIRouter()


@router.on_event('startup')
async def initialize():
    global store
    store = bootstrap()
    await store.reload_all()


@router.get('/config/{name}/{env}')
async def get_config(
    name: str = Annotated[str, Path(..., pattern='^[a-zA-Z_-]+$')],
    env: str = Annotated[str, Path(..., pattern='^[a-zA-Z_-]+$')],
) -> dict:
    config = await store.get_config(name, env)
    return responses.JSONResponse(config)


@router.put('/reload/{name}', description='Reload specific configuration by name')
async def reload_config(
    name: Annotated[str, Path(..., pattern='^[a-zA-Z_-]+$')],
) -> dict:
    await store.reload(name)
    return responses.JSONResponse(
        {
            'message': 'Loaded successcully',
            'status_code': status.HTTP_201_CREATED,
        },
        status_code=status.HTTP_201_CREATED,
    )


@router.put('/reload_all', description='Reload all configurations')
async def reload_all_configs() -> dict:
    await store.reload_all()
    return responses.JSONResponse(
        {
            'message': 'Reloaded all configurations successfully',
            'status_code': status.HTTP_201_CREATED,
        },
        status_code=status.HTTP_201_CREATED,
    )

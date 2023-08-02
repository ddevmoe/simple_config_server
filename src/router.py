from fastapi import APIRouter, responses, status

from src.bootstraper import bootstrap
from src.store import ConfigStore


store: ConfigStore = None


router = APIRouter()


@router.on_event('startup')
async def initialize():
    global store
    store = bootstrap()
    await store.refresh()


@router.get('/config/{name}/{env}')
async def get_config(name: str, env: str):
    config = await store.get_config(name, env)
    return responses.JSONResponse(config)


@router.post('/reload')
async def reload_config(name: str):
    await store.reload(name)
    return responses.JSONResponse(
        {
            'message': 'Loaded successcully',
            'status_code': status.HTTP_201_CREATED,
        },
        status_code=status.HTTP_201_CREATED
    )


@router.post('/refresh')
async def refresh_config_store():
    await store.refresh()
    return responses.JSONResponse(
        {
            'message': 'Reloaded all files successfully',
            'status_code': status.HTTP_201_CREATED,
        },
        status_code=status.HTTP_201_CREATED,
    )

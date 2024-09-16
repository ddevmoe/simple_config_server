import time

import uvicorn
from fastapi import FastAPI, responses, status

from src import __VERSION__
from src.router import router, register_error_handlers
from src.common import config


START_TIME = time.time()


app = FastAPI(title='Simple Config Server', version=__VERSION__)


@app.get('/', include_in_schema=False)
def root_redirect():
    return responses.RedirectResponse('/docs')


@app.get('/healthcheck')
def healthcheck():
    return responses.JSONResponse(
        {
            'message': 'Up and running!', 'uptime_seconds': int(time.time() - START_TIME),
            'status_code': status.HTTP_200_OK,
        },
    )


app.include_router(router)
register_error_handlers(app)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=config.HTTP_PORT)

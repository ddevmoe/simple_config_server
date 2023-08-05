import uvicorn
from fastapi import FastAPI, responses, Request, status

from src import config, merger, __VERSION__
from src.router import router
from src.common import errors


app = FastAPI(title='Simple Config Server', version=__VERSION__)
app.include_router(router)


#region Custom Error Handling

@app.exception_handler(errors.ConfigNotFoundError)
async def handle_config_not_found_error(_request: Request, error: errors.ConfigNotFoundError):
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
async def handle_config_not_found_error(_request: Request, error: errors.EnvNotFoundError):
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


@app.exception_handler(merger.MergeUnequalTypesError)
async def handle_merger_unequal_type_error(_request: Request, error: merger.MergeUnequalTypesError):
    return responses.JSONResponse(
        {
            'message': error.message,
            'detailed_message': str(error),
            'status_code': status.HTTP_422_UNPROCESSABLE_ENTITY,
            'base_type': error.base_type,
            'extra_type': error.extra_type,
            'key': error.key,
            'path': error.pretty_path,
        },
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )

#endregion


@app.get('/', include_in_schema=False)
async def root_redirect():
    return responses.RedirectResponse('/docs')



if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=config.HTTP_PORT)

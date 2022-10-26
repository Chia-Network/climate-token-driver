import traceback

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api import v1
from app.config import ExecutionMode, settings
from app.logger import log_config
from app.utils import wait_until_dir_exists

app = FastAPI(
    title="Ivern Chia Service Suite",
)

if settings.MODE == ExecutionMode.DEV:

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, e: Exception):
        content: str = "".join(traceback.format_exception(e))
        return Response(content, status_code=500)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1.router)

if __name__ == "__main__":
    wait_until_dir_exists(settings.CHIA_ROOT)

    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level="info",
        log_config=log_config,
    )

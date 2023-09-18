import sys
import time
import traceback

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api import v1
from app.config import ExecutionMode, settings
from app.logger import log_config, logger
from app.utils import wait_until_dir_exists

app = FastAPI(
    title="Ivern Chia Service Suite",
)

if settings.MODE == ExecutionMode.DEV:

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, e: Exception):
        content: str = "".join(traceback.format_exception(e))
        return Response(content, status_code=500)


app.include_router(v1.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    logger.info(f"Using settings {settings.dict()}")
    wait_until_dir_exists(settings.CHIA_ROOT)

    if (
        settings.MODE in [ExecutionMode.EXPLORER, ExecutionMode.DEV]
        or settings.SERVER_HOST in ["127.0.0.1", "localhost"]
    ):
        while settings is None:
            print("Waiting for settings to load...")
            time.sleep(1)
        uvicorn.run(
            app,
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            log_level="info",
            log_config=log_config,
        )
    else:
        print(
            f'Climate Token Driver can only run on localhost in {settings.MODE.name} mode. Please update'
            f' SERVER_HOST in {settings.CHIA_ROOT / settings.CONFIG_PATH}'
        )
        sys.exit(1)

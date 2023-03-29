from pathlib import Path
print(f"{__file__=} - {__name__=}", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
import traceback

print(f"{__file__=} ==== 1", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
import uvicorn
print(f"{__file__=} ==== 2", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
print(f"{__file__=} ==== 3", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
from starlette.requests import Request
from starlette.responses import Response

print(f"{__file__=} ==== 4", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
import app.api.v1.core as app_core
from app.config import ExecutionMode, settings
from app.logger import log_config, logger
from app.utils import wait_until_dir_exists

print(f"{__file__=} ==== A", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
app = FastAPI(
    title="Ivern Chia Service Suite",
)

print(f"{__file__=} ==== B", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
if settings.MODE == ExecutionMode.DEV:

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, e: Exception):
        content: str = "".join(traceback.format_exception(e))
        return Response(content, status_code=500)


print(f"{__file__=} ==== C", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
app.include_router(app_core.router)

print(f"{__file__=} ==== D", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"{__file__=} ==== E", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
if __name__ == "__main__":
    print(f"{__file__=} ==== F", file=Path("/home/altendky/repos/climate-wallet/machete/log").open(mode="a"))
    logger.info(f"Using settings {settings.dict()}")
    wait_until_dir_exists(settings.CHIA_ROOT)

    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level="info",
        log_config=log_config,
    )

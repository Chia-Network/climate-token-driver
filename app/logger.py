import logging

import uvicorn

from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    filename=settings.LOG_PATH,
    format="%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    filemode="w",
)

logger = logging.getLogger("uvicorn.error")
log_config = uvicorn.config.LOGGING_CONFIG

log_config["formatters"]["default"].update(
    {
        "fmt": "%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        "datefmt": "%Y-%m-%d:%H:%M:%S",
    }
)

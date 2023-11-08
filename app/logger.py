from __future__ import annotations

import logging
from typing import Any, Dict

import colorlog
import uvicorn
from concurrent_log_handler import ConcurrentRotatingFileHandler

from app.config import settings


def get_file_log_handler(formatter: logging.Formatter) -> ConcurrentRotatingFileHandler:
    log_path = settings.LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = ConcurrentRotatingFileHandler(log_path, "a", maxBytes=50 * 1024 * 1024, backupCount=7, use_gzip=False)
    handler.setFormatter(formatter)
    return handler


def initialize_logging() -> Dict[str, Any]:
    log_date_format = "%Y-%m-%dT%H:%M:%S"
    file_log_formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d %(name)s: %(levelname)-8s %(message)s",
        datefmt=log_date_format,
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if settings.LOG_PATH.name == "stdout":
        stdout_handler = colorlog.StreamHandler()
        stdout_handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(asctime)s.%(msecs)03d %(name)s: %(log_color)s%(levelname)-8s%(reset)s %(message)s",
                datefmt=log_date_format,
                reset=True,
            )
        )
        root_logger.addHandler(stdout_handler)
    else:
        root_logger
        root_logger.addHandler(get_file_log_handler(file_log_formatter))

    logger = logging.getLogger("ClimateToken")
    logger.info("Logging initialized")

    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"].update(
        {
            "fmt": "%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d:%H:%M:%S",
        }
    )
    return log_config

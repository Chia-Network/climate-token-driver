import logging

import uvicorn

logger = logging.getLogger("uvicorn.error")
log_config = uvicorn.config.LOGGING_CONFIG

log_config["formatters"]["default"].update(
    {
        "fmt": "%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        "datefmt": "%Y-%m-%d:%H:%M:%S",
    }
)

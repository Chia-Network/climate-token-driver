from __future__ import annotations

import logging
import uvicorn
import toml
from app.config import settings

# Parse pyproject.toml to get the version
with open('pyproject.toml', 'r') as toml_file:
    pyproject = toml.load(toml_file)
version = pyproject['tool']['poetry']['version']

# Define the log format with version
log_format = f"%(asctime)s,%(msecs)d {version} %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"

logging.basicConfig(
    level=logging.INFO,
    filename=settings.LOG_PATH,
    format=log_format,
    filemode="w",
)

logger = logging.getLogger("uvicorn.error")
log_config = uvicorn.config.LOGGING_CONFIG

log_config["formatters"]["default"].update(
    {
        "fmt": log_format,
        "datefmt": "%Y-%m-%d:%H:%M:%S",
    }
)

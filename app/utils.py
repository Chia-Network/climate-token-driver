from __future__ import annotations

import os
import time
from typing import Any, Callable, Concatenate, Coroutine, List, ParamSpec, TypeVar

from fastapi import status

from app.config import ExecutionMode, settings
from app.logger import logger

P = ParamSpec("P")
R = TypeVar("R")


def disallow(
    modes: List[ExecutionMode],
) -> Callable[[Callable[Concatenate[P], Coroutine[Any, Any, R]]], Callable[Concatenate[P], Coroutine[Any, Any, R]],]:
    def decorator(
        f: Callable[Concatenate[P], Coroutine[Any, Any, R]]
    ) -> Callable[Concatenate[P], Coroutine[Any, Any, R]]:
        if settings.MODE in modes:

            async def not_allowed(*args: P.args, **kwargs: P.kwargs) -> Any:
                return status.HTTP_405_METHOD_NOT_ALLOWED

            return not_allowed

        return f

    return decorator


def wait_until_dir_exists(path: str, interval: int = 1) -> None:
    while not os.path.exists(path):
        logger.info(f"Checking if {path} exists")
        if os.path.exists(path):
            return

        logger.warning(f"Path {path} does not exist, sleeping for {interval} seconds")
        time.sleep(interval)

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, Concatenate, Coroutine, ParamSpec, TypeVar

from fastapi import HTTPException

from app.config import ExecutionMode, settings

logger = logging.getLogger("ClimateToken")

P = ParamSpec("P")
R = TypeVar("R")


def disallow_route(
    modes: List[ExecutionMode],
) -> Callable[[Callable[Concatenate[P], Coroutine[Any, Any, R]]], Callable[Concatenate[P], Coroutine[Any, Any, R]],]:
    def decorator(
        f: Callable[Concatenate[P], Coroutine[Any, Any, R]]
    ) -> Callable[Concatenate[P], Coroutine[Any, Any, R]]:
        if settings.MODE in modes:
            # P.args & P.kwargs don't seem to work with fastapi decorators
            # see https://github.com/PrefectHQ/marvin/issues/625
            # putting any parameters here in this call results in fastapi always returning 422
            # if the request doesn't have the proper query parameters (literally "args" and "kwargs")
            # using () allows the 405 error to be returned by fastapi regardless of query parameters
            async def not_allowed() -> Any:
                raise HTTPException(status_code=405, detail="Method not allowed")

            return not_allowed  # type: ignore[return-value]

        return f

    return decorator


def disallow_startup(
    modes: list[ExecutionMode],
) -> Callable[
    [Callable[Concatenate[P], Coroutine[Any, Any, None]]],
    Callable[Concatenate[P], Coroutine[Any, Any, None]],
]:
    def decorator(
        f: Callable[Concatenate[P], Coroutine[Any, Any, None]]
    ) -> Callable[Concatenate[P], Coroutine[Any, Any, None]]:
        if settings.MODE in modes:

            async def not_allowed(*args: P.args, **kwargs: P.kwargs) -> None:
                return

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

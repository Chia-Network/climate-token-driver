from __future__ import annotations

import functools
import os
import time
from typing import Callable, List

from fastapi import status

from app.config import ExecutionMode, settings
from app.logger import logger

# from typing import Any, Callable, Concatenate, Coroutine, List, ParamSpec, TypeVar


# P = ParamSpec("P")
# R = TypeVar("R")


# def disallow(
#     modes: List[ExecutionMode],
# ) -> Callable[[Callable[Concatenate[P], Coroutine[Any, Any, R]]], Callable[Concatenate[P], Coroutine[Any, Any, R]],]:
#     def decorator(
#         f: Callable[Concatenate[P], Coroutine[Any, Any, R]]
#     ) -> Callable[Concatenate[P], Coroutine[Any, Any, R]]:
#         if settings.MODE in modes:

#             async def not_allowed(*args: P.args, **kwargs: P.kwargs) -> Any:
#                 return status.HTTP_405_METHOD_NOT_ALLOWED

#             return not_allowed

#         return f

#     return decorator


def disallow(modes: List[ExecutionMode]):
    def _disallow(f: Callable):
        if settings.MODE in modes:

            async def _f(*args, **kargs):
                return status.HTTP_405_METHOD_NOT_ALLOWED

        else:

            @functools.wraps(f)
            async def _f(*args, **kargs):
                return await f(*args, **kargs)

        return _f

    return _disallow


def wait_until_dir_exists(path: str, interval: int = 1) -> None:
    while not os.path.exists(path):
        logger.info(f"Checking if {path} exists")
        if os.path.exists(path):
            return

        logger.warning(f"Path {path} does not exist, sleeping for {interval} seconds")
        time.sleep(interval)

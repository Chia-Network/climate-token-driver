import functools
import inspect
import os
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Callable, List

from fastapi import status
from fastapi.concurrency import contextmanager_in_threadpool

from app.config import ExecutionMode, settings
from app.logger import logger


def as_async_contextmanager(func: Callable, *args, **kwargs):
    if inspect.isasyncgenfunction(func):
        return asynccontextmanager(func)(*args, **kwargs)

    elif inspect.isgeneratorfunction(func):
        return contextmanager_in_threadpool(contextmanager(func)(*args, **kwargs))


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

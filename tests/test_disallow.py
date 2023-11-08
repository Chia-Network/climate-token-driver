from __future__ import annotations

import math
from typing import Any, Dict
from urllib.parse import urlencode

import anyio
import pytest
from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.config import ExecutionMode, settings
from app.utils import disallow_route, disallow_startup


@pytest.mark.asyncio
async def test_disallow() -> None:
    settings.MODE = ExecutionMode.DEV

    @disallow_route([ExecutionMode.DEV])
    async def disallow_dev() -> int:
        return 5

    @disallow_route([ExecutionMode.REGISTRY])
    async def allow_dev() -> int:
        return 5

    with pytest.raises(HTTPException) as e:
        await disallow_dev()
    assert e.value.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    assert await allow_dev() == 5


def test_disallowed_route() -> None:
    settings.MODE = ExecutionMode.DEV
    app = FastAPI()
    router = APIRouter()

    @router.get("/disallow")
    @disallow_route([ExecutionMode.DEV])
    async def get_disallow() -> Dict[str, str]:
        return {
            "success": "true",
        }

    @router.get("/disallow2/")
    @disallow_route([ExecutionMode.DEV])
    async def get_disallow2(id: int, timeout: int, why: str) -> Dict[str, Any]:
        return {
            "id": id,
            "timeout": timeout,
            "why": why,
            "success": "true",
        }

    @router.get("/allow")
    @disallow_route([ExecutionMode.EXPLORER])
    async def get_allow() -> Dict[str, str]:
        return {
            "success": "true",
        }

    @router.get("/allow2")
    @disallow_route([ExecutionMode.EXPLORER])
    async def get_allow2(id: int, timeout: int, why: str) -> Dict[str, Any]:
        return {
            "id": id,
            "timeout": timeout,
            "why": why,
            "success": "true",
        }

    app.include_router(router)
    test_client = TestClient(app)

    with anyio.from_thread.start_blocking_portal() as portal:
        test_client.portal = portal  # workaround anyio 4.0.0 incompat with TestClient
        response = test_client.get("/disallow")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        test_request = {"id": 3, "timeout": 5, "why": "because"}
        params = urlencode(test_request)
        response = test_client.get("/disallow2", params=params)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = test_client.get("/allow")
        assert response.status_code == status.HTTP_200_OK

        response = test_client.get("/allow2", params=params)
        assert response.status_code == status.HTTP_200_OK
        assert response.text == '{"id":3,"timeout":5,"why":"because","success":"true"}'


def test_disallowed_startup() -> None:
    settings.MODE = ExecutionMode.DEV
    app = FastAPI()
    router = APIRouter()

    @router.on_event("startup")
    @disallow_startup([ExecutionMode.DEV])
    async def my_startup() -> None:
        raise ValueError("Should not get here")

    app.include_router(router)

    test_client = TestClient(app)
    with anyio.from_thread.start_blocking_portal() as portal:
        test_client.portal = portal  # workaround anyio 4.0.0 incompat with TestClient
        test_client.stream_send = anyio.streams.stapled.StapledObjectStream(
            *anyio.create_memory_object_stream(math.inf)
        )
        test_client.stream_receive = anyio.streams.stapled.StapledObjectStream(
            *anyio.create_memory_object_stream(math.inf)
        )
        test_client.task = test_client.portal.start_task_soon(test_client.lifespan)
        test_client.portal.call(test_client.wait_startup)
        test_client.portal.call(test_client.wait_shutdown)


def test_allowed_startup() -> None:
    settings.MODE = ExecutionMode.DEV
    app = FastAPI()
    router = APIRouter()

    @router.on_event("startup")
    @disallow_startup([ExecutionMode.EXPLORER])
    async def my_startup() -> None:
        raise ValueError("Should not get here")

    app.include_router(router)
    test_client = TestClient(app)

    with pytest.raises(ValueError, match="Should not get here"):
        with anyio.from_thread.start_blocking_portal() as portal:
            test_client.portal = portal  # workaround anyio 4.0.0 incompat with TestClient
            test_client.stream_send = anyio.streams.stapled.StapledObjectStream(
                *anyio.create_memory_object_stream(math.inf)
            )
            test_client.stream_receive = anyio.streams.stapled.StapledObjectStream(
                *anyio.create_memory_object_stream(math.inf)
            )
            test_client.task = test_client.portal.start_task_soon(test_client.lifespan)
            test_client.portal.call(test_client.wait_startup)
            test_client.portal.call(test_client.wait_shutdown)

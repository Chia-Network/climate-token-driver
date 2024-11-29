from __future__ import annotations

import pytest
from fastapi import status

from app.config import ExecutionMode, settings
from app.utils import disallow


@pytest.mark.anyio
async def test_disallow() -> None:
    settings.MODE = ExecutionMode.DEV

    @disallow([ExecutionMode.DEV])  # type: ignore[misc]
    async def disallow_dev() -> int:
        return 5

    @disallow([ExecutionMode.REGISTRY])  # type: ignore[misc]
    async def allow_dev() -> int:
        return 5

    assert await disallow_dev() == status.HTTP_405_METHOD_NOT_ALLOWED
    assert await allow_dev() == 5

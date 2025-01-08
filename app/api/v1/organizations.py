# noqa: I002
# ignore the required import["from __future__ import annotations"]
# This import breaks everything - seems something to do with pydantic

from typing import Any

from fastapi import APIRouter

from app import crud
from app.config import ExecutionMode, settings
from app.utils import disallow

router = APIRouter()


# pass through resource to expose organization data from cadt
@router.get("/", response_model=Any)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])  # type: ignore[misc]
async def get_organizations() -> Any:
    all_organizations = crud.ClimateWareHouseCrud(
        url=settings.CADT_API_SERVER_HOST,
        api_key=settings.CADT_API_KEY,
    ).get_climate_organizations()
    return all_organizations

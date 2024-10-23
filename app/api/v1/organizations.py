from typing import Any

from fastapi import APIRouter
from fastapi.params import Depends

from app import crud
from app.config import ExecutionMode, settings
from app.utils import disallow

router = APIRouter()

# pass through resource to expose organization data from cadt
@router.get("/", response_model=Any)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def get_organizations() -> Any:
    all_organizations = crud.ClimateWareHouseCrud(
        url=settings.CADT_API_SERVER_HOST,
        api_key=settings.CADT_API_KEY,
    ).get_climate_organizations()
    return all_organizations
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import dependencies as deps
from app.config import ExecutionMode, settings
from app.core.types import GatewayMode
from app.errors import ErrorCode
from app.logger import logger
from app.utils import disallow

router = APIRouter()


@router.get("/", response_model=schemas.ActivitiesResponse)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def get_activity(
    search: Optional[str] = None,
    search_by: Optional[schemas.ActivitySearchBy] = None,
    mode: Optional[GatewayMode] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(deps.get_db_session),
):
    """Get activity.

    This endpoint is to be called by the explorer.
    """

    db_crud = crud.DBCrud(db=db)

    activity_filters = {"or": [], "and": []}
    cw_filters = {}
    match search_by:
        case schemas.ActivitySearchBy.ONCHAIN_METADATA:
            if search is not None:
                activity_filters["or"].extend(
                    [
                        models.Activity.beneficiary_name.like(f"%{search}%"),
                        models.Activity.beneficiary_address.like(f"%{search}%"),
                        models.Activity.beneficiary_puzzle_hash.like(f"%{search}%"),
                    ]
                )
        case schemas.ActivitySearchBy.CLIMATE_WAREHOUSE:
            if search is not None:
                cw_filters["search"] = search
        case None:
            pass
        case _:
            raise ErrorCode().bad_request_error(message="search_by is invalid")

    climate_data = crud.ClimateWareHouseCrud(
        url=settings.CADT_API_SERVER_HOST,
        api_key=settings.CADT_API_KEY,
    ).combine_climate_units_and_metadata(search=cw_filters)
    if len(climate_data) == 0:
        logger.warning(f"No data to get from climate warehouse. search:{cw_filters}")
        return schemas.ActivitiesResponse()

    units = {unit["marketplaceIdentifier"]: unit for unit in climate_data}
    if len(units) != 0:
        activity_filters["and"].append(models.Activity.asset_id.in_(units.keys()))

    if mode is not None:
        activity_filters["and"].append(models.Activity.mode.ilike(mode.name))

    activities: List[models.Activity]
    total: int

    (activities, total) = db_crud.select_activity_with_pagination(
        model=models.Activity,
        filters=activity_filters,
        order_by=models.Activity.height,
        page=page,
        limit=limit,
    )
    if len(activities) == 0:
        logger.warning(
            f"No data to get from activities. filters:{activity_filters} page:{page} limit:{limit}"
        )
        return schemas.ActivitiesResponse()

    activities_with_cw: List[schemas.ActivityWithCW] = []
    for activity in activities:
        unit: Dict = units.get(activity.asset_id).copy()
        token = unit.pop("token", None)
        org = unit.pop("organization", None)
        project = unit.pop("project", None)

        activity_with_cw = schemas.ActivityWithCW(
            token=token,
            cw_unit=unit,
            cw_org=org,
            cw_project=project,
            metadata=activity.metadata_,
            **jsonable_encoder(activity),
        )
        activities_with_cw.append(activity_with_cw)

    return schemas.ActivitiesResponse(activities=activities_with_cw, total=total)

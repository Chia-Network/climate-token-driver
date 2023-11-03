from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
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
    minHeight: Optional[int] = None,
    mode: Optional[GatewayMode] = None,
    page: int = 1,
    limit: int = 10,
    sort: str = "desc",
    db: Session = Depends(deps.get_db_session),
) -> schemas.ActivitiesResponse:
    """Get activity.

    This endpoint is to be called by the explorer.
    """

    db_crud = crud.DBCrud(db=db)

    activity_filters: Dict[str, Any] = {"or": [], "and": []}
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

    if minHeight is not None:
        activity_filters["and"].append(models.Activity.height >= minHeight)

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

    order_by_clause = []
    if sort.lower() == "desc":
        order_by_clause.append(models.Activity.height.desc())
        order_by_clause.append(models.Activity.coin_id.desc())
    else:
        order_by_clause.append(models.Activity.height.asc())
        order_by_clause.append(models.Activity.coin_id.asc())

    (activities, total) = db_crud.select_activity_with_pagination(
        model=models.Activity,
        filters=activity_filters,
        order_by=order_by_clause,
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
        unit = units.get(activity.asset_id)
        if unit is None:
            continue
        unit = unit.copy()
        token = unit.pop("token", None)
        org = unit.pop("organization", None)
        project = unit.pop("project", None)

        try:
            token_on_chain = schemas.TokenOnChain.parse_obj(token)
            print("instantiated TokenOnChain with parse_obj", flush=True)
        except ValidationError:
            print("failed to instantiate TokenOnChain with parse_obj", flush=True)
            raise

        activity_with_cw = schemas.ActivityWithCW(
            token=token_on_chain,
            cw_unit=unit,
            cw_org=org,
            cw_project=project,
            metadata=activity.metadata_,
            **jsonable_encoder(activity),
        )
        activities_with_cw.append(activity_with_cw)

    return schemas.ActivitiesResponse(activities=activities_with_cw, total=total)

import logging
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
from app.utils import disallow_route

router = APIRouter()
logger = logging.getLogger("ClimateToken")


@router.get("/", response_model=schemas.ActivitiesResponse)
@disallow_route([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def get_activity(
    search: Optional[str] = None,
    search_by: Optional[schemas.ActivitySearchBy] = None,
    min_height: Optional[int] = None,
    mode: Optional[GatewayMode] = None,
    page: int = 1,
    limit: int = 10,
    org_uid: Optional[str] = None,
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

    if min_height is not None:
        activity_filters["and"].append(models.Activity.height >= min_height)

    if org_uid is not None:
        cw_filters["orgUid"] = org_uid

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
        logger.warning(f"No data to get from activities. filters:{activity_filters} page:{page} limit:{limit}")
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


@router.get("/activity-record", response_model=schemas.ActivityRecordResponse)
@disallow_route([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def get_activity_by_cw_unit_id(
    cw_unit_id: str,
    coin_id: str,
    action_mode: str,
    db: Session = Depends(deps.get_db_session),
) -> schemas.ActivityRecordResponse:
    """Get a single activity based on the unit's unitWarehouseId.

    This endpoint is to be called by the explorer.
    """

    db_crud = crud.DBCrud(db=db)

    # fetch unit and related data from CADT
    cw_filters: Dict[str, str] = {"warehouseUnitId": cw_unit_id}

    climate_data = crud.ClimateWareHouseCrud(
        url=settings.CADT_API_SERVER_HOST,
        api_key=settings.CADT_API_KEY,
    ).combine_climate_units_and_metadata(search=cw_filters)
    if len(climate_data) == 0:
        logger.warning(f"Failed to retrieve unit from climate warehouse. search:{cw_filters}")
        return schemas.ActivityRecordResponse()

    unit_with_metadata = climate_data[0]

    # set filters to fetch activity data related to specified unit
    activity_filters: Dict[str, Any] = {"or": [], "and": []}
    if unit_with_metadata["marketplaceIdentifier"]:
        activity_filters["and"].append(models.Activity.asset_id == unit_with_metadata["marketplaceIdentifier"])
    else:
        logger.warning("retrieved unit does not contain marketplace identifier. unable to get activity record")
        return schemas.ActivityRecordResponse()

    activity_filters["and"].append(models.Activity.mode == action_mode)
    activity_filters["and"].append(models.Activity.coin_id == coin_id)

    activities = [models.Activity]
    total: int

    # fetch activities with filters, 'total' var ignored
    (activities, total) = db_crud.select_activity_with_pagination(
        model=models.Activity,
        filters=activity_filters,
        order_by=[models.Activity.height.asc()],
    )
    if len(activities) == 0:
        logger.warning(f"No data to get from activities. filters:{activity_filters}")
        return schemas.ActivityRecordResponse()

    try:
        activity = next(
            (activity for activity in activities if activity.coin_id == coin_id and activity.mode == action_mode), None
        )
        if activity is None:
            return schemas.ActivityRecordResponse()
    except Exception:
        logger.warning("an exception occurred while processing activity record")
        return schemas.ActivityRecordResponse()

    unit_with_metadata = unit_with_metadata.copy()
    token = unit_with_metadata.pop("token", None)
    org = unit_with_metadata.pop("organization", None)
    project = unit_with_metadata.pop("project", None)

    try:
        token_on_chain = schemas.TokenOnChain.parse_obj(token)
        print("instantiated TokenOnChain with parse_obj", flush=True)
    except ValidationError:
        print("failed to instantiate TokenOnChain with parse_obj", flush=True)
        raise

    activity_with_cw = schemas.ActivityWithCW(
        token=token_on_chain,
        cw_unit=unit_with_metadata,
        cw_org=org,
        cw_project=project,
        metadata=activity.metadata_,
        **jsonable_encoder(activity),
    )

    return schemas.ActivityRecordResponse(activity=activity_with_cw)

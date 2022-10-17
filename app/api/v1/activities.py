from typing import Optional, List, Dict, Any

from fastapi import APIRouter

from app import crud, schemas, models
from app.api import dependencies as deps
from app.config import ExecutionMode
from app.config import Settings
from app.core.types import GatewayMode
from app.errors import ErrorCode
from app.utils import as_async_contextmanager
from app.utils import disallow

router = APIRouter()


@router.get("/", response_model=schemas.ActivitiesResponse)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def get_activity(
        search: str,
        search_by: str,
        mode: GatewayMode = 2,
        page: int = 1,
        limit: int = 1,
):
    """Get activity.

    This endpoint is to be called by the explorer.
    """
    async with (
        as_async_contextmanager(deps.get_db_session) as db,
    ):
        db_crud = crud.DBCrud(db=db)

        if mode not in GatewayMode:
            raise ErrorCode().bad_request_error(message="mode is invalid")

        activity_filters = {"or": [], "and": []}
        cw_filters = []
        match search_by:
            case "activities":
                if search is not None:
                    activity_filters["or"].append(models.Activity.beneficiary_name.like("%" + search + "%"))
                    activity_filters["or"].append(models.Activity.beneficiary_puzzle_hash.like("%" + search + "%"))
            case "climatewarehouse":
                if search is not None:
                    cw_filters.append(search)
            case _:
                raise ErrorCode().bad_request_error(message="search_by is invalid")

        climate_data = crud.ClimateWareHouseCrud(url=Settings().CLIMATE_API_URL).combine_climate_units_and_metadata(
            search=cw_filters)
        if len(climate_data) == 0:
            return schemas.ActivitiesResponse(
                list=[],
                total=0
            )

        activities: List[models.activity] = db_crud.select_activity_with_pagination(
            model=models.Activity,
            filters=activity_filters,
            order_by=models.Activity.height,
            page=page,
            limit=limit,
        )
        if len(activities) == 0:
            return schemas.ActivitiesResponse(
                list=[],
                total=0
            )

        detail_list: List[schemas.ActivitiesDetail] = []
        for unit in climate_data:
            for activity in activities:
                if unit["orgUid"] == activity[0].org_uid:
                    detail = schemas.ActivitiesDetail(
                        amount=activity[0].amount,
                        height=activity[0].height,
                        timestamp=activity[0].timestamp,
                        mode=activity[0].mode,
                        climate_warehouse=unit
                    )
                    detail_list.append(detail)

        return schemas.ActivitiesResponse(
            list=detail_list,
            total=activities[0][1]
        )

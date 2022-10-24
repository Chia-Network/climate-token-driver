from typing import List, Optional

from fastapi import APIRouter

from app import crud, models, schemas
from app.api import dependencies as deps
from app.config import ExecutionMode, Settings
from app.core.types import GatewayMode
from app.errors import ErrorCode
from app.utils import as_async_contextmanager, disallow

router = APIRouter()
settings = Settings()


@router.get("/", response_model=schemas.ActivitiesResponse)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def get_activity(
    search: Optional[str] = None,
    search_by: Optional[schemas.SearchBy] = None,
    mode: Optional[GatewayMode] = None,
    page: int = 1,
    limit: int = 1,
):
    """Get activity.

    This endpoint is to be called by the explorer.
    """
    async with (as_async_contextmanager(deps.get_db_session) as db,):
        db_crud = crud.DBCrud(db=db)

        activity_filters = {"or": [], "and": []}
        cw_filters = {}
        if search_by is not None:
            match search_by:
                case "activities":
                    if search is not None:
                        activity_filters["or"].append(
                            models.Activity.beneficiary_name.like("%" + search + "%")
                        )
                        activity_filters["or"].append(
                            models.Activity.beneficiary_puzzle_hash.like("%" + search + "%")
                        )
                case "climatewarehouse":
                    if search is not None:
                        cw_filters["search"] = search
                case _:
                    raise ErrorCode().bad_request_error(message="search_by is invalid")

        climate_data = crud.ClimateWareHouseCrud(
            url=settings.CLIMATE_API_URL
        ).combine_climate_units_and_metadata(search=cw_filters)
        if len(climate_data) == 0:
            return schemas.ActivitiesResponse()

        if mode is not None:
            activity_filters["and"].append(models.Activity.mode.ilike(mode.name))

        activities: List[models.activity] = db_crud.select_activity_with_pagination(
            model=models.Activity,
            filters=activity_filters,
            order_by=models.Activity.height,
            page=page,
            limit=limit,
        )
        if len(activities) == 0:
            return schemas.ActivitiesResponse()

        total = activities[0][1]
        detail_list: List[schemas.ActivitiesDetail] = []
        for unit in climate_data:
            i = 0
            for activity in activities[0]:
                if i == len(activities[0]) - 1:
                    break

                if unit["orgUid"] == activity.org_uid:
                    detail = schemas.ActivitiesDetail(
                        amount=activity.amount,
                        height=activity.height,
                        timestamp=activity.timestamp,
                        mode=GatewayMode[activity.mode],
                        climate_warehouse=unit,
                    )
                    detail_list.append(detail)
                i += 1

        return schemas.ActivitiesResponse(list=detail_list, total=total)

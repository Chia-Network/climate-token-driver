from typing import Optional, List

from fastapi import APIRouter

from app import crud, schemas, models
from app.config import ExecutionMode
from app.utils import disallow
from app.utils import as_async_contextmanager
from app.api import dependencies as deps
from app.config import Settings
from app.errors import ErrorCode
from app.core.types import GatewayMode

router = APIRouter()


@router.get("/", response_model=List[schemas.ActivitiesResponse])
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def get_activity(
        asset_id: str,
        search: str,
        search_by: str,
        mode: GatewayMode = 2,
        page: int = 1,
        limit: int = 1,
        start_height: Optional[int] = None,
        end_height: Optional[int] = None,
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

        activity_filters = []
        cw_filters = []
        match search_by:
            case "activities":
                if search is not None:
                    activity_filters.append(models.Activity.beneficiary_name.like("%"+search+"%"))
                    activity_filters.append(models.Activity.beneficiary_puzzle_hash.like("%" + search + "%"))
            case "climatewarehouse":
                if search is not None:
                    cw_filters.append(search)
            case _:
                raise ErrorCode().bad_request_error(message="search_by is invalid")

        climate_data = crud.ClimateWareHouseCrud(url=Settings().CLIMATE_API_URL).combine_climate_units_and_metadata(search=cw_filters)
        if len(climate_data) == 0:
            return []

        activities: List[models.activity] = db_crud.select_activity_with_pagination(
            model=models.Activity,
            filters=activity_filters,
            order_by=models.Activity.created_at,
            page=page,
            limit=limit,
        )
        if len(activities) == 0:
            return

        ret: List[schemas.ActivitiesResponse] = []
        for unit in climate_data:
            for activity in activities:
                if unit["orgUid"] == activity.org_uid:
                    activity_res = schemas.ActivitiesResponse(
                        amount=activity.amount,
                        height=activity.height,
                        timestamp=activity.timestamp,
                        mode=activity.mode,
                        climate_warehouse=unit
                    )
                ret.append(activity_res)

        return ret

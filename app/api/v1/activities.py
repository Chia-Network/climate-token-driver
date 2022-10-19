from typing import Optional

from fastapi import APIRouter

from app import schemas
from app.config import ExecutionMode
from app.utils import disallow

router = APIRouter()


@router.get("/", response_model=schemas.Activities)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def get_activity(
    asset_id: str,
    mode: str,
    start_height: Optional[int] = None,
    end_height: Optional[int] = None,
):
    """Get activity.

    This endpoint is to be called by the explorer.
    """

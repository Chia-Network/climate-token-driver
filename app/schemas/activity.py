from datetime import datetime
from typing import Dict, List, Optional

from app.core.types import GatewayMode
from app.schemas.core import BaseModel


class Activity(BaseModel):
    org_uid: str
    warehouse_project_id: str
    vintage_year: int
    sequence_num: int
    asset_id: bytes

    coin_id: bytes
    height: int
    amount: int
    mode: str
    metadata: Dict[str, str]
    timestamp: int


class ActivityInDB(Activity):
    id: int
    created_at: datetime
    updated_at: datetime


class Activities(BaseModel):
    asset_id: str
    mode: GatewayMode
    start_height: Optional[int]
    end_height: Optional[int]
    activities: List[Activity]

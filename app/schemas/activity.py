from datetime import datetime
from typing import Dict, List, Optional, Any

from app.core.types import GatewayMode
from app.schemas.core import BaseModel


class Activity(BaseModel):
    org_uid: str
    sid: str
    warehouse_project_id: str
    vintage_year: int
    sequence_num: int
    asset_id: bytes
    beneficiary_name: str
    beneficiary_puzzle_hash: str

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


class ActivitiesResponse(BaseModel):
    amount: int
    height: int
    timestamp: int
    mode: str
    climate_warehouse: Any


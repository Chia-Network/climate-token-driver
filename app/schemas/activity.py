from datetime import datetime

import enum
from typing import Any, Dict, List

from pydantic import Field

from app.core.types import GatewayMode
from app.schemas.core import BaseModel


class ActivitySearchBy(enum.Enum):
    ACTIVITIES = "activities"
    CLIMATEWAREHOUSE = "climatewarehouse"


class Activity(BaseModel):
    org_uid: str
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


class ActivitiesDetail(BaseModel):
    amount: int
    height: int
    timestamp: int
    mode: GatewayMode
    climate_warehouse: Dict[str, Any]


class ActivitiesResponse(BaseModel):
    list: List[ActivitiesDetail] = Field(default_factory=list)
    total: int = 0

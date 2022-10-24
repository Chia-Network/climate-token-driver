import enum
from typing import Any, Dict, List, Optional

from pydantic import Field, validator

from app.core.types import GatewayMode
from app.schemas.core import BaseModel


class ActivitySearchBy(enum.Enum):
    ONCHAIN_METADATA = "onchain_metadata"
    CLIMATE_WAREHOUSE = "climate_warehouse"


class Activity(BaseModel):
    org_uid: str
    warehouse_project_id: str
    vintage_year: int
    sequence_num: int
    asset_id: bytes
    beneficiary_name: Optional[str]
    beneficiary_puzzle_hash: Optional[str]

    coin_id: bytes
    height: int
    amount: int
    mode: GatewayMode | str
    metadata_: Dict[str, str]
    timestamp: int

    @validator("mode")
    def convert_mode_str(cls, v):
        if isinstance(v, str):
            return GatewayMode[v]
        elif isinstance(v, int):
            return GatewayMode(v)

        return v


class ActivityWithCW(Activity):
    cw_unit: Dict[str, Any]
    cw_org: Dict[str, Any]
    cw_token: Dict[str, Any]


class ActivitiesResponse(BaseModel):
    activities: List[ActivityWithCW] = Field(default_factory=list)
    total: int = 0

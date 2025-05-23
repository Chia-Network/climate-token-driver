from __future__ import annotations

import enum
from typing import Any, Optional, Union

from pydantic import Field, validator

from app.core.types import GatewayMode
from app.schemas.core import BaseModel
from app.schemas.token import TokenOnChain


class ActivitySearchBy(enum.Enum):
    ONCHAIN_METADATA = "onchain_metadata"
    CLIMATE_WAREHOUSE = "climate_warehouse"


class ActivityBase(BaseModel):
    metadata: dict[str, str]
    beneficiary_name: Optional[str]
    beneficiary_address: Optional[str]
    beneficiary_puzzle_hash: Optional[str]

    coin_id: bytes
    height: int
    amount: int
    mode: GatewayMode | str
    timestamp: int

    @validator("mode")
    def mode_from_str(cls, v: Union[str, GatewayMode]) -> GatewayMode:
        if isinstance(v, GatewayMode):
            return v
        for mode in GatewayMode:
            if v in {mode.name, mode.value}:
                return mode

        raise ValueError(f"Invalid mode {v}")


class Activity(ActivityBase):
    org_uid: str
    warehouse_project_id: str
    vintage_year: int
    sequence_num: int
    asset_id: bytes
    coin_id: bytes


class ActivityWithCW(ActivityBase):
    token: TokenOnChain

    cw_unit: dict[str, Any]
    cw_org: dict[str, Any]
    cw_project: dict[str, Any]


class ActivitiesResponse(BaseModel):
    activities: list[ActivityWithCW] = Field(default_factory=list)
    total: int = 0


class ActivityRecordResponse(BaseModel):
    activity: Optional[ActivityWithCW] = Field(default=None)

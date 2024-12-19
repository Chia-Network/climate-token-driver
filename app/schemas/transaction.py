from __future__ import annotations

from typing import Optional

from app.schemas.core import BaseModel
from app.schemas.types import ChiaJsonObject


class Transaction(BaseModel):
    id: bytes
    record: ChiaJsonObject


class Transactions(BaseModel):
    wallet_id: int
    start: int
    end: int
    sort_key: str
    reverse: bool
    to_address: Optional[str]
    transactions: list[ChiaJsonObject]

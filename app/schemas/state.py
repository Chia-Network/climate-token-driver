from __future__ import annotations

from pydantic import BaseModel


class State(BaseModel):
    id: int | None = None
    current_height: int | None = None
    block_height: int | None = None

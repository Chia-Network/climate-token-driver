from typing import Optional

from pydantic import BaseModel


class State(BaseModel):
    id: Optional[int] = None
    current_height: Optional[int] = None
    block_height: Optional[int] = None

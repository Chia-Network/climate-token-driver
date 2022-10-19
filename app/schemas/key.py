from app.schemas.core import BaseModel


class Key(BaseModel):
    hex: bytes
    bech32m: str

from __future__ import annotations

from typing import Any, ClassVar, get_type_hints

from chia.util.byte_types import hexstr_to_bytes
from pydantic import BaseModel as PydanticBaseModel
from pydantic import root_validator

from app.core.types import GatewayMode


class BaseModel(PydanticBaseModel):
    @root_validator(pre=True)
    def convert(cls, values: dict[str, Any]) -> dict[str, Any]:
        field_to_type = get_type_hints(cls)

        return_values: dict[str, Any] = {}
        for key, value in values.items():
            if key not in cls.__fields__.keys():
                continue

            type_ = field_to_type[key]
            if (type_ is bytes) and isinstance(value, str):
                value = hexstr_to_bytes(value)

            return_values[key] = value

        return return_values

    class Config:
        json_encoders: ClassVar[dict[type[bytes] | type[GatewayMode], Any]] = {
            bytes: lambda b: "0x" + b.hex(),
            GatewayMode: lambda v: v.name,
        }

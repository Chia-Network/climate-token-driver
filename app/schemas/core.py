from typing import Any, Dict, Type, get_type_hints

from chia.util.byte_types import hexstr_to_bytes
from pydantic import BaseModel as PydanticBaseModel
from pydantic import root_validator


class BaseModel(PydanticBaseModel):
    @root_validator(pre=True)
    def convert(cls, values: Dict[str, Any]):
        field_to_type: Dict[str, Type] = get_type_hints(cls)

        return_values: Dict[str, Any] = {}
        for (key, value) in values.items():
            if key not in cls.__fields__.keys():
                continue

            type_: Type = field_to_type[key]
            if (type_ is bytes) and isinstance(value, str):
                value = hexstr_to_bytes(value)

            return_values[key] = value

        return return_values

    class Config:
        json_encoders = {bytes: lambda b: "0x" + b.hex()}

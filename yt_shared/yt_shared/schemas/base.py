from typing import ClassVar

from pydantic import BaseModel, Extra, validator

from yt_shared.enums import RabbitPayloadType


class RealBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid

    def json(self, *args, **kwargs) -> str:
        if 'separators' not in kwargs:
            kwargs['separators'] = (',', ':')
        return super().json(*args, **kwargs)


class BaseRabbitPayloadModel(RealBaseModel):
    _TYPE: ClassVar[RabbitPayloadType] = None

    type: RabbitPayloadType = None

    @classmethod
    @validator('type')
    def validate_type_value(cls, v: RabbitPayloadType) -> RabbitPayloadType:
        if v is not cls._TYPE:
            raise ValueError(f'Value "{v}" must be {cls._TYPE}')
        return v

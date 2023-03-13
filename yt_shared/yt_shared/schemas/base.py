from pydantic import BaseModel, Extra

from yt_shared.enums import RabbitPayloadType


class RealBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid

    def json(self, *args, **kwargs) -> str:
        if 'separators' not in kwargs:
            kwargs['separators'] = (',', ':')
        return super().json(*args, **kwargs)


class BaseRabbitPayloadModel(RealBaseModel):
    type: RabbitPayloadType

from pydantic import BaseModel, Extra

from yt_shared.enums import RabbitPayloadType


class RealBaseModel(BaseModel):
    """Base Pydantic model. All models should inherit from this."""

    class Config:
        extra = Extra.forbid

    def json(self, *args, **kwargs) -> str:
        """By default, dump without whitespaces."""
        if 'separators' not in kwargs:
            kwargs['separators'] = (',', ':')
        return super().json(*args, **kwargs)


class BaseRabbitPayloadModel(RealBaseModel):
    """Base RabbitMQ payload model. All RabbitMQ models should inherit from this."""

    type: RabbitPayloadType

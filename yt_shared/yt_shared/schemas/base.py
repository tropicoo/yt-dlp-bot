from pydantic import BaseModel, ConfigDict

from yt_shared.enums import RabbitPayloadType


class RealBaseModel(BaseModel):
    """Base Pydantic model. All models should inherit from this."""

    model_config = ConfigDict(extra='forbid')


class BaseOrmModel(RealBaseModel):
    model_config = ConfigDict(from_attributes=True, **RealBaseModel.model_config)


class BaseRabbitPayloadModel(RealBaseModel):
    """Base RabbitMQ payload model. All RabbitMQ models should inherit from this."""

    type: RabbitPayloadType

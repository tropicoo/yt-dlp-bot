from abc import ABC

from pydantic import BaseModel, ConfigDict

from yt_shared.enums import RabbitPayloadType


class RealBaseModel(BaseModel, ABC):
    """Base Pydantic model. All non-strict models should inherit from it."""

    model_config = ConfigDict(extra='forbid', validate_default=True)


class StrictRealBaseModel(RealBaseModel, ABC):
    """Base Pydantic model. All strict models should inherit from it."""

    model_config = ConfigDict(**RealBaseModel.model_config, strict=True)


class BaseOrmModel(RealBaseModel, ABC):
    model_config = ConfigDict(**RealBaseModel.model_config, from_attributes=True)


class StrictBaseOrmModel(BaseOrmModel, ABC):
    model_config = ConfigDict(**BaseOrmModel.model_config, strict=True)


class StrictBaseConfigModel(StrictRealBaseModel, ABC):
    model_config = ConfigDict(**StrictRealBaseModel.model_config, frozen=True)


class BaseRabbitPayloadModel(RealBaseModel, ABC):
    """Base RabbitMQ payload model. All RabbitMQ models should inherit from this."""

    type: RabbitPayloadType


class StrictBaseRabbitPayloadModel(BaseRabbitPayloadModel, ABC):
    """Base RabbitMQ payload model. All RabbitMQ models should inherit from this."""

    model_config = ConfigDict(**BaseRabbitPayloadModel.model_config, strict=True)

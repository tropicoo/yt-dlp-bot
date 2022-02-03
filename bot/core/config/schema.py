from pydantic import StrictStr, validator

from yt_shared.schemas.base import RealBaseModel

_LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}


class TelegramSchema(RealBaseModel):
    token: StrictStr
    allowed_user_ids: list[int]


class ConfigSchema(RealBaseModel):
    telegram: TelegramSchema
    log_level: StrictStr

    @validator('log_level')
    def validate_log_level_value(cls, value):
        if value not in _LOG_LEVELS:
            raise ValueError(f'"log_level" must be one of {_LOG_LEVELS}')
        return value

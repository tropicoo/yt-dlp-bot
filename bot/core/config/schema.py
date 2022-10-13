from pydantic import StrictStr, StrictInt, constr, validator

from yt_shared.schemas.base import RealBaseModel

_LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}

_LANG_CODE_LEN = 2
_LANG_CODE_REGEX = rf'^[a-z]{{{_LANG_CODE_LEN}}}$'


class TelegramSchema(RealBaseModel):
    api_id: StrictInt
    api_hash: StrictStr
    token: StrictStr
    allowed_user_ids: list[int]
    lang_code: constr(regex=_LANG_CODE_REGEX, to_lower=True)


class ConfigSchema(RealBaseModel):
    telegram: TelegramSchema
    log_level: StrictStr

    @validator('log_level')
    def validate_log_level_value(cls, value):
        if value not in _LOG_LEVELS:
            raise ValueError(f'"log_level" must be one of {_LOG_LEVELS}')
        return value

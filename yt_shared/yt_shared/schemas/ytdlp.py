import datetime

from pydantic import Field, StrictStr, validator

from yt_shared.schemas.base import RealBaseModel


def _remove_microseconds(dt_obj: datetime.datetime) -> datetime.datetime:
    return dt_obj.replace(microsecond=0)


class Latest(RealBaseModel):
    version: StrictStr
    retrieved_at: datetime.datetime

    @validator('retrieved_at', pre=True)
    def remove_microseconds(cls, value: datetime.datetime) -> datetime.datetime:
        return _remove_microseconds(value)


class Current(RealBaseModel):
    version: StrictStr = Field(..., alias='current_version')
    updated_at: datetime.datetime

    @validator('updated_at', pre=True)
    def remove_microseconds(cls, value: datetime.datetime) -> datetime.datetime:
        return _remove_microseconds(value)

    class Config(RealBaseModel.Config):
        orm_mode = True

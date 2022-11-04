import datetime

from pydantic import Field, StrictStr, validator

from yt_shared.schemas.base import RealBaseModel


def _remove_microseconds(dt_obj: datetime.datetime) -> datetime.datetime:
    return dt_obj.replace(microsecond=0)


class LatestVersion(RealBaseModel):
    version: StrictStr
    retrieved_at: datetime.datetime

    @classmethod
    @validator('retrieved_at', pre=True)
    def remove_microseconds(cls, value: datetime.datetime) -> datetime.datetime:
        return _remove_microseconds(value)


class CurrentVersion(RealBaseModel):
    version: StrictStr = Field(..., alias='current_version')
    updated_at: datetime.datetime

    @classmethod
    @validator('updated_at', pre=True)
    def remove_microseconds(cls, value: datetime.datetime) -> datetime.datetime:
        return _remove_microseconds(value)

    class Config(RealBaseModel.Config):
        orm_mode = True


class VersionContext(RealBaseModel):
    latest: LatestVersion
    current: CurrentVersion

    @property
    def has_new_version(self) -> bool:
        return [int(x) for x in self.latest.version.split('.')] > [
            int(x) for x in self.current.version.split('.')
        ]

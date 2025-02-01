import datetime

from pydantic import Field, field_validator

from yt_shared.schemas.base import StrictBaseOrmModel, StrictRealBaseModel
from yt_shared.utils.common import remove_microseconds


class LatestVersion(StrictRealBaseModel):
    version: str
    retrieved_at: datetime.datetime

    @field_validator('retrieved_at', mode='after')
    @classmethod
    def remove_microseconds(cls, value: datetime.datetime) -> datetime.datetime:
        return remove_microseconds(value)


class CurrentVersion(StrictBaseOrmModel):
    version: str = Field(..., alias='current_version')
    updated_at: datetime.datetime

    @field_validator('updated_at', mode='after')
    @classmethod
    def remove_microseconds(cls, value: datetime.datetime) -> datetime.datetime:
        return remove_microseconds(value)


class VersionContext(StrictRealBaseModel):
    latest: LatestVersion
    current: CurrentVersion

    @property
    def has_new_version(self) -> bool:
        return [int(x) for x in self.latest.version.split('.')] > [
            int(x) for x in self.current.version.split('.')
        ]

import uuid
from datetime import datetime

from pydantic import Field, StrictFloat, StrictInt, StrictStr
from typing_extensions import Annotated
from yt_shared.enums import DownMediaType, TaskSource, TaskStatus
from yt_shared.schemas.base import BaseOrmModel, StrictRealBaseModel


class CacheSchema(BaseOrmModel):
    id: uuid.UUID
    created: datetime
    updated: datetime
    cache_id: StrictStr
    cache_unique_id: StrictStr
    file_size: StrictInt
    date_timestamp: datetime


class FileSimpleSchema(BaseOrmModel):
    id: uuid.UUID
    created: datetime
    updated: datetime
    title: StrictStr | None
    name: StrictStr | None
    thumb_name: StrictStr | None
    duration: StrictFloat | StrictInt | None
    width: StrictInt | None
    height: StrictInt | None
    cache: CacheSchema | None = ...


class FileSchema(FileSimpleSchema):
    meta: dict | None = ...


class TaskSimpleSchema(BaseOrmModel):
    id: uuid.UUID
    added_at: datetime
    created: datetime
    updated: datetime
    status: TaskStatus
    url: StrictStr
    source: TaskSource
    from_user_id: StrictInt | None
    message_id: StrictInt | None
    yt_dlp_version: StrictStr | None
    error: StrictStr | None
    files: list[FileSimpleSchema]


class TaskSchema(TaskSimpleSchema):
    files: list[FileSchema]


class CreateTaskIn(StrictRealBaseModel):
    url: str = ...
    download_media_type: Annotated[DownMediaType, Field(strict=False)] = ...
    save_to_storage: bool = ...
    custom_filename: str = ...
    automatic_extension: bool = ...


class CreateTaskOut(StrictRealBaseModel):
    id: uuid.UUID
    url: str
    source: TaskSource
    added_at: datetime


class TasksStatsSchema(BaseOrmModel):
    total: StrictInt
    unique_urls: StrictInt
    pending: StrictInt
    processing: StrictInt
    failed: StrictInt
    done: StrictInt

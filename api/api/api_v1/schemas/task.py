import uuid
from datetime import datetime
from typing import Optional

from pydantic import StrictStr

from api.api_v1.schemas.base import BaseOrmModel
from yt_shared.constants import TaskSource, TaskStatus
from yt_shared.schemas.base import RealBaseModel


class CacheSchema(BaseOrmModel):
    id: uuid.UUID
    created: datetime
    updated: datetime
    cache_id: str
    cache_unique_id: str
    file_size: int
    date_timestamp: datetime


class FileSimpleSchema(BaseOrmModel):
    id: uuid.UUID
    created: datetime
    updated: datetime
    title: Optional[str]
    name: Optional[str]
    cache: Optional[CacheSchema] = ...


class FileSchema(FileSimpleSchema):
    meta: Optional[dict] = ...


class TaskSimpleSchema(BaseOrmModel):
    id: uuid.UUID
    added_at: datetime
    created: datetime
    updated: datetime
    status: TaskStatus
    url: str
    source: TaskSource
    from_user_id: Optional[int]
    message_id: Optional[int]
    yt_dlp_version: Optional[str]
    error: Optional[str]
    file: Optional[FileSimpleSchema]


class TaskSchema(TaskSimpleSchema):
    file: Optional[FileSchema]


class CreateTaskIn(RealBaseModel):
    url: StrictStr


class CreateTaskOut(RealBaseModel):
    id: uuid.UUID
    url: StrictStr
    source: TaskSource
    added_at: datetime


class TasksStatsSchema(BaseOrmModel):
    total: int
    unique_urls: int
    pending: int
    processing: int
    failed: int
    done: int

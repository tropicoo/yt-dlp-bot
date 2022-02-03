import uuid
from datetime import datetime
from typing import Optional

from pydantic import StrictStr

from api.api_v1.schemas.base import BaseOrmModel
from yt_shared.constants import TaskSource, TaskStatus
from yt_shared.schemas.base import RealBaseModel


class FileSimpleSchema(BaseOrmModel):
    id: uuid.UUID
    created: datetime
    updated: datetime
    name: Optional[str]
    ext: Optional[str]


class FileSchema(FileSimpleSchema):
    meta: Optional[dict] = ...


class TaskSimpleSchema(BaseOrmModel):
    id: uuid.UUID
    status: TaskStatus
    url: str
    source: TaskSource
    added_at: datetime
    created: datetime
    updated: datetime
    message_id: Optional[int]
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

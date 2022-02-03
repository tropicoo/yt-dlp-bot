import uuid
from datetime import datetime, timezone
from typing import Optional, Type, Union

from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.schemas.task import (
    CreateTaskIn,
    CreateTaskOut,
    TaskSchema,
    TaskSimpleSchema,
)
from core.exceptions import TaskServiceError
from core.repository import DatabaseRepository
from yt_shared.constants import TaskSource, TaskStatus
from yt_shared.models import Task
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.video import VideoPayload


class TaskService:

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repository = DatabaseRepository(db)

    @staticmethod
    def _get_schema(include_meta: bool) -> Type[Union[TaskSchema, TaskSimpleSchema]]:
        return TaskSchema if include_meta else TaskSimpleSchema

    async def delete_task(self, id: Union[str, uuid.UUID]) -> None:
        await self._repository.delete_task(id)

    async def get_latest_task(self, include_meta: bool) -> Task:
        schema = self._get_schema(include_meta)
        task = await self._repository.get_latest_task(include_meta)
        return schema.from_orm(task)

    async def get_task(self,
                       id: Union[str, uuid.UUID],
                       include_meta: bool,
                       ) -> Task:
        schema = self._get_schema(include_meta)
        task = await self._repository.get_task(id, include_meta)
        return schema.from_orm(task)

    async def get_all_tasks(
            self,
            include_meta: bool,
            status: Optional[list[TaskStatus]] = None,
            limit: int = 100,
            offset: int = 0,
    ) -> list[Task]:
        schema = self._get_schema(include_meta)
        tasks = await self._repository.get_all_tasks(
            include_meta, status, limit, offset)
        return [schema.from_orm(task) for task in tasks]

    @staticmethod
    async def create_task_non_db(task: CreateTaskIn,
                                 publisher: Publisher,
                                 source: TaskSource = TaskSource.API,
                                 ) -> CreateTaskOut:
        task_id = uuid.uuid4()
        added_at = datetime.now(timezone.utc)
        payload = VideoPayload(id=task_id, url=task.url, added_at=added_at,
                               source=source)
        if not await publisher.send_for_download(payload):
            raise TaskServiceError('Failed to create task')
        return CreateTaskOut(id=task_id, url=task.url, added_at=added_at,
                             source=source)

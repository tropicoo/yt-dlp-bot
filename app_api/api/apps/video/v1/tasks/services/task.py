import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.enums import TaskSource, TaskStatus
from yt_shared.rabbit.publisher import RmqPublisher
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.media import InbMediaPayload

from api.apps.video.v1.tasks.schemas.task import (
    CreateTaskIn,
    CreateTaskOut,
    TaskSchema,
    TaskSimpleSchema,
    TasksStatsSchema,
)
from api.common.exceptions import TaskServiceError


class TaskService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repository = TaskRepository(db=db)

    @staticmethod
    def _get_schema(include_meta: bool) -> type[TaskSchema | TaskSimpleSchema]:
        return TaskSchema if include_meta else TaskSimpleSchema

    async def delete_task(self, id_: str | uuid.UUID) -> None:
        await self._repository.delete_task(id_)

    async def get_latest_task(
        self, include_meta: bool
    ) -> TaskSchema | TaskSimpleSchema:
        schema = self._get_schema(include_meta)
        task = await self._repository.get_latest_task(include_meta)
        return schema.model_validate(task)

    async def get_task(
        self, id_: str | uuid.UUID, include_meta: bool
    ) -> TaskSchema | TaskSimpleSchema:
        schema = self._get_schema(include_meta)
        task = await self._repository.get_task(id_, include_meta)
        return schema.model_validate(task)

    async def get_all_tasks(
        self,
        include_meta: bool,
        status: list[TaskStatus] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskSimpleSchema | TaskSchema]:
        schema = self._get_schema(include_meta)
        tasks = await self._repository.get_all_tasks(
            include_meta, status, limit, offset
        )
        return [schema.model_validate(task) for task in tasks]

    @staticmethod
    async def create_task_non_db(
        task: CreateTaskIn, publisher: RmqPublisher
    ) -> CreateTaskOut:
        task_id = uuid.uuid4()
        source = TaskSource.API
        added_at = datetime.now(UTC)
        payload = InbMediaPayload(
            id=task_id,
            url=task.url,
            original_url=task.url,
            added_at=added_at,
            source=source,
            download_media_type=task.download_media_type,
            save_to_storage=task.save_to_storage,
            from_chat_id=None,
            from_chat_type=None,
            from_user_id=None,
            message_id=None,
            ack_message_id=None,
            custom_filename=task.custom_filename,
            automatic_extension=task.automatic_extension,
        )
        if not await publisher.send_for_download(payload):
            raise TaskServiceError('Failed to create task')
        return CreateTaskOut(id=task_id, url=task.url, added_at=added_at, source=source)

    async def get_stats(self) -> TasksStatsSchema:
        return TasksStatsSchema.model_validate(await self._repository.get_stats())

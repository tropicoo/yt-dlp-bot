import logging
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from yt_shared.constants import TaskStatus
from yt_shared.models import Cache, File, Task
from yt_shared.schemas.cache import CacheSchema
from yt_shared.schemas.video import DownVideo, VideoPayload


class TaskRepository:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    async def get_or_create_task(
        self, db: AsyncSession, video_payload: VideoPayload
    ) -> Task:
        if video_payload.id is None:
            return await self._create_task(db, video_payload)

        stmt = select(Task).filter_by(id=video_payload.id)
        task = await db.execute(stmt)
        try:
            return task.scalar_one()
        except NoResultFound:
            return await self._create_task(db, video_payload)

    @staticmethod
    async def _create_task(db: AsyncSession, video_payload: VideoPayload) -> Task:
        task = Task(**video_payload.dict())
        db.add(task)
        await db.commit()
        return task

    @staticmethod
    async def save_file_cache(
        db: AsyncSession, task_id: str | UUID, cache: CacheSchema
    ) -> None:
        stmt = insert(Cache).values(
            cache_id=cache.cache_id,
            cache_unique_id=cache.cache_unique_id,
            file_size=cache.file_size,
            date_timestamp=cache.date_timestamp,
            file_id=(select(File.id).filter_by(task_id=task_id).scalar_subquery()),
        )
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def save_as_done(
        db: AsyncSession, task: Task, downloaded_video: DownVideo
    ) -> None:
        task.file = File(**downloaded_video.dict())
        task.status = TaskStatus.DONE
        await db.commit()

    @staticmethod
    async def save_as_processing(db: AsyncSession, task: Task) -> None:
        task.status = TaskStatus.PROCESSING
        await db.commit()

    @staticmethod
    async def save_as_failed(db: AsyncSession, task: Task, error_message: str) -> None:
        task.status = TaskStatus.FAILED
        task.error = error_message
        await db.commit()

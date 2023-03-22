import logging
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.enums import TaskStatus
from yt_shared.models import Cache, File, Task
from yt_shared.schemas.cache import CacheSchema
from yt_shared.schemas.media import BaseMedia, IncomingMediaPayload, Video
from yt_shared.utils.common import ASYNC_LOCK


class TaskRepository:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    async def get_or_create_task(
        self, db: AsyncSession, media_payload: IncomingMediaPayload
    ) -> Task:
        if media_payload.id is None:
            return await self._create_task(db, media_payload)

        stmt = select(Task).filter_by(id=media_payload.id)
        task = await db.execute(stmt)
        try:
            return task.scalar_one()
        except NoResultFound:
            return await self._create_task(db, media_payload)

    @staticmethod
    async def _create_task(
        db: AsyncSession, media_payload: IncomingMediaPayload
    ) -> Task:
        task = Task(
            id=media_payload.id,
            url=media_payload.url,
            source=media_payload.source,
            from_user_id=media_payload.from_user_id,
            message_id=media_payload.message_id,
            added_at=media_payload.added_at,
        )
        db.add(task)
        await db.commit()
        return task

    @staticmethod
    async def save_file_cache(
        db: AsyncSession, file_id: str | UUID, cache: CacheSchema
    ) -> None:
        stmt = insert(Cache).values(
            cache_id=cache.cache_id,
            cache_unique_id=cache.cache_unique_id,
            file_size=cache.file_size,
            date_timestamp=cache.date_timestamp,
            file_id=file_id,
        )
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def save_file(
        db: AsyncSession, task: Task, media: BaseMedia, meta: dict
    ) -> File:
        file = File(
            title=media.title,
            name=media.filename,
            duration=media.duration,
            meta=meta,
            task_id=task.id,
        )
        # TODO: Rework this.
        if isinstance(media, Video):
            file.width = media.width
            file.height = media.height
            file.thumb_name = media.thumb_name

        db.add(file)
        async with ASYNC_LOCK:
            await db.flush([file])
        return file

    @staticmethod
    async def save_as_done(db: AsyncSession, task: Task) -> None:
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

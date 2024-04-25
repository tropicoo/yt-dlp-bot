import logging
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.constants import ASYNC_LOCK
from yt_shared.enums import TaskStatus
from yt_shared.models import Cache, File, Task
from yt_shared.schemas.cache import CacheSchema
from yt_shared.schemas.media import BaseMedia, InbMediaPayload, Video


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._session = session

    async def get_or_create_task(self, media_payload: InbMediaPayload) -> Task:
        if media_payload.id is None:
            return await self._create_task(media_payload)

        stmt = select(Task).filter_by(id=media_payload.id)
        task = await self._session.execute(stmt)
        try:
            return task.scalar_one()
        except NoResultFound:
            return await self._create_task(media_payload)

    async def _create_task(self, media_payload: InbMediaPayload) -> Task:
        task = Task(
            id=media_payload.id,
            url=media_payload.url,
            source=media_payload.source,
            from_user_id=media_payload.from_user_id,
            message_id=media_payload.message_id,
            added_at=media_payload.added_at,
        )
        self._session.add(task)
        await self._session.commit()
        return task

    async def save_file_cache(self, file_id: str | UUID, cache: CacheSchema) -> None:
        stmt = insert(Cache).values(
            cache_id=cache.cache_id,
            cache_unique_id=cache.cache_unique_id,
            file_size=cache.file_size,
            date_timestamp=cache.date_timestamp,
            file_id=file_id,
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def save_file(self, task: Task, media: BaseMedia, meta: dict) -> File:
        file = File(
            title=media.title,
            name=media.current_filename,
            duration=media.duration,
            meta=meta,
            task_id=task.id,
        )
        # TODO: Rework this.
        if isinstance(media, Video):
            file.width = media.width
            file.height = media.height
            file.thumb_name = media.thumb_name

        self._session.add(file)
        async with ASYNC_LOCK:
            await self._session.flush([file])
        return file

    async def save_as_done(self, task: Task) -> None:
        task.status = TaskStatus.DONE
        await self._session.commit()

    async def save_as_processing(self, task: Task) -> None:
        task.status = TaskStatus.PROCESSING
        await self._session.commit()

    async def save_as_failed(self, task: Task, error_message: str) -> None:
        task.status = TaskStatus.FAILED
        task.error = error_message
        await self._session.commit()

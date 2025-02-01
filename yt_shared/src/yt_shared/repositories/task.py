import logging
import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, Row, delete, desc, distinct, func, insert, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from yt_shared.constants import SHARED_ASYNC_LOCK
from yt_shared.enums import TaskStatus
from yt_shared.models import Cache, File, Task
from yt_shared.schemas.cache import CacheSchema
from yt_shared.schemas.media import BaseMedia, InbMediaPayload, Video

if TYPE_CHECKING:
    from sqlalchemy.engine import CursorResult


class TaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._db = db

    async def get_or_create_task(self, media_payload: InbMediaPayload) -> Task:
        if media_payload.id is None:
            return await self._create_task(media_payload)

        stmt = select(Task).filter_by(id=media_payload.id)
        task = await self._db.execute(stmt)
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
        self._db.add(task)
        await self._db.commit()
        return task

    async def save_file_cache(self, file_id: str | UUID, cache: CacheSchema) -> None:
        stmt = insert(Cache).values(
            cache_id=cache.cache_id,
            cache_unique_id=cache.cache_unique_id,
            file_size=cache.file_size,
            date_timestamp=cache.date_timestamp,
            file_id=file_id,
        )
        await self._db.execute(stmt)
        await self._db.commit()

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

        self._db.add(file)
        async with SHARED_ASYNC_LOCK:
            await self._db.flush([file])
        return file

    async def save_as_done(self, task: Task) -> None:
        task.status = TaskStatus.DONE
        await self._db.commit()

    async def save_as_processing(self, task: Task) -> None:
        task.status = TaskStatus.PROCESSING
        await self._db.commit()

    async def save_as_failed(self, task: Task, error_message: str) -> None:
        task.status = TaskStatus.FAILED
        task.error = error_message
        await self._db.commit()

    async def purge_user_tasks(self, user_ids: Sequence[int]) -> None:
        await self._db.execute(
            delete(Task).where(
                ((Task.from_user_id.in_(user_ids)) | (Task.from_user_id.is_(None)))
                & ~(Task.status.in_([TaskStatus.PENDING, TaskStatus.PROCESSING]))
            )
        )
        await self._db.commit()

    async def get_all_tasks(
        self,
        include_meta: bool,
        status: list[TaskStatus] | None,
        limit: int,
        offset: int,
    ) -> list[Task]:
        stmt = (
            select(Task)
            .options(
                joinedload(Task.files)
                .load_only(*self._get_load_file_cols(include_meta))
                .options(joinedload(File.cache))
            )
            .order_by(desc(Task.created))
            .offset(offset)
            .limit(limit)
        )

        if status:
            stmt = stmt.filter(Task.status.in_(status))

        tasks = await self._db.execute(stmt)
        tasks.unique()
        return tasks.scalars().all()

    @staticmethod
    def _get_load_file_cols(include_meta: bool) -> list[Column]:
        """Load 'File' model columns depending on 'include_meta' bool variable."""
        load_cols = [
            File.created,
            File.updated,
            File.name,
            File.thumb_name,
            File.duration,
            File.width,
            File.height,
            File.title,
        ]
        if include_meta:
            load_cols.append(File.meta)
        return load_cols

    async def get_task(self, id_: str | uuid.UUID, include_meta: bool) -> Task:
        stmt = (
            select(Task)
            .options(
                joinedload(Task.files)
                .load_only(*self._get_load_file_cols(include_meta))
                .options(joinedload(File.cache))
            )
            .filter(Task.id == id_)
        )
        task = await self._db.execute(stmt)
        task.unique()
        return task.scalar_one()

    async def get_latest_task(self, include_meta: bool) -> Task:
        stmt = (
            select(Task)
            .order_by(desc(Task.created))
            .options(
                joinedload(Task.files)
                .load_only(*self._get_load_file_cols(include_meta))
                .options(joinedload(File.cache))
            )
            .limit(1)
        )
        task = await self._db.execute(stmt)
        task.unique()
        return task.scalar_one()

    async def delete_task(self, id_: str | uuid.UUID) -> None:
        stmt = delete(Task).where(Task.id == id_)
        res: CursorResult = await self._db.execute(stmt)
        if not res.rowcount:
            raise NoResultFound
        await self._db.commit()

    async def get_stats(
        self,
    ) -> Row[tuple[int, int, int, int, int, int]]:
        count_ = func.count(Task.id)
        stmt = select(
            count_.label('total'),
            func.count(distinct(Task.url)).label('unique_urls'),
            count_.filter(Task.status == TaskStatus.PENDING).label('pending'),
            count_.filter(Task.status == TaskStatus.PROCESSING).label('processing'),
            count_.filter(Task.status == TaskStatus.FAILED).label('failed'),
            count_.filter(Task.status == TaskStatus.DONE).label('done'),
        )
        result = await self._db.execute(stmt)
        return result.one()

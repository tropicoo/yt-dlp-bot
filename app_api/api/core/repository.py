import uuid

from sqlalchemy import delete, desc, distinct, func, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import count
from yt_shared.enums import TaskStatus
from yt_shared.models import File, Task


class DatabaseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

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
    def _get_load_file_cols(include_meta: bool) -> list:
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

    async def get_task(self, id: str | uuid.UUID, include_meta: bool) -> Task:
        stmt = (
            select(Task)
            .options(
                joinedload(Task.files)
                .load_only(*self._get_load_file_cols(include_meta))
                .options(joinedload(File.cache))
            )
            .filter(Task.id == id)
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

    async def delete_task(self, id: str | uuid.UUID) -> None:
        stmt = delete(Task).where(Task.id == id)
        res: CursorResult = await self._db.execute(stmt)
        if not res.rowcount:
            raise NoResultFound
        await self._db.commit()

    async def get_stats(self):
        count_: count = func.count('*')
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

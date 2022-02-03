import uuid
from typing import Optional, Union

from sqlalchemy import delete, desc, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from yt_shared.constants import TaskStatus
from yt_shared.models import File, Task


class DatabaseRepository:

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all_tasks(
            self,
            include_meta: bool,
            status: Optional[list[TaskStatus]],
            limit: int,
            offset: int,
    ) -> list[Task]:
        load_cols = self._load_file_cols(include_meta)
        stmt = select(Task) \
            .options(joinedload(Task.file)
                     .load_only(*load_cols)) \
            .order_by(desc(Task.created)) \
            .offset(offset) \
            .limit(limit)

        if status:
            stmt = stmt.filter(Task.status.in_(status))

        tasks = await self._db.execute(stmt)
        return tasks.scalars().all()

    @staticmethod
    def _load_file_cols(include_meta: bool) -> list:
        """Load 'File' model columns depending on 'include_meta' bool variable."""
        load_cols = [File.created, File.updated, File.name, File.ext]
        if include_meta:
            load_cols.append(File.meta)
        return load_cols

    async def get_task(self,
                       id: Union[str, uuid.UUID],
                       include_meta: bool) -> Task:
        load_cols = self._load_file_cols(include_meta)
        stmt = select(Task) \
            .filter_by(id=id) \
            .options(joinedload(Task.file)
                     .load_only(*load_cols))
        task = await self._db.execute(stmt)
        return task.scalar_one()

    async def get_latest_task(self, include_meta: bool) -> Task:
        load_cols = self._load_file_cols(include_meta)
        stmt = select(Task) \
            .order_by(desc(Task.created)) \
            .options(joinedload(Task.file)
                     .load_only(*load_cols)) \
            .limit(1)
        task = await self._db.execute(stmt)
        return task.scalar_one()

    async def delete_task(self, id: Union[str, uuid.UUID]) -> None:
        stmt = delete(Task).where(Task.id == id)
        res: CursorResult = await self._db.execute(stmt)
        if not res.rowcount:
            raise NoResultFound
        await self._db.commit()

import logging

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from yt_shared.models import Task
from yt_shared.schemas.video import VideoPayload


class TaskRepository:

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    async def get_or_create_task(self, db: AsyncSession,
                                 video_payload: VideoPayload) -> Task:
        try:
            stmt = select(Task).filter_by(id=video_payload.id)
            task = await db.execute(stmt)
            return task.scalar_one()
        except NoResultFound:
            task = Task(**video_payload.dict())  # noqa
            db.add(task)
            await db.commit()
            return task

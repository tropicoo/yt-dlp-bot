from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.db.session import get_db
from yt_shared.rabbit.publisher import RmqPublisher


async def get_rmq_publisher() -> AsyncGenerator[RmqPublisher, None]:
    yield RmqPublisher()


RMQDep = Annotated[RmqPublisher, Depends(get_rmq_publisher)]
DBDep = Annotated[AsyncSession, Depends(get_db)]

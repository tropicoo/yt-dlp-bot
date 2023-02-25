import re
import uuid
from typing import AsyncGenerator

import sqlalchemy as sa
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy_utils import UUIDType
from yt_shared.config import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI_ASYNC,
    echo=settings.SQLALCHEMY_ECHO,
    pool_pre_ping=True,
    connect_args={'server_settings': {'application_name': settings.APPLICATION_NAME}},
)

metadata = MetaData()
metadata.bind = engine
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=settings.SQLALCHEMY_EXPIRE_ON_COMMIT,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


class CustomBase:
    id: uuid.UUID = sa.Column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    __name__: str

    @declared_attr
    def __tablename__(cls):  # noqa
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()


Base = declarative_base(cls=CustomBase, metadata=metadata)

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Index, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy_utils import Timestamp, UUIDType

from yt_shared.db.session import Base
from yt_shared.enums import TaskSource, TaskStatus
from yt_shared.models.yt_dlp import YTDLP


class Task(Base, Timestamp):
    id = sa.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    status = sa.Column(
        sa.Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING.name,
        server_default=TaskStatus.PENDING.name,
        index=True,
    )
    url = sa.Column(sa.String, nullable=False)
    source = sa.Column(
        sa.Enum(TaskSource),
        nullable=False,
        index=True,
    )
    files = relationship(
        'File',
        backref='task',
        cascade='all, delete-orphan',
    )
    added_at = sa.Column(sa.DateTime, nullable=False)
    from_user_id = sa.Column(sa.Integer, nullable=True)
    message_id = sa.Column(sa.Integer, nullable=True)
    error = sa.Column(sa.String, nullable=True)
    yt_dlp_version = sa.Column(
        sa.String, nullable=True, default=select(YTDLP.current_version)
    )

    @validates('added_at')
    def validate_added_at(self, key: str, added_at: datetime) -> datetime:
        """Remove UTC timezone from aware datetime before saving."""
        return added_at.replace(tzinfo=None)

    # Fetch the value of server-generated default values like 'yt_dlp_version'.
    __mapper_args__ = {'eager_defaults': True}


task_created_at_index = Index('task_created_at_idx', Task.created)


class File(Base, Timestamp):
    id = sa.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    title = sa.Column(sa.String, nullable=True)
    name = sa.Column(sa.String, nullable=True)
    thumb_name = sa.Column(sa.String, nullable=True)
    duration = sa.Column(sa.Integer, nullable=True)
    width = sa.Column(sa.Integer, nullable=True)
    height = sa.Column(sa.Integer, nullable=True)
    meta = sa.Column(JSONB, nullable=True)
    task_id = sa.Column(
        UUIDType(binary=False),
        sa.ForeignKey('task.id', ondelete='CASCADE'),
        nullable=False,
        unique=False,
        index=True,
    )
    cache = relationship(
        'Cache',
        backref='file',
        uselist=False,
        cascade='all, delete-orphan',
    )

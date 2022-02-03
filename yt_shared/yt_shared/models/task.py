import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy_utils import Timestamp, UUIDType

from yt_shared.constants import TaskSource, TaskStatus
from yt_shared.db import Base


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
    file = relationship(
        'File',
        backref='task',
        uselist=False,
        cascade='all, delete-orphan',
    )
    added_at = sa.Column(sa.DateTime, nullable=False)
    message_id = sa.Column(sa.Integer, nullable=True)
    error = sa.Column(sa.String, nullable=True)

    @validates('added_at')
    def validate_added_at(self, key: str, added_at: datetime) -> datetime:
        """Remove UTC timezone from aware datetime before saving."""
        return added_at.replace(tzinfo=None)


task_created_at_index = Index('task_created_at_idx', Task.created)


class File(Base, Timestamp):
    id = sa.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String, nullable=True)
    ext = sa.Column(sa.String, nullable=True)
    meta = sa.Column(JSONB, nullable=True)
    task_id = sa.Column(
        UUIDType(binary=False),
        sa.ForeignKey('task.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True,
    )

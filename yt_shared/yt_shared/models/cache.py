import uuid

import sqlalchemy as sa
from sqlalchemy_utils import Timestamp, UUIDType

from yt_shared.db.session import Base


class Cache(Base, Timestamp):
    """Telegram file cache model."""

    id = sa.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    cache_id = sa.Column(sa.String, nullable=False)
    cache_unique_id = sa.Column(sa.String, nullable=False)
    file_size = sa.Column(sa.BigInteger, nullable=False)
    date_timestamp = sa.Column(sa.DateTime, nullable=False)
    file_id = sa.Column(
        UUIDType(binary=False),
        sa.ForeignKey('file.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True,
    )

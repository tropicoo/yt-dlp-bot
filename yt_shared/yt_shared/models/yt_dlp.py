import datetime

import sqlalchemy as sa
from sqlalchemy import func

from yt_shared.db.session import Base


class YTDLP(Base):
    __tablename__ = 'yt_dlp'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True, nullable=False)
    current_version = sa.Column(sa.String, nullable=False)
    updated_at = sa.Column(
        sa.DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=func.now(),
    )

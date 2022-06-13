import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import Field, StrictStr

from yt_shared.constants import TaskSource
from yt_shared.schemas.base import RealBaseModel


class VideoPayload(RealBaseModel):
    id: Optional[uuid.UUID]
    from_user_id: Optional[int]
    message_id: Optional[int]
    url: StrictStr
    source: TaskSource
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DownVideo(RealBaseModel):
    """Downloaded video object context."""

    title: StrictStr
    name: StrictStr
    meta: dict

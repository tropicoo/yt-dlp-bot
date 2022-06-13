import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import Field, StrictStr, root_validator

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
    thumb_name: Optional[str] = None
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    meta: dict

    @root_validator(pre=False)
    def _set_fields(cls, values: dict) -> dict:
        values['thumb_name'] = f'{values["name"]}.jpg'
        return values

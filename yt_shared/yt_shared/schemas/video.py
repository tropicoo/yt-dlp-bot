import uuid
from datetime import datetime, timezone

from pydantic import Field, StrictFloat, StrictInt, StrictStr, root_validator

from yt_shared.enums import TaskSource, TelegramChatType
from yt_shared.schemas.base import RealBaseModel


class VideoPayload(RealBaseModel):
    id: uuid.UUID | None
    from_chat_id: StrictInt | None
    from_chat_type: TelegramChatType | None
    from_user_id: StrictInt | None
    message_id: StrictInt | None
    url: StrictStr
    source: TaskSource
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DownVideo(RealBaseModel):
    """Downloaded video object context."""

    title: StrictStr
    name: StrictStr
    thumb_name: StrictStr | None = None
    duration: StrictFloat | None = None
    width: int | None = None
    height: int | None = None
    meta: dict
    filepath: StrictStr
    thumb_path: StrictStr | None = None
    root_path: StrictStr

    @root_validator(pre=False)
    def _set_fields(cls, values: dict) -> dict:
        if not values['thumb_name']:
            values['thumb_name'] = f'{values["name"]}-thumb.jpg'
        return values

import uuid
from typing import ClassVar

from pydantic import StrictStr, StrictInt
from pydantic.types import StrictFloat

from yt_shared.enums import RabbitPayloadType, TelegramChatType
from yt_shared.schemas.base import BaseRabbitPayloadModel
from yt_shared.schemas.video import VideoPayload


class SuccessPayload(BaseRabbitPayloadModel):
    _TYPE: ClassVar = RabbitPayloadType.SUCCESS

    type: RabbitPayloadType = _TYPE
    task_id: uuid.UUID
    from_chat_id: StrictInt | None
    from_chat_type: TelegramChatType | None
    from_user_id: StrictInt | None
    message_id: StrictInt | None
    title: StrictStr
    filename: StrictStr
    thumb_name: StrictStr
    duration: StrictFloat | None
    width: StrictInt | None
    height: StrictInt | None
    context: VideoPayload

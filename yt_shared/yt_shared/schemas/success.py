import uuid
from typing import ClassVar

from pydantic import StrictInt, StrictStr

from yt_shared.enums import RabbitPayloadType, TelegramChatType
from yt_shared.schemas.base import BaseRabbitPayloadModel
from yt_shared.schemas.media import DownMedia, IncomingMediaPayload


class SuccessPayload(BaseRabbitPayloadModel):
    _TYPE: ClassVar = RabbitPayloadType.SUCCESS

    type: RabbitPayloadType = _TYPE
    task_id: uuid.UUID
    from_chat_id: StrictInt | None
    from_chat_type: TelegramChatType | None
    from_user_id: StrictInt | None
    message_id: StrictInt | None
    media: DownMedia
    context: IncomingMediaPayload
    yt_dlp_version: StrictStr | None

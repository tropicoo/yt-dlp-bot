import uuid
from typing import Literal

from pydantic import StrictInt, StrictStr

from yt_shared.enums import RabbitPayloadType, TelegramChatType
from yt_shared.schemas.base import BaseRabbitPayloadModel
from yt_shared.schemas.media import DownMedia, IncomingMediaPayload


class SuccessPayload(BaseRabbitPayloadModel):
    """Payload with downloaded media context."""

    type: Literal[RabbitPayloadType.SUCCESS] = RabbitPayloadType.SUCCESS
    task_id: uuid.UUID
    from_chat_id: StrictInt | None
    from_chat_type: TelegramChatType | None
    from_user_id: StrictInt | None
    message_id: StrictInt | None
    media: DownMedia
    context: IncomingMediaPayload
    yt_dlp_version: StrictStr | None

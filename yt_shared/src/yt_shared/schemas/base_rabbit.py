from abc import ABC

from yt_shared.enums import TelegramChatType
from yt_shared.schemas.base import StrictBaseRabbitPayloadModel
from yt_shared.schemas.media import InbMediaPayload


class BaseRabbitDownloadPayload(StrictBaseRabbitPayloadModel, ABC):
    context: InbMediaPayload
    from_chat_id: int | None
    from_chat_type: TelegramChatType | None
    from_user_id: int | None
    message_id: int | None

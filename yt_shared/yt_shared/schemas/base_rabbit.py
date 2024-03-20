import abc

from pydantic import StrictInt

from yt_shared.enums import TelegramChatType
from yt_shared.schemas.base import BaseRabbitPayloadModel
from yt_shared.schemas.media import InbMediaPayload


class BaseRabbitDownloadPayload(BaseRabbitPayloadModel, abc.ABC):
    context: InbMediaPayload
    from_chat_id: StrictInt | None
    from_chat_type: TelegramChatType | None
    from_user_id: StrictInt | None
    message_id: StrictInt | None

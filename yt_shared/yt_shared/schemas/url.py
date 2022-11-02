from pydantic import StrictInt, StrictStr

from yt_shared.enums import TelegramChatType
from yt_shared.schemas.base import RealBaseModel


class URL(RealBaseModel):
    url: StrictStr
    from_chat_id: StrictInt
    from_chat_type: TelegramChatType
    from_user_id: StrictInt
    message_id: StrictInt

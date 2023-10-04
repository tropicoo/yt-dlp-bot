from pydantic import StrictBool, StrictInt, StrictStr

from yt_shared.enums import DownMediaType, TelegramChatType
from yt_shared.schemas.base import RealBaseModel


class URL(RealBaseModel):
    url: StrictStr
    original_url: StrictStr
    from_chat_id: StrictInt
    from_chat_type: TelegramChatType
    from_user_id: StrictInt | None
    message_id: StrictInt
    ack_message_id: StrictInt
    save_to_storage: StrictBool
    download_media_type: DownMediaType

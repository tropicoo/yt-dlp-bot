from pydantic import ConfigDict

from yt_shared.enums import DownMediaType, TelegramChatType
from yt_shared.schemas.base import StrictRealBaseModel


class URL(StrictRealBaseModel):
    model_config = ConfigDict(**StrictRealBaseModel.model_config, frozen=True)

    url: str
    original_url: str
    from_chat_id: int
    from_chat_type: TelegramChatType
    from_user_id: int | None
    message_id: int
    ack_message_id: int
    save_to_storage: bool
    download_media_type: DownMediaType

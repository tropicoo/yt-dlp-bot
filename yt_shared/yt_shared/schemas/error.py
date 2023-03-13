import uuid
from typing import Literal

from pydantic import StrictInt, StrictStr

from yt_shared.enums import RabbitPayloadType, TelegramChatType
from yt_shared.schemas.base import BaseRabbitPayloadModel
from yt_shared.schemas.media import IncomingMediaPayload


class ErrorGeneralPayload(BaseRabbitPayloadModel):
    type: Literal[RabbitPayloadType.GENERAL_ERROR] = RabbitPayloadType.GENERAL_ERROR
    task_id: uuid.UUID | StrictStr | None
    from_chat_id: StrictInt | None
    from_chat_type: TelegramChatType | None
    from_user_id: StrictInt | None
    message_id: StrictInt | None
    message: StrictStr
    url: StrictStr
    context: IncomingMediaPayload
    exception_msg: StrictStr
    exception_type: StrictStr
    yt_dlp_version: StrictStr | None


class ErrorDownloadPayload(ErrorGeneralPayload):
    type: Literal[RabbitPayloadType.DOWNLOAD_ERROR] = RabbitPayloadType.DOWNLOAD_ERROR
    task_id: uuid.UUID

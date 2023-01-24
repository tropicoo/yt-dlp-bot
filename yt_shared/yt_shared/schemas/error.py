import uuid
from typing import ClassVar

from pydantic import StrictInt, StrictStr

from yt_shared.enums import RabbitPayloadType, TelegramChatType
from yt_shared.schemas.base import BaseRabbitPayloadModel
from yt_shared.schemas.video import VideoPayload


class ErrorGeneralPayload(BaseRabbitPayloadModel):
    _TYPE: ClassVar = RabbitPayloadType.GENERAL_ERROR

    type: RabbitPayloadType = _TYPE
    task_id: uuid.UUID | StrictStr | None
    from_chat_id: StrictInt | None
    from_chat_type: TelegramChatType | None
    from_user_id: StrictInt | None
    message_id: StrictInt | None
    message: StrictStr
    url: StrictStr
    context: VideoPayload
    exception_msg: StrictStr
    exception_type: StrictStr
    yt_dlp_version: StrictStr | None


class ErrorDownloadPayload(ErrorGeneralPayload):
    _TYPE: ClassVar = RabbitPayloadType.DOWNLOAD_ERROR

    type: RabbitPayloadType = _TYPE
    task_id: uuid.UUID

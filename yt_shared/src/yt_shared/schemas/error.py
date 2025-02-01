import uuid
from typing import Literal

from yt_shared.enums import RabbitPayloadType
from yt_shared.schemas.base_rabbit import BaseRabbitDownloadPayload


class ErrorDownloadGeneralPayload(BaseRabbitDownloadPayload):
    type: Literal[RabbitPayloadType.GENERAL_ERROR] = RabbitPayloadType.GENERAL_ERROR
    task_id: uuid.UUID | str | None
    message: str
    url: str
    exception_msg: str
    exception_type: str
    yt_dlp_version: str | None


class ErrorDownloadPayload(ErrorDownloadGeneralPayload):
    type: Literal[RabbitPayloadType.DOWNLOAD_ERROR] = RabbitPayloadType.DOWNLOAD_ERROR
    task_id: uuid.UUID

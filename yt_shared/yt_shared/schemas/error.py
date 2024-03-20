import uuid
from typing import Literal

from pydantic import StrictStr

from yt_shared.enums import RabbitPayloadType
from yt_shared.schemas.base_rabbit import BaseRabbitDownloadPayload


class ErrorDownloadGeneralPayload(BaseRabbitDownloadPayload):
    type: Literal[RabbitPayloadType.GENERAL_ERROR] = RabbitPayloadType.GENERAL_ERROR
    task_id: uuid.UUID | StrictStr | None
    message: StrictStr
    url: StrictStr
    exception_msg: StrictStr
    exception_type: StrictStr
    yt_dlp_version: StrictStr | None


class ErrorDownloadPayload(ErrorDownloadGeneralPayload):
    type: Literal[RabbitPayloadType.DOWNLOAD_ERROR] = RabbitPayloadType.DOWNLOAD_ERROR
    task_id: uuid.UUID

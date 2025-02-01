import uuid
from typing import Literal

from pydantic import StrictStr

from yt_shared.enums import RabbitPayloadType
from yt_shared.schemas.base_rabbit import BaseRabbitDownloadPayload
from yt_shared.schemas.media import DownMedia


class SuccessDownloadPayload(BaseRabbitDownloadPayload):
    """Payload with downloaded media context."""

    type: Literal[RabbitPayloadType.SUCCESS] = RabbitPayloadType.SUCCESS
    task_id: uuid.UUID
    media: DownMedia
    yt_dlp_version: StrictStr | None

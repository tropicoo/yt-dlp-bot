import uuid
from typing import Optional

from pydantic import StrictStr

from yt_shared.schemas.base import RealBaseModel


class ErrorPayload(RealBaseModel):
    task_id: uuid.UUID
    from_user_id: Optional[int]
    message_id: Optional[int]
    message: StrictStr
    url: StrictStr
    original_body: dict
    exception_msg: StrictStr
    exception_type: StrictStr
    yt_dlp_version: Optional[StrictStr]

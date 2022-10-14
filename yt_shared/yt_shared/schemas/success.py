import uuid
from typing import Optional

from pydantic import StrictStr

from yt_shared.schemas.base import RealBaseModel
from yt_shared.schemas.video import VideoPayload


class SuccessPayload(RealBaseModel):
    task_id: uuid.UUID
    from_user_id: Optional[int]
    message_id: Optional[int]
    title: StrictStr
    filename: StrictStr
    thumb_name: StrictStr
    duration: Optional[int]
    width: Optional[int]
    height: Optional[int]
    context: VideoPayload

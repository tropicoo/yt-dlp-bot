import uuid
from typing import Optional

from pydantic import StrictStr

from yt_shared.schemas.base import RealBaseModel


class SuccessPayload(RealBaseModel):
    task_id: uuid.UUID
    from_user_id: Optional[int]
    message_id: Optional[int]
    filename: StrictStr

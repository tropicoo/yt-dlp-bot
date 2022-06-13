from pydantic import StrictStr

from yt_shared.schemas.base import RealBaseModel


class URL(RealBaseModel):
    url: StrictStr
    from_user_id: int
    message_id: int

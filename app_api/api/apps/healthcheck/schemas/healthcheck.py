from typing import Literal

from yt_shared.schemas.base import StrictRealBaseModel


class HealthcheckSchema(StrictRealBaseModel):
    status: Literal['OK'] = 'OK'

from pydantic import StrictStr

from yt_shared.schemas.base import RealBaseModel


class HealthcheckSchema(RealBaseModel):
    status: StrictStr = 'OK'

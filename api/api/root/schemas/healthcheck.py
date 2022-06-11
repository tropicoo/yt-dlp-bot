from yt_shared.schemas.base import RealBaseModel


class HealthcheckSchema(RealBaseModel):
    status: str = 'OK'

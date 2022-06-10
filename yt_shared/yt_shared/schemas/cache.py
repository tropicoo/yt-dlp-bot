import datetime

from yt_shared.schemas.base import RealBaseModel


class CacheSchema(RealBaseModel):
    cache_id: str
    cache_unique_id: str
    file_size: int
    date_timestamp: datetime.datetime

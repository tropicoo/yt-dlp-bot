from yt_shared.schemas.base import RealBaseModel
from yt_shared.schemas.ytdlp import Current, Latest


class YTDLPLatestVersion(RealBaseModel):
    latest: Latest
    current: Current
    need_upgrade: bool

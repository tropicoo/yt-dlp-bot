from yt_shared.schemas.base import RealBaseModel
from yt_shared.schemas.ytdlp import CurrentVersion, LatestVersion


class YTDLPLatestVersion(RealBaseModel):
    latest: LatestVersion
    current: CurrentVersion
    need_upgrade: bool

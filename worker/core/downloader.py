import logging

import yt_dlp
from pydantic import StrictStr

from yt_shared.schemas.base import RealBaseModel

try:
    from ytdl_opts.user import YTDL_OPTS
except ImportError:
    from ytdl_opts.default import YTDL_OPTS


class DownVideo(RealBaseModel):
    """Downloaded video object context."""

    name: StrictStr
    ext: StrictStr
    meta: dict


class VideoDownloader:

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    def download_video(self, url: str) -> DownVideo:
        return self._download(url)

    def _download(self, url: str) -> DownVideo:
        self._log.info('Downloading %s', url)
        with yt_dlp.YoutubeDL(YTDL_OPTS) as ytdl:
            info = ytdl.extract_info(url, download=False)
            info_sanitized = ytdl.sanitize_info(info)
            ytdl.download(url)
        self._log.info('Finished downloading %s', url)
        return DownVideo(name=info_sanitized['title'],
                         ext=info_sanitized['ext'],
                         meta=info_sanitized)

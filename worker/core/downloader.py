import logging
import os

import yt_dlp
from pydantic import StrictStr

from yt_shared.config import STORAGE_PATH
from yt_shared.schemas.base import RealBaseModel


class DownVideo(RealBaseModel):
    name: StrictStr
    ext: StrictStr
    meta: dict


class VideoDownloader:
    YTDL_OPTS = {
        'outtmpl': os.path.join(STORAGE_PATH, '%(title)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'noplaylist': True,
    }

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    def download_video(self, url: str) -> DownVideo:
        return self._download(url)

    def _download(self, url: str) -> DownVideo:
        with yt_dlp.YoutubeDL(self.YTDL_OPTS) as ytdl:
            info = ytdl.extract_info(url, download=False)
            info_sanitized = ytdl.sanitize_info(info)
            ytdl.download(url)
        return DownVideo(name=info_sanitized['title'],
                               ext=info_sanitized['ext'],
                               meta=info_sanitized)

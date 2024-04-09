import datetime
import logging

import aiohttp
from yt_shared.schemas.ytdlp import LatestVersion


class YtdlpGithubClient:
    """yt-dlp Github version number checker."""

    LATEST_TAG_URL = 'https://github.com/yt-dlp/yt-dlp/releases/latest'

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    async def get_latest_version(self) -> LatestVersion:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.LATEST_TAG_URL) as resp:
                version = resp.url.parts[-1]
                self._log.info('Latest yt-dlp version: %s', version)
                return LatestVersion(
                    version=version, retrieved_at=datetime.datetime.utcnow()
                )

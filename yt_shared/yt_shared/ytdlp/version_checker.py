import datetime
import logging

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from yt_shared.repositories.ytdlp import YtdlpRepository
from yt_shared.schemas.ytdlp import Current, Latest


class VersionChecker:
    """yt-dlp version number checker."""

    LATEST_TAG_URL = 'https://github.com/yt-dlp/yt-dlp/releases/latest'
    REPOSITORY_CLS = YtdlpRepository

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    async def get_latest_version(self) -> Latest:
        self._log.info('Get latest yt-dlp version number')
        async with aiohttp.ClientSession() as session:
            async with session.get(self.LATEST_TAG_URL) as resp:
                version = resp.url.parts[-1]
                self._log.info('Latest yt-dlp version number: %s', version)
                return Latest(version=version,
                              retrieved_at=datetime.datetime.utcnow())

    async def get_current_version(self, db: AsyncSession) -> Current:
        self._log.info('Get current yt-dlp version number')
        ytdlp_ = await self.REPOSITORY_CLS().get_current_version(db)
        self._log.info('Current yt-dlp version number: %s',
                       ytdlp_.current_version)
        return Current.from_orm(ytdlp_)

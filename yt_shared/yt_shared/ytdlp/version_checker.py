import asyncio
import datetime
import logging

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.repositories.ytdlp import YtdlpRepository
from yt_shared.schemas.ytdlp import CurrentVersion, LatestVersion, VersionContext


class YtdlpVersionChecker:
    """yt-dlp version number checker."""

    LATEST_TAG_URL = 'https://github.com/yt-dlp/yt-dlp/releases/latest'

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._ytdlp_repository = YtdlpRepository()

    async def get_version_context(self, db: AsyncSession) -> VersionContext:
        latest, current = await asyncio.gather(
            self.get_latest_version(), self.get_current_version(db)
        )
        return VersionContext(latest=latest, current=current)

    async def get_latest_version(self) -> LatestVersion:
        self._log.info('Get latest yt-dlp version')
        async with aiohttp.ClientSession() as session:
            async with session.get(self.LATEST_TAG_URL) as resp:
                version = resp.url.parts[-1]
                self._log.info('Latest yt-dlp version: %s', version)
                return LatestVersion(
                    version=version, retrieved_at=datetime.datetime.utcnow()
                )

    async def get_current_version(self, db: AsyncSession) -> CurrentVersion:
        self._log.info('Get current yt-dlp version')
        ytdlp_ = await self._ytdlp_repository.get_current_version(db)
        self._log.info('Current yt-dlp version: %s', ytdlp_.current_version)
        return CurrentVersion.from_orm(ytdlp_)

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.clients.github import YtdlpGithubClient
from yt_shared.repositories.ytdlp import YtdlpRepository
from yt_shared.schemas.ytdlp import CurrentVersion, LatestVersion, VersionContext


class YtdlpVersionChecker:
    """yt-dlp version number checker."""

    LATEST_TAG_URL = 'https://github.com/yt-dlp/yt-dlp/releases/latest'

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._ytdlp_repository = YtdlpRepository()
        self._ytdlp_client = YtdlpGithubClient()

    async def get_version_context(self, db: AsyncSession) -> VersionContext:
        latest, current = await asyncio.gather(
            self.get_latest_version(), self.get_current_version(db)
        )
        return VersionContext(latest=latest, current=current)

    async def get_latest_version(self) -> LatestVersion:
        return await self._ytdlp_client.get_latest_version()

    async def get_current_version(self, db: AsyncSession) -> CurrentVersion:
        ytdlp_ = await self._ytdlp_repository.get_current_version(db)
        self._log.info('Current yt-dlp version: %s', ytdlp_.current_version)
        return CurrentVersion.model_validate(ytdlp_)

import asyncio
import logging

from yt_shared.clients.github import YtdlpGithubClient
from yt_shared.repositories.ytdlp import YtdlpRepository
from yt_shared.schemas.ytdlp import CurrentVersion, LatestVersion, VersionContext


class YtdlpVersionChecker:
    """yt-dlp version number checker."""

    def __init__(self, client: YtdlpGithubClient, repository: YtdlpRepository) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._ytdlp_repository = repository
        self._ytdlp_client = client

    async def get_version_context(self) -> VersionContext:
        latest, current = await asyncio.gather(
            self.get_latest_version(), self.get_current_version()
        )
        return VersionContext(latest=latest, current=current)

    async def get_latest_version(self) -> LatestVersion:
        latest_version = await self._ytdlp_client.get_latest_version()
        self._log.info('Latest yt-dlp version: %s', latest_version.version)
        return latest_version

    async def get_current_version(self) -> CurrentVersion:
        ytdlp_ = await self._ytdlp_repository.get_current_version()
        self._log.info('Current yt-dlp version: %s', ytdlp_.current_version)
        return CurrentVersion.model_validate(ytdlp_)

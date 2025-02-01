import datetime
import logging
from typing import Final

import aiohttp
from yt_shared.enums import YtdlpReleaseChannelType
from yt_shared.schemas.ytdlp import LatestVersion


class YtdlpGithubClient:
    """yt-dlp Github version number checker."""

    LATEST_TAG_URL_TPL: Final[str] = (
        'https://github.com/yt-dlp/{repository}/releases/latest'
    )
    LATEST_TAG_REPOSITORY_MAP: Final[dict[YtdlpReleaseChannelType, str]] = {
        YtdlpReleaseChannelType.STABLE: 'yt-dlp',
        YtdlpReleaseChannelType.NIGHTLY: 'yt-dlp-nightly-builds',
        YtdlpReleaseChannelType.MASTER: 'yt-dlp-master-builds',
    }

    def __init__(self, release_channel: YtdlpReleaseChannelType) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._release_channel = release_channel

    async def get_latest_version(self) -> LatestVersion:
        tag_url = self.LATEST_TAG_URL_TPL.format(
            repository=self.LATEST_TAG_REPOSITORY_MAP[self._release_channel]
        )
        async with aiohttp.ClientSession() as session, session.get(tag_url) as resp:
            version = resp.url.parts[-1]
            return LatestVersion(
                version=version, retrieved_at=datetime.datetime.now(datetime.UTC)
            )

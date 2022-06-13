import asyncio
import datetime
from typing import TYPE_CHECKING

from pyrogram.enums import ParseMode

from core.tasks.abstract import AbstractTask
from core.utils import bold, code
from yt_shared.config import YTDLP_VERSION_CHECK_INTERVAL
from yt_shared.db import get_db
from yt_shared.emoji import INFORMATION_EMOJI
from yt_shared.schemas.ytdlp import VersionContext
from yt_shared.ytdlp.version_checker import VersionChecker

if TYPE_CHECKING:
    from core.bot import VideoBot


class YtdlpNewVersionNotifyTask(AbstractTask):
    def __init__(self, bot: 'VideoBot') -> None:
        super().__init__()
        self._bot = bot
        self._version_checker = VersionChecker()
        self._startup_message_sent = False

    async def run(self) -> None:
        while True:
            self._log.info('Checking for new yt-dlp version')
            try:
                await self._notify_if_new_version()
            except Exception:
                self._log.exception('Failed check new yt-dlp version')
            self._log.info(
                'Next yt-dlp version check planned at %s',
                self._get_next_check_datetime().isoformat(' '),
            )
            await asyncio.sleep(YTDLP_VERSION_CHECK_INTERVAL)

    @staticmethod
    def _get_next_check_datetime() -> datetime.datetime:
        return (
            datetime.datetime.now()
            + datetime.timedelta(seconds=YTDLP_VERSION_CHECK_INTERVAL)
        ).replace(microsecond=0)

    async def _notify_if_new_version(self) -> None:
        async for db in get_db():
            context = await self._version_checker.get_version_context(db)
            if context.has_new_version:
                await self._notify_outdated(context)
            elif not self._startup_message_sent:
                await self._notify_up_to_date(context)
                self._startup_message_sent = True

    async def _notify_outdated(self, ctx: VersionContext) -> None:
        text = (
            f'New {code("yt-dlp")} version available: {bold(ctx.latest.version)}\n'
            f'Current version: {bold(ctx.current.version)}\n'
            f'Rebuild worker with {code("docker-compose build --no-cache worker")}'
        )
        await self._send_to_chat(text)

    async def _notify_up_to_date(self, ctx: VersionContext) -> None:
        """Send startup message that yt-dlp version is up to date."""
        text = (
            f'{INFORMATION_EMOJI} Your {code("yt-dlp")} version '
            f'{bold(ctx.current.version)} is up to date, have fun'
        )
        await self._send_to_chat(text)

    async def _send_to_chat(self, text: str) -> None:
        await self._bot.send_message_all(text)

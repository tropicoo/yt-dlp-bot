import asyncio
import datetime
from typing import TYPE_CHECKING

from yt_shared.db.session import get_db
from yt_shared.emoji import INFORMATION_EMOJI
from yt_shared.schemas.ytdlp import VersionContext
from yt_shared.utils.tasks.abstract import AbstractTask
from yt_shared.ytdlp.version_checker import YtdlpVersionChecker

from bot.core.config.config import get_main_config
from bot.core.utils import bold, code

if TYPE_CHECKING:
    from bot.bot import VideoBotClient


class YtdlpNewVersionNotifyTask(AbstractTask):
    def __init__(self, bot: 'VideoBotClient') -> None:
        super().__init__()
        self._bot = bot
        self._version_checker = YtdlpVersionChecker()
        self._startup_message_sent = False

        ytdlp_conf = get_main_config().ytdlp
        self._version_check_enabled = ytdlp_conf.version_check_enabled
        self._version_check_interval = ytdlp_conf.version_check_interval
        self._notify_users_on_new_version = ytdlp_conf.notify_users_on_new_version

    async def run(self) -> None:
        await self._run()

    async def _run(self) -> None:
        if not self._version_check_enabled:
            self._log.info('New "yt-dlp" version check disabled, exiting from task')
            return

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
            await asyncio.sleep(self._version_check_interval)

    def _get_next_check_datetime(self) -> datetime.datetime:
        return (
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=self._version_check_interval)
        ).replace(microsecond=0)

    async def _notify_if_new_version(self) -> None:
        async for db in get_db():
            context = await self._version_checker.get_version_context(db)
            if context.has_new_version and self._notify_users_on_new_version:
                await self._notify_outdated(context)
                return

            if not self._startup_message_sent:
                await self._notify_up_to_date(
                    context, user_ids=self._bot.get_startup_users()
                )
                self._startup_message_sent = True

    async def _notify_outdated(self, ctx: VersionContext) -> None:
        text = (
            f'New {code("yt-dlp")} version available: {bold(ctx.latest.version)}\n'
            f'Current version: {bold(ctx.current.version)}\n'
            f'Rebuild worker with {code("docker compose build --no-cache worker")}'
        )
        await self._bot.send_message_admins(text)

    async def _notify_up_to_date(
        self, ctx: VersionContext, user_ids: list[int]
    ) -> None:
        """Send startup message that yt-dlp version is up to date."""
        text = (
            f'{INFORMATION_EMOJI} Your {code("yt-dlp")} version '
            f'{bold(ctx.current.version)} is up to date, have fun'
        )
        await self._bot.send_message_to_users(text=text, user_ids=user_ids)

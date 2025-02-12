import asyncio
import datetime
from typing import TYPE_CHECKING

from yt_shared.clients.github import YtdlpGithubClient
from yt_shared.db.session import get_db
from yt_shared.emoji import INFORMATION_EMOJI
from yt_shared.repositories.ytdlp import YtdlpRepository
from yt_shared.schemas.ytdlp import VersionContext
from yt_shared.utils.tasks.abstract import AbstractTask
from yt_shared.ytdlp.version_checker import YtdlpVersionChecker

from bot.core.config.config import get_main_config
from bot.core.utils import bold, code

if TYPE_CHECKING:
    from bot.bot.client import VideoBotClient


class YtdlpNewVersionNotifyTask(AbstractTask):
    def __init__(self, bot: 'VideoBotClient') -> None:
        super().__init__()
        self._bot = bot
        self._startup_message_sent = False
        self._ytdlp_conf = get_main_config().ytdlp

    async def run(self) -> None:
        await self._run()

    async def _run(self) -> None:
        release_channel = self._ytdlp_conf.release_channel
        if not self._ytdlp_conf.version_check_enabled:
            self._log.info(
                'New %s "yt-dlp" version check disabled, exiting from task',
                release_channel,
            )
            return

        while True:
            self._log.info('Checking for new %s yt-dlp version', release_channel)
            try:
                await self._notify_if_new_version()
            except Exception:
                self._log.exception(
                    'Failed check new %s yt-dlp version', release_channel
                )
            self._log.info(
                'Next %s yt-dlp version check planned at %s',
                release_channel,
                self._get_next_check_datetime().isoformat(' '),
            )
            await asyncio.sleep(self._ytdlp_conf.version_check_interval)

    def _get_next_check_datetime(self) -> datetime.datetime:
        return (
            datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(seconds=self._ytdlp_conf.version_check_interval)
        ).replace(microsecond=0)

    async def _notify_if_new_version(self) -> None:
        async for db in get_db():
            context = await YtdlpVersionChecker(
                client=YtdlpGithubClient(self._ytdlp_conf.release_channel),
                repository=YtdlpRepository(db),
            ).get_version_context()
            if context.has_new_version:
                self._log.info('yt-dlp has new version: %s', context.latest.version)
                if self._ytdlp_conf.notify_users_on_new_version:
                    await self._notify_outdated(context)
                    return

            if not self._startup_message_sent:
                await self._notify_up_to_date(
                    context, user_ids=self._bot.get_startup_users()
                )
                self._startup_message_sent = True

    async def _notify_outdated(self, ctx: VersionContext) -> None:
        text = (
            f'New {bold(self._ytdlp_conf.release_channel)} {code("yt-dlp")} version available: '
            f'{bold(ctx.latest.version)}\n'
            f'Current version: {bold(ctx.current.version)}\n'
            f'Rebuild worker with {code("docker compose build --no-cache yt_worker && docker compose up -d -t 0 yt_worker")}'
        )
        await self._bot.send_message_admins(text)

    async def _notify_up_to_date(
        self, ctx: VersionContext, user_ids: list[int]
    ) -> None:
        """Send startup message that yt-dlp version is up-to-date."""
        text = (
            f'{INFORMATION_EMOJI} Your {bold(self._ytdlp_conf.release_channel)} {code("yt-dlp")} '
            f'version {bold(ctx.current.version)} is up to date, have fun'
        )
        await self._bot.send_message_to_users(text=text, user_ids=user_ids)

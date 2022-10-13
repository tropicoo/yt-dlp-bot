import asyncio
import logging

from pyrogram import Client
from pyrogram.enums import ParseMode

from core.config.config import get_main_config
from core.utils import bold


class VideoBot(Client):
    """Extended Pyrogram's `Client` class."""

    def __init__(self) -> None:
        conf = get_main_config()
        super().__init__(
            name='default_name',
            api_id=conf.telegram.api_id,
            api_hash=conf.telegram.api_hash,
            bot_token=conf.telegram.token,
        )
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.info('Initializing bot client')

        self.user_ids: list[int] = conf.telegram.allowed_user_ids

    @staticmethod
    async def run_forever() -> None:
        """Firstly 'await bot.start()' should be called."""
        while True:
            await asyncio.sleep(86400)

    async def send_startup_message(self) -> None:
        """Send welcome message after bot launch."""
        self._log.info('Sending welcome message')
        await self.send_message_all(
            f'✨ {bold((await self.get_me()).first_name)} started, paste video URL to '
            f'start download'
        )

    async def send_message_all(
        self, text: str, parse_mode: ParseMode = ParseMode.HTML
    ) -> None:
        """Send message to all defined user IDs in config.json."""
        for user_id in self.user_ids:
            try:
                await self.send_message(user_id, text, parse_mode=parse_mode)
            except Exception:
                self._log.exception(
                    'Failed to send message "%s" to user ID %s', text, user_id
                )

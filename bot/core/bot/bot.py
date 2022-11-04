import asyncio
import logging

from core.config.config import get_main_config
from core.config.schema import UserSchema
from core.utils import bold
from pyrogram import Client
from pyrogram.enums import ParseMode


class VideoBot(Client):
    """Extended Pyrogram's `Client` class."""

    def __init__(self) -> None:
        self.conf = get_main_config()
        super().__init__(
            name='default_name',
            api_id=self.conf.telegram.api_id,
            api_hash=self.conf.telegram.api_hash,
            bot_token=self.conf.telegram.token,
        )
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.info('Initializing bot client')

        self.allowed_users: dict[int, UserSchema] = {
            user.id: user for user in self.conf.telegram.allowed_users
        }

    async def run_forever(self) -> None:
        """Firstly 'await bot.start()' should be called."""
        if not self.is_initialized:
            raise RuntimeError('Bot was not started (initialized).')
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
        for user_id in self.allowed_users:
            try:
                await self.send_message(user_id, text, parse_mode=parse_mode)
            except Exception:
                self._log.exception(
                    'Failed to send message "%s" to user ID %s', text, user_id
                )

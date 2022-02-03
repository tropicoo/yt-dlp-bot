import asyncio
import logging
from typing import Optional

from aiogram import Dispatcher

from core.bot.bot import VideoBot
from core.bot.setup import BotSetup
from core.config.config import get_main_config
from yt_shared.rabbit import get_rabbitmq
from yt_shared.task_utils.tasks import create_task


class BotLauncher:
    """Bot launcher which parses configuration file, creates bot with
    camera instances and finally starts the bot.
    """

    def __init__(self) -> None:
        """Constructor."""
        self._log = logging.getLogger(self.__class__.__name__)
        logging.getLogger().setLevel(get_main_config().log_level)

        self._setup: Optional[BotSetup] = None
        self._bot: Optional[VideoBot] = None
        self._dispatcher: Optional[Dispatcher] = None

        self._rabbit_mq = get_rabbitmq()

    async def run(self) -> None:
        """Run bot."""
        await self._setup_rabbit()
        await self._setup_bot()
        await self._start_bot()

    async def _setup_rabbit(self) -> None:
        task_name = f'Setup RabbitMQ Task ({self._rabbit_mq.__class__.__name__})'
        await create_task(
            self._rabbit_mq.register(),
            task_name=task_name,
            logger=self._log,
            exception_message='Task %s raised an exception',
            exception_message_args=(task_name,),
        )

    async def _setup_bot(self) -> None:
        self._setup = BotSetup()
        self._bot = self._setup.get_bot()
        self._dispatcher = self._setup.get_dispatcher()

    async def _start_bot(self) -> None:
        """Start telegram bot and related processes."""
        self._log.info('Starting %s bot', (await self._bot.me).first_name)
        await self._bot.start_tasks()
        await self._bot.send_startup_message()

        # TODO: Look into aiogram `executor`.
        try:
            await self._dispatcher.start_polling()
        finally:
            await asyncio.gather(self._dispatcher.bot.close(),
                                 self._rabbit_mq.close())

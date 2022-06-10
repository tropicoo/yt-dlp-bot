import asyncio
import logging

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from core.bot import VideoBot
from core.callbacks import TelegramCallback
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
        self._bot = VideoBot()
        self._rabbit_mq = get_rabbitmq()

    async def run(self) -> None:
        """Run bot."""
        await self._setup_rabbit()
        await self._setup_handlers()
        await self._start_bot()

    async def _setup_handlers(self):
        cb = TelegramCallback()
        self._bot.add_handler(
            MessageHandler(
                cb.on_message,
                filters=filters.user(self._bot.user_ids) & filters.private,
            ),
        )

    async def _setup_rabbit(self) -> None:
        task_name = f'Setup RabbitMQ Task ({self._rabbit_mq.__class__.__name__})'
        await create_task(
            self._rabbit_mq.register(),
            task_name=task_name,
            logger=self._log,
            exception_message='Task %s raised an exception',
            exception_message_args=(task_name,),
        )

    async def _start_bot(self) -> None:
        """Start telegram bot and related processes."""
        await self._bot.start()

        self._log.info('Starting %s bot', (await self._bot.get_me()).first_name)
        await self._bot.start_tasks()
        await self._bot.send_startup_message()
        await self._run_bot_forever()

    @staticmethod
    async def _run_bot_forever() -> None:
        while True:
            await asyncio.sleep(86400)

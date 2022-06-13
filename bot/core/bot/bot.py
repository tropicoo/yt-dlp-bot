import logging

from pyrogram import Client

from core.config.config import get_main_config
from core.tasks.manager import RabbitWorkerManager
from core.tasks.ytdlp import YtdlpNewVersionNotifyTask
from core.utils import bold
from yt_shared.rabbit import get_rabbitmq
from yt_shared.task_utils.tasks import create_task


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
        self.rabbit_mq = get_rabbitmq()
        self.rabbit_worker_manager = RabbitWorkerManager(bot=self)

    async def start_tasks(self):
        await self.rabbit_worker_manager.start_worker_tasks()

        task_name = YtdlpNewVersionNotifyTask.__class__.__name__
        create_task(
            YtdlpNewVersionNotifyTask(bot=self).run(),
            task_name=task_name,
            logger=self._log,
            exception_message='Task %s raised an exception',
            exception_message_args=(task_name,),
        )

    async def send_startup_message(self) -> None:
        """Send welcome message after bot launch."""
        self._log.info('Sending welcome message')
        await self.send_message_all(
            f'✨ {bold((await self.get_me()).first_name)} started, paste video URL to '
            f'start download'
        )

    async def send_message_all(self, msg: str) -> None:
        """Send message to all defined user IDs in config.json."""
        for user_id in self.user_ids:
            try:
                await self.send_message(user_id, msg)
            except Exception:
                self._log.exception(
                    'Failed to send message "%s" to user ID ' '%s', msg, user_id
                )

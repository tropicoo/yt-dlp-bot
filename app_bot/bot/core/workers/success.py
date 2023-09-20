from yt_shared.rabbit.rabbit_config import SUCCESS_QUEUE
from yt_shared.schemas.success import SuccessDownloadPayload
from yt_shared.utils.tasks.tasks import create_task

from bot.core.handlers.success import SuccessDownloadHandler
from bot.core.workers.abstract import AbstractDownloadResultWorker, RabbitWorkerType


class SuccessDownloadResultWorker(AbstractDownloadResultWorker):
    TYPE = RabbitWorkerType.SUCCESS
    QUEUE_TYPE = SUCCESS_QUEUE
    SCHEMA_CLS = (SuccessDownloadPayload,)
    HANDLER_CLS = SuccessDownloadHandler

    async def _process_body(self, body: SuccessDownloadPayload) -> None:
        self._spawn_handler_task(body)

    def _spawn_handler_task(self, body: SuccessDownloadPayload) -> None:
        task_name = self.HANDLER_CLS.__class__.__name__
        create_task(
            self.HANDLER_CLS(body=body, bot=self._bot).handle(),
            task_name=task_name,
            logger=self._log,
            exception_message='Task "%s" raised an exception',
            exception_message_args=(task_name,),
        )

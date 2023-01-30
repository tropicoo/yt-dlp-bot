from yt_shared.rabbit.rabbit_config import ERROR_QUEUE
from yt_shared.schemas.error import ErrorDownloadPayload, ErrorGeneralPayload

from bot.core.handlers.error import ErrorHandler
from bot.core.workers.abstract import AbstractResultWorker, RabbitWorkerType


class ErrorResultWorker(AbstractResultWorker):
    TYPE = RabbitWorkerType.ERROR
    QUEUE_TYPE = ERROR_QUEUE
    SCHEMA_CLS = (ErrorDownloadPayload, ErrorGeneralPayload)
    HANDLER_CLS = ErrorHandler

    async def _process_body(
        self, body: ErrorDownloadPayload | ErrorGeneralPayload
    ) -> None:
        await self.HANDLER_CLS(body=body, bot=self._bot).handle()

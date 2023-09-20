from yt_shared.rabbit.rabbit_config import ERROR_QUEUE
from yt_shared.schemas.error import ErrorDownloadGeneralPayload, ErrorDownloadPayload

from bot.core.handlers.error import ErrorDownloadHandler
from bot.core.workers.abstract import AbstractDownloadResultWorker, RabbitWorkerType


class ErrorDownloadResultWorker(AbstractDownloadResultWorker):
    TYPE = RabbitWorkerType.ERROR
    QUEUE_TYPE = ERROR_QUEUE
    SCHEMA_CLS = (ErrorDownloadPayload, ErrorDownloadGeneralPayload)
    HANDLER_CLS = ErrorDownloadHandler

    async def _process_body(
        self, body: ErrorDownloadPayload | ErrorDownloadGeneralPayload
    ) -> None:
        await self.HANDLER_CLS(body=body, bot=self._bot).handle()

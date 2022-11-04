from core.handlers.error import ErrorHandler
from core.workers.abstract import AbstractResultWorker, RabbitWorkerType
from yt_shared.rabbit.rabbit_config import ERROR_QUEUE
from yt_shared.schemas.error import ErrorDownloadPayload, ErrorGeneralPayload


class ErrorResultWorker(AbstractResultWorker):
    TYPE = RabbitWorkerType.ERROR
    QUEUE_TYPE = ERROR_QUEUE
    SCHEMA_CLS = (ErrorDownloadPayload, ErrorGeneralPayload)
    HANDLER_CLS = ErrorHandler

    async def _process_body(
        self, body: ErrorDownloadPayload | ErrorGeneralPayload
    ) -> None:
        await self.HANDLER_CLS(body=body, bot=self._bot).handle()

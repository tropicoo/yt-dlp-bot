from core.handlers.success import SuccessHandler
from core.workers.abstract import AbstractResultWorker, RabbitTaskType
from yt_shared.rabbit.rabbit_config import SUCCESS_QUEUE
from yt_shared.schemas.success import SuccessPayload


class SuccessResultWorker(AbstractResultWorker):
    TYPE = RabbitTaskType.SUCCESS
    QUEUE_TYPE = SUCCESS_QUEUE
    SCHEMA_CLS = (SuccessPayload,)
    HANDLER_CLS = SuccessHandler

    async def _process_body(self, body: SuccessPayload) -> None:
        await self.HANDLER_CLS(body=body, bot=self._bot).handle()

from yt_shared.rabbit.rabbit_config import PROGRESS_QUEUE
from yt_shared.schemas.progress import ProgressPayload

from bot.core.handlers.progress import ProgressHandler
from bot.core.workers.abstract import AbstractDownloadResultWorker, RabbitWorkerType


class ProgressWorker(AbstractDownloadResultWorker):
    """Consumes progress updates and applies them to the status message.

    Updates are handled inline rather than in spawned tasks, so they cannot
    overtake each other and show a stale percentage.
    """

    TYPE = RabbitWorkerType.PROGRESS
    QUEUE_TYPE = PROGRESS_QUEUE
    SCHEMA_CLS = (ProgressPayload,)

    def __init__(self, bot) -> None:
        super().__init__(bot)
        self._handler = ProgressHandler(bot=bot)

    async def _process_body(self, body: ProgressPayload) -> None:
        await self._handler.handle(body)

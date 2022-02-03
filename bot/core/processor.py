import logging

from yt_shared.constants import TaskSource
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.video import VideoPayload


class IncomingURLProcessor:

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._publisher = Publisher()

    async def process(self, url: str, message_id: int) -> bool:
        return await self._send_to_worker(url, message_id)

    async def _send_to_worker(self, url: str, message_id: int) -> bool:
        payload = VideoPayload(url=url, message_id=message_id,
                               source=TaskSource.BOT)
        is_sent = await self._publisher.send_for_download(payload)
        if not is_sent:
            self._log.error('Failed to publish URL %s to message broker', url)
        return is_sent

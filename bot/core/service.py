import logging

from yt_shared.constants import TaskSource
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.url import URL
from yt_shared.schemas.video import VideoPayload


class URLService:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._publisher = Publisher()

    async def process_url(self, url: URL) -> bool:
        return await self._send_to_worker(url)

    async def _send_to_worker(self, url: URL) -> bool:
        payload = VideoPayload(
            url=url.url,
            message_id=url.message_id,
            from_user_id=url.from_user_id,
            source=TaskSource.BOT,
        )
        is_sent = await self._publisher.send_for_download(payload)
        if not is_sent:
            self._log.error('Failed to publish URL %s to message broker', url.url)
        return is_sent

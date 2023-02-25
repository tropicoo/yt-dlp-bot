import logging

from yt_shared.enums import TaskSource
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.media import IncomingMediaPayload
from yt_shared.schemas.url import URL


class URLService:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._publisher = Publisher()

    async def process_urls(self, urls: list[URL]) -> None:
        for url in urls:
            await self._send_to_worker(url)

    async def _send_to_worker(self, url: URL) -> bool:
        payload = IncomingMediaPayload(
            url=url.url,
            message_id=url.message_id,
            from_user_id=url.from_user_id,
            from_chat_id=url.from_chat_id,
            from_chat_type=url.from_chat_type,
            source=TaskSource.BOT,
            save_to_storage=url.save_to_storage,
            download_media_type=url.download_media_type,
        )
        is_sent = await self._publisher.send_for_download(payload)
        if not is_sent:
            self._log.error('Failed to publish URL %s to message broker', url.url)
        return is_sent

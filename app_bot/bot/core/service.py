import logging
import re
from itertools import product

from pyrogram.types import Message
from yt_shared.enums import TaskSource, TelegramChatType
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.media import IncomingMediaPayload
from yt_shared.schemas.url import URL

from bot.core.config.schema import UserSchema


class UrlService:
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


class UrlParser:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def parse_urls(urls: list[str], message: Message, user: UserSchema) -> list[URL]:
        return [
            URL(
                url=url,
                from_chat_id=message.chat.id,
                from_chat_type=TelegramChatType(message.chat.type.value),
                from_user_id=message.from_user.id,
                message_id=message.id,
                save_to_storage=user.save_to_storage,
                download_media_type=user.download_media_type,
            )
            for url in urls
        ]

    def filter_urls(self, urls: list[str], regexes: list[str]) -> list[str]:
        """Return valid urls."""
        self._log.debug('Matching urls: %s against regexes %s', urls, regexes)
        valid = []
        for url, regex in product(urls, regexes):
            if re.match(regex, url):
                valid.append(url)

        valid = list(dict.fromkeys(valid))
        self._log.debug('Matched urls: %s', valid)
        return valid

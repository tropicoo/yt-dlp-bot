import logging

from pyrogram.enums import ParseMode
from pyrogram.types import Message

from core.bot import VideoBot
from core.service import URLService
from core.utils import bold
from yt_shared.enums import TelegramChatType
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.schemas.url import URL


class TelegramCallback:
    _MSG_SEND_OK = f'{SUCCESS_EMOJI} {bold("URL sent for download")}'
    _MSG_SEND_FAIL = f'🛑 {bold("Failed to send URL for download")}'

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._url_service = URLService()

    @staticmethod
    async def on_start(client: VideoBot, message: Message) -> None:
        await message.reply(
            bold('Send video URL to start processing'),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.id,
        )

    async def on_message(self, client: VideoBot, message: Message) -> None:
        """Receive video URL and send to the download worker."""
        self._log.debug(message)
        urls = self._get_urls(message)
        await self._url_service.process_urls(urls=urls)
        await message.reply(
            self._MSG_SEND_OK,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.id,
        )

    @staticmethod
    def _get_urls(message: Message) -> list[URL]:
        return [
            URL(
                url=url,
                from_chat_id=message.chat.id,
                from_chat_type=TelegramChatType(message.chat.type.value),
                from_user_id=message.from_user.id,
                message_id=message.id,
            )
            for url in message.text.splitlines()
        ]

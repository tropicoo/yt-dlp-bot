import logging

from pyrogram.enums import ParseMode
from pyrogram.types import Message
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.enums import TelegramChatType
from yt_shared.schemas.url import URL

from bot.core.bot import VideoBot
from bot.core.service import URLService
from bot.core.utils import bold


class TelegramCallback:
    _MSG_SEND_OK = f'{SUCCESS_EMOJI} {bold("{count}URL{plural} sent for download")}'
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
        urls = self._parse_urls(message)
        await self._url_service.process_urls(urls=urls)
        await self._send_acknowledge_message(message=message, urls=urls)

    async def _send_acknowledge_message(
        self, message: Message, urls: list[URL]
    ) -> None:
        urls_count = len(urls)
        is_multiple = urls_count > 1
        await message.reply(
            self._MSG_SEND_OK.format(
                count=f'{urls_count} ' if is_multiple else '',
                plural='s' if is_multiple else '',
            ),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.id,
        )

    def _parse_urls(self, message: Message) -> list[URL]:
        bot: VideoBot = message._client  # noqa
        user = bot.allowed_users[message.from_user.id]
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
            for url in message.text.splitlines()
        ]

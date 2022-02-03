import logging

from aiogram.types import Message, ParseMode

from core.processor import IncomingURLProcessor
from core.utils.utils import bold
from yt_shared.emoji import SUCCESS_EMOJI


class TelegramCallback:
    _MSG_SEND_OK = f'{SUCCESS_EMOJI} {bold("URL sent for download")}'
    _MSG_SEND_FAIL = f'🛑 {bold("Failed to send URL for download")}'

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._url_processor = IncomingURLProcessor()

    async def on_message(self, message: Message) -> None:
        """Receive video URL and send to the download worker."""
        is_sent = await self._url_processor.process(message.text,
                                                    message.message_id)
        await message.reply(
            self._MSG_SEND_OK if is_sent else self._MSG_SEND_FAIL,
            parse_mode=ParseMode.HTML)

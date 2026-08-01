import asyncio
import html
from typing import Any, ClassVar

from pyrogram.enums import ParseMode
from yt_shared.enums import RabbitPayloadType
from yt_shared.schemas.error import ErrorDownloadGeneralPayload, ErrorDownloadPayload

from bot.core.config import settings
from bot.core.error_messages import FriendlyError, classify, strip_extractor_prefix
from bot.core.handlers.abstract import AbstractDownloadHandler
from bot.core.utils import split_telegram_message
from bot.version import __version__


class ErrorDownloadHandler(AbstractDownloadHandler):
    _body: ErrorDownloadPayload | ErrorDownloadGeneralPayload
    _ERR_MSG_TPL = (
        '🛑 <b>{header}</b>\n\n'
        'ℹ <b>Task ID:</b> <code>{task_id}</code>\n'  # noqa: RUF001
        '💬 <b>Message:</b> {message}\n'
        '📹 <b>Video URL:</b> <code>{url}</code>\n'
        '🌊 <b>Source:</b> <code>{source}</code>\n'
        '👀 <b>Details:</b> <code>{{details}}</code>\n'
        '⬇️ <b>yt-dlp version:</b> <code>{yt_dlp_version}</code>\n'
        '🤖 <b>yt-dlp-bot version:</b> <code>{yt_dlp_bot_version}</code>\n'
        '🏷️ <b>Tag:</b> #error'
    )

    _FRIENDLY_MSG_TPL = (
        '{emoji} <b>{title}</b>\n\n'
        '{hint}\n\n'
        '🔗 <b>URL:</b> <code>{url}</code>\n'
        '💬 <b>Site response:</b> <code>{reason}</code>\n'
        '🏷️ <b>Tag:</b> #unavailable'
    )

    _ERR_MSG_HEADER_MAP: ClassVar[dict[RabbitPayloadType, str]] = {
        RabbitPayloadType.DOWNLOAD_ERROR: 'Download error',
        RabbitPayloadType.GENERAL_ERROR: 'General error',
    }

    async def handle(self) -> None:
        self._send_error_text()

    def _send_error_text(self) -> None:
        for user in self._get_receiving_users():
            kwargs: dict[str, Any] = {
                'chat_id': user.id,
                'text': self._format_error_message(),
                'parse_mode': ParseMode.HTML,
            }
            if self._body.message_id:
                kwargs['reply_to_message_id'] = self._body.message_id
            asyncio.create_task(self._bot.send_message(**kwargs))  # noqa:RUF006

    def _format_error_message(self) -> str:
        """Explain expected failures, report everything else in full detail."""
        friendly_error = classify(self._body.exception_msg)
        if friendly_error is not None:
            self._log.info(
                'Reporting expected download failure "%s" for %s',
                friendly_error.title,
                self._body.url,
            )
            return self._format_friendly_message(friendly_error)
        return self._format_detailed_message()

    def _format_friendly_message(self, friendly_error: FriendlyError) -> str:
        reason = strip_extractor_prefix(self._body.exception_msg)
        return self._FRIENDLY_MSG_TPL.format(
            emoji=friendly_error.emoji,
            title=friendly_error.title,
            hint=friendly_error.hint,
            url=html.escape(self._body.url),
            reason=html.escape(reason),
        )

    def _format_detailed_message(self) -> str:
        exception_msg = html.escape(self._body.exception_msg)
        pre_formatted_message = self._ERR_MSG_TPL.format(
            header=self._ERR_MSG_HEADER_MAP[self._body.type],
            message=self._body.message,
            url=self._body.url,
            source=self._body.context.source.value,
            task_id=self._body.task_id,
            yt_dlp_version=self._body.yt_dlp_version,
            yt_dlp_bot_version=__version__,
        )

        msg_len = len(pre_formatted_message) - 9  # len('{details}') == 9
        exc_msg_len = len(exception_msg)
        self._log.debug('Length of exception_msg %s', exc_msg_len)
        self._log.debug('Length of pre_formatted_message %s', msg_len)
        if msg_len + exc_msg_len > settings.TG_MAX_MSG_SIZE:
            exception_msg = next(
                split_telegram_message(
                    text=exception_msg,
                    chunk_size=settings.TG_MAX_MSG_SIZE - msg_len,
                    return_first=True,
                    negate=True,
                )
            )
        message = pre_formatted_message.format(details=exception_msg)
        self._log.debug('Length of formatted_message %s', len(message))
        return message

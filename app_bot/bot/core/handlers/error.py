import asyncio
import html
from typing import Any, ClassVar

from pyrogram.enums import ParseMode
from yt_shared.enums import RabbitPayloadType
from yt_shared.schemas.error import ErrorDownloadGeneralPayload, ErrorDownloadPayload

from bot.core.config import settings
from bot.core.error_messages import (
    FriendlyError,
    classify,
    extract_reason,
    strip_extractor_prefix,
)
from bot.core.handlers.abstract import AbstractDownloadHandler
from bot.core.utils import split_telegram_message
from bot.version import __version__


class ErrorDownloadHandler(AbstractDownloadHandler):
    _body: ErrorDownloadPayload | ErrorDownloadGeneralPayload
    _ERR_MSG_TPL = (
        '🛑 <b>{header}</b>\n\n'
        '💬 <b>Reason:</b> {reason}\n'
        '📹 <b>Video URL:</b> <code>{url}</code>\n'
        'ℹ <b>Task ID:</b> <code>{task_id}</code>\n'  # noqa: RUF001
        '🌊 <b>Source:</b> <code>{source}</code>\n'
        '{details_block}'
        '⬇️ <b>yt-dlp version:</b> <code>{yt_dlp_version}</code>\n'
        '🤖 <b>yt-dlp-bot version:</b> <code>{yt_dlp_bot_version}</code>\n'
        '🏷️ <b>Tag:</b> #error'
    )
    _DETAILS_TPL = '👀 <b>Details:</b> <code>{details}</code>\n'
    _DETAILS_PLACEHOLDER = '{details}'

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
        """Report an unrecognised failure, leading with whatever reason we have.

        The raw text is only repeated under "Details" when it says more than the
        reason line, which spares the reader a duplicated one-liner.
        """
        raw_msg = (self._body.exception_msg or '').strip()
        stripped_msg = strip_extractor_prefix(raw_msg)
        reason = extract_reason(raw_msg)
        has_details = bool(stripped_msg) and stripped_msg != reason

        pre_formatted_message = self._ERR_MSG_TPL.format(
            header=self._ERR_MSG_HEADER_MAP[self._body.type],
            reason=html.escape(reason or self._body.message),
            url=self._body.url,
            source=self._body.context.source.value,
            task_id=self._body.task_id,
            yt_dlp_version=self._body.yt_dlp_version,
            yt_dlp_bot_version=__version__,
            details_block=self._DETAILS_TPL if has_details else '',
        )
        if not has_details:
            return pre_formatted_message

        exception_msg = html.escape(raw_msg)
        msg_len = len(pre_formatted_message) - len(self._DETAILS_PLACEHOLDER)
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
        # Substituted rather than formatted: the reason comes from yt-dlp and
        # may itself contain braces, which would break another format pass.
        message = pre_formatted_message.replace(
            self._DETAILS_PLACEHOLDER, exception_msg
        )
        self._log.debug('Length of formatted_message %s', len(message))
        return message

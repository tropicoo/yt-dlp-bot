import asyncio
import html

from pyrogram.enums import ParseMode

from core.handlers.abstract import AbstractHandler
from yt_shared.enums import RabbitPayloadType
from yt_shared.schemas.error import ErrorDownloadPayload, ErrorGeneralPayload


class UserBaseSchema:
    pass


class ErrorHandler(AbstractHandler):
    _body: ErrorDownloadPayload | ErrorGeneralPayload
    _ERR_MSG_TPL = (
        '🛑 <b>{header}</b>\n\n'
        'ℹ <b>ID:</b> <code>{task_id}</code>\n'
        '💬 <b>Message:</b> {message}\n'
        '📹 <b>Video URL:</b> <code>{url}</code>\n'
        '🌊 <b>Source:</b> <code>{source}</code>\n'
        '👀 <b>Details:</b> <code>{details}</code>\n'
        '⬇️ <b>yt-dlp version:</b> <code>{yt_dlp_version}</code>\n'
        '🏷️ <b>Tag:</b> #error'
    )

    _ERR_MSG_HEADER_MAP = {
        RabbitPayloadType.DOWNLOAD_ERROR: 'Download error',
        RabbitPayloadType.GENERAL_ERROR: 'General error',
    }

    async def handle(self) -> None:
        await self._handle()

    async def _handle(self) -> None:
        self._send_error_text()

    def _send_error_text(self) -> None:
        for user in self._get_receiving_users():
            kwargs = {
                'chat_id': user.id,
                'text': self._format_error_message(),
                'parse_mode': ParseMode.HTML,
            }
            if self._body.message_id:
                kwargs['reply_to_message_id'] = self._body.message_id
            asyncio.create_task(self._bot.send_message(**kwargs))

    def _format_error_message(self) -> str:
        return self._ERR_MSG_TPL.format(
            header=self._ERR_MSG_HEADER_MAP[self._body.type],
            message=self._body.message,
            url=self._body.url,
            source=self._body.context.source.value,
            task_id=self._body.task_id,
            details=html.escape(self._body.exception_msg),
            yt_dlp_version=self._body.yt_dlp_version,
        )

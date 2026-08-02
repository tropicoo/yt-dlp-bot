"""Handler refreshing the acknowledgement message with download progress."""

import logging
from typing import TYPE_CHECKING

from pyrogram.enums import ParseMode
from yt_shared.schemas.progress import ProgressPayload

from bot.core.progress import format_download_progress

if TYPE_CHECKING:
    from bot.bot.client import VideoBotClient


class ProgressHandler:
    """Applies a progress update to the message that tracks the task."""

    def __init__(self, bot: 'VideoBotClient') -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._bot = bot

    async def handle(self, payload: ProgressPayload) -> None:
        try:
            await self._bot.edit_message_text(
                chat_id=payload.from_chat_id,
                message_id=payload.ack_message_id,
                text=format_download_progress(
                    payload, self._bot.language_for(payload.from_chat_id)
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as err:
            # The message may already be gone or unchanged, and a stale update
            # is never worth failing over.
            self._log.debug(
                'Could not refresh progress for message %s: %s',
                payload.ack_message_id,
                err,
            )

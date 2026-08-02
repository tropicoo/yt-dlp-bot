"""Rendering and pacing of live progress updates."""

import logging
import time
from typing import Final

from yt_shared.enums import ProgressStage
from yt_shared.schemas.progress import ProgressPayload
from yt_shared.utils.common import format_bytes

from bot.core.i18n import has_message, t

_BAR_SEGMENTS: Final[int] = 10
_BAR_FILLED: Final[str] = '▰'
_BAR_EMPTY: Final[str] = '▱'

# Telegram rejects frequent edits of the same message, and Pyrogram reports an
# upload every chunk, so refreshes are spaced out.
_UPLOAD_MIN_INTERVAL_SECONDS: Final[float] = 3.0


def _progress_bar(percent: float) -> str:
    filled = int(percent / 100 * _BAR_SEGMENTS)
    filled = max(0, min(filled, _BAR_SEGMENTS))
    return f'{_BAR_FILLED * filled}{_BAR_EMPTY * (_BAR_SEGMENTS - filled)}'


def _format_eta(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f'{hours}:{minutes:02d}:{secs:02d}'
    return f'{minutes}:{secs:02d}'


def _headline(key: str, language: str, percent: float | None) -> list[str]:
    if percent is None:
        return [t(f'{key}_plain', language)]
    return [t(key, language, percent=f'{percent:.1f}'), _progress_bar(percent)]


def format_download_progress(payload: ProgressPayload, language: str) -> str:
    """Render a download progress update for the acknowledgement message."""
    if payload.stage is ProgressStage.POSTPROCESSING:
        # There is no percentage to show here, so the step and how long it has
        # been running are what tell the user it is progressing at all.
        lines = [t('progress.processing', language)]
        lines.append(
            t(payload.detail_key, language)
            if has_message(payload.detail_key)
            else t('progress.processing_generic', language)
        )
        if payload.elapsed:
            lines.append(
                t('progress.elapsed', language, time=_format_eta(payload.elapsed))
            )
        return '\n'.join(lines)

    lines = _headline('progress.downloading', language, payload.percent)
    if has_message(payload.detail_key):
        lines.append(
            t('progress.notice', language, text=t(payload.detail_key, language))
        )

    details = []
    if payload.eta is not None:
        details.append(t('progress.eta', language, time=_format_eta(payload.eta)))
    if payload.total_bytes:
        details.append(
            t(
                'progress.size',
                language,
                done=format_bytes(payload.downloaded_bytes or 0),
                total=format_bytes(payload.total_bytes),
            )
        )
    elif payload.downloaded_bytes:
        details.append(
            t(
                'progress.size_done',
                language,
                done=format_bytes(payload.downloaded_bytes),
            )
        )
    if payload.speed:
        details.append(
            t('progress.speed', language, speed=format_bytes(int(payload.speed)))
        )

    if details:
        lines.append(' · '.join(details))
    return '\n'.join(lines)


def format_upload_progress(current: int, total: int, language: str) -> str:
    """Render an upload progress update for the acknowledgement message."""
    percent = round(min(current / total, 1.0) * 100, 1) if total else None
    lines = _headline('progress.uploading', language, percent)
    if total:
        lines.append(
            t(
                'progress.size',
                language,
                done=format_bytes(current),
                total=format_bytes(total),
            )
        )
    return '\n'.join(lines)


class UploadProgressReporter:
    """Throttled Pyrogram upload callback that refreshes a status message."""

    def __init__(self, bot, chat_id: int, message_id: int, language: str) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._bot = bot
        self._chat_id = chat_id
        self._message_id = message_id
        self._language = language
        self._last_sent_at = 0.0

    async def __call__(self, current: int, total: int) -> None:
        now = time.monotonic()
        is_last = total and current >= total
        if not is_last and now - self._last_sent_at < _UPLOAD_MIN_INTERVAL_SECONDS:
            return
        self._last_sent_at = now
        # Progress is cosmetic, so a failed refresh must not abort the upload.
        try:
            await self._bot.edit_message_text(
                chat_id=self._chat_id,
                message_id=self._message_id,
                text=format_upload_progress(current, total, self._language),
            )
        except Exception as err:
            self._log.debug('Could not refresh upload progress: %s', err)

"""Logger adapter that keeps track of what yt-dlp reported."""

import logging
from typing import Final

_DEBUG_PREFIX: Final[str] = '[debug] '
_ERROR_PREFIX: Final[str] = 'ERROR: '
_PROGRESS_PREFIX: Final[str] = '[download] '
# Openers of the traceback yt-dlp logs separately from the reason itself. The
# header is absent for expected errors, which start right at the first frame.
_TRACEBACK_MARKERS: Final[tuple[str, ...]] = ('Traceback (most recent call last)', 'File "')


class YtdlpLogger:
    """Forward yt-dlp output to the app logger and collect its error messages.

    yt-dlp runs with the ``ignoreerrors`` option enabled, which makes it swallow
    extractor errors and return empty metadata instead of raising. Without
    collecting the messages here, the actual reason a download failed (suspended
    account, private video, geo block, ...) never leaves this process and the
    user only sees a generic failure.
    """

    def __init__(self, log: logging.Logger) -> None:
        self._log = log
        self.errors: list[str] = []

    def debug(self, msg: str) -> None:
        # yt-dlp routes both debug and info lines here, only debug ones are prefixed.
        if msg.startswith(_DEBUG_PREFIX) or self._is_progress_tick(msg):
            self._log.debug(msg)
        else:
            self._log.info(msg)

    @staticmethod
    def _is_progress_tick(msg: str) -> bool:
        """Recognise the download ticker, which arrives many times a second.

        Progress is reported to the user in Telegram, so at info level these
        only bury the lines that matter. Other "[download]" lines, such as the
        destination, are worth keeping.
        """
        return msg.startswith(_PROGRESS_PREFIX) and ('% of' in msg or 'ETA ' in msg)

    def info(self, msg: str) -> None:
        self._log.info(msg)

    def warning(self, msg: str) -> None:
        self._log.warning(msg)

    def error(self, msg: str) -> None:
        self._log.error(msg)
        self.errors.append(msg)

    def last_error(self) -> str | None:
        """Return the most recent error reason, or ``None`` if nothing was reported.

        In verbose mode yt-dlp reports the reason and the traceback as two separate
        calls, and only the reason carries the ``ERROR: `` prefix, so prefer those.
        Just the first line is kept, since a message may still span several lines.
        """
        reported = [msg for msg in self.errors if msg.startswith(_ERROR_PREFIX)]
        for msg in reversed(reported or self.errors):
            reason = msg.removeprefix(_ERROR_PREFIX).splitlines()[0].strip()
            if reason and not reason.startswith(_TRACEBACK_MARKERS):
                return reason
        return None

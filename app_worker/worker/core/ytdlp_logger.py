"""Logger adapter that keeps track of what yt-dlp reported."""

import logging
from typing import Final

_DEBUG_PREFIX: Final[str] = '[debug] '
_ERROR_PREFIX: Final[str] = 'ERROR: '


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
        if msg.startswith(_DEBUG_PREFIX):
            self._log.debug(msg)
        else:
            self._log.info(msg)

    def info(self, msg: str) -> None:
        self._log.info(msg)

    def warning(self, msg: str) -> None:
        self._log.warning(msg)

    def error(self, msg: str) -> None:
        self._log.error(msg)
        self.errors.append(msg)

    def last_error(self) -> str | None:
        """Return the most recent error reason, or ``None`` if nothing was reported.

        Strips yt-dlp's ``ERROR: `` prefix and keeps only the first line, since in
        verbose mode the traceback is appended to the very same message.
        """
        for msg in reversed(self.errors):
            reason = msg.removeprefix(_ERROR_PREFIX).splitlines()[0].strip()
            if reason:
                return reason
        return None

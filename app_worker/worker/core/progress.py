"""Reporting download progress back to the bot."""

import asyncio
import logging
import threading
import time
from concurrent.futures import Future
from typing import Any, Final

from yt_shared.enums import ProgressStage
from yt_shared.rabbit.publisher import RmqPublisher
from yt_shared.schemas.media import InbMediaPayload
from yt_shared.schemas.progress import ProgressPayload

# yt-dlp calls the hook many times per second, while Telegram starts rejecting
# message edits after a handful per minute, so updates are thinned out here at
# the source rather than flooding the queue.
_MIN_INTERVAL_SECONDS: Final[float] = 3.0
# Post-processing gives no progress of its own, so it is refreshed just often
# enough to show it is still alive.
_POSTPROCESSING_TICK_SECONDS: Final[float] = 10.0

# yt-dlp names its post-processors after their classes.
_STEP_LABELS: Final[dict[str, str]] = {
    'Merger': 'Merging video and audio',
    'FFmpegVideoConvertor': 'Converting video',
    'FFmpegVideoRemuxer': 'Repackaging video',
    'FFmpegExtractAudio': 'Extracting audio',
    'FFmpegThumbnailsConvertor': 'Converting the thumbnail',
    'FFmpegMetadata': 'Writing metadata',
    'EmbedThumbnail': 'Embedding the cover',
    'FFmpegConcat': 'Joining the parts',
    'FFmpegFixupM3u8': 'Repairing the stream',
}


class ProgressReporter:
    """Publishes throttled progress updates from yt-dlp's download thread.

    The download runs in an executor, so the hook is called outside the event
    loop and publishing has to be scheduled back onto it.
    """

    def __init__(
        self, media_payload: InbMediaPayload, loop: asyncio.AbstractEventLoop
    ) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._payload = media_payload
        self._loop = loop
        self._publisher = RmqPublisher()
        self._last_sent_at = 0.0
        self._last_stage: ProgressStage | None = None
        self._last_sample: tuple[float, int] | None = None
        self._in_flight: Future | None = None
        self._postprocessing_since: float | None = None
        self._step: str | None = None
        self._ticker: Future | None = None
        # yt-dlp calls the hook from every fragment thread at once, so deciding
        # whether to publish has to be atomic or each of them publishes a tick.
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        """Progress is only reportable when there is a message to refresh."""
        return (
            self._payload.from_chat_id is not None
            and self._payload.ack_message_id is not None
        )

    def hook(self, status: dict[str, Any]) -> None:
        """Entry point for yt-dlp's ``progress_hooks``."""
        try:
            self._handle(status)
        except Exception:
            # Progress is cosmetic and must never break an ongoing download.
            self._log.exception('Failed to report progress')

    def _handle(self, status: dict[str, Any]) -> None:
        match status.get('status'):
            case 'downloading':
                stage = ProgressStage.DOWNLOADING
            case 'finished':
                # The bytes are in, but merging or converting may still follow.
                stage = ProgressStage.POSTPROCESSING
                self._begin_postprocessing()
            case _:
                return

        # Both the decision and the rate measurement read and update shared
        # state, so they are made together under the lock.
        with self._lock:
            if not self._should_send(stage):
                return
            payload = self._build_payload(stage, status)
        self._publish(payload)

    def postprocessor_hook(self, status: dict[str, Any]) -> None:
        """Entry point for yt-dlp's ``postprocessor_hooks``.

        These only mark the boundaries of each step and carry no percentage, so
        the most that can be reported is which step is running.
        """
        try:
            if status.get('status') != 'started':
                return
            with self._lock:
                self._step = _STEP_LABELS.get(status.get('postprocessor', ''))
            self._report_postprocessing()
        except Exception:
            self._log.exception('Failed to report a post-processing step')

    def _begin_postprocessing(self) -> None:
        """Start reporting elapsed time until the download call returns."""
        with self._lock:
            if self._postprocessing_since is not None:
                return
            self._postprocessing_since = time.monotonic()
        self._ticker = asyncio.run_coroutine_threadsafe(self._tick(), self._loop)

    async def _tick(self) -> None:
        """Refresh the elapsed time so a long step does not look like a hang."""
        try:
            while True:
                await asyncio.sleep(_POSTPROCESSING_TICK_SECONDS)
                self._report_postprocessing()
        except asyncio.CancelledError:
            pass

    def _report_postprocessing(self) -> None:
        with self._lock:
            if self._postprocessing_since is None:
                return
            if self._in_flight is not None and not self._in_flight.done():
                return
            payload = ProgressPayload(
                from_chat_id=self._payload.from_chat_id,
                ack_message_id=self._payload.ack_message_id,
                stage=ProgressStage.POSTPROCESSING,
                detail=self._step,
                elapsed=int(time.monotonic() - self._postprocessing_since),
            )
        self._publish(payload)

    def stop(self) -> None:
        """Stop reporting once the download call has returned."""
        ticker, self._ticker = self._ticker, None
        if ticker is not None:
            ticker.cancel()

    def _should_send(self, stage: ProgressStage) -> bool:
        if self._in_flight is not None and not self._in_flight.done():
            # The broker has not caught up with the previous update; another one
            # would only queue behind it and arrive already stale.
            return False

        now = time.monotonic()
        # A stage change is always worth showing immediately.
        if stage == self._last_stage and now - self._last_sent_at < _MIN_INTERVAL_SECONDS:
            return False
        self._last_sent_at = now
        self._last_stage = stage
        return True

    def _build_payload(
        self, stage: ProgressStage, status: dict[str, Any]
    ) -> ProgressPayload:
        downloaded = status.get('downloaded_bytes')
        total = status.get('total_bytes') or status.get('total_bytes_estimate')

        percent = None
        if downloaded is not None and total:
            percent = round(min(downloaded / total, 1.0) * 100, 1)

        speed = self._measure_speed(downloaded)
        eta = None
        if speed and total and downloaded is not None:
            eta = int(max(total - downloaded, 0) / speed)

        return ProgressPayload(
            from_chat_id=self._payload.from_chat_id,
            ack_message_id=self._payload.ack_message_id,
            stage=stage,
            percent=percent,
            downloaded_bytes=int(downloaded) if downloaded is not None else None,
            total_bytes=int(total) if total else None,
            speed=speed,
            eta=eta,
        )

    def _measure_speed(self, downloaded: int | None) -> float | None:
        """Average the transfer rate over our own reporting interval.

        yt-dlp restarts its speed counter whenever a fragment completes, so with
        concurrent fragments its figure is regularly unknown or off by an order
        of magnitude. Measuring across our own samples sidesteps that entirely.
        """
        now = time.monotonic()
        previous, self._last_sample = self._last_sample, None
        if downloaded is None:
            return None

        self._last_sample = (now, downloaded)
        if previous is None:
            return None

        previous_time, previous_bytes = previous
        elapsed = now - previous_time
        transferred = downloaded - previous_bytes
        if elapsed <= 0 or transferred <= 0:
            return None
        return transferred / elapsed

    def _publish(self, payload: ProgressPayload) -> None:
        future = asyncio.run_coroutine_threadsafe(
            self._publisher.send_progress(payload), self._loop
        )
        self._in_flight = future
        future.add_done_callback(self._log_publish_failure)

    def _log_publish_failure(self, future: Future) -> None:
        try:
            future.result()
        except Exception:
            self._log.exception('Failed to publish a progress update')

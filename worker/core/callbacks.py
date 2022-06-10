import logging

from aio_pika import IncomingMessage

from core.video_service import VideoService
from yt_shared.db import get_db
from yt_shared.schemas.video import VideoPayload


class _Callbacks:
    """RabbitMQ callbacks."""

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._video_service = VideoService()

    async def on_input_message(self, message: IncomingMessage) -> None:
        self._log.info('[x] Received message %s', message.body)
        try:
            video_payload = VideoPayload.parse_raw(message.body)
        except Exception:
            self._log.exception('Failed to decode message body')
            await self._reject_invalid_body(message)
            return

        async for session in get_db():
            await self._video_service.process(video_payload, session)

        await message.ack()
        self._log.info('Download done with %s', video_payload)

    async def _reject_invalid_body(self, message: IncomingMessage) -> None:
        body = message.body
        self._log.error('Invalid message body: %s, type: %s', body, type(body))
        await message.reject(requeue=False)


callbacks = _Callbacks()

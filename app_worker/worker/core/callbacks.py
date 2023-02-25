import logging

from aio_pika import IncomingMessage
from yt_shared.schemas.media import IncomingMediaPayload

from worker.core.payload_handler import PayloadHandler


class _RMQCallbacks:
    """RabbitMQ's callbacks."""

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._payload_handler = PayloadHandler()

    async def on_input_message(self, message: IncomingMessage) -> None:
        try:
            await self._process_incoming_message(message)
        except Exception:
            self._log.exception('Critical exception in worker rabbit callback')
            await message.reject(requeue=False)

    async def _process_incoming_message(self, message: IncomingMessage) -> None:
        self._log.info('[x] Received message %s', message.body)
        media_payload = self._deserialize_message(message)
        if not media_payload:
            await self._reject_invalid_message(message)
            return

        await self._payload_handler.handle(media_payload=media_payload)
        await message.ack()
        self._log.info('Processing done with payload: %s', media_payload)

    def _deserialize_message(
        self, message: IncomingMessage
    ) -> IncomingMediaPayload | None:
        try:
            return IncomingMediaPayload.parse_raw(message.body)
        except Exception:
            self._log.exception('Failed to deserialize message body: %s', message.body)
            return None

    async def _reject_invalid_message(self, message: IncomingMessage) -> None:
        body = message.body
        self._log.error('Invalid message body: %s, type: %s', body, type(body))
        await message.reject(requeue=False)


rmq_callbacks = _RMQCallbacks()

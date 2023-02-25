import logging

import aio_pika
from aiormq.abc import ConfirmationFrameType
from pamqp.commands import Basic

from yt_shared.rabbit import get_rabbitmq
from yt_shared.rabbit.rabbit_config import (
    ERROR_EXCHANGE,
    ERROR_QUEUE,
    INPUT_EXCHANGE,
    INPUT_QUEUE,
    SUCCESS_EXCHANGE,
    SUCCESS_QUEUE,
)
from yt_shared.schemas.error import ErrorDownloadPayload, ErrorGeneralPayload
from yt_shared.schemas.media import IncomingMediaPayload
from yt_shared.schemas.success import SuccessPayload
from yt_shared.utils.common import Singleton


class Publisher(metaclass=Singleton):
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._rabbit_mq = get_rabbitmq()

    @staticmethod
    def _is_sent(confirm: ConfirmationFrameType | None) -> bool:
        return isinstance(confirm, Basic.Ack)

    async def send_for_download(self, media_payload: IncomingMediaPayload) -> bool:
        message = aio_pika.Message(body=media_payload.json().encode())
        exchange = self._rabbit_mq.exchanges[INPUT_EXCHANGE]
        confirm = await exchange.publish(
            message, routing_key=INPUT_QUEUE, mandatory=True
        )
        return self._is_sent(confirm)

    async def send_download_error(
        self, error_payload: ErrorDownloadPayload | ErrorGeneralPayload
    ) -> bool:
        err_exchange = self._rabbit_mq.exchanges[ERROR_EXCHANGE]
        err_message = aio_pika.Message(body=error_payload.json().encode())
        confirm = await err_exchange.publish(
            err_message, routing_key=ERROR_QUEUE, mandatory=True
        )
        return self._is_sent(confirm)

    async def send_download_finished(self, success_payload: SuccessPayload) -> bool:
        message = aio_pika.Message(body=success_payload.json().encode())
        exchange = self._rabbit_mq.exchanges[SUCCESS_EXCHANGE]
        confirm = await exchange.publish(
            message, routing_key=SUCCESS_QUEUE, mandatory=True
        )
        return self._is_sent(confirm)

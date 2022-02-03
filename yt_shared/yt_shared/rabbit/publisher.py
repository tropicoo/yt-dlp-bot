import logging

import aio_pika
from pamqp.commands import Basic

from yt_shared.rabbit import get_rabbitmq
from yt_shared.rabbit.rabbit_config import INPUT_EXCHANGE, INPUT_QUEUE
from yt_shared.schemas.video import VideoPayload
from yt_shared.utils import Singleton


class Publisher(metaclass=Singleton):

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._rabbit_mq = get_rabbitmq()
        self._exchange = self._rabbit_mq.exchanges[INPUT_EXCHANGE]

    async def send_for_download(self, video_payload: VideoPayload) -> bool:
        message = aio_pika.Message(body=video_payload.json().encode())
        confirm = await self._exchange.publish(message, routing_key=INPUT_QUEUE, mandatory=True)
        return isinstance(confirm, Basic.Ack)

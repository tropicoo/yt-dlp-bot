"""RabbitMQ Queue abstract worker module."""

from abc import abstractmethod
from typing import TYPE_CHECKING, Type

from aio_pika import IncomingMessage
from pydantic import BaseModel
from yt_shared.rabbit import get_rabbitmq
from yt_shared.utils.tasks.abstract import AbstractTask

from bot.core.config.config import get_main_config
from bot.core.exceptions import InvalidBodyError
from bot.core.workers.enums import RabbitWorkerType

if TYPE_CHECKING:
    from bot.bot.client import VideoBotClient


class AbstractDownloadResultWorker(AbstractTask):
    TYPE: RabbitWorkerType | None = None
    QUEUE_TYPE: str | None = None
    SCHEMA_CLS: tuple[Type[BaseModel]] = ()

    def __init__(self, bot: 'VideoBotClient') -> None:
        super().__init__()
        self._conf = get_main_config()
        self._bot = bot
        self._rabbit_mq = get_rabbitmq()
        self._queue = self._rabbit_mq.queues[self.QUEUE_TYPE]

    async def run(self) -> None:
        await self._watch_queue()

    @abstractmethod
    async def _process_body(self, body: BaseModel) -> bool:
        pass

    async def _watch_queue(self) -> None:
        message: IncomingMessage
        async with self._queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    await self._process_message(message)
                except Exception:
                    self._log.exception('Failed to process message %s', message.body)
                    if not message.processed:
                        await message.nack(requeue=False)

    async def _process_message(self, message: IncomingMessage) -> None:
        self._log.debug('[x] Received message %s', message.body)
        body = await self._deserialize_message(message)
        await self._process_body(body)
        await message.ack()

    async def _deserialize_message(self, message: IncomingMessage) -> BaseModel:
        for schema_cls in self.SCHEMA_CLS:
            try:
                return schema_cls.model_validate_json(message.body)
            except Exception:
                # Skip unmatched schema class that failed to parse the body.
                pass
        else:
            self._log.error('Failed to decode message body')
            await self._reject_invalid_body(message)
            raise InvalidBodyError

    async def _reject_invalid_body(self, message: IncomingMessage) -> None:
        body = message.body
        self._log.critical('Invalid message body: %s, type: %s', body, type(body))
        await message.reject(requeue=False)

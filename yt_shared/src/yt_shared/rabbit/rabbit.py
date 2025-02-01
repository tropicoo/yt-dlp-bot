import logging
from asyncio import get_running_loop
from typing import TYPE_CHECKING

import aio_pika
from aio_pika import RobustChannel, RobustConnection

from yt_shared.config import settings
from yt_shared.rabbit.rabbit_config import get_rabbit_config

if TYPE_CHECKING:
    from aio_pika.abc import AbstractRobustExchange, AbstractRobustQueue


class RabbitMQ:
    MAX_UNACK_MESSAGES_PER_CHANNEL: int = 10
    RABBITMQ_RECONNECT_INTERVAL: int = 2

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._config = get_rabbit_config()

        self.connection: RobustConnection | None = None
        self.channel: RobustChannel | None = None
        self.exchanges: dict[str, AbstractRobustExchange] = {}
        self.queues: dict[str, AbstractRobustQueue] = {}

    async def register(self) -> None:
        await self._set_connection()
        await self._set_channel()
        await self._set_exchanges()
        await self._set_queues()

    async def _set_connection(self) -> None:
        self.connection = await aio_pika.connect_robust(
            url=settings.RABBITMQ_URI,
            loop=get_running_loop(),
            reconnect_interval=self.RABBITMQ_RECONNECT_INTERVAL,
        )

    async def _set_channel(self) -> None:
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.MAX_UNACK_MESSAGES_PER_CHANNEL)

    async def _set_exchanges(self) -> None:
        for exchange_data in self._config.get('exchanges', []):
            exchange = await self.channel.declare_exchange(**exchange_data)
            self.exchanges[exchange_data['name']] = exchange

    async def _set_queues(self) -> None:
        for queue_data in self._config.get('queues', []):
            queue = await self.channel.declare_queue(**queue_data)
            queue_name = queue_data['name']
            bindings = self._config['queue_bindings'][queue_name]
            for _settings in bindings:
                await queue.bind(self.exchanges[_settings['exchange_name']])
            self.queues[queue_name] = queue

    async def close(self) -> None:
        self._log.debug('[RabbitMQ] Closing connection')
        await self.channel.close()
        await self.connection.close()
        self._log.debug('[RabbitMQ] Connection closed')


_rabbit_mq = RabbitMQ()


def get_rabbitmq() -> RabbitMQ:
    return _rabbit_mq

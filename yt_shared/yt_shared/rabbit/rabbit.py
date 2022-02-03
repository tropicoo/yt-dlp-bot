from asyncio import get_running_loop
from typing import Optional

import aio_pika
from aio_pika import Exchange, RobustChannel, RobustConnection

from yt_shared.config import RABBITMQ_URI
from yt_shared.rabbit.rabbit_config import get_rabbit_config


class RabbitMQ:

    MAX_UNACK_MESSAGES_PER_CHANNEL = 10
    RABBITMQ_RECONNECT_INTERVAL = 2

    def __init__(self) -> None:
        self._config = get_rabbit_config()

        self.connection: Optional[RobustConnection] = None
        self.channel: Optional[RobustChannel] = None
        self.exchanges: dict[str, Exchange] = {}
        self.queues: dict[str, aio_pika.queue.Queue] = {}

    async def register(self) -> None:
        await self._set_connection()
        await self._set_channel()
        await self._set_exchanges()
        await self._set_queues()

    async def _set_connection(self):
        self.connection = await aio_pika.connect_robust(
            RABBITMQ_URI,
            loop=get_running_loop(),
            reconnect_interval=self.RABBITMQ_RECONNECT_INTERVAL,
        )

    async def _set_channel(self):
        self.channel = await self.connection.channel()
        await self.channel.set_qos(
            prefetch_count=self.MAX_UNACK_MESSAGES_PER_CHANNEL)

    async def _set_exchanges(self):
        for exchange_data in self._config.get('exchanges', []):
            exchange = await self.channel.declare_exchange(**exchange_data)
            self.exchanges[exchange_data['name']] = exchange

    async def _set_queues(self):
        for queue_data in self._config.get('queues', []):
            queue = await self.channel.declare_queue(**queue_data)
            queue_name = queue_data['name']
            bindings = self._config['queue_bindings'][queue_name]
            for settings in bindings:
                await queue.bind(self.exchanges[settings['exchange_name']])
            self.queues[queue_name] = queue

    async def close(self) -> None:
        await self.channel.close()
        await self.connection.close()


_rabbit_mq = RabbitMQ()


def get_rabbitmq() -> RabbitMQ:
    return _rabbit_mq

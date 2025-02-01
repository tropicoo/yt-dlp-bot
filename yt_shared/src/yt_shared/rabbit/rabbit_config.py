from typing import Any

from aio_pika import ExchangeType

INPUT_QUEUE = 'input.q'
ERROR_QUEUE = 'error.q'
SUCCESS_QUEUE = 'success.q'

INPUT_EXCHANGE = 'input.dx'
SUCCESS_EXCHANGE = 'success.dx'
ERROR_EXCHANGE = 'error.dx'


def get_rabbit_config() -> dict[str, list[dict[str, Any]]]:
    return {
        'queues': [
            {'name': INPUT_QUEUE, 'auto_delete': False, 'durable': True},
            {'name': ERROR_QUEUE, 'auto_delete': False, 'durable': True},
            {'name': SUCCESS_QUEUE, 'auto_delete': False, 'durable': True},
        ],
        'exchanges': [
            {
                'name': INPUT_EXCHANGE,
                'auto_delete': False,
                'durable': True,
                'type': ExchangeType.DIRECT.value,
            },
            {
                'name': ERROR_EXCHANGE,
                'auto_delete': False,
                'durable': True,
                'type': ExchangeType.DIRECT.value,
            },
            {
                'name': SUCCESS_EXCHANGE,
                'auto_delete': False,
                'durable': True,
                'type': ExchangeType.DIRECT.value,
            },
        ],
        'queue_bindings': {
            INPUT_QUEUE: [{'exchange_name': INPUT_EXCHANGE}],
            ERROR_QUEUE: [{'exchange_name': ERROR_EXCHANGE}],
            SUCCESS_QUEUE: [{'exchange_name': SUCCESS_EXCHANGE}],
        },
    }

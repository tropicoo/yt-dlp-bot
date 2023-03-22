"""Over-engineered Python 3.10+ version of bash script with netcat (nc) just for fun.

    #!/bin/bash

    check_reachability() {
    while ! nc -z "$1" "${!2}"
    do
      echo "Waiting for $3 to be reachable on port ${!2}"
      sleep 1
    done
    echo "Connection to $3 on port ${!2} verified"
    return 0
    }


    wait_for_services_to_be_reachable() {
      check_reachability rabbitmq RABBITMQ_PORT RabbitMQ
      check_reachability postgres POSTGRES_PORT PostgreSQL
    }

    wait_for_services_to_be_reachable
    exit 0
"""

import asyncio
import logging
import os
import socket
import sys
from contextlib import closing
from dataclasses import dataclass, field
from typing import Type

SOCK_CONNECTED = 0
DEFAULT_PORT = 0
DEFAULT_SLEEP_TIME = 1


class ServiceRegistry(type):
    REGISTRY: dict[str, type['BaseService']] = {}

    def __new__(
        mcs: Type['ServiceRegistry'],
        name: str,
        bases: tuple[type['BaseService']],
        attrs: dict,
    ) -> type['BaseService']:
        service_cls: type['BaseService'] = type.__new__(mcs, name, bases, attrs)
        mcs.REGISTRY[service_cls.__name__] = service_cls
        return service_cls

    @classmethod
    def get_services(mcs) -> dict[str, type['BaseService']]:
        return mcs.REGISTRY.copy()


@dataclass
class BaseService:
    name: str = field(default='', init=False)
    host: str = field(default='', init=False)
    port: int = field(default=DEFAULT_PORT, init=False)

    def __post_init__(self) -> None:
        if self.__class__ is BaseService:
            raise TypeError('Cannot instantiate abstract class.')


@dataclass
class RabbitMQService(BaseService, metaclass=ServiceRegistry):
    name: str = field(default='RabbitMQ')
    host: str = field(default=os.getenv('RABBITMQ_HOST'))
    port: int = field(default=int(os.getenv('RABBITMQ_PORT')))


@dataclass
class PostgreSQLService(BaseService, metaclass=ServiceRegistry):
    name: str = field(default='PostgreSQL')
    host: str = field(default=os.getenv('POSTGRES_HOST'))
    port: int = field(default=int(os.getenv('POSTGRES_PORT')))


async def is_port_open(host: str, port: int) -> bool:
    sock: socket.socket
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return await asyncio.to_thread(sock.connect_ex, (host, port)) == SOCK_CONNECTED


async def check_reachability(service: BaseService) -> None:
    while True:
        print(f'Waiting for {service.name} to be reachable on port {service.port}')
        if await is_port_open(host=service.host, port=service.port):
            break
        await asyncio.sleep(DEFAULT_SLEEP_TIME)
    print(f'Connection to {service.name} on port {service.port} verified')


async def main() -> None:
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    coros = []
    for service_cls in ServiceRegistry.get_services().values():
        coros.append(check_reachability(service_cls()))
    await asyncio.gather(*coros)


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

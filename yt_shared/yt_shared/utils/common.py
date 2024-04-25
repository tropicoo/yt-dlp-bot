import asyncio
import atexit
import datetime
import random
import signal
from functools import partial, wraps
from string import ascii_lowercase, digits
from typing import Any, Callable

_UNIT_SIZE_NAMES = ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi')
_BASE = 1024.0


def format_bytes(num: int, suffix: str = 'B') -> str:
    """Format bytes to human-readable size."""
    for unit in _UNIT_SIZE_NAMES:
        if abs(num) < _BASE:
            return f'{num:3.1f}{unit}{suffix}'
        num /= _BASE
    return f'{num:.1f}Yi{suffix}'


class Singleton(type):
    """Singleton class."""

    _instances = {}

    def __call__(cls, *args, **kwargs) -> Any:
        """Check whether instance already exists.

        Return existing or create new instance and save to dict."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def get_env_bool(string: str | bool) -> bool:
    if isinstance(string, str):
        return string.lower() in ('true',)
    return string


def wrap(func):
    """Run sync code in executor."""

    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, partial(func, *args, **kwargs))

    return run


def gen_random_str(length: int = 4, use_digits: bool = False) -> str:
    if use_digits:
        choices = ascii_lowercase + digits
    else:
        choices = ascii_lowercase

    return ''.join(random.SystemRandom().choice(choices) for _ in range(length))


def register_shutdown(callback: Callable) -> None:
    atexit.register(callback)
    signal.signal(signal.SIGTERM, callback)
    signal.signal(signal.SIGINT, callback)


def remove_microseconds(dt_: datetime.datetime) -> datetime.datetime:
    return dt_.replace(microsecond=0)

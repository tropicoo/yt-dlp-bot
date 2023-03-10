import asyncio
import random
from functools import partial, wraps
from string import ascii_lowercase
from typing import Any

ASYNC_LOCK = asyncio.Lock()

_UNIT_SIZE_NAMES = ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi')
_BASE = 1024.0


def format_bytes(num: int, suffix: str = "B") -> str:
    """Format bytes to human-readable size."""
    for unit in _UNIT_SIZE_NAMES:
        if abs(num) < _BASE:
            return f"{num:3.1f}{unit}{suffix}"
        num /= _BASE
    return f"{num:.1f}Yi{suffix}"


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


def random_string(number: int) -> str:
    return ''.join(random.choice(ascii_lowercase) for _ in range(number))

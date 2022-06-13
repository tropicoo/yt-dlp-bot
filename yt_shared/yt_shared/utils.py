import asyncio
from functools import partial, wraps
from typing import Any


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

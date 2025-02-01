import asyncio
import atexit
import datetime
import random
import signal
from collections.abc import Callable
from concurrent.futures import Executor
from functools import partial, wraps
from string import ascii_lowercase, digits
from typing import Any, ClassVar, Final

_UNIT_SIZE_NAMES: Final[tuple[str, ...]] = (
    '',
    'Ki',
    'Mi',
    'Gi',
    'Ti',
    'Pi',
    'Ei',
    'Zi',
)
_BASE: Final[float] = 1024.0


def format_bytes(num: int, suffix: str = 'B') -> str:
    """Format bytes to human-readable size."""
    for unit in _UNIT_SIZE_NAMES:
        if abs(num) < _BASE:
            return f'{num:3.1f}{unit}{suffix}'
        num /= _BASE
    return f'{num:.1f}Yi{suffix}'


class Singleton(type):
    """Singleton class."""

    _instances: ClassVar[dict] = {}

    def __call__(cls, *args, **kwargs) -> Any:
        """Check whether instance already exists.

        Return existing or create new instance and save to dict.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def wrap(func: Callable[..., Any]) -> Callable[..., Any]:
    """Run sync code in executor."""

    @wraps(func)
    async def run(
        *args,
        loop: asyncio.AbstractEventLoop | None = None,
        executor: Executor | None = None,
        **kwargs,
    ) -> Any:
        if loop is None:
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, partial(func, *args, **kwargs))

    return run


def gen_random_str(length: int = 4, use_digits: bool = False) -> str:
    choices = ascii_lowercase + digits if use_digits else ascii_lowercase
    return ''.join(random.SystemRandom().choice(choices) for _ in range(length))


def register_shutdown(callback: Callable) -> None:
    atexit.register(callback)
    signal.signal(signal.SIGTERM, callback)
    signal.signal(signal.SIGINT, callback)


def remove_microseconds(dt_: datetime.datetime) -> datetime.datetime:
    return dt_.replace(microsecond=0)


def calculate_aspect_ratio(width: int, height: int) -> tuple[int, int]:
    # Calculate the greatest common divisor using Euclid's algorithm
    def gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a

    divisor = gcd(width, height)

    aspect_width = width // divisor
    aspect_height = height // divisor

    return aspect_width, aspect_height

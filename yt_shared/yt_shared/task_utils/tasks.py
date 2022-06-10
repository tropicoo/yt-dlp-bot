import asyncio
import functools
import logging
from functools import partial, wraps
from typing import Any, Awaitable, Tuple, TypeVar


T = TypeVar('T')


def create_task(
    coroutine: Awaitable[T],
    logger: logging.Logger,
    loop: asyncio.AbstractEventLoop = None,
    task_name: str = None,
    exception_message: str = 'Task raised an exception',
    exception_message_args: Tuple[Any, ...] = (),
    thread_safe: bool = False,
) -> asyncio.Task[T]:
    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning('No running asyncio loop, creating new')
            loop = asyncio.get_event_loop()

    if thread_safe:
        task = asyncio.run_coroutine_threadsafe(coroutine, loop)
    else:
        task = loop.create_task(coroutine, name=task_name)

    task.add_done_callback(
        functools.partial(
            _handle_task_result,
            logger=logger,
            exception_message=exception_message,
            exception_message_args=exception_message_args,
        )
    )
    return task


def _handle_task_result(
    task: asyncio.Task,
    logger: logging.Logger,
    exception_message: str,
    exception_message_args: Tuple[Any, ...] = (),
) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception(exception_message, *exception_message_args)


def wrap(func):
    """Run sync code in executor."""

    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run

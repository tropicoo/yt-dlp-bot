import asyncio
import functools
import logging
from collections.abc import Awaitable
from typing import Any, TypeVar

T = TypeVar('T')


def create_task[T](  # noqa: PLR0913
    coroutine: Awaitable[T],
    logger: logging.Logger,
    loop: asyncio.AbstractEventLoop | None = None,
    task_name: str | None = None,
    exception_message: str = 'Task raised an exception',
    exception_message_args: tuple[Any, ...] = (),
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
    exception_message_args: tuple[Any, ...] = (),
) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception(exception_message, *exception_message_args)
        raise

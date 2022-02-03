import logging
from asyncio import Task
from typing import TYPE_CHECKING

from core.tasks.rabbit_tasks import (
    ErrorResultWorkerTask,
    RabbitTaskType,
    SuccessResultWorkerTask,
)
from yt_shared.task_utils.tasks import create_task

if TYPE_CHECKING:
    from core.bot import VideoBot


class RabbitWorkerManager:
    _TASKS_TYPES = [ErrorResultWorkerTask, SuccessResultWorkerTask]
    _tasks: dict[RabbitTaskType, Task]

    def __init__(self, bot: 'VideoBot') -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._bot = bot
        self._tasks = {}

    async def start_worker_tasks(self) -> None:
        for task_cls in self._TASKS_TYPES:
            self._log.info('Starting %s', task_cls.__name__)
            self._tasks[task_cls.TYPE] = create_task(
                task_cls(self._bot).run(),
                task_name=task_cls.__name__,
                logger=self._log,
                exception_message='Rabbit task %s raised an exception',
                exception_message_args=(task_cls.__name__,),
            )

    def stop_workers(self):
        self._log.info('Stopping %d rabbit tasks', len(self._tasks))
        for task_type, task in self._tasks.items():
            self._log.info('Stopping %s rabbit task', task_type.value)
            task.cancel()

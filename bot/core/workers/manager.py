import logging
from asyncio import Task
from typing import TYPE_CHECKING

from core.workers.abstract import RabbitTaskType
from core.workers.error import ErrorResultWorker
from core.workers.success import SuccessResultWorker
from yt_shared.utils.tasks.tasks import create_task

if TYPE_CHECKING:
    from core.bot import VideoBot


class RabbitWorkerManager:
    _TASK_TYPES = (ErrorResultWorker, SuccessResultWorker)

    def __init__(self, bot: 'VideoBot') -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._bot = bot
        self._tasks: dict[RabbitTaskType, Task] = {}

    async def start_worker_tasks(self) -> None:
        for task_cls in self._TASK_TYPES:
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

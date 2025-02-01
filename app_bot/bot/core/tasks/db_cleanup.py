import asyncio
from collections.abc import Sequence

from yt_shared.db.session import get_db
from yt_shared.repositories.task import TaskRepository
from yt_shared.utils.tasks.abstract import AbstractTask


class DbCleanupTask(AbstractTask):
    _SLEEP_TIME: int = 60

    def __init__(self, user_ids: Sequence[int]) -> None:
        super().__init__()
        self._user_ids = user_ids

    async def run(self) -> None:
        await self._run()

    async def _run(self) -> None:
        while True:
            self._log.info('Deleting DB data')
            await self._delete_data()
            await asyncio.sleep(self._SLEEP_TIME)

    async def _delete_data(self) -> None:
        async for db in get_db():
            await TaskRepository(db=db).purge_user_tasks(user_ids=self._user_ids)

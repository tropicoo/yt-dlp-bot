import asyncio

import uvloop

from worker.core.launcher import WorkerLauncher
from worker.core.log import setup_logging


async def main() -> None:
    setup_logging()
    await WorkerLauncher().start()


if __name__ == '__main__':
    uvloop.install()
    asyncio.run(main())

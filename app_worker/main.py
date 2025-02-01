import asyncio

import uvloop

from worker.core.launcher import WorkerLauncher
from worker.core.log import setup_logging


async def main() -> None:
    """Set up logging and start the worker launcher.

    This function sets up the logging configuration and starts the WorkerLauncher.
    It is intended to be run as the main entry point of the application.
    """
    setup_logging()
    await WorkerLauncher().start()


if __name__ == '__main__':
    uvloop.install()
    asyncio.run(main())

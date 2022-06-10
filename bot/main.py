#!/usr/bin/env python3
"""Bot Launcher Module."""
import asyncio

from core.bot import BotLauncher
from core.utils import setup_logging


async def main() -> None:
    setup_logging()
    await BotLauncher().run()


if __name__ == '__main__':
    asyncio.run(main())

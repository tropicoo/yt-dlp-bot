#!/usr/bin/env python3
"""Bot Launcher Module."""

import asyncio

import uvloop

from bot.bot.launcher import BotLauncher
from bot.core.log import setup_logging


async def main() -> None:
    setup_logging()
    await BotLauncher().run()


if __name__ == '__main__':
    uvloop.install()
    asyncio.run(main())

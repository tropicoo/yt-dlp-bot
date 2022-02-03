import asyncio

from core.launcher import WorkerLauncher


def main() -> None:
    worker = WorkerLauncher()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker.start())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(worker.stop())


if __name__ == '__main__':
    main()

from worker.core.launcher import WorkerLauncher
from worker.core.log import setup_logging


def main() -> None:
    setup_logging()
    WorkerLauncher().start()


if __name__ == '__main__':
    main()

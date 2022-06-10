from core.launcher import WorkerLauncher
from core.log import setup_logging


def main() -> None:
    setup_logging()
    WorkerLauncher().start()


if __name__ == '__main__':
    main()

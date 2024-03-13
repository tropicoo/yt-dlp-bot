import abc
import logging


class AbstractTask(abc.ABC):
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    async def run(self) -> None:
        """Main entry point."""
        pass

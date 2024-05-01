import logging
from abc import ABC, abstractmethod


class AbstractTask(ABC):
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def run(self) -> None:
        """Main entry point."""
        pass

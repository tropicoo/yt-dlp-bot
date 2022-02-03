import logging

from aiogram import Dispatcher

from core.bot import VideoBot
from core.callbacks import TelegramCallback


class BotSetup:
    """Setup everything before bot start."""

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._bot = VideoBot()
        self._dispatcher = Dispatcher(bot=self._bot)
        self._callbacks = TelegramCallback()
        self._register_callbacks()

    def _register_callbacks(self) -> None:
        self._dispatcher.register_message_handler(self._callbacks.on_message)

    def get_bot(self) -> VideoBot:
        return self._bot

    def get_dispatcher(self) -> Dispatcher:
        return self._dispatcher

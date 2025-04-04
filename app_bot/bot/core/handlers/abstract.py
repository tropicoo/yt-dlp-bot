import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from yt_shared.enums import TaskSource, TelegramChatType
from yt_shared.schemas.base_rabbit import BaseRabbitDownloadPayload

from bot.core.schemas import AnonymousUserSchema, UserSchema

if TYPE_CHECKING:
    from bot.bot import VideoBotClient


class AbstractDownloadHandler(ABC):
    def __init__(self, body: BaseRabbitDownloadPayload, bot: 'VideoBotClient') -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._body = body
        self._bot = bot
        self._receiving_users = self._get_receiving_users()

    @abstractmethod
    async def handle(self) -> None:
        pass

    def _get_sender_id(self) -> int | None:
        if self._body.context.source is TaskSource.API:
            return None
        if self._body.context.from_chat_type is TelegramChatType.PRIVATE:
            return self._body.context.from_user_id
        return self._body.context.from_chat_id

    def _get_receiving_users(self) -> list[AnonymousUserSchema | UserSchema]:
        if self._body.context.source is TaskSource.API:
            return self._bot.conf.telegram.api.upload_to_chat_ids.copy()
        return [self._bot.allowed_users[self._get_sender_id()]]

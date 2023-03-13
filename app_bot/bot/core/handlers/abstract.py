import abc
import logging
from typing import TYPE_CHECKING

from yt_shared.enums import TaskSource, TelegramChatType
from yt_shared.schemas.error import ErrorDownloadPayload, ErrorGeneralPayload
from yt_shared.schemas.success import SuccessPayload

from bot.core.config.schema import BaseUserSchema, UserSchema

if TYPE_CHECKING:
    from bot.core.bot import VideoBot


class AbstractHandler(metaclass=abc.ABCMeta):
    def __init__(
        self,
        body: SuccessPayload | ErrorDownloadPayload | ErrorGeneralPayload,
        bot: 'VideoBot',
    ) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._body = body
        self._bot = bot
        self._receiving_users = self._get_receiving_users()

    async def handle(self) -> None:
        await self._handle()

    @abc.abstractmethod
    async def _handle(self, *args, **kwargs) -> None:
        pass

    def _get_sender_id(self) -> int | None:
        if self._body.context.source is TaskSource.API:
            return None
        if self._body.context.from_chat_type is TelegramChatType.PRIVATE:
            return self._body.context.from_user_id
        return self._body.context.from_chat_id

    def _get_receiving_users(self) -> list[BaseUserSchema | UserSchema]:
        if self._body.context.source is TaskSource.API:
            return self._bot.conf.telegram.api.upload_to_chat_ids.copy()
        return [self._bot.allowed_users[self._get_sender_id()]]

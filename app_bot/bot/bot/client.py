import asyncio
import html
import logging
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import RPCError

from bot.core.i18n import t
from bot.core.schemas import ConfigSchema, UserSchema


class VideoBotClient(Client):
    """Extended Pyrogram's `Client` class."""

    _RUN_FOREVER_SLEEP_SECONDS: int = 86400

    def __init__(self, *args, conf: ConfigSchema, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.info('Initializing bot client')
        self.conf = conf

        self.allowed_users: dict[int, UserSchema] = {}
        self.admin_users: dict[int, UserSchema] = {}

        for user in self.conf.telegram.allowed_users:
            self.allowed_users[user.id] = user
            if user.is_admin:
                self.admin_users[user.id] = user

    async def run_forever(self) -> None:
        """Firstly, 'await bot.start()' should be called."""
        if not self.is_initialized:
            raise RuntimeError('Bot was not started (initialized).')
        while True:
            await asyncio.sleep(self._RUN_FOREVER_SLEEP_SECONDS)

    def get_startup_users(self) -> list[int]:
        user_ids: list[int] = []
        for user in self.allowed_users.values():
            if user.send_startup_message:
                user_ids.append(user.id)
        return user_ids

    def language_for(self, *candidate_ids: int | None) -> str:
        """Pick the language to address someone in: theirs, or the global default.

        Several ids may be offered because a group is configured under its chat
        id while the person writing has one of their own; the first that names a
        user with a language of their own wins.
        """
        for candidate_id in candidate_ids:
            user = self.allowed_users.get(candidate_id) if candidate_id else None
            if user is not None and user.lang_code:
                return user.lang_code
        return self.conf.telegram.lang_code

    async def send_startup_message(self) -> None:
        """Send welcome message after bot launch."""
        self._log.info('Sending welcome message')
        await self.send_translated_to_users(
            key='start.startup',
            user_ids=self.get_startup_users(),
            name=html.escape((await self.get_me()).first_name),
        )

    async def send_translated_to_users(
        self, key: str, user_ids: Iterable[int], **params: Any
    ) -> None:
        """Send one message, rendered in each recipient's own language.

        Recipients are grouped by language so a message still costs one render
        and one gather, however many people receive it.
        """
        by_language: dict[str, list[int]] = defaultdict(list)
        for user_id in user_ids:
            by_language[self.language_for(user_id)].append(user_id)
        for language, ids in by_language.items():
            await self.send_message_to_users(
                text=t(key, language, **params), user_ids=ids
            )

    async def send_translated_to_admins(self, key: str, **params: Any) -> None:
        await self.send_translated_to_users(
            key=key, user_ids=self.admin_users.keys(), **params
        )

    async def send_message_to_users(
        self, text: str, user_ids: Iterable[int], parse_mode: ParseMode = ParseMode.HTML
    ) -> None:
        coros = []
        self._log.debug('Sending message "%s" to chat ids %s', text, user_ids)
        for user_id in user_ids:
            coros.append(self.send_message(user_id, text, parse_mode=parse_mode))
        results = await asyncio.gather(*coros, return_exceptions=True)
        for user_id, result in zip(user_ids, results, strict=False):
            if isinstance(result, RPCError):
                self._log.error('User %s did not receive message: %s', user_id, result)

    async def send_message_all(
        self, text: str, parse_mode: ParseMode = ParseMode.HTML
    ) -> None:
        """Send a message to all defined user IDs in config.json."""
        await self.send_message_to_users(
            text=text, user_ids=self.allowed_users.keys(), parse_mode=parse_mode
        )

    async def send_message_admins(
        self, text: str, parse_mode: ParseMode = ParseMode.HTML
    ) -> None:
        """Send a message to all defined user IDs in config.json."""
        await self.send_message_to_users(
            text=text, user_ids=self.admin_users.keys(), parse_mode=parse_mode
        )

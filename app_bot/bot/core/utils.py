"""Utils module."""

import asyncio
from datetime import datetime
from typing import Generator, Iterable
from urllib.parse import urlparse

from pyrogram.enums import ChatType
from pyrogram.types import Message

from bot.core.config import settings
from bot.core.schema import AnonymousUserSchema, ConfigSchema, UserSchema


async def shallow_sleep_async(sleep_time: float = 0.1) -> None:
    await asyncio.sleep(sleep_time)


def format_ts(ts: float, time_format: str = '%a %b %d %H:%M:%S %Y') -> str:
    return datetime.fromtimestamp(ts).strftime(time_format)


def bold(text: str) -> str:
    """Wrap input string in HTML bold tag."""
    return f'<b>{text}</b>'


def code(text: str) -> str:
    """Wrap input string in HTML code tag."""
    return f'<code>{text}</code>'


def get_user_info(message: Message) -> str:
    """Return user information who interacts with bot."""
    chat = message.chat
    return (
        f'Request from user_id: {chat.id}, username: {chat.username}, '
        f'full name: {chat.first_name} {chat.last_name}'
    )


def get_user_id(message: Message) -> int:
    """Make explicit selection to not forget how this works since we just can return
    `message.chat.id` for all cases.
    """
    match message.chat.type:
        case ChatType.PRIVATE:
            return message.from_user.id
        case ChatType.GROUP:
            return message.chat.id
        case _:
            return message.chat.id


def build_command_presentation(commands: dict[str, list]) -> str:
    groups = []
    for desc, cmds in commands.items():
        groups.append('{0}\n{1}'.format(desc, '\n'.join(['/' + c for c in cmds])))
    return '\n\n'.join(groups)


def split_telegram_message(
    text: str,
    chunk_size: int = settings.TG_MAX_MSG_SIZE,
    return_first: bool = False,
    negate: bool = False,
) -> Generator[str, None, None]:
    text_len = len(text)
    if text_len > chunk_size:
        for x in range(0, text_len, chunk_size):
            if negate:
                yield text[-chunk_size - x : text_len - x]
            else:
                yield text[x : x + chunk_size]
            if return_first:
                break
    else:
        yield text


def can_remove_url_params(url: str, matching_hosts: Iterable[str]) -> bool:
    return urlparse(url).netloc in set(matching_hosts)


def is_user_upload_silent(
    user: UserSchema | AnonymousUserSchema, conf: ConfigSchema
) -> bool:
    if isinstance(user, AnonymousUserSchema):
        return conf.telegram.api.silent
    return user.upload.silent

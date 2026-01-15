"""Storage for pending download requests awaiting user format selection."""

import logging
from dataclasses import dataclass
from typing import ClassVar

from yt_shared.enums import TelegramChatType

from bot.core.schemas import UserSchema


@dataclass
class PendingDownload:
    """Pending download request data."""

    url: str
    original_url: str
    from_chat_id: int
    from_chat_type: TelegramChatType
    from_user_id: int | None
    message_id: int
    ack_message_id: int
    save_to_storage: bool
    user: UserSchema


class PendingDownloadsStore:
    """In-memory store for pending download requests.

    Uses a simple dict with url_id as key. URL ID is generated from
    message_id and chat_id to ensure uniqueness.
    """

    _store: ClassVar[dict[str, PendingDownload]] = {}
    _log = logging.getLogger('PendingDownloadsStore')

    @classmethod
    def generate_url_id(cls, chat_id: int, message_id: int) -> str:
        """Generate unique URL ID from chat and message IDs."""
        return f'{chat_id}_{message_id}'

    @classmethod
    def add(cls, url_id: str, pending: PendingDownload) -> None:
        """Add pending download to store."""
        cls._log.debug('Adding pending download: %s', url_id)
        cls._store[url_id] = pending

    @classmethod
    def get(cls, url_id: str) -> PendingDownload | None:
        """Get pending download by URL ID."""
        return cls._store.get(url_id)

    @classmethod
    def remove(cls, url_id: str) -> PendingDownload | None:
        """Remove and return pending download by URL ID."""
        cls._log.debug('Removing pending download: %s', url_id)
        return cls._store.pop(url_id, None)

    @classmethod
    def clear(cls) -> None:
        """Clear all pending downloads."""
        cls._store.clear()

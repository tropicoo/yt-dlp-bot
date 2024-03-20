import abc
import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import (
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    model_validator,
)

from yt_shared.enums import DownMediaType, MediaFileType, TaskSource, TelegramChatType
from yt_shared.schemas.base import RealBaseModel
from yt_shared.utils.common import format_bytes
from yt_shared.utils.file import file_size


class InbMediaPayload(RealBaseModel):
    """RabbitMQ inbound media payload from Telegram Bot or API service."""

    id: uuid.UUID | None = None
    from_chat_id: StrictInt | None
    from_chat_type: TelegramChatType | None
    from_user_id: StrictInt | None
    message_id: StrictInt | None
    ack_message_id: StrictInt | None
    url: StrictStr
    original_url: StrictStr
    source: TaskSource
    save_to_storage: StrictBool
    download_media_type: DownMediaType
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseMedia(RealBaseModel, abc.ABC):
    """Model representing abstract downloaded media with common fields."""

    file_type: MediaFileType
    title: StrictStr
    filename: StrictStr
    filepath: StrictStr
    file_size: StrictInt
    duration: StrictFloat | None = None
    orm_file_id: uuid.UUID | None = None

    saved_to_storage: StrictBool = False
    storage_path: StrictStr | None = None

    is_converted: StrictBool = False
    converted_filepath: StrictStr | None = None
    converted_filename: StrictStr | None = None
    converted_file_size: StrictInt | None = None

    def file_size_human(self) -> str:
        return format_bytes(num=self.current_file_size())

    def current_file_size(self) -> int:
        if self.converted_file_size is not None:
            return self.converted_file_size
        return self.file_size

    def mark_as_saved_to_storage(self, storage_path: str) -> None:
        self.storage_path = storage_path
        self.saved_to_storage = True

    def mark_as_converted(self, filepath: str) -> None:
        self.converted_filepath = filepath
        self.converted_filename = filepath.rsplit('/', 1)[-1]
        self.converted_file_size = file_size(filepath)
        self.is_converted = True


class Audio(BaseMedia):
    """Model representing downloaded audio file."""

    file_type: Literal[MediaFileType.AUDIO] = MediaFileType.AUDIO


class Video(BaseMedia):
    """Model representing downloaded video file with separate thumbnail."""

    file_type: Literal[MediaFileType.VIDEO] = MediaFileType.VIDEO
    thumb_name: StrictStr | None = None
    width: int | float | None = None
    height: int | float | None = None
    thumb_path: StrictStr | None = None

    @model_validator(mode='before')
    @classmethod
    def _set_fields(cls, values: dict) -> dict:
        if not values['thumb_name']:
            values['thumb_name'] = f'{values["filename"]}-thumb.jpg'
        return values


class DownMedia(RealBaseModel):
    """Downloaded media (audio, video with muxed audio or both) object context."""

    audio: Audio | None
    video: Video | None

    media_type: DownMediaType
    root_path: StrictStr
    meta: dict

    @model_validator(mode='before')
    @classmethod
    def _validate(cls, values: dict) -> dict:
        if values['audio'] is None and values['video'] is None:
            raise ValueError('Provide audio, video or both.')
        return values

    def get_media_objects(self) -> tuple[Audio | Video, ...]:
        return tuple(filter(None, (self.audio, self.video)))

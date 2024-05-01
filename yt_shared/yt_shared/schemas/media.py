import uuid
from abc import ABC
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from PIL import Image
from pydantic import (
    ConfigDict,
    DirectoryPath,
    Field,
    FilePath,
    model_validator,
)
from typing_extensions import Annotated, Self

from yt_shared.enums import DownMediaType, MediaFileType, TaskSource, TelegramChatType
from yt_shared.schemas.base import StrictRealBaseModel
from yt_shared.utils.common import calculate_aspect_ratio, format_bytes
from yt_shared.utils.file import file_size


class InbMediaPayload(StrictRealBaseModel):
    """RabbitMQ inbound media payload from Telegram Bot or API service."""

    model_config = ConfigDict(**StrictRealBaseModel.model_config, frozen=True)

    id: uuid.UUID | None = None
    from_chat_id: int | None
    from_chat_type: TelegramChatType | None
    from_user_id: int | None
    message_id: int | None
    ack_message_id: int | None
    url: str
    original_url: str
    source: TaskSource
    save_to_storage: bool
    download_media_type: DownMediaType
    custom_filename: str | None
    automatic_extension: bool
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseMedia(StrictRealBaseModel, ABC):
    """Model representing abstract downloaded media with common fields."""

    file_type: MediaFileType
    title: str
    original_filename: str
    directory_path: Annotated[DirectoryPath, Field(strict=False)]
    file_size: int
    duration: float | None = None
    orm_file_id: uuid.UUID | None = None

    saved_to_storage: bool = False
    storage_path: Annotated[Path, Field(strict=False)] | None = None

    is_converted: bool = False
    converted_filename: str | None = None
    converted_file_size: int | None = None

    custom_filename: str | None = None

    def file_size_human(self) -> str:
        return format_bytes(num=self.current_file_size())

    def current_file_size(self) -> int:
        if self.converted_file_size is not None:
            return self.converted_file_size
        return self.file_size

    @property
    def current_filename(self) -> str:
        if self.custom_filename:
            return self.custom_filename
        if self.is_converted:
            return self.converted_filename
        return self.original_filename

    @property
    def current_filepath(self) -> Path:
        if self.custom_filename:
            filename = self.custom_filename
        elif self.is_converted:
            filename = self.converted_filename
        else:
            filename = self.original_filename
        return self.directory_path / filename

    def mark_as_saved_to_storage(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.saved_to_storage = True

    def mark_as_converted(self, filepath: Path) -> None:
        self.converted_filename = filepath.name
        self.converted_file_size = file_size(filepath)
        self.is_converted = True


class Audio(BaseMedia):
    """Model representing downloaded audio file."""

    file_type: Literal[MediaFileType.AUDIO] = MediaFileType.AUDIO


class Video(BaseMedia):
    """Model representing downloaded video file with separate thumbnail."""

    file_type: Literal[MediaFileType.VIDEO] = MediaFileType.VIDEO
    thumb_name: str | None = None
    width: int | float | None = None
    height: int | float | None = None
    thumb_path: Annotated[FilePath, Field(strict=False)] | None = None

    @model_validator(mode='after')
    def set_thumb_name(self) -> Self:
        if not self.thumb_name:
            self.thumb_name = f'{self.current_filename}-thumb.jpg'
        return self

    @property
    def aspect_ratio(self) -> tuple[int, int] | None:
        if self.width and self.height:
            return calculate_aspect_ratio(
                width=int(self.width), height=int(self.height)
            )
        return None

    @property
    def thumb_aspect_ratio(self) -> tuple[int, int] | None:
        if not self.thumb_path:
            return None
        with Image.open(self.thumb_path) as thumb:
            width, height = thumb.size
        return calculate_aspect_ratio(width=width, height=height)


class DownMedia(StrictRealBaseModel):
    """Downloaded media (audio, video with muxed audio or both) object context."""

    audio: Audio | None
    video: Video | None

    media_type: Annotated[DownMediaType, Field(strict=False)]
    root_path: Annotated[DirectoryPath, Field(strict=False)]
    meta: dict

    @model_validator(mode='after')
    def validate_media(self) -> Self:
        if not (self.audio or self.video):
            raise ValueError('Provide audio, video or both.')
        return self

    def get_media_objects(self) -> tuple[Audio | Video, ...]:
        return tuple(filter(None, (self.audio, self.video)))

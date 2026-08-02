from abc import ABC
from typing import Annotated

from pydantic import AfterValidator, Field, PositiveInt, field_validator
from yt_shared.enums import DownMediaType, YtdlpReleaseChannelType
from yt_shared.schemas.base import StrictBaseConfigModel

from bot.core.i18n import LANGUAGES


def _validate_language(value: str) -> str:
    """Reject an unknown language here rather than silently speaking English."""
    language = value.strip().lower()
    if language not in LANGUAGES:
        raise ValueError(
            f'unsupported language "{value}", choose one of: {", ".join(LANGUAGES)}'
        )
    return language


Language = Annotated[str, AfterValidator(_validate_language)]


class _BaseUserSchema(StrictBaseConfigModel, ABC):
    id: int


class AnonymousUserSchema(_BaseUserSchema):
    pass


class VideoCaptionSchema(StrictBaseConfigModel):
    include_title: bool
    include_filename: bool
    include_link: bool
    include_size: bool


class UploadSchema(StrictBaseConfigModel):
    upload_video_file: bool
    upload_video_max_file_size: PositiveInt
    forward_to_group: bool
    forward_group_id: int | None
    silent: bool
    video_caption: VideoCaptionSchema


class UserSchema(_BaseUserSchema):
    is_admin: bool
    send_startup_message: bool
    download_media_type: Annotated[DownMediaType, Field(strict=False)]
    save_to_storage: bool
    use_url_regex_match: bool
    upload: UploadSchema
    save_to_database: bool = True
    # Leave unset to follow telegram.delete_source_message; set it here to opt
    # this user in or out regardless of the global default.
    delete_source_message: bool | None = None
    # Leave unset to follow telegram.lang_code.
    lang_code: Language | None = None


class ApiSchema(StrictBaseConfigModel):
    upload_video_file: bool
    upload_video_max_file_size: PositiveInt
    upload_to_chat_ids: list[AnonymousUserSchema]
    silent: bool
    video_caption: VideoCaptionSchema

    @field_validator('upload_to_chat_ids', mode='before')
    @classmethod
    def transform_chat_ids(cls, values: list[int]) -> list[AnonymousUserSchema]:
        return [AnonymousUserSchema(id=id_) for id_ in values]


class TelegramSchema(StrictBaseConfigModel):
    api_id: int
    api_hash: str
    token: str
    # The language everyone gets unless they set their own below.
    lang_code: Language
    max_upload_tasks: PositiveInt
    url_validation_regexes: list[str]
    # Default for everyone; a user may still opt out individually.
    delete_source_message: bool = False
    allowed_users: list[UserSchema]
    api: ApiSchema


class YtdlpSchema(StrictBaseConfigModel):
    version_check_enabled: bool
    version_check_interval: PositiveInt
    notify_users_on_new_version: bool
    release_channel: Annotated[YtdlpReleaseChannelType, Field(strict=False)]


class ConfigSchema(StrictBaseConfigModel):
    telegram: TelegramSchema
    ytdlp: YtdlpSchema

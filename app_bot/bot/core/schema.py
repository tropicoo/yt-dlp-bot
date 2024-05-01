from abc import ABC

from pydantic import Field, PositiveInt, StringConstraints, field_validator
from typing_extensions import Annotated
from yt_shared.enums import DownMediaType
from yt_shared.schemas.base import StrictBaseConfigModel

_LANG_CODE_LEN = 2
_LANG_CODE_REGEX = rf'^[a-z]{{{_LANG_CODE_LEN}}}$'


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
    lang_code: Annotated[
        str, StringConstraints(pattern=_LANG_CODE_REGEX, to_lower=True)
    ]
    max_upload_tasks: PositiveInt
    url_validation_regexes: list[str]
    allowed_users: list[UserSchema]
    api: ApiSchema


class YtdlpSchema(StrictBaseConfigModel):
    version_check_enabled: bool
    version_check_interval: PositiveInt
    notify_users_on_new_version: bool


class ConfigSchema(StrictBaseConfigModel):
    telegram: TelegramSchema
    ytdlp: YtdlpSchema

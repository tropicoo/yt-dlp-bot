from enum import StrEnum, unique


@unique
class StrChoiceEnum(StrEnum):
    @classmethod
    def choices(cls) -> tuple[str, ...]:
        return tuple(x.value for x in cls)


class TaskStatus(StrChoiceEnum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    FAILED = 'FAILED'
    DONE = 'DONE'


class TaskSource(StrChoiceEnum):
    API = 'API'
    BOT = 'BOT'


class RabbitPayloadType(StrChoiceEnum):
    DOWNLOAD_ERROR = 'DOWNLOAD_ERROR'
    GENERAL_ERROR = 'GENERAL_ERROR'
    SUCCESS = 'SUCCESS'


class TelegramChatType(StrChoiceEnum):
    PRIVATE = 'private'
    BOT = 'bot'
    GROUP = 'group'
    SUPERGROUP = 'supergroup'
    CHANNEL = 'channel'


class DownMediaType(StrChoiceEnum):
    """Media can be audio, video or both.

    1. Only download/extract audio
    2. Video with muxed audio
    3. Both 1) and 2)
    """

    AUDIO = 'AUDIO'
    VIDEO = 'VIDEO'
    AUDIO_VIDEO = 'AUDIO_VIDEO'


class MediaFileType(StrChoiceEnum):
    AUDIO = 'AUDIO'
    VIDEO = 'VIDEO'

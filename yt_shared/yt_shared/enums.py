import enum


@enum.unique
class ChoiceEnum(enum.Enum):
    @classmethod
    def choices(cls) -> tuple[str, ...]:
        return tuple(x.value for x in cls)


class TaskStatus(str, ChoiceEnum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    FAILED = 'FAILED'
    DONE = 'DONE'


class TaskSource(str, ChoiceEnum):
    API = 'API'
    BOT = 'BOT'


class RabbitPayloadType(ChoiceEnum):
    DOWNLOAD_ERROR = 'ERROR_DOWNLOAD'
    GENERAL_ERROR = 'GENERAL_ERROR'
    SUCCESS = 'SUCCESS'


class TelegramChatType(ChoiceEnum):
    PRIVATE = 'private'
    BOT = 'bot'
    GROUP = 'group'
    SUPERGROUP = 'supergroup'
    CHANNEL = 'channel'

from enum import Enum, auto, unique


@unique
class ChoiceEnum(Enum):
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
    DOWNLOAD_ERROR = auto()
    GENERAL_ERROR = auto()
    SUCCESS = auto()


class TelegramChatType(ChoiceEnum):
    PRIVATE = 'private'
    BOT = 'bot'
    GROUP = 'group'
    SUPERGROUP = 'supergroup'
    CHANNEL = 'channel'

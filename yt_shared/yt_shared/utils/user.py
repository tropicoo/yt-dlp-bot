from pyrogram.enums import ChatType
from pyrogram.types import Message


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

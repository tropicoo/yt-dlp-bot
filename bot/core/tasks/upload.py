import os
from typing import Optional, TYPE_CHECKING

from pyrogram.enums import ChatAction, ParseMode
from pyrogram.types import Message
from tenacity import retry, stop_after_attempt, wait_fixed

from core.config import settings
from core.utils import bold
from yt_shared.db import get_db
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.cache import CacheSchema
from yt_shared.schemas.success import SuccessPayload
from yt_shared.task_utils.abstract import AbstractTask

if TYPE_CHECKING:
    from core.bot import VideoBot


class UploadTask(AbstractTask):
    def __init__(self, body: SuccessPayload, bot: 'VideoBot') -> None:
        super().__init__()
        self._body = body
        self.filename = body.filename
        self.filepath = os.path.join(settings.TMP_DOWNLOAD_PATH, self.filename)
        self.thumb_path = os.path.join(settings.TMP_DOWNLOAD_PATH, body.thumb_name)
        self._bot = bot

    async def run(self) -> None:
        text = f'⬆️ {bold("Uploading")} {self.filename}'
        self._log.info(text)
        try:
            await self._bot.send_message(
                chat_id=self._body.from_user_id,
                text=text,
                reply_to_message_id=self._body.message_id,
                parse_mode=ParseMode.HTML,
            )
            message = await self._upload_video_file()
            if message:
                await self._save_cache(message)
        except Exception:
            self._log.exception('Something went wrong during video file upload')

    @retry(wait=wait_fixed(10), stop=stop_after_attempt(10), reraise=True)
    async def _upload_video_file(self) -> Optional[Message]:
        user_id = self._body.from_user_id
        self._log.info('Uploading to user id %s', user_id)
        try:
            await self._bot.send_chat_action(user_id, action=ChatAction.UPLOAD_VIDEO)
            return await self._bot.send_video(
                chat_id=user_id,
                caption=self._generate_video_caption(),
                file_name=self.filename,
                video=self.filepath,
                duration=self._body.duration or 0,
                height=self._body.height or 0,
                width=self._body.width or 0,
                thumb=self.thumb_path,
                supports_streaming=True,
            )
        except Exception:
            self._log.exception('Failed to upload %s', self.filename)
            raise

    def _generate_video_caption(self) -> str:
        return (
            f'{bold("Title:")} {self._body.title}\n'
            f'{bold("Filename:")} {self.filename}\n'
            f'{bold("URL:")} {self._body.context.url}'
        )

    async def _save_cache(self, message: Message) -> None:
        self._log.debug('Saving telegram file cache - %s', message)
        cache = CacheSchema(
            cache_id=message.video.file_id,
            cache_unique_id=message.video.file_unique_id,
            file_size=message.video.file_size,
            date_timestamp=message.video.date,
        )

        async for db in get_db():
            await TaskRepository().save_file_cache(
                cache=cache, task_id=self._body.task_id, db=db
            )

import os
from typing import Optional, TYPE_CHECKING

from pyrogram.enums import ChatAction
from pyrogram.types import Message
from tenacity import retry, stop_after_attempt, wait_fixed

from core.tasks.abstract import AbstractTask
from core.utils import bold
from yt_shared.config import TMP_DOWNLOAD_PATH
from yt_shared.db import get_db
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.cache import CacheSchema
from yt_shared.schemas.success import SuccessPayload

if TYPE_CHECKING:
    from core.bot import VideoBot


class UploadTask(AbstractTask):
    def __init__(self, body: SuccessPayload, bot: 'VideoBot') -> None:
        super().__init__()
        self._body = body
        self.filename = body.filename
        self.filepath = os.path.join(TMP_DOWNLOAD_PATH, self.filename)
        self.thumb_path = os.path.join(TMP_DOWNLOAD_PATH, body.thumb_name)
        self._bot = bot

    async def run(self) -> None:
        tg_msg = f'⬆️ {bold("Uploading")} {self.filename}'
        self._log.info(tg_msg)
        try:
            await self._bot.send_message(self._body.from_user_id, tg_msg)
            message = await self._upload_video_file()
            if message:
                await self._save_cache(message)
        except Exception:
            self._log.exception('Something went wrong during video file upload')

    @retry(wait=wait_fixed(10), stop=stop_after_attempt(10), reraise=True)
    async def _upload_video_file(self) -> Optional[Message]:
        user_id = self._body.from_user_id
        try:
            self._log.info('Uploading for user id %s', user_id)
            await self._bot.send_chat_action(user_id, action=ChatAction.UPLOAD_VIDEO)
            return await self._bot.send_video(
                chat_id=user_id,
                caption=self.filename,
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

import asyncio
import os
from itertools import chain
from typing import Coroutine, TYPE_CHECKING

from pydantic import StrictInt, StrictStr
from pyrogram.enums import ChatAction, MessageMediaType, ParseMode
from pyrogram.types import Animation, Message, Video
from tenacity import retry, stop_after_attempt, wait_fixed

from core.config import settings
from core.config.config import get_main_config
from core.config.schema import BaseUserSchema, UserSchema
from core.utils import bold
from yt_shared.db import get_db
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.base import RealBaseModel
from yt_shared.schemas.cache import CacheSchema
from yt_shared.schemas.success import SuccessPayload
from yt_shared.utils.tasks.abstract import AbstractTask
from yt_shared.utils.tasks.tasks import create_task

if TYPE_CHECKING:
    from core.bot import VideoBot


class VideoContext(RealBaseModel):
    caption: StrictStr
    file_name: StrictStr
    video_path: StrictStr
    duration: StrictInt
    height: StrictInt
    width: StrictInt
    thumb: StrictStr
    type: MessageMediaType


class UploadTask(AbstractTask):
    def __init__(
        self,
        body: SuccessPayload,
        users: list[BaseUserSchema | UserSchema],
        bot: 'VideoBot',
    ) -> None:
        super().__init__()
        self._config = get_main_config()
        self._body = body
        self.filename = body.filename
        self.filepath = os.path.join(settings.TMP_DOWNLOAD_PATH, self.filename)
        self.thumb_path = os.path.join(settings.TMP_DOWNLOAD_PATH, body.thumb_name)
        self._bot = bot
        self._users = users
        self._upload_chat_ids, self._forward_chat_ids = self._get_upload_chat_ids()

        self._video_ctx = self._create_video_context()
        self._cached_message: Message | None = None

    async def run(self) -> None:
        try:
            await self._send_upload_text()
            await self._upload_video_file()
        except Exception:
            self._log.exception('Exception in upload task for "%s"', self.filename)

    async def _send_upload_text(self) -> None:
        text = f'⬆️ {bold("Uploading")} {self.filename}'
        coros = []
        for chat_id in self._upload_chat_ids:
            kwargs = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': ParseMode.HTML,
            }
            if self._body.message_id:
                kwargs['reply_to_message_id'] = self._body.message_id
            coros.append(self._bot.send_message(**kwargs))
        await asyncio.gather(*coros)

    def _get_upload_chat_ids(self) -> tuple[list[int], list[int]]:
        chat_ids = []
        forward_chat_ids = []
        for user in self._users:
            chat_ids.append(user.id)
            if isinstance(user, UserSchema):
                if user.upload.forward_to_group and user.upload.forward_group_id:
                    forward_chat_ids.append(user.upload.forward_group_id)
        return chat_ids, forward_chat_ids

    async def _upload_video_file(self) -> None:
        for chat_id in chain(self._upload_chat_ids, self._forward_chat_ids):
            self._log.info('Uploading "%s" to chat id "%d"', self.filename, chat_id)
            await self._bot.send_chat_action(chat_id, action=ChatAction.UPLOAD_VIDEO)
            try:
                message = await self.__upload(chat_id=chat_id)
            except Exception:
                self._log.error(
                    'Failed to upload "%s" to "%d"',
                    self._video_ctx.video_path,
                    chat_id,
                )
                raise

            self._log.debug('Telegram response message: %s', message)
            if not self._cached_message and message:
                self._cache_data(message)

    @retry(wait=wait_fixed(3), stop=stop_after_attempt(3), reraise=True)
    async def __upload(self, chat_id: int) -> Message | None:
        self._log.debug('Uploading to "%d" with context: %s', chat_id, self._video_ctx)
        return await self._generate_send_media_coroutine(chat_id)

    def _generate_send_media_coroutine(self, chat_id: int) -> Coroutine:
        kwargs = {
            'chat_id': chat_id,
            'caption': self._video_ctx.caption,
            'file_name': self._video_ctx.file_name,
            'duration': self._video_ctx.duration,
            'height': self._video_ctx.height,
            'width': self._video_ctx.width,
            'thumb': self._video_ctx.thumb,
        }
        if self._video_ctx.type is MessageMediaType.ANIMATION:
            send_func_name = 'send_animation'
            kwargs['animation'] = self._video_ctx.video_path
        else:
            send_func_name = 'send_video'
            kwargs['video'] = self._video_ctx.video_path
            kwargs['supports_streaming'] = True
        return getattr(self._bot, send_func_name)(**kwargs)

    def _cache_data(self, message: Message) -> None:
        self._log.info('Saving telegram file cache')
        video = message.video or message.animation
        if not video:
            err_msg = 'Telegram message response does not contain video or animation'
            self._log.error('%s: %s', err_msg, message)
            raise RuntimeError(err_msg)

        self._video_ctx.type = message.media
        self._video_ctx.video_path = video.file_id
        self._video_ctx.thumb = video.thumbs[0].file_id
        self._cached_message = message

        db_cache_task_name = 'Save cache to DB'
        create_task(
            self._save_cache_to_db(video),
            task_name=db_cache_task_name,
            logger=self._log,
            exception_message='Task %s raised an exception',
            exception_message_args=(db_cache_task_name,),
        )

    def _create_video_context(self) -> VideoContext:
        return VideoContext(
            caption=self._generate_video_caption(),
            file_name=self.filename,
            video_path=self.filepath,
            duration=self._body.duration or 0,
            height=self._body.height or 0,
            width=self._body.width or 0,
            thumb=self.thumb_path,
            type=MessageMediaType.VIDEO,
        )

    def _generate_video_caption(self) -> str:
        return (
            f'{bold("Title:")} {self._body.title}\n'
            f'{bold("URL:")} {self._body.context.url}'
        )

    async def _save_cache_to_db(self, video: Video | Animation) -> None:
        cache = CacheSchema(
            cache_id=video.file_id,
            cache_unique_id=video.file_unique_id,
            file_size=video.file_size,
            date_timestamp=video.date,
        )

        async for db in get_db():
            await TaskRepository().save_file_cache(
                cache=cache, task_id=self._body.task_id, db=db
            )

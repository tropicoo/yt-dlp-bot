import abc
import asyncio
from itertools import chain
from typing import TYPE_CHECKING, Coroutine

from pydantic import StrictBool, StrictFloat, StrictInt, StrictStr
from pyrogram.enums import ChatAction, MessageMediaType, ParseMode
from pyrogram.types import Animation, Message
from pyrogram.types import Audio as _Audio
from pyrogram.types import Video as _Video
from tenacity import retry, stop_after_attempt, wait_fixed
from yt_shared.db.session import get_db
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.base import RealBaseModel
from yt_shared.schemas.cache import CacheSchema
from yt_shared.schemas.media import BaseMedia, Video
from yt_shared.schemas.success import SuccessPayload
from yt_shared.utils.tasks.abstract import AbstractTask
from yt_shared.utils.tasks.tasks import create_task

from bot.core.config.config import get_main_config
from bot.core.config.schema import BaseUserSchema, UserSchema
from bot.core.utils import bold

if TYPE_CHECKING:
    from bot.core.bot import VideoBot


class BaseUploadContext(RealBaseModel):
    caption: StrictStr
    filename: StrictStr
    filepath: StrictStr
    duration: StrictFloat
    type: MessageMediaType
    is_cached: StrictBool = False


class VideoUploadContext(BaseUploadContext):
    height: StrictInt
    width: StrictInt
    thumb: StrictStr


class AudioUploadContext(BaseUploadContext):
    pass


class AbstractUploadTask(AbstractTask, metaclass=abc.ABCMeta):
    _UPLOAD_ACTION: ChatAction

    def __init__(
        self,
        media_object: BaseMedia,
        users: list[BaseUserSchema | UserSchema],
        bot: 'VideoBot',
        semaphore: asyncio.Semaphore,
        context: SuccessPayload,
    ) -> None:
        super().__init__()
        self._config = get_main_config()
        self._media_object = media_object
        self._filename = media_object.filename
        self._filepath = media_object.filepath
        self._bot = bot
        self._users = users
        self._semaphore = semaphore
        self._ctx = context
        self._media_ctx = self._create_media_context()

        self._upload_chat_ids, self._forward_chat_ids = self._get_upload_chat_ids()
        self._cached_message: Message | None = None

    async def run(self) -> None:
        async with self._semaphore:
            self._log.debug('Semaphore for "%s" acquired', self._filename)
            await self._run()
        self._log.debug('Semaphore for "%s" released', self._filename)

    async def _run(self) -> None:
        try:
            await asyncio.gather(*(self._send_upload_text(), self._upload_file()))
        except Exception:
            self._log.exception('Exception in upload task for "%s"', self._filename)
            raise

    async def _send_upload_text(self) -> None:
        text = (
            f'⬆️ {bold("Uploading")} {self._filename}\n'
            f'📏 {bold("Size")} {self._media_object.file_size_human()}'
        )
        coros = []
        for chat_id in self._upload_chat_ids:
            kwargs = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': ParseMode.HTML,
            }
            if self._ctx.message_id:
                kwargs['reply_to_message_id'] = self._ctx.message_id
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

    @retry(wait=wait_fixed(3), stop=stop_after_attempt(3), reraise=True)
    async def __upload(self, chat_id: int) -> Message | None:
        self._log.debug('Uploading to "%d" with context: %s', chat_id, self._media_ctx)
        return await self._generate_send_media_coroutine(chat_id)

    @abc.abstractmethod
    def _generate_send_media_coroutine(self, chat_id: int) -> Coroutine:
        pass

    @abc.abstractmethod
    def _create_media_context(self) -> AudioUploadContext | VideoUploadContext:
        pass

    async def _upload_file(self) -> None:
        for chat_id in chain(self._upload_chat_ids, self._forward_chat_ids):
            self._log.info(
                'Uploading "%s" [%s] [cached: %s] to chat id "%d"',
                self._filename,
                self._media_object.file_size_human(),
                self._media_ctx.is_cached,
                chat_id,
            )
            await self._bot.send_chat_action(chat_id, action=self._UPLOAD_ACTION)
            try:
                message = await self.__upload(chat_id=chat_id)
            except Exception:
                self._log.error(
                    'Failed to upload "%s" to "%d"',
                    self._media_ctx.filepath,
                    chat_id,
                )
                raise

            self._log.debug('Telegram response message: %s', message)
            if not self._cached_message and message:
                self._cache_data(message)

    def _create_cache_task(self, cache_object: _Audio | _Video | Animation) -> None:
        self._log.debug('Creating cache task for %s', cache_object)
        db_cache_task_name = 'Save cache to DB'
        create_task(
            self._save_cache_to_db(cache_object),
            task_name=db_cache_task_name,
            logger=self._log,
            exception_message='Task "%s" raised an exception',
            exception_message_args=(db_cache_task_name,),
        )

    @abc.abstractmethod
    def _cache_data(self, message: Message) -> None:
        pass

    async def _save_cache_to_db(self, file: _Audio | _Video | Animation) -> None:
        cache = CacheSchema(
            cache_id=file.file_id,
            cache_unique_id=file.file_unique_id,
            file_size=file.file_size,
            date_timestamp=file.date,
        )

        async for db in get_db():
            await TaskRepository().save_file_cache(
                cache=cache,
                file_id=self._media_object.orm_file_id,
                db=db,
            )


class AudioUploadTask(AbstractUploadTask):
    _UPLOAD_ACTION = ChatAction.UPLOAD_AUDIO
    _media_ctx: AudioUploadContext

    def _generate_send_media_coroutine(self, chat_id: int) -> Coroutine:
        kwargs = {
            'chat_id': chat_id,
            'audio': self._media_ctx.filepath,
            'caption': self._media_ctx.caption,
            'file_name': self._media_ctx.filename,
            'duration': int(self._media_ctx.duration),
        }
        return self._bot.send_audio(**kwargs)

    def _create_media_context(self) -> AudioUploadContext:
        return AudioUploadContext(
            caption=self._generate_file_caption(),
            filename=self._filename,
            filepath=self._filepath,
            duration=self._media_object.duration or 0.0,
            type=MessageMediaType.AUDIO,
        )

    def _cache_data(self, message: Message) -> None:
        self._log.info('Saving telegram file cache')
        audio = message.audio
        if not audio:
            err_msg = 'Telegram message response does not contain audio'
            self._log.error('%s: %s', err_msg, message)
            raise RuntimeError(err_msg)

        self._media_ctx.type = message.media
        self._media_ctx.filepath = audio.file_id
        self._media_ctx.duration = audio.duration
        self._media_ctx.is_cached = True
        self._cached_message = message

        self._create_cache_task(cache_object=audio)

    def _generate_file_caption(self) -> str:
        caption_items = (
            f'{bold("Title:")} {self._media_object.title}',
            f'{bold("Filename:")} {self._filename}',
            f'{bold("URL:")} {self._ctx.context.url}',
            f'{bold("Size:")} {self._media_object.file_size_human()}',
        )
        return '\n'.join(caption_items)


class VideoUploadTask(AbstractUploadTask):
    _UPLOAD_ACTION = ChatAction.UPLOAD_VIDEO
    _media_ctx: VideoUploadContext
    _media_object: Video

    def _create_media_context(self) -> VideoUploadContext:
        return VideoUploadContext(
            caption=self._generate_file_caption(),
            filename=self._filename,
            filepath=self._filepath,
            duration=self._media_object.duration or 0.0,
            height=self._media_object.height or 0,
            width=self._media_object.width or 0,
            thumb=self._media_object.thumb_path,
            type=MessageMediaType.VIDEO,
        )

    def _generate_file_caption(self) -> str:
        caption_items = []
        if self._users[0].is_base_user:
            caption_conf = self._bot.conf.telegram.api.video_caption
        else:
            caption_conf = self._users[0].upload.video_caption

        if caption_conf.include_title:
            caption_items.append(f'{bold("Title:")} {self._media_object.title}')
        if caption_conf.include_filename:
            caption_items.append(f'{bold("Filename:")} {self._filename}')
        if caption_conf.include_link:
            caption_items.append(f'{bold("URL:")} {self._ctx.context.url}')
        if caption_conf.include_size:
            caption_items.append(
                f'{bold("Size:")} {self._media_object.file_size_human()}'
            )
        return '\n'.join(caption_items)

    def _generate_send_media_coroutine(self, chat_id: int) -> Coroutine:
        kwargs = {
            'chat_id': chat_id,
            'caption': self._media_ctx.caption,
            'file_name': self._media_ctx.filename,
            'duration': int(self._media_ctx.duration),
            'height': self._media_ctx.height,
            'width': self._media_ctx.width,
            'thumb': self._media_ctx.thumb,
        }
        if self._media_ctx.type is MessageMediaType.ANIMATION:
            kwargs['animation'] = self._media_ctx.filepath
            return self._bot.send_animation(**kwargs)

        kwargs['video'] = self._media_ctx.filepath
        kwargs['supports_streaming'] = True
        return self._bot.send_video(**kwargs)

    def _cache_data(self, message: Message) -> None:
        self._log.info('Saving telegram file cache')
        video = message.video or message.animation
        if not video:
            err_msg = 'Telegram message response does not contain video or animation'
            self._log.error('%s: %s', err_msg, message)
            raise RuntimeError(err_msg)

        self._media_ctx.type = message.media
        self._media_ctx.filepath = video.file_id
        self._media_ctx.thumb = video.thumbs[0].file_id
        self._media_ctx.is_cached = True
        self._cached_message = message

        self._create_cache_task(cache_object=video)

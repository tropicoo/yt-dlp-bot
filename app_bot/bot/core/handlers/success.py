import asyncio
import os
import traceback

from pyrogram.enums import ParseMode
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.enums import MediaFileType, TaskSource
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.error import ErrorGeneralPayload
from yt_shared.schemas.media import BaseMedia
from yt_shared.schemas.success import SuccessPayload
from yt_shared.utils.file import remove_dir
from yt_shared.utils.tasks.tasks import create_task

from bot.core.handlers.abstract import AbstractHandler
from bot.core.tasks.upload import AudioUploadTask, VideoUploadTask
from bot.core.utils import bold


class SuccessHandler(AbstractHandler):
    _body: SuccessPayload
    _UPLOAD_TASK_MAP = {
        MediaFileType.AUDIO: AudioUploadTask,
        MediaFileType.VIDEO: VideoUploadTask,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._publisher = Publisher()

    async def handle(self) -> None:
        try:
            coro_tasks = []
            for media_object in self._body.media.get_media_objects():
                coro_tasks.append(self._handle(media_object))
            await asyncio.gather(*coro_tasks)
        finally:
            self._cleanup()

    async def _publish_error_message(self, err: Exception) -> None:
        err_payload = ErrorGeneralPayload(
            task_id=self._body.task_id,
            message_id=self._body.message_id,
            from_chat_id=self._body.from_chat_id,
            from_chat_type=self._body.from_chat_type,
            from_user_id=self._body.from_user_id,
            message='Upload error',
            url=self._body.context.url,
            context=self._body.context,
            yt_dlp_version=self._body.yt_dlp_version,
            exception_msg=traceback.format_exc(),
            exception_type=err.__class__.__name__,
        )
        await self._publisher.send_download_error(err_payload)

    async def _handle(self, media_object: BaseMedia) -> None:
        try:
            await self._send_success_text(media_object)
            if self._upload_is_enabled():
                self._validate_file_size_for_upload(media_object)
                await self._create_upload_task(media_object)
            else:
                self._log.warning(
                    'File %s will not be uploaded due to upload configuration',
                    media_object.filepath,
                )
        except Exception as err:
            self._log.exception('Upload of "%s" failed', media_object.filepath)
            await self._publish_error_message(err)

    def _cleanup(self) -> None:
        root_path = self._body.media.root_path
        self._log.info(
            'Final task "%s" cleanup. Removing download content directory "%s" with files %s',
            self._body.task_id,
            root_path,
            os.listdir(root_path),
        )
        remove_dir(root_path)

    async def _create_upload_task(self, media_object: BaseMedia) -> None:
        """Upload video to Telegram chat."""
        semaphore = asyncio.Semaphore(value=self._bot.conf.telegram.max_upload_tasks)
        upload_task_cls = self._UPLOAD_TASK_MAP[media_object.file_type]
        task_name = upload_task_cls.__class__.__name__
        await create_task(
            upload_task_cls(
                media_object=media_object,
                users=self._receiving_users,
                bot=self._bot,
                semaphore=semaphore,
                context=self._body,
            ).run(),
            task_name=task_name,
            logger=self._log,
            exception_message='Task "%s" raised an exception',
            exception_message_args=(task_name,),
        )

    @staticmethod
    def _create_success_text(media_object: BaseMedia) -> str:
        text = f'{SUCCESS_EMOJI} {bold("Downloaded")} {media_object.filename}'
        if media_object.saved_to_storage:
            text = f'{text}\n💾 {bold("Saved to media storage")}'
        return f'{text}\n📏 {bold("Size")} {media_object.file_size_human()}'

    async def _send_success_text(self, media_object: BaseMedia) -> None:
        text = self._create_success_text(media_object)
        for user in self._receiving_users:
            kwargs = {
                'chat_id': user.id,
                'text': text,
                'parse_mode': ParseMode.HTML,
            }
            if self._body.message_id:
                kwargs['reply_to_message_id'] = self._body.message_id
            await self._bot.send_message(**kwargs)

    def _upload_is_enabled(self) -> bool:
        """Check whether upload is allowed for particular user configuration."""
        if self._body.context.source is TaskSource.API:
            return self._bot.conf.telegram.api.upload_video_file

        user = self._bot.allowed_users[self._get_sender_id()]
        return user.upload.upload_video_file

    def _validate_file_size_for_upload(self, media_object: BaseMedia) -> None:
        if self._body.context.source is TaskSource.API:
            max_file_size = self._bot.conf.telegram.api.upload_video_max_file_size
        else:
            user = self._bot.allowed_users[self._get_sender_id()]
            max_file_size = user.upload.upload_video_max_file_size

        if not os.path.exists(media_object.filepath):
            raise ValueError(
                f'{media_object.file_type} {media_object.filepath} not found'
            )

        file_size = os.stat(media_object.filepath).st_size
        if file_size > max_file_size:
            err_msg = (
                f'{media_object.file_type} file size {file_size} bytes bigger than '
                f'allowed {max_file_size} bytes. Will not upload'
            )
            self._log.warning(err_msg)
            raise ValueError(err_msg)

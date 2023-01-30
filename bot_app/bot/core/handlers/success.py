import asyncio
import os
import traceback

from pyrogram.enums import ParseMode
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.enums import TaskSource
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.error import ErrorGeneralPayload
from yt_shared.schemas.success import SuccessPayload
from yt_shared.utils.file import file_cleanup
from yt_shared.utils.tasks.tasks import create_task

from bot.core.config import settings
from bot.core.handlers.abstract import AbstractHandler
from bot.core.tasks.upload import UploadTask


class SuccessHandler(AbstractHandler):
    _body: SuccessPayload

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._publisher = Publisher()

    async def handle(self) -> None:
        try:
            await self._handle()
        except Exception as err:
            await self._publish_error_message(err)

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

    async def _handle(self) -> None:
        await self._send_success_text()
        video_path: str = os.path.join(settings.TMP_DOWNLOAD_PATH, self._body.filename)
        thumb_path: str = os.path.join(
            settings.TMP_DOWNLOAD_PATH, self._body.thumb_name
        )
        try:
            self._validate_file_size_for_upload(video_path)
            await self._create_upload_task()
        except Exception:
            self._log.error('Upload of "%s" failed, performing cleanup', video_path)
            raise
        finally:
            file_cleanup(file_paths=(video_path, thumb_path), log=self._log)

    async def _create_upload_task(self) -> None:
        """Upload video to Telegram chat."""
        semaphore = asyncio.Semaphore(value=self._bot.conf.telegram.max_upload_tasks)
        task_name = UploadTask.__class__.__name__
        await create_task(
            UploadTask(
                body=self._body,
                users=self._receiving_users,
                bot=self._bot,
                semaphore=semaphore,
            ).run(),
            task_name=task_name,
            logger=self._log,
            exception_message='Task "%s" raised an exception',
            exception_message_args=(task_name,),
        )

    async def _send_success_text(self) -> None:
        text = f'{SUCCESS_EMOJI} <b>Downloaded</b> {self._body.filename}'
        for user in self._receiving_users:
            kwargs = {
                'chat_id': user.id,
                'text': text,
                'parse_mode': ParseMode.HTML,
            }
            if self._body.message_id:
                kwargs['reply_to_message_id'] = self._body.message_id
            await self._bot.send_message(**kwargs)

    def _validate_file_size_for_upload(self, video_path: str) -> None:
        if self._body.context.source is TaskSource.API:
            upload_video_file = self._bot.conf.telegram.api.upload_video_file
            max_file_size = self._bot.conf.telegram.api.upload_video_max_file_size
        else:
            user = self._bot.allowed_users[self._get_sender_id()]
            upload_video_file = user.upload.upload_video_file
            max_file_size = user.upload.upload_video_max_file_size

        if not upload_video_file:
            raise ValueError(f'Video {video_path} not found')

        file_size = os.stat(video_path).st_size
        if file_size > max_file_size:
            err_msg = (
                f'Video file size {file_size} bytes bigger then allowed {max_file_size}'
                f' bytes. Will not upload'
            )
            self._log.warning(err_msg)
            raise ValueError(err_msg)

import asyncio
import os
import traceback

from pyrogram.enums import ParseMode
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.enums import TaskSource
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.error import ErrorGeneralPayload
from yt_shared.schemas.success import SuccessPayload
from yt_shared.utils.file import remove_dir
from yt_shared.utils.tasks.tasks import create_task

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
        try:
            if self._upload_is_enabled():
                self._validate_file_size_for_upload()
                await self._create_upload_task()
            else:
                self._log.warning(
                    'File %s will not be uploaded due to upload configuration',
                    self._body.filepath,
                )
        except Exception:
            self._log.exception(
                'Upload of "%s" failed, performing cleanup', self._body.filepath
            )
            raise
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        self._log.info(
            'Final task cleanup. Removing download content directory "%s" with files %s for task "%s"',
            self._body.root_path,
            os.listdir(self._body.root_path),
            self._body.task_id,
        )
        remove_dir(self._body.root_path)

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

    def _upload_is_enabled(self) -> bool:
        """Check whether upload is allowed for particular user configuration."""
        if self._body.context.source is TaskSource.API:
            return self._bot.conf.telegram.api.upload_video_file

        user = self._bot.allowed_users[self._get_sender_id()]
        return user.upload.upload_video_file

    def _validate_file_size_for_upload(self) -> None:
        if self._body.context.source is TaskSource.API:
            max_file_size = self._bot.conf.telegram.api.upload_video_max_file_size
        else:
            user = self._bot.allowed_users[self._get_sender_id()]
            max_file_size = user.upload.upload_video_max_file_size

        if not os.path.exists(self._body.filepath):
            raise ValueError(f'Video {self._body.filepath} not found')

        file_size = os.stat(self._body.filepath).st_size
        if file_size > max_file_size:
            err_msg = (
                f'Video file size {file_size} bytes bigger then allowed {max_file_size}'
                f' bytes. Will not upload'
            )
            self._log.warning(err_msg)
            raise ValueError(err_msg)

import asyncio
import os

from pyrogram.enums import ParseMode

from core.config import settings
from core.handlers.abstract import AbstractHandler
from core.tasks.upload import UploadTask
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.enums import TaskSource
from yt_shared.schemas.success import SuccessPayload
from yt_shared.utils.file import file_cleanup
from yt_shared.utils.tasks.tasks import create_task


class SuccessHandler(AbstractHandler):
    _body: SuccessPayload

    async def handle(self) -> None:
        await self._handle()

    async def _handle(self) -> None:
        await self._send_success_text()
        video_path: str = os.path.join(settings.TMP_DOWNLOAD_PATH, self._body.filename)
        thumb_path: str = os.path.join(
            settings.TMP_DOWNLOAD_PATH, self._body.thumb_name
        )
        try:
            if not self._eligible_for_upload(video_path):
                self._log.warning(
                    'File %s will not be uploaded to Telegram', self._body.filename
                )
                return
            await self._create_upload_task()
        except Exception:
            self._log.error('Upload of "%s" failed, performing cleanup', video_path)
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

    def _eligible_for_upload(self, video_path: str) -> bool:
        if self._body.context.source is TaskSource.API:
            upload_video_file = self._bot.conf.telegram.api.upload_video_file
            max_file_size = self._bot.conf.telegram.api.upload_video_max_file_size
        else:
            user = self._bot.allowed_users[self._get_sender_id()]
            upload_video_file = user.upload.upload_video_file
            max_file_size = user.upload.upload_video_max_file_size

        if not upload_video_file:
            return False

        file_size = os.stat(video_path).st_size
        if file_size > max_file_size:
            self._log.warning(
                'Video file size %d bigger then allowed %d. Will not upload',
                file_size,
                max_file_size,
            )
            return False
        return True

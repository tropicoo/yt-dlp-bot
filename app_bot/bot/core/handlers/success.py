import asyncio
import os
import traceback

from pyrogram.enums import ParseMode
from pyrogram.errors import MessageIdInvalid, MessageNotModified
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.enums import MediaFileType, TaskSource
from yt_shared.rabbit.publisher import RmqPublisher
from yt_shared.schemas.error import ErrorDownloadGeneralPayload
from yt_shared.schemas.media import BaseMedia
from yt_shared.schemas.success import SuccessDownloadPayload
from yt_shared.utils.file import list_files, remove_dir
from yt_shared.utils.tasks.tasks import create_task

from bot.core.handlers.abstract import AbstractDownloadHandler
from bot.core.tasks.upload import AudioUploadTask, VideoUploadTask
from bot.core.utils import bold, is_user_upload_silent


class SuccessDownloadHandler(AbstractDownloadHandler):
    """Handle successfully downloaded media context."""

    _body: SuccessDownloadPayload
    _UPLOAD_TASK_MAP = {
        MediaFileType.AUDIO: AudioUploadTask,
        MediaFileType.VIDEO: VideoUploadTask,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._rmq_publisher = RmqPublisher()

    async def handle(self) -> None:
        try:
            await self._handle()
        finally:
            self._cleanup()

    async def _handle(self) -> None:
        coro_tasks = []
        for media_object in self._body.media.get_media_objects():
            coro_tasks.append(self._handle_media_object(media_object))
        try:
            await asyncio.gather(*coro_tasks)
        finally:
            await self._delete_acknowledgment_message()

    async def _delete_acknowledgment_message(self) -> None:
        if self._body.from_chat_id and self._body.context.ack_message_id:
            await self._bot.delete_messages(
                chat_id=self._body.from_chat_id,
                message_ids=self._body.context.ack_message_id,
            )

    async def _set_upload_message(self, media_object: BaseMedia) -> None:
        if not (self._body.from_chat_id and self._body.context.ack_message_id):
            return

        try:
            await self._bot.edit_message_text(
                chat_id=self._body.from_chat_id,
                message_id=self._body.context.ack_message_id,
                text=f'⬆️ {bold(f"Uploading {media_object.file_size_human()}")}',
            )
        except (MessageIdInvalid, MessageNotModified) as err:
            # Expected behaviour when several links where pasted in one message and
            # the acknowledgment message was deleted after the first successful upload
            self._log.warning(
                'Could not edit the message id "%s": %s',
                self._body.context.ack_message_id,
                err,
            )

    async def _publish_error_message(self, err: Exception) -> None:
        err_payload = ErrorDownloadGeneralPayload(
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
        await self._rmq_publisher.send_download_error(err_payload)

    async def _handle_media_object(self, media_object: BaseMedia) -> None:
        try:
            await self._send_success_text(media_object)
            if self._upload_is_enabled():
                self._validate_file_size_for_upload(media_object)
                coros = (
                    self._create_upload_task(media_object),
                    self._set_upload_message(media_object),
                )
                await asyncio.gather(*coros)
            else:
                self._log.warning(
                    'File "%s" will not be uploaded due to upload configuration',
                    media_object.filepath,
                )
        except Exception as err:
            self._log.exception('Upload of "%s" failed', media_object.filepath)
            await self._publish_error_message(err)

    def _cleanup(self) -> None:
        root_path = self._body.media.root_path
        self._log.info(
            'Cleaning up task "%s": removing download content directory "%s" with files %s',
            self._body.task_id,
            root_path,
            list_files(root_path),
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
            if not is_user_upload_silent(user=user, conf=self._bot.conf):
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

    def _validate_file_size_for_upload(self, media_obj: BaseMedia) -> None:
        if self._body.context.source is TaskSource.API:
            max_file_size = self._bot.conf.telegram.api.upload_video_max_file_size
        else:
            user = self._bot.allowed_users[self._get_sender_id()]
            max_file_size = user.upload.upload_video_max_file_size

        if not os.path.exists(media_obj.filepath):
            raise ValueError(f'{media_obj.file_type} {media_obj.filepath} not found')

        _file_size = media_obj.current_file_size()
        if _file_size > max_file_size:
            err_msg = (
                f'{media_obj.file_type} file size of {_file_size} bytes bigger than '
                f'allowed {max_file_size} bytes. Will not upload'
            )
            self._log.warning(err_msg)
            raise ValueError(err_msg)

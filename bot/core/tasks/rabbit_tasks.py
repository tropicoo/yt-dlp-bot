import abc
import asyncio
import enum
import os
from typing import Optional, TYPE_CHECKING, Type

from aio_pika import IncomingMessage
from pydantic import BaseModel
from pyrogram.enums import ParseMode

from core.exceptions import InvalidBodyError
from core.tasks.abstract import AbstractTask
from core.tasks.upload import UploadTask
from core.utils import bold
from yt_shared.config import (
    MAX_UPLOAD_VIDEO_FILE_SIZE,
    TMP_DOWNLOAD_PATH,
    UPLOAD_VIDEO_FILE,
)
from yt_shared.emoji import SUCCESS_EMOJI
from yt_shared.rabbit import get_rabbitmq
from yt_shared.rabbit.rabbit_config import ERROR_QUEUE, SUCCESS_QUEUE
from yt_shared.schemas.error import ErrorPayload
from yt_shared.schemas.success import SuccessPayload
from yt_shared.task_utils.tasks import create_task

if TYPE_CHECKING:
    from core.bot import VideoBot


class RabbitTaskType(enum.Enum):
    ERROR = 'ERROR'
    SUCCESS = 'SUCCESS'


class AbstractResultWorkerTask(AbstractTask):
    TYPE: Optional[RabbitTaskType] = None
    QUEUE_TYPE: Optional[str] = None
    SCHEMA_CLS: Optional[Type[BaseModel]] = None

    def __init__(self, bot: 'VideoBot') -> None:
        super().__init__()
        self._bot = bot
        self._rabbit_mq = get_rabbitmq()
        self._queue = self._rabbit_mq.queues[self.QUEUE_TYPE]

    async def run(self) -> None:
        await self._watch_queue()

    @abc.abstractmethod
    async def _process_body(self, body: BaseModel) -> bool:
        pass

    async def _watch_queue(self) -> None:
        message: IncomingMessage
        async with self._queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    await self._process_message(message)
                except Exception:
                    self._log.exception('Failed to process message %s', message.body)
                    await message.nack(requeue=False)

    async def _process_message(self, message: IncomingMessage) -> None:
        self._log.info('[x] Received message %s', message.body)
        body = await self._deserialize_message(message)
        await self._process_body(body)
        await message.ack()

    async def _deserialize_message(self, message: IncomingMessage) -> BaseModel:
        try:
            return self.SCHEMA_CLS.parse_raw(message.body)
        except Exception:
            self._log.exception('Failed to decode message body')
            await self._reject_invalid_body(message)
            raise InvalidBodyError

    async def _reject_invalid_body(self, message: IncomingMessage) -> None:
        body = message.body
        self._log.critical('Invalid message body: %s, type: %s', body, type(body))
        await message.reject(requeue=False)


class SuccessResultWorkerTask(AbstractResultWorkerTask):
    TYPE = RabbitTaskType.SUCCESS
    QUEUE_TYPE = SUCCESS_QUEUE
    SCHEMA_CLS = SuccessPayload

    async def _process_body(self, body: SuccessPayload) -> None:
        await self._send_success_text(body)
        video_path: str = os.path.join(TMP_DOWNLOAD_PATH, body.filename)
        thumb_path: str = os.path.join(TMP_DOWNLOAD_PATH, body.thumb_name)
        if self._eligible_for_upload(video_path):
            await self._create_upload_task(body)
        else:
            self._log.warning('File %s will not be uploaded to Telegram', body.filename)
        self._cleanup([video_path, thumb_path])

    def _cleanup(self, file_paths: list[str]) -> None:
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except Exception:
                self._log.exception('Failed to remove "%s" during cleanup', file_path)

    @staticmethod
    def _eligible_for_upload(video_path: str) -> bool:
        return (
            UPLOAD_VIDEO_FILE
            and os.stat(video_path).st_size <= MAX_UPLOAD_VIDEO_FILE_SIZE
        )

    async def _create_upload_task(self, body: SuccessPayload) -> None:
        """Upload video to Telegram chat."""
        task_name = UploadTask.__class__.__name__
        await create_task(
            UploadTask(body=body, bot=self._bot).run(),
            task_name=task_name,
            logger=self._log,
            exception_message='Task %s raised an exception',
            exception_message_args=(task_name,),
        )

    async def _send_success_text(self, body: SuccessPayload) -> None:
        text = f'{SUCCESS_EMOJI} Downloaded {bold(body.filename)}'
        await self._bot.send_message(
            chat_id=body.from_user_id,
            reply_to_message_id=body.message_id,
            text=text,
            parse_mode=ParseMode.HTML,
        )


class ErrorResultWorkerTask(AbstractResultWorkerTask):
    TYPE = RabbitTaskType.ERROR
    QUEUE_TYPE = ERROR_QUEUE
    SCHEMA_CLS = ErrorPayload

    _ERR_MSG_TPL = (
        '🛑 <strong>Download failed</strong>\n\n'
        'ℹ <strong>ID:</strong> <code>{task_id}</code>\n'
        '💬 <strong>Message:</strong> {message}\n'
        '📹 <strong>Video URL:</strong> <code>{url}</code>\n'
        '👀 <strong>Details:</strong> <code>{details}</code>\n'
        '⬇️ <strong>yt-dlp version:</strong> <code>{yt_dlp_version}</code>'
    )

    async def _process_body(self, body: ErrorPayload) -> None:
        await self._send_error_text(body)

    async def _send_error_text(self, body: ErrorPayload) -> None:
        await self._bot.send_message(
            chat_id=body.from_user_id,
            reply_to_message_id=body.message_id,
            text=self._format_error_message(body),
            parse_mode=ParseMode.HTML,
        )

    def _format_error_message(self, body: ErrorPayload) -> str:
        return self._ERR_MSG_TPL.format(
            message=body.message,
            url=body.url,
            task_id=body.task_id,
            details=body.exception_msg,
            yt_dlp_version=body.yt_dlp_version,
        )

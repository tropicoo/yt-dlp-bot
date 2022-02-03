import asyncio
import logging
from typing import Optional

import aio_pika
from pamqp.commands import Basic
from sqlalchemy.ext.asyncio import AsyncSession

from core.downloader import DownVideo, VideoDownloader
from core.repository import TaskRepository
from yt_shared.constants import TaskStatus
from yt_shared.models import File, Task
from yt_shared.rabbit import get_rabbitmq
from yt_shared.rabbit.rabbit_config import (
    ERROR_EXCHANGE,
    ERROR_QUEUE,
    SUCCESS_EXCHANGE,
    SUCCESS_QUEUE,
)
from yt_shared.schemas.error import ErrorPayload
from yt_shared.schemas.success import SuccessPayload
from yt_shared.schemas.video import VideoPayload


class VideoService:

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._downloader = VideoDownloader()
        self._repository = TaskRepository()
        self._rabbit_mq = get_rabbitmq()

    async def process(self, db: AsyncSession,
                      video_payload: VideoPayload) -> None:
        task = await self._repository.get_or_create_task(db, video_payload)
        if task.status != TaskStatus.PENDING:
            return

        downloaded_video = await self._start_download(db, task, video_payload)
        if downloaded_video:
            await self._save_task_file(db, task, downloaded_video)
            await self._send_finished_task(task)

    @staticmethod
    async def _save_task_file(db: AsyncSession,
                              task: Task,
                              downloaded_video: DownVideo) -> None:
        task.file = File(**downloaded_video.dict())  # noqa
        task.status = TaskStatus.DONE
        await db.commit()

    async def _start_download(
            self,
            db: AsyncSession,
            task: Task,
            video_payload: VideoPayload) -> Optional[DownVideo]:
        task.status = TaskStatus.PROCESSING
        await db.commit()
        try:
            return await asyncio.get_running_loop().run_in_executor(
                None, lambda: self._downloader.download_video(task.url))
        except Exception as err:
            await self._handle_download_exception(db, err, task, video_payload)
            return None

    async def _handle_download_exception(self,
                                         db: AsyncSession,
                                         err: Exception, task: Task,
                                         video_payload: VideoPayload) -> None:
        task.status = TaskStatus.FAILED
        exception_msg = str(err)
        task.error = exception_msg
        await db.commit()
        err_exchange = self._rabbit_mq.exchanges[ERROR_EXCHANGE]
        err_payload = ErrorPayload(
            task_id=task.id,
            message_id=task.message_id,
            message='Download error',
            url=task.url,
            original_body=video_payload.dict(),
            exception_msg=exception_msg,
            exception_type=err.__class__.__name__,
        )
        err_message = aio_pika.Message(body=err_payload.json().encode())
        confirm = await err_exchange.publish(err_message,
                                             routing_key=ERROR_QUEUE,
                                             mandatory=True)
        if not isinstance(confirm, Basic.Ack):
            raise Exception(
                f'Failed to send errored message to {ERROR_EXCHANGE} '
                f'exchange: {confirm}')

    async def _send_finished_task(self, task: Task) -> None:
        filename = f'{task.file.name}.{task.file.ext}'
        exchange = self._rabbit_mq.exchanges[SUCCESS_EXCHANGE]
        payload = SuccessPayload(task_id=task.id, filename=filename)
        message = aio_pika.Message(body=payload.json().encode())
        confirm = await exchange.publish(message, routing_key=SUCCESS_QUEUE,
                                         mandatory=True)
        if not isinstance(confirm, Basic.Ack):
            raise Exception(
                f'Failed to send errored message to {SUCCESS_EXCHANGE} '
                f'exchange: {confirm}')

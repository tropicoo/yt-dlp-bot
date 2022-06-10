import asyncio
import logging
import os
import shutil
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.downloader import VideoDownloader
from yt_shared.config import SAVE_VIDEO_FILE, STORAGE_PATH, TMP_DOWNLOAD_PATH
from yt_shared.constants import TaskStatus
from yt_shared.models import Task
from yt_shared.rabbit.publisher import Publisher
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.error import ErrorPayload
from yt_shared.schemas.success import SuccessPayload
from yt_shared.schemas.video import DownVideo, VideoPayload


class VideoService:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._downloader = VideoDownloader()
        self._repository = TaskRepository()
        self._publisher = Publisher()

    async def process(self, video_payload: VideoPayload, db: AsyncSession) -> None:
        task = await self._repository.get_or_create_task(db, video_payload)
        if task.status != TaskStatus.PENDING:
            return

        await self._repository.save_as_processing(db, task)
        downloaded_video = await self._start_download(db, task, video_payload)
        if downloaded_video:
            await self._post_process_file(downloaded_video, task, db)

    async def _post_process_file(
        self, video: DownVideo, task: Task, db: AsyncSession
    ) -> None:
        post_process_coros = [self._repository.save_as_done(db, task, video)]

        if SAVE_VIDEO_FILE:
            post_process_coros.append(self._copy_file_to_storage(video))

        await asyncio.gather(*post_process_coros)
        await self._send_finished_task(task)

    @staticmethod
    async def _copy_file_to_storage(video: DownVideo) -> None:
        src = os.path.join(TMP_DOWNLOAD_PATH, video.name)
        dst = os.path.join(STORAGE_PATH, video.name)
        await asyncio.to_thread(shutil.copy2, src, dst)

    async def _start_download(
        self, db: AsyncSession, task: Task, video_payload: VideoPayload
    ) -> Optional[DownVideo]:
        try:
            return await asyncio.get_running_loop().run_in_executor(
                None, lambda: self._downloader.download_video(task.url)
            )
        except Exception as err:
            await self._handle_download_exception(db, err, task, video_payload)
            return None

    async def _handle_download_exception(
        self, db: AsyncSession, err: Exception, task: Task, video_payload: VideoPayload
    ) -> None:
        exception_msg = str(err)
        await self._repository.save_as_failed(db, task, exception_msg)
        await self._send_failed_task(
            task=task,
            video_payload=video_payload,
            exception_msg=exception_msg,
            err=err,
        )

    async def _send_finished_task(self, task: Task) -> None:
        success_payload = SuccessPayload(task_id=task.id, filename=task.file.name)
        await self._publisher.send_download_finished(success_payload)

    async def _send_failed_task(
        self,
        task: Task,
        video_payload: VideoPayload,
        exception_msg: str,
        err: Exception,
    ) -> None:
        err_payload = ErrorPayload(
            task_id=task.id,
            message_id=task.message_id,
            message='Download error',
            url=task.url,
            original_body=video_payload.dict(),
            yt_dlp_version=task.yt_dlp_version,
            exception_msg=exception_msg,
            exception_type=err.__class__.__name__,
        )
        await self._publisher.send_download_error(err_payload)

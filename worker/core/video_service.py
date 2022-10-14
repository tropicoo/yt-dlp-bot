import asyncio
import logging
import os
import shutil
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.downloader import VideoDownloader
from core.tasks.ffprobe_context import GetFfprobeContextTask
from core.tasks.thumbnail import MakeThumbnailTask
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

        self._db: AsyncSession | None = None
        self._video_payload: VideoPayload | None = None

    async def process(self, video_payload: VideoPayload, db: AsyncSession) -> None:
        try:
            self._video_payload = video_payload
            self._db = db
            await self._process()
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Cleanup temporary set attributes."""
        self._db = None
        self._video_payload = None

    async def _process(self) -> None:
        task = await self._repository.get_or_create_task(self._db, self._video_payload)
        if task.status != TaskStatus.PENDING:
            return

        await self._repository.save_as_processing(self._db, task)
        downloaded_video = await self._start_download(task)
        if downloaded_video:
            await self._post_process_file(downloaded_video, task)

    async def _post_process_file(self, video: DownVideo, task: Task) -> None:
        file_path = os.path.join(settings.TMP_DOWNLOAD_PATH, video.name)
        thumb_path = os.path.join(settings.TMP_DOWNLOAD_PATH, video.thumb_name)

        post_process_coros = [
            self._set_probe_ctx(file_path, video),
            MakeThumbnailTask(thumb_path, file_path).run(),
        ]

        if settings.SAVE_VIDEO_FILE:
            post_process_coros.append(self._copy_file_to_storage(video))

        await asyncio.gather(*post_process_coros)
        await self._repository.save_as_done(self._db, task, video),
        await self._send_finished_task(task, video)

    @staticmethod
    async def _set_probe_ctx(file_path: str, video: DownVideo) -> None:
        probe_ctx = await GetFfprobeContextTask(file_path).run()
        if not probe_ctx:
            return
        video_streams = [
            stream for stream in probe_ctx['streams'] if stream['codec_type'] == 'video'
        ]

        video.duration = int(float(probe_ctx['format']['duration']))
        video.width = video_streams[0]['width']
        video.height = video_streams[0]['height']

    @staticmethod
    async def _copy_file_to_storage(video: DownVideo) -> None:
        src: str = os.path.join(settings.TMP_DOWNLOAD_PATH, video.name)
        dst: str = os.path.join(settings.STORAGE_PATH, video.name)
        await asyncio.to_thread(shutil.copy2, src, dst)

    async def _start_download(self, task: Task) -> Optional[DownVideo]:
        try:
            return await asyncio.get_running_loop().run_in_executor(
                None, lambda: self._downloader.download_video(task.url)
            )
        except Exception as err:
            await self._handle_download_exception(err, task)
            return None

    async def _handle_download_exception(self, err: Exception, task: Task) -> None:
        exception_msg = str(err)
        await self._repository.save_as_failed(self._db, task, exception_msg)
        await self._send_failed_task(
            task=task,
            exception_msg=exception_msg,
            err=err,
        )

    async def _send_finished_task(self, task: Task, video: DownVideo) -> None:
        success_payload = SuccessPayload(
            task_id=task.id,
            title=task.file.title,
            filename=task.file.name,
            thumb_name=video.thumb_name,
            duration=video.duration,
            width=video.width,
            height=video.height,
            message_id=task.message_id,
            from_user_id=task.from_user_id,
            context=self._video_payload.dict(),
        )
        await self._publisher.send_download_finished(success_payload)

    async def _send_failed_task(
        self,
        task: Task,
        exception_msg: str,
        err: Exception,
    ) -> None:
        err_payload = ErrorPayload(
            task_id=task.id,
            message_id=task.message_id,
            from_user_id=self._video_payload.from_user_id,
            message='Download error',
            url=task.url,
            original_body=self._video_payload.dict(),
            yt_dlp_version=task.yt_dlp_version,
            exception_msg=exception_msg,
            exception_type=err.__class__.__name__,
        )
        await self._publisher.send_download_error(err_payload)

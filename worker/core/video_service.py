import asyncio
import logging
import os
import shutil

from core.config import settings
from core.downloader import VideoDownloader
from core.exceptions import DownloadVideoServiceError
from core.tasks.ffprobe_context import GetFfprobeContextTask
from core.tasks.thumbnail import MakeThumbnailTask
from sqlalchemy.ext.asyncio import AsyncSession

from yt_shared.enums import TaskStatus
from yt_shared.models import Task
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.video import DownVideo, VideoPayload
from yt_shared.utils.file import file_cleanup
from yt_shared.utils.tasks.tasks import create_task


class VideoService:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._downloader = VideoDownloader()
        self._repository = TaskRepository()

    async def process(
        self, video_payload: VideoPayload, db: AsyncSession
    ) -> tuple[DownVideo | None, Task | None]:
        task = await self._repository.get_or_create_task(db, video_payload)
        if task.status != TaskStatus.PENDING.value:
            return None, None
        return (
            await self._process(video_payload=video_payload, task=task, db=db),
            task,
        )

    async def _process(
        self, video_payload: VideoPayload, task: Task, db: AsyncSession
    ) -> DownVideo:
        await self._repository.save_as_processing(db, task)
        downloaded_video = await self._start_download(task, video_payload, db)
        try:
            await self._post_process_file(downloaded_video, task, db)
        except Exception:
            self._log.exception('Failed to post-process file %s', downloaded_video)
            self._err_file_cleanup(downloaded_video)
            raise
        return downloaded_video

    async def _start_download(
        self, task: Task, video_payload: VideoPayload, db: AsyncSession
    ) -> DownVideo:
        try:
            return await asyncio.get_running_loop().run_in_executor(
                None, lambda: self._downloader.download_video(task.url)
            )
        except Exception as err:
            self._log.exception('Failed to download video. Context: %s', video_payload)
            await self._handle_download_exception(err, task, db)
            exception = DownloadVideoServiceError(str(err))
            exception.task = task
            raise exception

    async def _post_process_file(
        self,
        video: DownVideo,
        task: Task,
        db: AsyncSession,
    ) -> None:
        file_path: str = os.path.join(settings.TMP_DOWNLOAD_PATH, video.name)
        thumb_path: str = os.path.join(settings.TMP_DOWNLOAD_PATH, video.thumb_name)

        # yt-dlp meta may not contain needed video metadata.
        if not all([video.duration, video.height, video.width]):
            await self._set_probe_ctx(file_path, video)

        tasks = [self._create_thumbnail_task(file_path, thumb_path, video.duration)]
        if settings.SAVE_VIDEO_FILE:
            tasks.append(self._create_copy_file_task(video))
        await asyncio.gather(*tasks)

        final_coros = [self._repository.save_as_done(db, task, video)]
        await asyncio.gather(*final_coros)

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

    def _create_copy_file_task(self, video: DownVideo) -> asyncio.Task:
        task_name = 'Copy file to storage task'
        return create_task(
            self._copy_file_to_storage(video),
            task_name=task_name,
            logger=self._log,
            exception_message='Task %s raised an exception',
            exception_message_args=(task_name,),
        )

    def _create_thumbnail_task(
        self, file_path: str, thumb_path: str, duration: int
    ) -> asyncio.Task:
        return create_task(
            MakeThumbnailTask(thumb_path, file_path, duration=duration).run(),
            task_name=MakeThumbnailTask.__class__.__name__,
            logger=self._log,
            exception_message='Task %s raised an exception',
            exception_message_args=(MakeThumbnailTask.__class__.__name__,),
        )

    @staticmethod
    async def _copy_file_to_storage(video: DownVideo) -> None:
        src: str = os.path.join(settings.TMP_DOWNLOAD_PATH, video.name)
        dst: str = os.path.join(settings.STORAGE_PATH, video.name)
        await asyncio.to_thread(shutil.copy2, src, dst)

    def _err_file_cleanup(self, downloaded_video: DownVideo) -> None:
        """Cleanup any downloaded/created data if post-processing failed."""
        _file_paths = (downloaded_video.name, downloaded_video.thumb_name)
        file_cleanup(file_paths=tuple(x for x in _file_paths if x), log=self._log)

    async def _handle_download_exception(
        self, err: Exception, task: Task, db: AsyncSession
    ) -> None:
        exception_msg = str(err)
        await self._repository.save_as_failed(db, task, exception_msg)

import asyncio
import logging
import os
import shutil

from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.enums import TaskStatus
from yt_shared.models import Task
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.video import DownVideo, VideoPayload
from yt_shared.utils.file import remove_dir
from yt_shared.utils.tasks.tasks import create_task

from worker.core.config import settings
from worker.core.downloader import VideoDownloader
from worker.core.exceptions import DownloadVideoServiceError
from worker.core.tasks.ffprobe_context import GetFfprobeContextTask
from worker.core.tasks.thumbnail import MakeThumbnailTask


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
            raise DownloadVideoServiceError(message=str(err), task=task)

    async def _post_process_file(
        self,
        video: DownVideo,
        task: Task,
        db: AsyncSession,
    ) -> None:
        thumb_path = os.path.join(video.filepath.rsplit('/', 1)[0], video.thumb_name)

        # yt-dlp meta may not contain needed video metadata.
        if not all([video.duration, video.height, video.width]):
            # TODO: Move to higher level and re-raise as DownloadVideoServiceError with task,
            # TODO: or create new exception type.
            try:
                await self._set_probe_ctx(video)
            except RuntimeError as err:
                raise DownloadVideoServiceError(message=str(err), task=task)

        tasks = [self._create_thumb_task(video.filepath, thumb_path, video.duration)]
        if settings.SAVE_VIDEO_FILE:
            tasks.append(self._create_copy_file_task(video))
        await asyncio.gather(*tasks)

        video.thumb_path = thumb_path

        final_coros = [self._repository.save_as_done(db, task, video)]
        await asyncio.gather(*final_coros)

    @staticmethod
    async def _set_probe_ctx(video: DownVideo) -> None:
        probe_ctx = await GetFfprobeContextTask(video.filepath).run()
        if not probe_ctx:
            return
        video_streams = [
            stream for stream in probe_ctx['streams'] if stream['codec_type'] == 'video'
        ]
        video.duration = float(probe_ctx['format']['duration'])
        video.width = video_streams[0]['width']
        video.height = video_streams[0]['height']

    def _create_copy_file_task(self, video: DownVideo) -> asyncio.Task:
        task_name = 'Copy file to storage task'
        return create_task(
            self._copy_file_to_storage(video),
            task_name=task_name,
            logger=self._log,
            exception_message='Task "%s" raised an exception',
            exception_message_args=(task_name,),
        )

    def _create_thumb_task(
        self, file_path: str, thumb_path: str, duration: float
    ) -> asyncio.Task:
        return create_task(
            MakeThumbnailTask(thumb_path, file_path, duration=duration).run(),
            task_name=MakeThumbnailTask.__class__.__name__,
            logger=self._log,
            exception_message='Task "%s" raised an exception',
            exception_message_args=(MakeThumbnailTask.__class__.__name__,),
        )

    @staticmethod
    async def _copy_file_to_storage(video: DownVideo) -> None:
        dst = os.path.join(settings.STORAGE_PATH, video.name)
        await asyncio.to_thread(shutil.copy2, video.filepath, dst)

    def _err_file_cleanup(self, video: DownVideo) -> None:
        """Cleanup any downloaded/created data if post-processing failed."""
        self._log.info('Performing error cleanup. Removing %s', video.root_path)
        remove_dir(video.root_path)

    async def _handle_download_exception(
        self, err: Exception, task: Task, db: AsyncSession
    ) -> None:
        exception_msg = str(err)
        await self._repository.save_as_failed(db, task, exception_msg)

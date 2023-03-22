import asyncio
import logging
import os
import shutil

from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.enums import DownMediaType, TaskStatus
from yt_shared.models import Task
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.media import (
    BaseMedia,
    DownMedia,
    IncomingMediaPayload,
    Video,
)
from yt_shared.utils.file import remove_dir
from yt_shared.utils.tasks.tasks import create_task

from worker.core.config import settings
from worker.core.downloader import MediaDownloader
from worker.core.exceptions import DownloadVideoServiceError
from worker.core.tasks.ffprobe_context import GetFfprobeContextTask
from worker.core.tasks.thumbnail import MakeThumbnailTask


class MediaService:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._downloader = MediaDownloader()
        self._repository = TaskRepository()

    async def process(
        self, media_payload: IncomingMediaPayload, db: AsyncSession
    ) -> tuple[DownMedia | None, Task | None]:
        task = await self._repository.get_or_create_task(db, media_payload)
        if task.status != TaskStatus.PENDING.value:
            return None, None
        return (
            await self._process(media_payload=media_payload, task=task, db=db),
            task,
        )

    async def _process(
        self, media_payload: IncomingMediaPayload, task: Task, db: AsyncSession
    ) -> DownMedia:
        await self._repository.save_as_processing(db, task)
        media = await self._start_download(task, media_payload, db)
        try:
            await self._post_process_media(media, task, media_payload, db)
        except Exception:
            self._log.exception('Failed to post-process media %s', media)
            self._err_file_cleanup(media)
            raise
        return media

    async def _start_download(
        self, task: Task, media_payload: IncomingMediaPayload, db: AsyncSession
    ) -> DownMedia:
        try:
            return await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: self._downloader.download(
                    task.url, media_type=media_payload.download_media_type
                ),
            )
        except Exception as err:
            self._log.exception('Failed to download media. Context: %s', media_payload)
            await self._handle_download_exception(err, task, db)
            raise DownloadVideoServiceError(message=str(err), task=task)

    async def _post_process_media(
        self,
        media: DownMedia,
        task: Task,
        media_payload: IncomingMediaPayload,
        db: AsyncSession,
    ) -> None:
        def post_process_audio():
            return self._post_process_audio(
                media=media, media_payload=media_payload, task=task, db=db
            )

        def post_process_video():
            return self._post_process_video(
                media=media, media_payload=media_payload, task=task, db=db
            )

        match media.media_type:  # noqa: E999
            case DownMediaType.AUDIO:
                await post_process_audio()
            case DownMediaType.VIDEO:
                await post_process_video()
            case DownMediaType.AUDIO_VIDEO:
                await asyncio.gather(*(post_process_audio(), post_process_video()))

        await self._repository.save_as_done(db, task)

    async def _post_process_video(
        self,
        media: DownMedia,
        media_payload: IncomingMediaPayload,
        task: Task,
        db: AsyncSession,
    ) -> None:
        """Post-process downloaded media files, e.g. make thumbnail and copy to storage."""
        video = media.video
        # yt-dlp's 'info-meta' may not contain all needed video metadata.
        if not all([video.duration, video.height, video.width]):
            # TODO: Move to higher level and re-raise as DownloadVideoServiceError with task,
            # TODO: or create new exception type.
            try:
                await self._set_probe_ctx(video)
            except RuntimeError as err:
                raise DownloadVideoServiceError(message=str(err), task=task)

        coro_tasks = []
        if not video.thumb_path:
            thumb_path = os.path.join(media.root_path, video.thumb_name)
            video.thumb_path = thumb_path
            coro_tasks.append(
                self._create_thumb_task(
                    file_path=video.filepath,
                    thumb_path=thumb_path,
                    duration=video.duration,
                )
            )

        if media_payload.save_to_storage:
            coro_tasks.append(self._create_copy_file_task(video))
        await asyncio.gather(*coro_tasks)

        file = await self._repository.save_file(db, task, media.video, media.meta)
        video.orm_file_id = file.id

    async def _post_process_audio(
        self,
        media: DownMedia,
        media_payload: IncomingMediaPayload,
        task: Task,
        db: AsyncSession,
    ) -> None:
        coro_tasks = [self._repository.save_file(db, task, media.audio, media.meta)]
        if media_payload.save_to_storage:
            coro_tasks.append(self._create_copy_file_task(media.audio))
        results = await asyncio.gather(*coro_tasks)
        file = results[0]
        media.audio.orm_file_id = file.id

    @staticmethod
    async def _set_probe_ctx(video: Video) -> None:
        probe_ctx = await GetFfprobeContextTask(video.filepath).run()
        if not probe_ctx:
            return
        video_streams = [
            stream for stream in probe_ctx['streams'] if stream['codec_type'] == 'video'
        ]
        video.duration = float(probe_ctx['format']['duration'])
        video.width = video_streams[0]['width']
        video.height = video_streams[0]['height']

    def _create_copy_file_task(self, file: BaseMedia) -> asyncio.Task:
        task_name = f'Copy {file.file_type} file to storage task'
        return create_task(
            self._copy_file_to_storage(file),
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
    async def _copy_file_to_storage(file: BaseMedia) -> None:
        dst = os.path.join(settings.STORAGE_PATH, file.filename)
        await asyncio.to_thread(shutil.copy2, file.filepath, dst)
        file.saved_to_storage = True
        file.storage_path = dst

    def _err_file_cleanup(self, video: DownMedia) -> None:
        """Cleanup any downloaded/created data if post-processing failed."""
        self._log.info('Performing error cleanup. Removing %s', video.root_path)
        remove_dir(video.root_path)

    async def _handle_download_exception(
        self, err: Exception, task: Task, db: AsyncSession
    ) -> None:
        exception_msg = str(err)
        await self._repository.save_as_failed(db, task, exception_msg)

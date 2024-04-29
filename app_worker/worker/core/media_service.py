import asyncio
import logging
import shutil
import time
from pathlib import Path
from urllib.parse import urlsplit

from yt_shared.enums import DownMediaType, TaskStatus
from yt_shared.models import Task
from yt_shared.repositories.task import TaskRepository
from yt_shared.schemas.media import (
    BaseMedia,
    DownMedia,
    InbMediaPayload,
    Video,
)
from yt_shared.utils.common import gen_random_str
from yt_shared.utils.file import remove_dir
from yt_shared.utils.tasks.tasks import create_task

from worker.core.config import settings
from worker.core.downloader import MediaDownloader
from worker.core.exceptions import DownloadVideoServiceError
from worker.core.tasks.encode import EncodeToH264Task
from worker.core.tasks.ffprobe_context import GetFfprobeContextTask
from worker.core.tasks.thumbnail import MakeThumbnailTask
from ytdl_opts.per_host._base import AbstractHostConfig
from ytdl_opts.per_host._registry import HostConfRegistry


class MediaService:
    def __init__(
        self,
        media_payload: InbMediaPayload,
        downloader: MediaDownloader,
        task_repository: TaskRepository,
    ) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._downloader = downloader
        self._repository = task_repository
        self._media_payload = media_payload

    async def process(
        self,
    ) -> tuple[DownMedia | None, Task | None]:
        task = await self._repository.get_or_create_task(self._media_payload)
        if task.status != TaskStatus.PENDING.value:
            return None, None
        return (
            await self._process(task=task),
            task,
        )

    async def _process(self, task: Task) -> DownMedia:
        host_conf = self._get_host_conf(url=task.url)
        await self._repository.save_as_processing(task)
        media = await self._start_download(task=task, host_conf=host_conf)
        try:
            await self._post_process_media(
                media=media,
                task=task,
                host_conf=host_conf,
            )
        except Exception:
            self._log.exception('Failed to post-process media %s', media)
            self._err_file_cleanup(media)
            raise
        return media

    @staticmethod
    def _get_host_conf(url: str) -> AbstractHostConfig:
        host_to_cls_map = HostConfRegistry.get_host_to_cls_map()
        host_cls = host_to_cls_map.get(urlsplit(url).netloc, host_to_cls_map[None])
        return host_cls(url=url)

    async def _start_download(
        self,
        task: Task,
        host_conf: AbstractHostConfig,
    ) -> DownMedia:
        try:
            return await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: self._downloader.download(
                    host_conf=host_conf,
                    media_payload=self._media_payload,
                ),
            )
        except Exception as err:
            self._log.exception(
                'Failed to download media. Context: %s', self._media_payload
            )
            await self._handle_download_exception(err, task)
            raise DownloadVideoServiceError(message=str(err), task=task)

    async def _post_process_media(
        self,
        media: DownMedia,
        task: Task,
        host_conf: AbstractHostConfig,
    ) -> None:
        def post_process_audio():
            return self._post_process_audio(
                media=media,
                task=task,
                host_conf=host_conf,
            )

        def post_process_video():
            return self._post_process_video(
                media=media,
                task=task,
                host_conf=host_conf,
            )

        match media.media_type:
            case DownMediaType.AUDIO:
                await post_process_audio()
            case DownMediaType.VIDEO:
                await post_process_video()
            case DownMediaType.AUDIO_VIDEO:
                await asyncio.gather(*(post_process_audio(), post_process_video()))

        await self._repository.save_as_done(task)

    async def _post_process_video(
        self,
        media: DownMedia,
        task: Task,
        host_conf: AbstractHostConfig,
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

        video_ar = video.aspect_ratio
        thumb_ar = video.thumb_aspect_ratio
        if not video.thumb_path or all([video_ar, thumb_ar, video_ar != thumb_ar]):
            thumb_path = Path(media.root_path) / Path(video.thumb_name)
            coro_tasks.append(
                self._create_thumb_task(
                    file_path=video.current_filepath,
                    thumb_path=thumb_path,
                    duration=video.duration,
                    video_ctx=video,
                )
            )

        if self._media_payload.save_to_storage:
            coro_tasks.append(self._create_copy_file_task(video))

        if host_conf.ENCODE_VIDEO:
            coro_tasks.append(
                create_task(
                    EncodeToH264Task(
                        media=media, cmd_tpl=host_conf.FFMPEG_VIDEO_OPTS
                    ).run(),
                    task_name=EncodeToH264Task.__class__.__name__,
                    logger=self._log,
                    exception_message='Task "%s" raised an exception',
                    exception_message_args=(EncodeToH264Task.__class__.__name__,),
                )
            )

        await asyncio.gather(*coro_tasks)

        file = await self._repository.save_file(task, media.video, media.meta)
        video.orm_file_id = file.id

    async def _post_process_audio(
        self,
        media: DownMedia,
        task: Task,
        host_conf: AbstractHostConfig,
    ) -> None:
        coro_tasks = [self._repository.save_file(task, media.audio, media.meta)]
        if self._media_payload.save_to_storage:
            coro_tasks.append(self._create_copy_file_task(media.audio))
        results = await asyncio.gather(*coro_tasks)
        file = results[0]
        media.audio.orm_file_id = file.id

    async def _set_probe_ctx(self, video: Video) -> None:
        probe_ctx = await GetFfprobeContextTask(video.current_filepath).run()
        if not probe_ctx:
            return

        video_streams = [s for s in probe_ctx['streams'] if s['codec_type'] == 'video']
        video.duration = float(probe_ctx['format']['duration'])
        if not video_streams:
            self._log.warning(
                'Video file does not contain video stream. Might be only audio. '
                'Ffprobe context: %s',
                probe_ctx,
            )
            return

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
        self,
        file_path: Path,
        thumb_path: Path,
        duration: float,
        video_ctx: Video,
    ) -> asyncio.Task:
        return create_task(
            MakeThumbnailTask(
                thumb_path, file_path, duration=duration, video_ctx=video_ctx
            ).run(),
            task_name=MakeThumbnailTask.__class__.__name__,
            logger=self._log,
            exception_message='Task "%s" raised an exception',
            exception_message_args=(MakeThumbnailTask.__class__.__name__,),
        )

    async def _copy_file_to_storage(self, file: BaseMedia) -> None:
        dst = settings.STORAGE_PATH / file.current_filename
        if dst.is_file():
            self._log.warning('Destination file in storage already exists: %s', dst)
            dst = (
                dst.parent
                / f'{dst.stem}-{int(time.time())}-{gen_random_str()}{dst.suffix}'
            )
            self._log.warning('Adding current timestamp to filename: %s', dst)

        self._log.info('Copying "%s" to storage "%s"', file.current_filepath, dst)
        await asyncio.to_thread(shutil.copy2, file.current_filepath, dst)
        file.mark_as_saved_to_storage(storage_path=dst)

    def _err_file_cleanup(self, video: DownMedia) -> None:
        """Cleanup any downloaded/created data if post-processing failed."""
        self._log.info('Performing error cleanup: removing %s', video.root_path)
        remove_dir(video.root_path)

    async def _handle_download_exception(self, err: Exception, task: Task) -> None:
        await self._repository.save_as_failed(task=task, error_message=str(err))

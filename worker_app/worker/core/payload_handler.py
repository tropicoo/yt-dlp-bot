import logging
import traceback

from yt_dlp import version as ytdlp_version
from yt_shared.db.session import get_db
from yt_shared.models import Task
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.error import ErrorDownloadPayload, ErrorGeneralPayload
from yt_shared.schemas.success import SuccessPayload
from yt_shared.schemas.video import DownVideo, VideoPayload

from worker.core.exceptions import DownloadVideoServiceError, GeneralVideoServiceError
from worker.core.video_service import VideoService


class PayloadHandler:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._video_service = VideoService()
        self._publisher = Publisher()

    async def handle(self, video_payload: VideoPayload) -> None:
        try:
            await self._handle(video_payload)
        except Exception as err:
            await self._send_general_error(err, video_payload)

    async def _handle(self, video_payload: VideoPayload) -> None:
        async for session in get_db():
            try:
                video, task = await self._video_service.process(video_payload, session)
            except DownloadVideoServiceError as err:
                await self._send_failed_video_download_task(err, video_payload)
                return

            if not video or not task:
                err_msg = (
                    f'Video or task is None, cannot proceed: '
                    f'video - {video}, task - {task}'
                )
                self._log.error(err_msg)
                raise RuntimeError(err_msg)
            await self._send_finished_task(task, video, video_payload)

    async def _send_finished_task(
        self, task: Task, video: DownVideo, video_payload: VideoPayload
    ) -> None:
        success_payload = SuccessPayload(
            task_id=task.id,
            title=video.title,
            filename=video.name,
            thumb_name=video.thumb_name,
            duration=video.duration,
            width=video.width,
            height=video.height,
            message_id=task.message_id,
            from_chat_id=video_payload.from_chat_id,
            from_chat_type=video_payload.from_chat_type,
            from_user_id=task.from_user_id,
            context=video_payload,
            yt_dlp_version=ytdlp_version.__version__,
        )
        await self._publisher.send_download_finished(success_payload)

    async def _send_failed_video_download_task(
        self,
        err: DownloadVideoServiceError,
        video_payload: VideoPayload,
    ) -> None:
        task = err.task
        err_payload = ErrorDownloadPayload(
            task_id=task.id,
            message_id=task.message_id,
            from_chat_id=video_payload.from_chat_id,
            from_chat_type=video_payload.from_chat_type,
            from_user_id=video_payload.from_user_id,
            message='Download error',
            url=video_payload.url,
            context=video_payload,
            yt_dlp_version=ytdlp_version.__version__,
            exception_msg=str(err),
            exception_type=err.__class__.__name__,
        )
        await self._publisher.send_download_error(err_payload)

    async def _send_general_error(
        self,
        err: GeneralVideoServiceError | Exception,
        video_payload: VideoPayload,
    ) -> None:
        task: Task | None = getattr(err, 'task', None)
        err_payload = ErrorGeneralPayload(
            task_id=task.id if task else 'N/A',
            message_id=video_payload.message_id,
            from_chat_id=video_payload.from_chat_id,
            from_chat_type=video_payload.from_chat_type,
            from_user_id=video_payload.from_user_id,
            message='General worker error',
            url=video_payload.url,
            context=video_payload,
            yt_dlp_version=ytdlp_version.__version__,
            exception_msg=traceback.format_exc(),
            exception_type=err.__class__.__name__,
        )
        await self._publisher.send_download_error(err_payload)

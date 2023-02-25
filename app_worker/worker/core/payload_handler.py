import logging
import traceback

from yt_dlp import version as ytdlp_version
from yt_shared.db.session import get_db
from yt_shared.models import Task
from yt_shared.rabbit.publisher import Publisher
from yt_shared.schemas.error import ErrorDownloadPayload, ErrorGeneralPayload
from yt_shared.schemas.media import DownMedia, IncomingMediaPayload
from yt_shared.schemas.success import SuccessPayload

from worker.core.exceptions import DownloadVideoServiceError, GeneralVideoServiceError
from worker.core.media_service import MediaService


class PayloadHandler:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._media_service = MediaService()
        self._publisher = Publisher()

    async def handle(self, media_payload: IncomingMediaPayload) -> None:
        try:
            await self._handle(media_payload)
        except Exception as err:
            await self._send_general_error(err, media_payload)

    async def _handle(self, media_payload: IncomingMediaPayload) -> None:
        async for session in get_db():
            try:
                media, task = await self._media_service.process(media_payload, session)
            except DownloadVideoServiceError as err:
                await self._send_failed_video_download_task(err, media_payload)
                return

            if not media or not task:
                err_msg = (
                    f'Media or task is None, cannot proceed: '
                    f'media - {media}, task - {task}'
                )
                self._log.error(err_msg)
                raise RuntimeError(err_msg)
            await self._send_finished_task(task, media, media_payload)

    async def _send_finished_task(
        self, task: Task, media: DownMedia, media_payload: IncomingMediaPayload
    ) -> None:
        success_payload = SuccessPayload(
            task_id=task.id,
            media=media,
            message_id=task.message_id,
            from_chat_id=media_payload.from_chat_id,
            from_chat_type=media_payload.from_chat_type,
            from_user_id=task.from_user_id,
            context=media_payload,
            yt_dlp_version=ytdlp_version.__version__,
        )
        await self._publisher.send_download_finished(success_payload)

    async def _send_failed_video_download_task(
        self,
        err: DownloadVideoServiceError,
        media_payload: IncomingMediaPayload,
    ) -> None:
        task = err.task
        err_payload = ErrorDownloadPayload(
            task_id=task.id,
            message_id=task.message_id,
            from_chat_id=media_payload.from_chat_id,
            from_chat_type=media_payload.from_chat_type,
            from_user_id=media_payload.from_user_id,
            message='Download error',
            url=media_payload.url,
            context=media_payload,
            yt_dlp_version=ytdlp_version.__version__,
            exception_msg=str(err),
            exception_type=err.__class__.__name__,
        )
        await self._publisher.send_download_error(err_payload)

    async def _send_general_error(
        self,
        err: GeneralVideoServiceError | Exception,
        media_payload: IncomingMediaPayload,
    ) -> None:
        task: Task | None = getattr(err, 'task', None)
        err_payload = ErrorGeneralPayload(
            task_id=task.id if task else 'N/A',
            message_id=media_payload.message_id,
            from_chat_id=media_payload.from_chat_id,
            from_chat_type=media_payload.from_chat_type,
            from_user_id=media_payload.from_user_id,
            message='General worker error',
            url=media_payload.url,
            context=media_payload,
            yt_dlp_version=ytdlp_version.__version__,
            exception_msg=traceback.format_exc(),
            exception_type=err.__class__.__name__,
        )
        await self._publisher.send_download_error(err_payload)

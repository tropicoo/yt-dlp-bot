from pathlib import Path

from yt_shared.schemas.media import Video

from worker.core.config import settings
from worker.core.tasks.abstract import AbstractFfBinaryTask


class MakeThumbnailTask(AbstractFfBinaryTask):
    _CMD = 'ffmpeg -y -loglevel error -i "{filepath}" -ss {time_point} -vframes 1 -q:v 7 "{thumbpath}"'

    def __init__(
        self, thumbnail_path: Path, *args, duration: float, video_ctx: Video, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._thumbnail_path = thumbnail_path
        self._duration = duration
        self._video_ctx = video_ctx

    async def run(self) -> bool:
        is_created = await self._make_thumbnail()
        if is_created:
            self._video_ctx.thumb_path = self._thumbnail_path
        return is_created

    async def _make_thumbnail(self) -> bool:
        cmd = self._CMD.format(
            filepath=self._file_path,
            time_point=self._get_thumb_time_point(),
            thumbpath=self._thumbnail_path,
        )
        self._log.info('Creating thumbnail with command "%s"', cmd)
        proc = await self._run_proc(cmd)
        if not proc:
            return False

        stdout, stderr = await self._get_stdout_stderr(proc)
        self._log.debug(
            'Process %s returncode: %d, stdout: %s, stderr: %s',
            cmd,
            proc.returncode,
            stdout,
            stderr,
        )
        if proc.returncode:
            self._log.error('Failed to make thumbnail for "%s"', self._file_path)
            return False
        return True

    def _get_thumb_time_point(self) -> float:
        """Get a valid thumbnail second (seek time point for FFmpeg).

        If the video is shorter the user-specified thumbnail frame second,
        just take it from the middle of the video because FFmpeg might error out.
        """
        if self._duration <= settings.THUMBNAIL_FRAME_SECOND:
            return round(self._duration / 2, 1)
        return settings.THUMBNAIL_FRAME_SECOND

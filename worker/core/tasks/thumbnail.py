from core.config import settings
from core.tasks.abstract import AbstractFfBinaryTask

from yt_shared.schemas.video import DownVideo


class MakeThumbnailTask(AbstractFfBinaryTask):
    _CMD = 'ffmpeg -y -loglevel error -i "{filepath}" -ss {second} -vframes 1 -q:v 7 "{thumbpath}"'

    def __init__(self, thumbnail_path: str, *args, duration: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._thumbnail_path = thumbnail_path
        self._duration = duration

    async def run(self) -> bool:
        return await self._make_thumbnail()

    async def _make_thumbnail(self) -> bool:
        cmd = self._CMD.format(
            filepath=self._file_path,
            second=self._get_thumb_second(),
            thumbpath=self._thumbnail_path,
        )
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
            self._log.error('Failed to make thumbnail for %s', self._file_path)
            return False
        return True

    def _get_thumb_second(self) -> float:
        """Get a valid thumbnail second (seek time point for FFmpeg).

        If the video is shorter the user-specified thumbnail frame second,
        just take it from the middle of the video because FFmpeg might error out.
        """
        if self._duration <= settings.THUMBNAIL_FRAME_SECOND:
            return round(self._duration / 2, 1)
        return settings.THUMBNAIL_FRAME_SECOND

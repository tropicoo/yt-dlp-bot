from core.tasks.abstract import AbstractFfBinaryTask


class MakeThumbnailTask(AbstractFfBinaryTask):
    _CMD = 'ffmpeg -y -loglevel error -i "{filepath}" -vframes 1 -q:v 31 "{thumbpath}"'

    def __init__(self, thumbnail_path: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._thumbnail_path = thumbnail_path

    async def run(self) -> bool:
        return await self._make_thumbnail()

    async def _make_thumbnail(self) -> bool:
        cmd = self._CMD.format(filepath=self._file_path, thumbpath=self._thumbnail_path)
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

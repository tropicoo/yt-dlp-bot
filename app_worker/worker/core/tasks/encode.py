import os

from yt_shared.schemas.media import DownMedia

from worker.core.tasks.abstract import AbstractFfBinaryTask


class EncodeToH264Task(AbstractFfBinaryTask):
    _EXT = 'mp4'
    _CMD_TIMEOUT = 120

    def __init__(self, media: DownMedia, cmd_tpl: str) -> None:
        super().__init__(file_path=media.video.filepath)
        self._media = media
        self._video = media.video
        self._CMD = cmd_tpl  # lol

    async def run(self) -> None:
        await self._encode_video()

    def _get_output_path(self) -> str:
        filename = f'{self._video.filename.rsplit(".", 1)[0]}-h264.{self._EXT}'
        return os.path.join(self._media.root_path, filename)

    async def _encode_video(self) -> None:
        output = self._get_output_path()
        cmd = self._CMD.format(filepath=self._file_path, output=output)
        self._log.info('Encoding: %s', cmd)

        proc = await self._run_proc(cmd)
        if not proc:
            return None

        stdout, stderr = await self._get_stdout_stderr(proc)
        self._log.info(
            'Process %s returncode: %d, stderr: %s', cmd, proc.returncode, stderr
        )
        if proc.returncode:
            err_msg = (
                f'Failed to make video context. Is file broken? {self._file_path}?'
            )
            self._log.error(err_msg)
            raise RuntimeError(err_msg)

        self._video.mark_as_converted(filepath=output)

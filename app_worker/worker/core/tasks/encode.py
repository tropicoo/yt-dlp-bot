import os

from yt_shared.schemas.media import DownMedia

from worker.core.tasks.abstract import AbstractFfBinaryTask
from worker.core.tasks.ffprobe_context import GetFfprobeContextTask
from worker.enums import VideoCodecName, VideoCodecType


class EncodeToH264Task(AbstractFfBinaryTask):
    _EXT = 'mp4'
    _CMD_TIMEOUT = 120

    def __init__(
        self, media: DownMedia, cmd_tpl: str, check_if_in_final_format: bool = True
    ) -> None:
        super().__init__(file_path=media.video.filepath)
        self._media = media
        self._video = media.video
        self._CMD = cmd_tpl  # lol

        self._check_if_in_final_format = check_if_in_final_format

    async def run(self) -> None:
        await self._run()

    async def _run(self) -> None:
        if self._check_if_in_final_format:
            if not await self._is_already_h264():
                await self._encode_video()
        else:
            await self._encode_video()

    async def _is_already_h264(self) -> bool:
        probe_ctx = await GetFfprobeContextTask(self._file_path).run()
        stream: dict
        for stream in probe_ctx['streams']:
            if (
                stream['codec_type'] == VideoCodecType.VIDEO.value
                and stream['codec_name'] == VideoCodecName.H264.value
            ):
                return True
        return False

    def _get_output_path(self) -> str:
        filename = f'{self._video.filename.rsplit(".", 1)[0]}-h264.{self._EXT}'
        return os.path.join(self._media.root_path, filename)

    async def _encode_video(self) -> None:
        output = self._get_output_path()
        cmd = self._CMD.format(filepath=self._file_path, output=output)
        self._log.info('Encoding: %s', cmd)

        proc = await self._run_proc(cmd)
        if not proc:
            return

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

import json

from core.tasks.abstract import AbstractFfBinaryTask


class GetFfprobeContextTask(AbstractFfBinaryTask):
    _CMD = 'ffprobe -loglevel error -show_format -show_streams -of json "{filepath}"'

    async def run(self) -> dict | None:
        return await self._get_context()

    async def _get_context(self) -> dict | None:
        cmd = self._CMD.format(filepath=self._file_path)
        proc = await self._run_proc(cmd)
        if not proc:
            return None

        stdout, stderr = await self._get_stdout_stderr(proc)
        self._log.debug(
            'Process %s returncode: %d, stderr: %s', cmd, proc.returncode, stderr
        )
        if proc.returncode:
            self._log.error(
                'Failed to make video context. Is file broken? %s?', self._file_path
            )
            return None
        try:
            return json.loads(stdout)
        except Exception:
            self._log.exception(
                'Failed to load ffprobe output [type %s]: %s', type(stdout), stdout
            )
            return None

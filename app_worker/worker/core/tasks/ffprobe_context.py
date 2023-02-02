import json

from worker.core.tasks.abstract import AbstractFfBinaryTask


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
        self._log.info(
            'Process %s returncode: %d, stderr: %s', cmd, proc.returncode, stderr
        )
        if proc.returncode:
            err_msg = (
                f'Failed to make video context. Is file broken? {self._file_path}?'
            )
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        try:
            return json.loads(stdout)
        except Exception as err:
            err_msg = f'Failed to load ffprobe output [type {type(stdout)}]: {stdout}'
            self._log.exception(err_msg)
            raise RuntimeError(err_msg) from err

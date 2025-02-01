import asyncio
import os
import signal
from abc import ABC
from pathlib import Path

from yt_shared.utils.common import wrap
from yt_shared.utils.tasks.abstract import AbstractTask


class AbstractFfBinaryTask(AbstractTask, ABC):
    _CMD: str | None = None
    _CMD_TIMEOUT = 60

    def __init__(self, file_path: Path) -> None:
        super().__init__()
        self._file_path = file_path
        self._killpg = wrap(os.killpg)

    async def _run_proc(self, cmd: str) -> asyncio.subprocess.Process | None:
        proc = await asyncio.create_subprocess_shell(
            cmd=cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            await asyncio.wait_for(proc.wait(), timeout=self._CMD_TIMEOUT)
        except TimeoutError:
            self._log.error(
                'Failed to execute %s: process ran longer than expected and was killed',
                cmd,
            )
            await self._killpg(os.getpgid(proc.pid), signal.SIGINT)
            return None

        return proc

    @staticmethod
    async def _get_stdout_stderr(proc: asyncio.subprocess.Process) -> tuple[str, str]:
        stdout, stderr = await proc.stdout.read(), await proc.stderr.read()
        return stdout.decode().strip(), stderr.decode().strip()

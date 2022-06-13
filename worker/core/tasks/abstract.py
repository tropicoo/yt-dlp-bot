import abc
import asyncio
import logging
import os
import signal
from typing import Optional

from yt_shared.utils import wrap


class AbstractFfBinaryTask(metaclass=abc.ABCMeta):
    _CMD: Optional[str] = None
    _CMD_TIMEOUT = 10

    def __init__(self, file_path: str) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._file_path = file_path
        self._killpg = wrap(os.killpg)

    async def _run_proc(self, cmd: str) -> Optional[asyncio.subprocess.Process]:
        proc = await asyncio.create_subprocess_shell(
            cmd=cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            await asyncio.wait_for(proc.wait(), timeout=self._CMD_TIMEOUT)
            return proc
        except asyncio.TimeoutError:
            self._log.error(
                'Failed to execute %s: process ran longer than '
                'expected and was killed',
                cmd,
            )
            await self._killpg(os.getpgid(proc.pid), signal.SIGINT)
            return None

    @staticmethod
    async def _get_stdout_stderr(proc: asyncio.subprocess.Process) -> tuple[str, str]:
        stdout, stderr = await proc.stdout.read(), await proc.stderr.read()
        return stdout.decode().strip(), stderr.decode().strip()

    @abc.abstractmethod
    async def run(self) -> None:
        """Main entry point."""
        pass

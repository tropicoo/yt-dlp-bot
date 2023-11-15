import logging
import os
import shutil
from typing import Iterable

from yt_shared.utils.common import format_bytes


def file_cleanup(file_paths: Iterable[str], log: logging.Logger = None) -> None:
    log = log or logging.getLogger()
    log.debug('Performing cleanup of %s', file_paths)
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as err:
                log.warning('File "%s" not deleted: %s', file_path, err)


def remove_dir(dir_path: str) -> None:
    shutil.rmtree(dir_path)


def file_size(filepath: str) -> int:
    """Return file size in bytes."""
    return os.path.getsize(filepath)


def list_files(path: str) -> dict[str, str]:
    return {
        filename: format_bytes(file_size(os.path.join(path, filename)))
        for filename in os.listdir(path)
    }

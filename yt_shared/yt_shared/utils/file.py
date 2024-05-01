import logging
import shutil
from pathlib import Path
from typing import Iterable

from yt_shared.utils.common import format_bytes


def file_cleanup(file_paths: Iterable[Path], log: logging.Logger = None) -> None:
    log = log or logging.getLogger()
    log.debug('Performing cleanup of %s', file_paths)
    for file_path in file_paths:
        if file_path.is_file():
            file_path.unlink()


def remove_dir(dir_path: Path) -> None:
    shutil.rmtree(dir_path)


def file_size(filepath: Path) -> int:
    """Return file size in bytes."""
    return filepath.stat().st_size


def list_files_human(path: Path) -> dict[Path, str]:
    return {
        filename: format_bytes(file_size(path / filename))
        for filename in path.iterdir()
    }

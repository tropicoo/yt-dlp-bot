import logging
import shutil
from collections.abc import Iterable
from pathlib import Path

from yt_shared.utils.common import format_bytes


def file_cleanup(file_paths: Iterable[Path], log: logging.Logger | None = None) -> None:
    """Delete the specified files if they exist.

    Args:
        file_paths (Iterable[Path]): An iterable of file paths to be deleted.
        log (logging.Logger, optional): Logger for logging the cleanup operation. Defaults to None.

    """
    log = log or logging.getLogger()
    log.debug('Performing cleanup of %s', file_paths)
    for file_path in file_paths:
        if file_path.is_file():
            file_path.unlink()


def remove_dir(dir_path: Path) -> None:
    """Remove the specified directory and all its contents.

    Args:
        dir_path (Path): The path of the directory to be removed.

    """
    shutil.rmtree(dir_path)


def file_size(filepath: Path) -> int:
    """Return the size of the specified file in bytes.

    Args:
        filepath (Path): The path of the file.

    Returns:
        int: The size of the file in bytes.

    """
    return filepath.stat().st_size


def list_files_human(path: Path) -> dict[str, str]:
    """List files in the specified directory with human-readable file sizes.

    Args:
        path (Path): The path of the directory.

    Returns:
        dict[str, str]: A dictionary where keys are file names and values are human-readable file sizes.

    """
    return {
        filepath.name: format_bytes(file_size(filepath)) for filepath in path.iterdir()
    }

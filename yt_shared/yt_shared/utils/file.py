import logging
import os
from typing import Iterable


def file_cleanup(file_paths: Iterable[str], log: logging.Logger = None) -> None:
    log = log or logging.getLogger()
    log.debug('Performing cleanup of %s', file_paths)
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as err:
                log.warning('File "%s" not deleted: %s', file_path, err)

import re

from pydantic import DirectoryPath, field_validator
from yt_shared.config import CommonSettings

_RATE_RE = re.compile(r'\d+(\.\d+)?[KMG]?', re.IGNORECASE)


class WorkerSettings(CommonSettings):
    APPLICATION_NAME: str
    MAX_SIMULTANEOUS_DOWNLOADS: int
    STORAGE_PATH: DirectoryPath
    THUMBNAIL_FRAME_SECOND: float
    INSTAGRAM_ENCODE_TO_H264: bool
    FACEBOOK_ENCODE_TO_H264: bool
    MAX_DOWNLOAD_THREADS: str
    DOWNLOAD_RATE_LIMIT: str = ''

    @field_validator('MAX_DOWNLOAD_THREADS')
    @classmethod
    def validate_max_download_threads(cls, value: str) -> str:
        """Value must be integer enclosed as string."""
        if not value.isdigit():
            raise ValueError('Value must be integer enclosed as string.')
        return value

    @field_validator('DOWNLOAD_RATE_LIMIT')
    @classmethod
    def validate_download_rate_limit(cls, value: str) -> str:
        """Bytes per second, optionally suffixed; empty means no limit.

        Checked here so a typo stops the worker at startup instead of failing
        every single download.
        """
        value = value.strip()
        if value and not _RATE_RE.fullmatch(value):
            raise ValueError(
                'Value must be a download rate such as "500K" or "4.2M", '
                'or empty for no limit.'
            )
        return value


settings = WorkerSettings()

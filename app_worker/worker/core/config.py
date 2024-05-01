from pydantic import DirectoryPath
from yt_shared.config import Settings


class WorkerSettings(Settings):
    APPLICATION_NAME: str
    MAX_SIMULTANEOUS_DOWNLOADS: int
    STORAGE_PATH: DirectoryPath
    THUMBNAIL_FRAME_SECOND: float
    INSTAGRAM_ENCODE_TO_H264: bool


settings = WorkerSettings()

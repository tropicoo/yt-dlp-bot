from yt_shared.config import Settings


class WorkerSettings(Settings):
    APPLICATION_NAME: str
    MAX_SIMULTANEOUS_DOWNLOADS: int
    SAVE_VIDEO_FILE: bool
    STORAGE_PATH: str
    THUMBNAIL_FRAME_SECOND: float


settings = WorkerSettings()

from yt_shared.models import Task


class BaseVideoServiceError(Exception):
    def __init__(self, message: str, task: Task | None = None) -> None:
        super().__init__(message)
        self.task = task


class GeneralVideoServiceError(BaseVideoServiceError):
    pass


class DownloadVideoServiceError(BaseVideoServiceError):
    pass


class MediaDownloaderError(Exception):
    pass

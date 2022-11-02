from yt_shared.models import Task


class BaseVideoServiceError(Exception):
    task: Task | None = None


class GeneralVideoServiceError(BaseVideoServiceError):
    pass


class DownloadVideoServiceError(BaseVideoServiceError):
    pass

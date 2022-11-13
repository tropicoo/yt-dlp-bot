import logging

import yt_dlp

from yt_shared.schemas.video import DownVideo

try:
    from ytdl_opts.user import YTDL_OPTS
except ImportError:
    from ytdl_opts.default import YTDL_OPTS


class VideoDownloader:

    _PLAYLIST = 'playlist'

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    def download_video(self, url: str) -> DownVideo:
        try:
            return self._download(url)
        except Exception:
            self._log.exception('Failed to download %s', url)
            raise

    def _download(self, url: str) -> DownVideo:
        self._log.info('Downloading %s', url)
        with yt_dlp.YoutubeDL(YTDL_OPTS) as ytdl:
            meta = ytdl.extract_info(url, download=True)
            meta_sanitized = ytdl.sanitize_info(meta)

        self._log.info('Finished downloading %s', url)
        self._log.debug('Download meta: %s', meta_sanitized)
        duration, width, height = self._get_video_context(meta)
        return DownVideo(
            title=meta['title'],
            name=self._get_filename(meta),
            duration=duration,
            width=width,
            height=height,
            meta=meta_sanitized,
        )

    def _get_video_context(self, meta: dict) -> tuple[float | None, int | None, int | None]:
        if meta['_type'] == self._PLAYLIST:
            entry: dict = meta['entries'][0]
            requested_video: dict = entry['requested_downloads'][0]
            return (
                self._to_float(entry.get('duration')),
                requested_video.get('width'),
                requested_video.get('height'),
            )
        return (
            self._to_float(meta.get('duration')),
            meta['requested_downloads'][0].get('width'),
            meta['requested_downloads'][0].get('height'),
        )

    @staticmethod
    def _to_float(duration: int | float | None) -> float | None:
        try:
            return float(duration)
        except TypeError:
            return duration

    def _get_filename(self, meta: dict) -> str:
        return self._get_filepath(meta).rsplit('/', maxsplit=1)[-1]

    def _get_filepath(self, meta: dict) -> str:
        if meta['_type'] == self._PLAYLIST:
            return meta['entries'][0]['requested_downloads'][0]['filepath']
        return meta['requested_downloads'][0]['filepath']

import logging
import os
import shutil
from copy import deepcopy
from tempfile import TemporaryDirectory

import yt_dlp

from core.config import settings
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
        root_tmp_dir = settings.TMP_DOWNLOAD_PATH
        with TemporaryDirectory(prefix='tmp_video_dir-', dir=root_tmp_dir) as tmp_dir:
            curr_tmp_dir: str = os.path.join(root_tmp_dir, tmp_dir)
            self._log.info('Downloading to %s', curr_tmp_dir)
            ytdl_opts = deepcopy(YTDL_OPTS)
            ytdl_opts['outtmpl'] = os.path.join(
                curr_tmp_dir,
                ytdl_opts['outtmpl'],
            )
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                meta = ytdl.extract_info(url, download=True)
                meta_sanitized = ytdl.sanitize_info(meta)

            filename = self._get_filename(meta)
            filepath = os.path.join(curr_tmp_dir, filename)
            self._log.info('Moving %s to %s', filepath, root_tmp_dir)
            self._log.info('Content of %s: %s', curr_tmp_dir, os.listdir(curr_tmp_dir))
            shutil.move(filepath, root_tmp_dir)
            self._log.info('Removing %s', curr_tmp_dir)

        self._log.info('Finished downloading %s', url)
        self._log.debug('Download meta: %s', meta_sanitized)
        duration, width, height = self._get_video_context(meta)
        return DownVideo(
            title=meta['title'],
            name=filename,
            duration=duration,
            width=width,
            height=height,
            meta=meta_sanitized,
        )

    def _get_video_context(
        self, meta: dict
    ) -> tuple[float | None, int | None, int | None]:
        if meta['_type'] == self._PLAYLIST:
            if not len(meta['entries']):
                raise ValueError(
                    'Item said to be downloaded but no entries to process.'
                )
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

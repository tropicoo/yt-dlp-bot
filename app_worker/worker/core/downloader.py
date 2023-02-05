import logging
import os
import shutil
from copy import deepcopy
from tempfile import TemporaryDirectory

import yt_dlp
from yt_shared.schemas.video import DownVideo
from yt_shared.utils.common import random_string

from worker.core.config import settings

try:
    from ytdl_opts.user import YTDL_OPTS
except ImportError:
    from ytdl_opts.default import YTDL_OPTS


class VideoDownloader:
    _PLAYLIST_TYPE = 'playlist'

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
        tmp_down_path = os.path.join(
            settings.TMP_DOWNLOAD_ROOT_PATH, settings.TMP_DOWNLOAD_DIR
        )
        with TemporaryDirectory(prefix='tmp_video_dir-', dir=tmp_down_path) as tmp_dir:
            curr_tmp_dir = os.path.join(tmp_down_path, tmp_dir)
            self._log.info('Downloading to %s', curr_tmp_dir)
            ytdl_opts = deepcopy(YTDL_OPTS)
            ytdl_opts['outtmpl'] = os.path.join(
                curr_tmp_dir,
                ytdl_opts['outtmpl'],
            )
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                meta = ytdl.extract_info(url, download=True)
                meta_sanitized = ytdl.sanitize_info(meta)

            self._log.info('Finished downloading %s', url)
            self._log.debug('Download meta: %s', meta_sanitized)

            filename = self._get_filename(meta)
            filepath = os.path.join(curr_tmp_dir, filename)
            destination_dir = os.path.join(
                os.path.join(
                    settings.TMP_DOWNLOAD_ROOT_PATH, settings.TMP_DOWNLOADED_DIR
                ),
                random_string(number=4),
            )
            self._log.info('Moving %s to %s', filepath, destination_dir)
            self._log.info('Content of %s: %s', curr_tmp_dir, os.listdir(curr_tmp_dir))
            os.mkdir(destination_dir)
            shutil.move(filepath, destination_dir)
            self._log.info('Removing %s', curr_tmp_dir)

        duration, width, height = self._get_video_context(meta)
        return DownVideo(
            title=meta['title'],
            name=filename,
            duration=duration,
            width=width,
            height=height,
            meta=meta_sanitized,
            filepath=os.path.join(destination_dir, filename),
            root_path=destination_dir,
        )

    def _get_video_context(
        self, meta: dict
    ) -> tuple[float | None, int | None, int | None]:
        if meta['_type'] == self._PLAYLIST_TYPE:
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
        if meta['_type'] == self._PLAYLIST_TYPE:
            return meta['entries'][0]['requested_downloads'][0]['filepath']
        return meta['requested_downloads'][0]['filepath']

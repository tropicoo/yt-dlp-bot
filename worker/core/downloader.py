import logging

import yt_dlp

from yt_shared.schemas.video import DownVideo

try:
    from ytdl_opts.user import YTDL_OPTS
except ImportError:
    from ytdl_opts.default import YTDL_OPTS


class VideoDownloader:
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
            meta = ytdl.extract_info(url, download=False)
            meta = ytdl.sanitize_info(meta)
            try:
                ytdl.download(url)
            except yt_dlp.utils.MaxDownloadsReached as err:
                self._log.warning(
                    'Check video URL %s. Looks like a page with videos. Stopped on %d: %s',
                    url,
                    YTDL_OPTS['max_downloads'],
                    err,
                )

        self._log.info('Finished downloading %s', url)
        self._log.debug('Download meta: %s', meta)
        filepath = ytdl.prepare_filename(meta)
        return DownVideo(
            title=meta['title'],
            name=filepath.rsplit('/', maxsplit=1)[-1],
            duration=meta.get('duration'),
            width=meta.get('width'),
            height=meta.get('height'),
            meta=meta,
        )

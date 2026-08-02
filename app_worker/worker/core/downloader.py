import glob
import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, ClassVar, Final

import yt_dlp
from yt_shared.enums import DownMediaType
from yt_shared.schemas.media import Audio, DownMedia, InbMediaPayload, Video
from yt_shared.utils.common import format_bytes, gen_random_str
from yt_shared.utils.file import file_size, list_files_human, remove_dir

from worker.core.config import settings
from worker.core.exceptions import MediaDownloaderError
from worker.core.ytdlp_logger import YtdlpLogger
from ytdl_opts.per_host._base import AbstractHostConfig

# Signs that the site rejected the session rather than the request itself, so
# dropping the cookies is worth a try.
_COOKIE_REJECTION_MARKERS: Final[tuple[str, ...]] = (
    "confirm you're not a bot",
    'cookies are no longer valid',
    'cookies are invalid',
    'account cookies are no longer valid',
)

# Signs that the site wants an authenticated session, so adding the cookies is
# worth a try. The bot check appears in both lists on purpose: which way to flip
# depends on whether the attempt that failed carried cookies.
_AUTH_REQUIRED_MARKERS: Final[tuple[str, ...]] = (
    "confirm you're not a bot",
    'sign in',
    'log in',
    'login required',
    'private video',
    'members-only',
    'join this channel',
    'age-restricted',
    'requires authentication',
)

try:
    from ytdl_opts.user import FINAL_AUDIO_FORMAT, FINAL_THUMBNAIL_FORMAT
except ImportError:
    from ytdl_opts.default import FINAL_AUDIO_FORMAT, FINAL_THUMBNAIL_FORMAT


class MediaDownloader:
    _PLAYLIST_TYPE = 'playlist'
    _DESTINATION_TMP_DIR_NAME_LEN = 4
    _KEEP_VIDEO_OPTION = '--keep-video'

    _EXT_TO_NAME: ClassVar[dict[str, str]] = {
        FINAL_AUDIO_FORMAT: 'audio',
        FINAL_THUMBNAIL_FORMAT: 'thumbnail',
    }

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._tmp_downloaded_dest_dir = (
            settings.TMP_DOWNLOAD_ROOT_PATH / settings.TMP_DOWNLOADED_DIR
        )

    def download(
        self,
        host_conf: AbstractHostConfig,
        media_payload: InbMediaPayload,
        progress_hook: Callable[[dict], None] | None = None,
        postprocessor_hook: Callable[[dict], None] | None = None,
        on_cookies_rejected: Callable[[], None] | None = None,
    ) -> DownMedia:
        try:
            return self._download(
                host_conf=host_conf,
                media_payload=media_payload,
                progress_hook=progress_hook,
                postprocessor_hook=postprocessor_hook,
                on_cookies_rejected=on_cookies_rejected,
            )
        except Exception:
            self._log.error('Failed to download %s', host_conf.url)
            raise

    def _download(
        self,
        host_conf: AbstractHostConfig,
        media_payload: InbMediaPayload,
        progress_hook: Callable[[dict], None] | None = None,
        postprocessor_hook: Callable[[dict], None] | None = None,
        on_cookies_rejected: Callable[[], None] | None = None,
    ) -> DownMedia:
        media_type = media_payload.download_media_type
        video_quality = media_payload.video_quality
        url = host_conf.url
        self._log.info(
            'Downloading %s, media_type %s, quality %s', url, media_type, video_quality
        )
        tmp_down_path = settings.TMP_DOWNLOAD_ROOT_PATH / settings.TMP_DOWNLOAD_DIR
        with TemporaryDirectory(prefix='tmp_media_dir-', dir=tmp_down_path) as tmp_dir:
            curr_tmp_dir = tmp_down_path / tmp_dir

            ytdl_opts_model = host_conf.build_config(
                media_type=media_type,
                curr_tmp_dir=curr_tmp_dir,
                video_quality=video_quality,
            )

            ytdl_opts = dict(ytdl_opts_model.ytdl_opts)
            if progress_hook is not None:
                ytdl_opts['progress_hooks'] = [progress_hook]
            if postprocessor_hook is not None:
                ytdl_opts['postprocessor_hooks'] = [postprocessor_hook]

            self._log.info('Downloading "%s" to "%s"', url, curr_tmp_dir)
            self._log.info('Downloading with options: %s', ytdl_opts_model.ytdl_opts)

            cookiefile = ytdl_opts.get('cookiefile')
            cookies_last = bool(cookiefile) and host_conf.COOKIES_LAST_RESORT
            if cookies_last:
                # This host is happier anonymously; the cookies stay in reserve.
                ytdl_opts.pop('cookiefile')

            meta, meta_sanitized, err_msg = self._extract(ytdl_opts, url)

            if meta is None and cookiefile:
                retry_opts = self._retry_with_other_cookie_state(
                    err_msg, ytdl_opts, cookiefile, url, on_cookies_rejected
                )
                if retry_opts is not None:
                    meta, meta_sanitized, err_msg = self._extract(retry_opts, url)

            if meta is None:
                raise MediaDownloaderError(err_msg)

            if not list(curr_tmp_dir.iterdir()):
                err_msg = 'Nothing downloaded. Is URL valid?'
                self._log.error(err_msg)
                raise MediaDownloaderError(err_msg)

            self._log.info('Finished downloading %s', url)
            self._log.debug('Downloaded "%s" meta: %s', url, meta_sanitized)
            self._log.info(
                'Content of "%s": %s', curr_tmp_dir, list_files_human(curr_tmp_dir)
            )

            destination_dir = self._tmp_downloaded_dest_dir / gen_random_str(
                length=self._DESTINATION_TMP_DIR_NAME_LEN
            )
            destination_dir.mkdir()

            audio, video = self._create_media_dtos(
                media_type=media_type,
                meta=meta,
                curr_tmp_dir=curr_tmp_dir,
                destination_dir=destination_dir,
                custom_video_filename=media_payload.custom_filename,
            )
            self._log.info(
                'Removing temporary download directory "%s" with leftover files %s',
                curr_tmp_dir,
                list_files_human(curr_tmp_dir),
            )

        return DownMedia(
            media_type=media_type,
            audio=audio,
            video=video,
            meta=meta_sanitized,
            root_path=destination_dir,
        )

    def _extract(
        self, ytdl_opts: dict, url: str
    ) -> tuple[dict | None, dict | None, str | None]:
        """Run yt-dlp once, returning its metadata or the reason it failed."""
        ytdlp_logger = YtdlpLogger(self._log)
        with yt_dlp.YoutubeDL({**ytdl_opts, 'logger': ytdlp_logger}) as ytdl:
            meta: dict | None = ytdl.extract_info(url, download=True)
            if not meta:
                # yt-dlp reported the reason and swallowed it due to
                # `ignoreerrors`, so take it from the collected messages.
                reason = (
                    ytdlp_logger.last_error()
                    or 'Error during media download. Check logs.'
                )
                self._log.error('%s. Meta: %s', reason, meta)
                return None, None, reason
            return meta, ytdl.sanitize_info(meta), None

    def _retry_with_other_cookie_state(
        self,
        reason: str | None,
        ytdl_opts: dict,
        cookiefile: str,
        url: str,
        on_cookies_rejected: Callable[[], None] | None,
    ) -> dict | None:
        """Options for one more attempt with the cookies flipped, or ``None``.

        Whichever state just failed, the other one is tried once — but only when
        the reason suggests it could help. A private video fails identically
        without cookies, and a rate limit is not fixed by adding them.
        """
        if not reason:
            return None
        # yt-dlp writes some of these with a typographic apostrophe.
        normalised = reason.replace('’', "'").lower()
        used_cookies = 'cookiefile' in ytdl_opts

        if used_cookies:
            if not any(m in normalised for m in _COOKIE_REJECTION_MARKERS):
                return None
            self._log.warning(
                'Cookies were rejected for "%s", retrying without them. They have '
                'most likely expired and are worth refreshing: for some sites '
                'stale cookies fail where an anonymous request succeeds.',
                url,
            )
            if on_cookies_rejected is not None:
                on_cookies_rejected()
            return {k: v for k, v in ytdl_opts.items() if k != 'cookiefile'}

        if not any(m in normalised for m in _AUTH_REQUIRED_MARKERS):
            return None
        self._log.info(
            'Anonymous request for "%s" needs an authenticated session, '
            'retrying with the cookie file.',
            url,
        )
        return {**ytdl_opts, 'cookiefile': cookiefile}

    def _create_media_dtos(
        self,
        media_type: DownMediaType,
        meta: dict,
        curr_tmp_dir: str,
        destination_dir: str,
        custom_video_filename: str | None = None,
    ) -> tuple[Audio | None, Video | None]:
        def get_audio() -> Audio:
            return create_dto(self._create_audio_dto)

        def get_video() -> Video:
            return create_dto(self._create_video_dto)

        def create_dto(
            func: Callable[[dict, str, str, str | None], Audio | Video],
        ) -> Audio | Video:
            try:
                return func(meta, curr_tmp_dir, destination_dir, custom_video_filename)
            except Exception:
                remove_dir(destination_dir)
                raise

        match media_type:
            case DownMediaType.AUDIO:
                return get_audio(), None
            case DownMediaType.VIDEO:
                return None, get_video()
            case DownMediaType.AUDIO_VIDEO:
                return get_audio(), get_video()
            case _:
                raise RuntimeError(f'Unknown media type "{media_type}"')

    def _create_video_dto(
        self,
        meta: dict,
        curr_tmp_dir: Path,
        destination_dir: Path,
        custom_video_filename: str | None = None,
    ) -> Video:
        video_filename = self._get_video_filename(meta)
        video_filepath = curr_tmp_dir / video_filename

        if custom_video_filename:
            dest_path = destination_dir / custom_video_filename
        else:
            dest_path = destination_dir / video_filename

        self._log.info('Moving "%s" to "%s"', video_filepath, dest_path)
        shutil.move(video_filepath, dest_path)

        thumb_path: Path | None = None
        thumb_name = self._find_downloaded_file(
            root_path=curr_tmp_dir, extension=FINAL_THUMBNAIL_FORMAT
        )
        if thumb_name:
            _thumb_path = curr_tmp_dir / thumb_name
            shutil.move(_thumb_path, destination_dir)
            thumb_path = destination_dir / thumb_name

        duration, width, height = self._get_video_context(meta)
        return Video(
            title=meta['title'],
            original_filename=video_filename,
            custom_filename=custom_video_filename,
            duration=duration,
            width=width,
            height=height,
            directory_path=destination_dir,
            file_size=file_size(dest_path),
            thumb_path=thumb_path,
            thumb_name=thumb_name,
            chapters=self._extract_chapters(meta),
        )

    def _create_audio_dto(
        self,
        meta: dict,
        curr_tmp_dir: Path,
        destination_dir: Path,
        custom_video_filename: str | None = None,  # noqa: ARG002 # TODO: Make for audio.
    ) -> Audio:
        audio_filename = self._find_downloaded_file(
            root_path=curr_tmp_dir, extension=FINAL_AUDIO_FORMAT
        )
        audio_filepath = curr_tmp_dir / audio_filename
        self._log.info('Moving "%s" to "%s"', audio_filepath, destination_dir)
        shutil.move(audio_filepath, destination_dir)

        # Find and move thumbnail for audio (same as for video)
        thumb_path: Path | None = None
        thumb_name = self._find_downloaded_file(
            root_path=curr_tmp_dir, extension=FINAL_THUMBNAIL_FORMAT
        )
        if thumb_name:
            _thumb_path = curr_tmp_dir / thumb_name
            shutil.move(_thumb_path, destination_dir)
            thumb_path = destination_dir / thumb_name

        return Audio(
            title=meta['title'],
            original_filename=audio_filename,
            duration=self._to_float(meta.get('duration')),
            directory_path=destination_dir,
            file_size=file_size(destination_dir / audio_filename),
            thumb_path=thumb_path,
            thumb_name=thumb_name,
            chapters=self._extract_chapters(meta),
            # Music sources name the artist outright; for everything else the
            # uploading channel is the closest thing to a performer.
            artist=self._to_str(
                meta.get('artist') or meta.get('uploader') or meta.get('channel')
            ),
            track=self._to_str(meta.get('track')),
        )

    @staticmethod
    def _extract_chapters(meta: dict) -> list[dict]:
        """Chapters as the source defines them, if it defines any.

        yt-dlp already fills in missing start times and titles, so anything left
        incomplete here is genuinely unusable and is dropped.
        """
        chapters = []
        for chapter in meta.get('chapters') or []:
            start = chapter.get('start_time')
            title = str(chapter.get('title') or '').strip()
            if start is None or not title:
                continue
            chapters.append({'start_time': float(start), 'title': title})
        return chapters

    @staticmethod
    def _to_str(value: Any) -> str | None:
        """Normalise a metadata field that may be missing, empty or a list."""
        if not value:
            return None
        if isinstance(value, (list, tuple)):
            value = ', '.join(str(item) for item in value if item)
        return str(value).strip() or None

    def _find_downloaded_file(self, root_path: Path, extension: str) -> str | None:
        """Try to find downloaded audio or thumbnail file."""
        verbose_name = self._EXT_TO_NAME[extension]
        for file_name in glob.glob(f'*.{extension}', root_dir=root_path):  # noqa: PTH207
            self._log.info(
                'Found downloaded %s: "%s" [%s]',
                verbose_name,
                file_name,
                format_bytes(file_size(root_path / file_name)),
            )
            return file_name
        self._log.info('Downloaded %s not found in "%s"', verbose_name, root_path)
        return None

    def _get_video_context(
        self, meta: dict
    ) -> tuple[float | None, int | float | None, int | float | None]:
        if meta['_type'] == self._PLAYLIST_TYPE:
            if not len(meta['entries']):
                raise ValueError(
                    'Item said to be downloaded but no entries to process.'
                )
            entry: dict = meta['entries'][0]
            requested_video = self._get_requested_video(entry['requested_downloads'])
            return (
                self._to_float(entry.get('duration')),
                requested_video.get('width'),
                requested_video.get('height'),
            )
        requested_video = self._get_requested_video(meta['requested_downloads'])
        return (
            self._to_float(meta.get('duration')),
            requested_video.get('width'),
            requested_video.get('height'),
        )

    def _get_requested_video(self, requested_downloads: list[dict]) -> dict | None:
        for download_obj in requested_downloads:
            if download_obj.get('ext', '') != FINAL_AUDIO_FORMAT:
                # Attempt to handle yt-dlp glitch.
                download_obj['filepath'] = download_obj.get(
                    'filepath', download_obj.get('filename', download_obj['_filename'])
                )
                return download_obj

        # When video was converted to audio but video kept.
        for download_obj in requested_downloads:
            if download_obj['ext'] != download_obj['_filename'].rsplit('.', 1)[-1]:
                download_obj_copy = download_obj.copy()
                self._log.info(
                    'Replacing video path in meta "%s" with "%s"',
                    download_obj_copy['filepath'],
                    download_obj_copy['_filename'],
                )
                download_obj_copy['filepath'] = download_obj_copy.get(
                    'filename', download_obj_copy['_filename']
                )
                return download_obj_copy
        return None

    @staticmethod
    def _to_float(duration: float | None) -> float | None:
        try:
            return float(duration)
        except TypeError:
            return duration

    def _get_video_filename(self, meta: dict) -> str:
        return self._get_video_filepath(meta).rsplit('/', maxsplit=1)[-1]

    def _get_video_filepath(self, meta: dict) -> str:
        if meta['_type'] == self._PLAYLIST_TYPE:
            requested_downloads: list[dict] = meta['entries'][0]['requested_downloads']
            requested_video = self._get_requested_video(requested_downloads)
        else:
            requested_downloads = meta['requested_downloads']
            requested_video = self._get_requested_video(requested_downloads)

        try:
            return requested_video['filepath']
        except (AttributeError, KeyError):
            err_msg = 'Video filepath not found'
            self._log.exception('%s, meta: %s', err_msg, meta)
            raise ValueError(err_msg) from None

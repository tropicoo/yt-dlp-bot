import glob
import logging
import os
import shutil
from tempfile import TemporaryDirectory
from typing import Callable

import yt_dlp
from yt_shared.enums import DownMediaType
from yt_shared.schemas.media import Audio, DownMedia, Video
from yt_shared.utils.common import format_bytes, random_string
from yt_shared.utils.file import file_size, list_files, remove_dir

from worker.core.config import settings
from worker.core.exceptions import MediaDownloaderError
from ytdl_opts.per_host._base import AbstractHostConfig

try:
    from ytdl_opts.user import FINAL_AUDIO_FORMAT, FINAL_THUMBNAIL_FORMAT
except ImportError:
    from ytdl_opts.default import FINAL_AUDIO_FORMAT, FINAL_THUMBNAIL_FORMAT


class MediaDownloader:
    _PLAYLIST_TYPE = 'playlist'
    _DESTINATION_TMP_DIR_NAME_LEN = 4
    _KEEP_VIDEO_OPTION = '--keep-video'

    _EXT_TO_NAME: dict[str, str] = {
        FINAL_AUDIO_FORMAT: 'audio',
        FINAL_THUMBNAIL_FORMAT: 'thumbnail',
    }

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._tmp_downloaded_dest_dir = os.path.join(
            settings.TMP_DOWNLOAD_ROOT_PATH, settings.TMP_DOWNLOADED_DIR
        )

    def download(
        self, host_conf: AbstractHostConfig, media_type: DownMediaType
    ) -> DownMedia:
        try:
            return self._download(host_conf=host_conf, media_type=media_type)
        except Exception:
            self._log.error('Failed to download %s', host_conf.url)
            raise

    def _download(
        self, host_conf: AbstractHostConfig, media_type: DownMediaType
    ) -> DownMedia:
        url = host_conf.url
        self._log.info('Downloading %s, media_type %s', url, media_type)
        tmp_down_path = os.path.join(
            settings.TMP_DOWNLOAD_ROOT_PATH, settings.TMP_DOWNLOAD_DIR
        )
        with TemporaryDirectory(prefix='tmp_media_dir-', dir=tmp_down_path) as tmp_dir:
            curr_tmp_dir = os.path.join(tmp_down_path, tmp_dir)

            ytdl_opts_model = host_conf.build_config(
                media_type=media_type, curr_tmp_dir=curr_tmp_dir
            )

            with yt_dlp.YoutubeDL(ytdl_opts_model.ytdl_opts) as ytdl:
                self._log.info('Downloading %s', url)
                self._log.info('Downloading to %s', curr_tmp_dir)
                self._log.info('Downloading with options %s', ytdl_opts_model.ytdl_opts)

                meta: dict | None = ytdl.extract_info(url, download=True)
                if not meta:
                    err_msg = 'Error during media download. Check logs.'
                    self._log.error('%s. Meta: %s', err_msg, meta)
                    raise MediaDownloaderError(err_msg)

                current_files = os.listdir(curr_tmp_dir)
                if not current_files:
                    err_msg = 'Nothing downloaded. Is URL valid?'
                    self._log.error(err_msg)
                    raise MediaDownloaderError(err_msg)

                meta_sanitized = ytdl.sanitize_info(meta)

            self._log.info('Finished downloading %s', url)
            self._log.debug('Downloaded "%s" meta: %s', url, meta_sanitized)
            self._log.info(
                'Content of "%s": %s', curr_tmp_dir, list_files(curr_tmp_dir)
            )

            destination_dir = os.path.join(
                self._tmp_downloaded_dest_dir,
                random_string(number=self._DESTINATION_TMP_DIR_NAME_LEN),
            )
            os.mkdir(destination_dir)

            audio, video = self._create_media_dtos(
                media_type=media_type,
                meta=meta,
                curr_tmp_dir=curr_tmp_dir,
                destination_dir=destination_dir,
            )
            self._log.info(
                'Removing temporary download directory "%s" with leftover files %s',
                curr_tmp_dir,
                os.listdir(curr_tmp_dir),
            )

        return DownMedia(
            media_type=media_type,
            audio=audio,
            video=video,
            meta=meta_sanitized,
            root_path=destination_dir,
        )

    def _create_media_dtos(
        self,
        media_type: DownMediaType,
        meta: dict,
        curr_tmp_dir: str,
        destination_dir: str,
    ) -> tuple[Audio | None, Video | None]:
        def get_audio() -> Audio:
            return create_dto(self._create_audio_dto)

        def get_video() -> Video:
            return create_dto(self._create_video_dto)

        def create_dto(
            func: Callable[[dict, str, str], Audio | Video],
        ) -> Audio | Video:
            try:
                return func(
                    meta,
                    curr_tmp_dir,
                    destination_dir,
                )
            except Exception:
                remove_dir(destination_dir)
                raise

        match media_type:  # noqa: E999
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
        curr_tmp_dir: str,
        destination_dir: str,
    ) -> Video:
        video_filename = self._get_video_filename(meta)
        video_filepath = os.path.join(curr_tmp_dir, video_filename)

        self._log.info('Moving "%s" to "%s"', video_filepath, destination_dir)
        shutil.move(video_filepath, destination_dir)

        thumb_path: str | None = None
        thumb_name = self._find_downloaded_file(
            root_path=curr_tmp_dir,
            extension=FINAL_THUMBNAIL_FORMAT,
        )
        if thumb_name:
            _thumb_path = os.path.join(curr_tmp_dir, thumb_name)
            shutil.move(_thumb_path, destination_dir)
            thumb_path = os.path.join(destination_dir, thumb_name)

        duration, width, height = self._get_video_context(meta)
        filepath = os.path.join(destination_dir, video_filename)
        return Video(
            title=meta['title'],
            filename=video_filename,
            duration=duration,
            width=width,
            height=height,
            filepath=filepath,
            file_size=file_size(filepath),
            thumb_path=thumb_path,
            thumb_name=thumb_name,
        )

    def _create_audio_dto(
        self,
        meta: dict,
        curr_tmp_dir: str,
        destination_dir: str,
    ) -> Audio:
        audio_filename = self._find_downloaded_file(
            root_path=curr_tmp_dir,
            extension=FINAL_AUDIO_FORMAT,
        )
        audio_filepath = os.path.join(curr_tmp_dir, audio_filename)
        self._log.info('Moving "%s" to "%s"', audio_filepath, destination_dir)
        shutil.move(audio_filepath, destination_dir)
        filepath = os.path.join(destination_dir, audio_filename)
        return Audio(
            title=meta['title'],
            filename=audio_filename,
            duration=None,
            filepath=filepath,
            file_size=file_size(filepath),
        )

    def _find_downloaded_file(self, root_path: str, extension: str) -> str | None:
        """Try to find downloaded audio or thumbnail file."""
        verbose_name = self._EXT_TO_NAME[extension]
        for file_name in glob.glob(f'*.{extension}', root_dir=root_path):
            self._log.info(
                'Found downloaded %s: "%s" [%s]',
                verbose_name,
                file_name,
                format_bytes(file_size(os.path.join(root_path, file_name))),
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
            if download_obj['ext'] != FINAL_AUDIO_FORMAT:
                return download_obj

        # When video was converted to audio but video kept.
        for download_obj in requested_downloads:
            if download_obj['ext'] != download_obj['_filename'].rsplit('.', 1)[-1]:
                download_obj = download_obj.copy()
                self._log.info(
                    'Replacing video path in meta "%s" with "%s"',
                    download_obj['filepath'],
                    download_obj['_filename'],
                )
                download_obj['filepath'] = download_obj['_filename']
                return download_obj
        return None

    @staticmethod
    def _to_float(duration: int | float | None) -> float | None:
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
            raise ValueError(err_msg)

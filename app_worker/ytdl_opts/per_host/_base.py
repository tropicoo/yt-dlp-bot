import logging
from abc import abstractmethod
from copy import deepcopy
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from yt_shared.enums import DownMediaType

from worker.utils import cli_to_api

try:
    from ytdl_opts.user import (
        AUDIO_FORMAT_YTDL_OPTS,
        AUDIO_YTDL_OPTS,
        DEFAULT_VIDEO_FORMAT_SORT_OPT,
        DEFAULT_YTDL_OPTS,
        FINAL_AUDIO_FORMAT,
        FINAL_THUMBNAIL_FORMAT,
        VIDEO_YTDL_OPTS,
    )
except ImportError:
    from ytdl_opts.default import (
        AUDIO_FORMAT_YTDL_OPTS,
        AUDIO_YTDL_OPTS,
        DEFAULT_VIDEO_FORMAT_SORT_OPT,
        DEFAULT_YTDL_OPTS,
        FINAL_AUDIO_FORMAT,
        FINAL_THUMBNAIL_FORMAT,
        VIDEO_YTDL_OPTS,
    )


class BaseHostConfModel(BaseModel):
    # TODO: Add validators.
    model_config = ConfigDict(strict=True, frozen=True)

    hostnames: tuple[str, ...]

    encode_audio: bool
    encode_video: bool

    ffmpeg_audio_opts: str | None
    ffmpeg_video_opts: str | None

    ytdl_opts: dict


class AbstractHostConfig:
    """Abstract yt-dlp host config."""

    ALLOW_NULL_HOSTNAMES: bool | None = None
    HOSTNAMES: tuple[str, ...] | None = None

    CUSTOM_VIDEO_YTDL_OPTS: list[str] | None = None

    ENCODE_AUDIO: bool | None = None
    ENCODE_VIDEO: bool | None = None

    KEEP_VIDEO_OPTION = '--keep-video'

    DEFAULT_YTDL_OPTS = DEFAULT_YTDL_OPTS

    AUDIO_YTDL_OPTS = AUDIO_YTDL_OPTS
    AUDIO_FORMAT_YTDL_OPTS = AUDIO_FORMAT_YTDL_OPTS

    FINAL_AUDIO_FORMAT = FINAL_AUDIO_FORMAT
    FINAL_THUMBNAIL_FORMAT = FINAL_THUMBNAIL_FORMAT

    DEFAULT_VIDEO_YTDL_OPTS = VIDEO_YTDL_OPTS
    DEFAULT_VIDEO_FORMAT_SORT_OPT = DEFAULT_VIDEO_FORMAT_SORT_OPT

    FFMPEG_AUDIO_OPTS: str | None = None
    FFMPEG_VIDEO_OPTS: str | None = None

    def __init__(self, url: str) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._validate_hostname()
        self.url = url
        self._log.info('Instantiating "%s" for url "%s"', self.__class__.__name__, url)

    def _validate_hostname(self) -> None:
        if not self.ALLOW_NULL_HOSTNAMES and not self.HOSTNAMES:
            raise ValueError('Hostname(s) must be set before instantiation.')

    @abstractmethod
    def build_config(
        self, media_type: DownMediaType, curr_tmp_dir: str
    ) -> BaseHostConfModel:
        pass

    def _build_ytdl_opts(self, media_type: DownMediaType, curr_tmp_dir: Path) -> dict:
        def _add_video_opts(ytdl_opts_: list[str]) -> None:
            ytdl_opts_.extend(self.DEFAULT_VIDEO_YTDL_OPTS)
            ytdl_opts_.extend(self._build_custom_ytdl_video_opts())

        ytdl_opts = deepcopy(self.DEFAULT_YTDL_OPTS)

        match media_type:
            case DownMediaType.AUDIO:
                ytdl_opts.extend(self.AUDIO_YTDL_OPTS)
                ytdl_opts.extend(self.AUDIO_FORMAT_YTDL_OPTS)
            case DownMediaType.VIDEO:
                _add_video_opts(ytdl_opts)
            case DownMediaType.AUDIO_VIDEO:
                ytdl_opts.extend(self.AUDIO_YTDL_OPTS)
                _add_video_opts(ytdl_opts)
                ytdl_opts.append(self.KEEP_VIDEO_OPTION)

        ytdl_opts = cli_to_api(ytdl_opts)
        ytdl_opts['outtmpl']['default'] = str(
            curr_tmp_dir / ytdl_opts['outtmpl']['default']
        )
        return ytdl_opts

    @abstractmethod
    def _build_custom_ytdl_video_opts(self) -> list[str]:
        pass

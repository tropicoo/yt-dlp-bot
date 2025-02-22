"""Default `yt-dlp` download CLI options.

Only CLI options are allowed to be stored as configuration. They are later converted to internal API options.
More here https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/options.py or 'yt-dlp --help'

If you want to change any of these values or add new ones, copy all content to the `user.py` in the same
directory as this file, and edit the values.

For example, if you want to the add proxy option, you should copy the whole content of this file and add
the proxy option line split by two into the 'DEFAULT_YTDL_OPTS' tuple of CLI options.

DEFAULT_YTDL_OPTS: Final[_OptsType] = (
    '--proxy',
    'http://<your_address>',
    ...
)
"""

from typing import Final

from worker.core.config import settings
from worker.utils import get_cookies_opts_if_not_empty

FINAL_AUDIO_FORMAT: Final[str] = 'mp3'
FINAL_THUMBNAIL_FORMAT: Final[str] = 'jpg'


type _OptsType = tuple[str, ...]

DEFAULT_YTDL_OPTS: Final[_OptsType] = (
    '--output',
    '%(title).200B.%(ext)s',
    '--no-playlist',
    '--playlist-items',
    '1:1',
    '--concurrent-fragments',
    settings.MAX_DOWNLOAD_THREADS,
    '--ignore-errors',
    '--verbose',
    *get_cookies_opts_if_not_empty(),
)

DEFAULT_VIDEO_FORMAT_SORT_OPT: Final[_OptsType] = (
    '--format-sort',
    'res,vcodec:h265,h264',
)

AUDIO_YTDL_OPTS: Final[_OptsType] = (
    '--extract-audio',
    '--audio-quality',
    '0',
    '--audio-format',
    FINAL_AUDIO_FORMAT,
)

AUDIO_FORMAT_YTDL_OPTS: Final[_OptsType] = ('--format', 'bestaudio/best')

VIDEO_YTDL_OPTS: Final[_OptsType] = (
    '--format',
    'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    '--write-thumbnail',
    '--convert-thumbnails',
    FINAL_THUMBNAIL_FORMAT,
)

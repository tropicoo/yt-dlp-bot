import os
from urllib.parse import urlparse

import yt_dlp

_COOKIES_FILEPATH = '/app/cookies/cookies.txt'
_INSTAGRAM_HOST = 'instagram.com'


def cli_to_api(opts: list) -> dict:
    """Convert yt-dlp CLI options to internal API ones."""
    default = yt_dlp.parse_options([]).ydl_opts
    diff = {
        k: v for k, v in yt_dlp.parse_options(opts).ydl_opts.items() if default[k] != v
    }
    if 'postprocessors' in diff:
        diff['postprocessors'] = [
            pp for pp in diff['postprocessors'] if pp not in default['postprocessors']
        ]
    return diff


def is_file_empty(filepath: str) -> bool:
    """Check whether the file is empty."""
    return os.path.isfile(filepath) and os.path.getsize(filepath) == 0


def get_cookies_opts_if_not_empty() -> list[str]:
    """Return yt-dlp cookies option with cookies filepath."""
    return [] if is_file_empty(_COOKIES_FILEPATH) else ['--cookies', _COOKIES_FILEPATH]


def is_instagram(url: str) -> bool:
    return _INSTAGRAM_HOST in urlparse(url).netloc


def get_media_format_options() -> str:
    pass

from pathlib import Path
from typing import Final

import yt_dlp

from worker.core.config import settings

_PRIVATE_COOKIES_FILEPATH: Final[Path] = Path('/app/cookies/_cookies.txt')
_COOKIES_FILEPATH: Final[Path] = Path('/app/cookies/cookies.txt')
_COOKIES_OPTION_NAME: Final[str] = '--cookies'
_RATE_LIMIT_OPTION_NAME: Final[str] = '--limit-rate'


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


def is_file_empty(filepath: Path) -> bool:
    """Check whether the file is empty."""
    return filepath.is_file() and filepath.stat().st_size == 0


def get_rate_limit_opts_if_set() -> tuple[str, str] | tuple:
    """Return yt-dlp rate limit option when a limit is configured."""
    if not settings.DOWNLOAD_RATE_LIMIT:
        return ()
    return _RATE_LIMIT_OPTION_NAME, settings.DOWNLOAD_RATE_LIMIT


def get_cookies_opts_if_not_empty() -> tuple[str, str] | tuple:
    """Return yt-dlp cookies option with cookies filepath."""
    if _PRIVATE_COOKIES_FILEPATH.exists() and not is_file_empty(
        _PRIVATE_COOKIES_FILEPATH
    ):
        return _COOKIES_OPTION_NAME, str(_PRIVATE_COOKIES_FILEPATH)

    if is_file_empty(_COOKIES_FILEPATH):
        return ()
    return _COOKIES_OPTION_NAME, str(_COOKIES_FILEPATH)

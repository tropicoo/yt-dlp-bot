from pathlib import Path
from typing import Final

import yt_dlp

_PRIVATE_COOKIES_FILEPATH: Final[Path] = Path('/app/cookies/_cookies.txt')
_COOKIES_FILEPATH: Final[Path] = Path('/app/cookies/cookies.txt')
_COOKIES_OPTION_NAME: Final[str] = '--cookies'


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


def get_cookies_opts_if_not_empty() -> tuple[str, str] | tuple:
    """Return yt-dlp cookies option with cookies filepath."""
    if _PRIVATE_COOKIES_FILEPATH.exists() and not is_file_empty(
        _PRIVATE_COOKIES_FILEPATH
    ):
        return _COOKIES_OPTION_NAME, str(_PRIVATE_COOKIES_FILEPATH)

    if is_file_empty(_COOKIES_FILEPATH):
        return ()
    return _COOKIES_OPTION_NAME, str(_COOKIES_FILEPATH)

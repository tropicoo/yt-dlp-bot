from pathlib import Path

import yt_dlp

_COOKIES_FILEPATH = Path('/app/cookies/cookies.txt')


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


def get_cookies_opts_if_not_empty() -> list[str]:
    """Return yt-dlp cookies option with cookies filepath."""
    if is_file_empty(_COOKIES_FILEPATH):
        return []
    return ['--cookies', str(_COOKIES_FILEPATH)]

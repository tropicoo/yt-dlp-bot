"""Fitting thumbnails into what Telegram is willing to accept."""

import logging
from pathlib import Path
from typing import Final

from PIL import Image

# Telegram silently discards a thumbnail that breaks these limits and shows one
# it generates itself instead, so a source cover has to be shrunk rather than
# passed through at its original resolution.
_MAX_SIDE: Final[int] = 320
_MAX_BYTES: Final[int] = 200 * 1024
_START_QUALITY: Final[int] = 85
_MIN_QUALITY: Final[int] = 40
_QUALITY_STEP: Final[int] = 15

_log = logging.getLogger(__name__)


def fit_for_telegram(thumb_path: Path | str | None) -> None:
    """Shrink a thumbnail in place so Telegram actually uses it."""
    if not thumb_path:
        return

    path = Path(thumb_path)
    if not path.is_file():
        return

    try:
        _fit(path)
    except Exception:
        # A thumbnail is a nicety, never a reason to fail an upload.
        _log.exception('Could not fit thumbnail "%s" for Telegram', path)


def _fit(path: Path) -> None:
    original_size = path.stat().st_size
    with Image.open(path) as opened:
        # Also drops any alpha channel, which JPEG cannot store.
        image = opened.convert('RGB')

    if max(image.size) <= _MAX_SIDE and original_size <= _MAX_BYTES:
        return

    image.thumbnail((_MAX_SIDE, _MAX_SIDE), Image.LANCZOS)

    quality = _START_QUALITY
    while True:
        image.save(path, format='JPEG', quality=quality, optimize=True)
        if path.stat().st_size <= _MAX_BYTES or quality <= _MIN_QUALITY:
            break
        quality -= _QUALITY_STEP

    _log.info(
        'Fitted thumbnail "%s" for Telegram: %d -> %d bytes, %dx%d',
        path.name,
        original_size,
        path.stat().st_size,
        *image.size,
    )

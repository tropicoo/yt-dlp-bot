"""Inline keyboard builders for format selection."""

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from yt_shared.enums import DownMediaType, VideoQuality


# Callback data prefixes
MEDIA_TYPE_PREFIX = 'mt:'
QUALITY_PREFIX = 'q:'
DOWNLOAD_PREFIX = 'dl:'
CANCEL_PREFIX = 'cancel:'


def build_media_type_keyboard(url_id: str) -> InlineKeyboardMarkup:
    """Build keyboard for selecting media type (Video/Audio)."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                '🎬 Video',
                callback_data=f'{MEDIA_TYPE_PREFIX}{DownMediaType.VIDEO}:{url_id}',
            ),
            InlineKeyboardButton(
                '🎵 Audio',
                callback_data=f'{MEDIA_TYPE_PREFIX}{DownMediaType.AUDIO}:{url_id}',
            ),
        ],
        [
            InlineKeyboardButton(
                '🎬+🎵 Both',
                callback_data=f'{MEDIA_TYPE_PREFIX}{DownMediaType.AUDIO_VIDEO}:{url_id}',
            ),
        ],
        [
            InlineKeyboardButton(
                '❌ Cancel',
                callback_data=f'{CANCEL_PREFIX}{url_id}',
            ),
        ],
    ])


def build_quality_keyboard(
    url_id: str, media_type: DownMediaType
) -> InlineKeyboardMarkup:
    """Build keyboard for selecting video quality."""
    if media_type == DownMediaType.AUDIO:
        # For audio, skip quality selection and go directly to download
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    '⬇️ Download Audio',
                    callback_data=f'{DOWNLOAD_PREFIX}{media_type}:{VideoQuality.BEST}:{url_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    '⬅️ Back',
                    callback_data=f'{MEDIA_TYPE_PREFIX}back:{url_id}',
                ),
            ],
        ])

    # For video, show quality options
    quality_buttons = [
        [
            InlineKeyboardButton(
                '🏆 Best Quality',
                callback_data=f'{DOWNLOAD_PREFIX}{media_type}:{VideoQuality.BEST}:{url_id}',
            ),
        ],
        [
            InlineKeyboardButton(
                '4K',
                callback_data=f'{DOWNLOAD_PREFIX}{media_type}:{VideoQuality.UHD_4K}:{url_id}',
            ),
            InlineKeyboardButton(
                '1440p',
                callback_data=f'{DOWNLOAD_PREFIX}{media_type}:{VideoQuality.QHD_1440P}:{url_id}',
            ),
        ],
        [
            InlineKeyboardButton(
                '1080p',
                callback_data=f'{DOWNLOAD_PREFIX}{media_type}:{VideoQuality.FHD_1080P}:{url_id}',
            ),
            InlineKeyboardButton(
                '720p',
                callback_data=f'{DOWNLOAD_PREFIX}{media_type}:{VideoQuality.HD_720P}:{url_id}',
            ),
        ],
        [
            InlineKeyboardButton(
                '480p',
                callback_data=f'{DOWNLOAD_PREFIX}{media_type}:{VideoQuality.SD_480P}:{url_id}',
            ),
            InlineKeyboardButton(
                '360p',
                callback_data=f'{DOWNLOAD_PREFIX}{media_type}:{VideoQuality.LD_360P}:{url_id}',
            ),
        ],
        [
            InlineKeyboardButton(
                '⬅️ Back',
                callback_data=f'{MEDIA_TYPE_PREFIX}back:{url_id}',
            ),
            InlineKeyboardButton(
                '❌ Cancel',
                callback_data=f'{CANCEL_PREFIX}{url_id}',
            ),
        ],
    ]

    return InlineKeyboardMarkup(quality_buttons)

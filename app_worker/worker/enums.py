from enum import StrEnum


class VideoCodecName(StrEnum):
    """Ffprobe video codec name."""

    H264 = 'h264'
    VP9 = 'vp9'


class VideoCodecType(StrEnum):
    """Ffprobe video codec type."""

    AUDIO = 'audio'
    VIDEO = 'video'

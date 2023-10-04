import enum


class VideoCodecName(enum.Enum):
    """Ffprobe video codec name."""

    H264 = 'h264'
    VP9 = 'vp9'


class VideoCodecType(enum.Enum):
    """Ffprobe video codec type."""

    AUDIO = 'audio'
    VIDEO = 'video'

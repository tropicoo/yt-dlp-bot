from pathlib import Path

from yt_shared.constants import INSTAGRAM_HOSTS
from yt_shared.enums import DownMediaType

from worker.core.config import settings
from ytdl_opts.per_host._base import AbstractHostConfig, BaseHostConfModel
from ytdl_opts.per_host._registry import HostConfRegistry


class InstagramHostModel(BaseHostConfModel):
    pass


class InstagramHost(AbstractHostConfig, metaclass=HostConfRegistry):
    ALLOW_NULL_HOSTNAMES = False
    HOSTNAMES = INSTAGRAM_HOSTS
    ENCODE_AUDIO = False
    ENCODE_VIDEO = settings.INSTAGRAM_ENCODE_TO_H264

    FFMPEG_AUDIO_OPTS = None
    # Instagram returns VP9+AAC in MP4 container for logged users and needs to be
    # encoded to H264 since Telegram doesn't play VP9 on iOS.
    FFMPEG_VIDEO_OPTS = 'ffmpeg -y -loglevel error -i "{filepath}" -c:v libx264 -pix_fmt yuv420p -preset veryfast -crf 22 -movflags +faststart -c:a copy "{output}"'

    def build_config(
        self, media_type: DownMediaType, curr_tmp_dir: Path
    ) -> InstagramHostModel:
        return InstagramHostModel(
            hostnames=self.HOSTNAMES,
            encode_audio=self.ENCODE_AUDIO,
            encode_video=self.ENCODE_VIDEO,
            ffmpeg_audio_opts=self.FFMPEG_AUDIO_OPTS,
            ffmpeg_video_opts=self.FFMPEG_VIDEO_OPTS,
            ytdl_opts=self._build_ytdl_opts(media_type, curr_tmp_dir),
        )

    def _build_custom_ytdl_video_opts(self) -> list[str]:
        return self.DEFAULT_VIDEO_FORMAT_SORT_OPT

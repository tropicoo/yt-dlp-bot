from pathlib import Path

from yt_shared.constants import FACEBOOK_HOSTS
from yt_shared.enums import DownMediaType

from worker.core.config import settings
from ytdl_opts.per_host._base import AbstractHostConfig, BaseHostConfModel
from ytdl_opts.per_host._registry import HostConfRegistry


class FacebookHostModel(BaseHostConfModel):
    pass


class FacebookHost(AbstractHostConfig, metaclass=HostConfRegistry):
    ALLOW_NULL_HOSTNAMES = False
    HOSTNAMES = FACEBOOK_HOSTS
    ENCODE_AUDIO = False
    ENCODE_VIDEO = settings.FACEBOOK_ENCODE_TO_H264

    FFMPEG_AUDIO_OPTS = None
    # Facebook returns VP9+AAC in MP4 container for logged users and needs to be
    # encoded to H264 since Telegram doesn't play VP9 on iOS.
    FFMPEG_VIDEO_OPTS = 'ffmpeg -y -loglevel error -i "{filepath}" -c:v libx264 -pix_fmt yuv420p -preset slow -threads 2 -crf 22 -movflags +faststart -c:a copy "{output}"'

    def build_config(
        self, media_type: DownMediaType, curr_tmp_dir: Path
    ) -> FacebookHostModel:
        return FacebookHostModel(
            hostnames=self.HOSTNAMES,
            encode_audio=self.ENCODE_AUDIO,
            encode_video=self.ENCODE_VIDEO,
            ffmpeg_audio_opts=self.FFMPEG_AUDIO_OPTS,
            ffmpeg_video_opts=self.FFMPEG_VIDEO_OPTS,
            ytdl_opts=self._build_ytdl_opts(media_type, curr_tmp_dir),
        )

    def _build_custom_ytdl_video_opts(self) -> tuple[str, ...]:
        return self.DEFAULT_VIDEO_FORMAT_SORT_OPT

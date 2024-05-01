from pathlib import Path

from yt_shared.constants import TIKTOK_HOSTS
from yt_shared.enums import DownMediaType

from ytdl_opts.per_host._base import AbstractHostConfig, BaseHostConfModel
from ytdl_opts.per_host._registry import HostConfRegistry


class TikTokHostModel(BaseHostConfModel):
    pass


class TikTokHost(AbstractHostConfig, metaclass=HostConfRegistry):
    ALLOW_NULL_HOSTNAMES = False
    HOSTNAMES = TIKTOK_HOSTS
    ENCODE_AUDIO = False
    ENCODE_VIDEO = False

    def build_config(
        self, media_type: DownMediaType, curr_tmp_dir: Path
    ) -> TikTokHostModel:
        return TikTokHostModel(
            hostnames=self.HOSTNAMES,
            encode_audio=self.ENCODE_AUDIO,
            encode_video=self.ENCODE_VIDEO,
            ffmpeg_audio_opts=self.FFMPEG_AUDIO_OPTS,
            ffmpeg_video_opts=self.FFMPEG_VIDEO_OPTS,
            ytdl_opts=self._build_ytdl_opts(media_type, curr_tmp_dir),
        )

    def _build_custom_ytdl_video_opts(self) -> list[str]:
        return self.DEFAULT_VIDEO_FORMAT_SORT_OPT

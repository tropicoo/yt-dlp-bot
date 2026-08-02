from pathlib import Path

from yt_shared.constants import YOUTUBE_HOSTS
from yt_shared.enums import DownMediaType, VideoQuality

from ytdl_opts.per_host._base import AbstractHostConfig, BaseHostConfModel
from ytdl_opts.per_host._registry import HostConfRegistry


class YoutubeHostModel(BaseHostConfModel):
    pass


class YoutubeHost(AbstractHostConfig, metaclass=HostConfRegistry):
    """YouTube, which is happier with an anonymous request than a stale session.

    An authenticated session coming from a server address draws the bot check
    far more readily than no session at all, and cookies exported from a browser
    you stay signed into are rotated away within hours. Downloads therefore
    start anonymously here, and the cookie file is only brought in if the site
    actually asks for one — the opposite of every other host.
    """

    ALLOW_NULL_HOSTNAMES = False
    HOSTNAMES = YOUTUBE_HOSTS
    ENCODE_AUDIO = False
    ENCODE_VIDEO = False

    COOKIES_LAST_RESORT = True

    def build_config(
        self,
        media_type: DownMediaType,
        curr_tmp_dir: Path,
        video_quality: VideoQuality = VideoQuality.BEST,
    ) -> YoutubeHostModel:
        return YoutubeHostModel(
            hostnames=self.HOSTNAMES,
            encode_audio=self.ENCODE_AUDIO,
            encode_video=self.ENCODE_VIDEO,
            ffmpeg_audio_opts=self.FFMPEG_AUDIO_OPTS,
            ffmpeg_video_opts=self.FFMPEG_VIDEO_OPTS,
            ytdl_opts=self._build_ytdl_opts(media_type, curr_tmp_dir, video_quality),
        )

    def _build_custom_ytdl_video_opts(self) -> tuple[str, ...]:
        return self.DEFAULT_VIDEO_FORMAT_SORT_OPT

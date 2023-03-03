"""yt-dlp download CLI options.

Only CLI options are allowed to be stored as configuration. They are later converted to internal API options.
More here https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/options.py or 'yt-dlp --help'
"""

FINAL_AUDIO_FORMAT = 'mp3'
FINAL_THUMBNAIL_FORMAT = 'jpg'

DEFAULT_YTDL_OPTS = [
    '--output',
    '%(title).200B.%(ext)s',
    '--no-playlist',
    '--playlist-items',
    '1:1',
    '--concurrent-fragments',
    '5',
    '--ignore-errors',
    '--verbose',
]

AUDIO_YTDL_OPTS = [
    '--extract-audio',
    '--audio-quality',
    '0',
    '--audio-format',
    FINAL_AUDIO_FORMAT,
]

AUDIO_FORMAT_YTDL_OPTS = [
    '--format',
    'bestaudio/best',
]

VIDEO_YTDL_OPTS = [
    '--format',
    'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    '--write-thumbnail',
    '--convert-thumbnails',
    FINAL_THUMBNAIL_FORMAT,
]

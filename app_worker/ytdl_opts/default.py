# More here https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/options.py or 'yt-dlp --help'
YTDL_OPTS = [
    '--output',
    '%(title).200B.%(ext)s',
    '--format',
    'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    '--no-playlist',
    '--playlist-items',
    '1:1',
    '--write-thumbnail',
    '--convert-thumbnails',
    'jpg',
    '--concurrent-fragments',
    '5',
    '--verbose',
]

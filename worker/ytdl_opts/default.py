import os

from yt_shared.config import TMP_DOWNLOAD_PATH

# More here https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/options.py
YTDL_OPTS = {
    'outtmpl': os.path.join(TMP_DOWNLOAD_PATH, '%(title)s.%(ext)s'),
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    'noplaylist': True,
    'max_downloads': 1,
    'concurrent_fragment_downloads': 2,
    'restrictfilenames': True,
}

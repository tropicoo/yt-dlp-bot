import os

from yt_shared.config import STORAGE_PATH

YTDL_OPTS = {
    'outtmpl': os.path.join(STORAGE_PATH, '%(title)s.%(ext)s'),
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    'noplaylist': True,
}

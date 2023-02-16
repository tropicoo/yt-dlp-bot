# Release info

Version: 0.9

Release date: February 16, 2023

# Important

1. Changed format of `YTDL_OPTS` in `app_worker/ytdl_opts/default.py` from `dict`
   to `list` for proper parsing on `yt_dlp` side:
   ```python
   # Old format
   YTDL_OPTS = {
       'outtmpl': '%(title).200B.%(ext)s',
       'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
       'noplaylist': True,
       'playlist_items': '1:1',
       'writethumbnail': True,
       'concurrent_fragment_downloads': 5,
   }
   
   # New format
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
   ```
   This means only `yt-dlp` CLI options can be added (`yt-dlp --help` to list all of them).

# New features

N/A

# Misc

N/A

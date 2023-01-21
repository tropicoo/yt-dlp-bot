# More here https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/options.py
YTDL_OPTS = {
    'outtmpl': '%(title).200B.%(ext)s',
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
    'noplaylist': True,
    'playlist_items': '1:1',
    'concurrent_fragment_downloads': 5,
}

# Release info

Version: 0.4

Release date: November 13, 2022

# Important

1. Changed default yt-dlp options in `worker/ytdl_opts/default.py`. Replaced `'max_downloads': 1` with `'playlist_items': '1:1'`
   to properly handle the result. 
2. It's important to know that the worker backend does not handle downloading more than one video from the playlist even if you change yt-dlp options. Only the first video will be downloaded and processed.

# New features

N/A

# Misc

N/A

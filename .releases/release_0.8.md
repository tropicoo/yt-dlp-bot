# Release info

Version: 0.8

Release date: February 15, 2023

# Important

N/A

# New features

1. yt-dlp will now try to download video thumbnail if it exists. This is done by
   setting `'writethumbnail': True` in `app_worker/ytdl_opts/default.py`. If thumbnail
   wasn't downloaded, `ffmpeg` task will create it as previously.

# Misc

N/A

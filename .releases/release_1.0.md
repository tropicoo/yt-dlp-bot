# Release info

Version: 1.0

Release date: February 25, 2023

# Important

1. Changed content yt-dlp options in `app_worker/DEFAULT_YTDL_OPTS/default.py`
2. Added two new user config options in `app_bot/config-example.yml`:
    1. `download_media_type`: What do download - audio (mp3), video or both. Values can
       be `AUDIO`, `VIDEO`, `AUDIO_VIDEO`.
    2. `save_to_storage`: Moved from `envs/.env_worker`
3. Creating task on API now requires previously mentioned two fields in payload to be
   sent.

# New features

1. Now bot can download audio (mp3), video (default), or both. Just configure the
   preferred mode for the particular user/group.

# Misc

N/A

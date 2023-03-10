# Release Info

Version: 1.1

Release date: March 11, 2023

# Important

* Added new config variable `include_size: !!bool True` for displaying uploaded file
  size.

# New Features

- Show uploaded file size in human-readable format.

# Misc

N/A

---

# Release Info

Version: 1.0

Release date: February 25, 2023

# Important

1. Changed content yt-dlp options in `app_worker/ytdl_opts/default.py`
2. Added two new user config options in `app_bot/config-example.yml`:
    1. `download_media_type`: What to download - audio (mp3), video or both. Values can
       be `AUDIO`, `VIDEO`, `AUDIO_VIDEO`.
    2. `save_to_storage`: Moved from `envs/.env_worker`
3. Creating task on API now requires previously mentioned two fields in payload to be
   sent.

# New Features

1. Now bot can download audio (mp3), video (default), or both. Just configure the
   preferred mode for the particular user/group.

# Misc

N/A


---

# Release Info

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
   This means only `yt-dlp` CLI options can be added (`yt-dlp --help` to list all of
   them).

# New Features

N/A

# Misc

N/A


---

# Release Info

Version: 0.8

Release date: February 15, 2023

# Important

N/A

# New Features

1. yt-dlp will now try to download video thumbnail if it exists. This is done by
   setting `'writethumbnail': True` in `app_worker/ytdl_opts/default.py`. If thumbnail
   wasn't downloaded, `ffmpeg` task will create it as previously.

# Misc

N/A

---

# Release Info

Version: 0.7

Release date: February 5, 2023

# Important

1. Configuration variable `TMP_DOWNLOAD_PATH` renamed to `TMP_DOWNLOAD_ROOT_PATH`
   in `envs/.env_common`.
2. Added 2 new configuration variables `TMP_DOWNLOAD_DIR` and `TMP_DOWNLOADED_DIR`
   to `envs/.env_common`.
3. Fixed bug [#52](https://github.com/tropicoo/yt-dlp-bot/issues/52).

# New Features

N/A

# Misc

N/A


---

# Release Info

Version: 0.6

Release date: January 31, 2023

# Important

1. API bugfixes
2. Renamed microservices directories, e.g. `api` -> `app_api`

# New Features

N/A

# Misc

N/A

---

# Release Info

Version: 0.5

Release date: January 21, 2023

# Important

N/A

# New Features

1. Updated handling failed video download logic. In case of failed post-processing by
   yt-dlp, the (broken) video file could still remain in the temporary directory.
   This update handles this potential issue.

# Misc

N/A



---

# Release Info

Version: 0.4

Release date: November 13, 2022

# Important

1. Changed default yt-dlp options in `worker/ytdl_opts/default.py`.
   Replaced `'max_downloads': 1` with `'playlist_items': '1:1'`
   to properly handle the result.
2. It's important to know that the worker backend does not handle downloading more than
   one video from the playlist even if you change yt-dlp options. Only the first video
   will be downloaded and processed.

# New Features

N/A

# Misc

N/A

---

# Release Info

Version: 0.3

Release date: November 7, 2022

# Important

1. Default config template `bot/config-template.yml` was changed, reconfiguration needed

# New Features

1. New or changed config variables in `bot/config-template.yml`:
    1. `send_startup_message` - send startup messages (per user in config) or not
    2. Fixed typo in `upload_vide_file` -> `upload_video_file`
    3. `ytdlp_version_check_interval` variable replaced with a new `ytdlp` config
       section:
        1. `version_check_enabled` - check for the new `yt-dlp` version or not
        2. `version_check_interval` - check interval in seconds when enabled,
           default `86400` (24 hours)
        3. `notify_users_on_new_version` - send a notification to Telegram chats about
           the new `yt-dlp` version or not (only log records will contain the message
           about the new version) for every user in the config

# Misc

1. Updated README

---

# Release Info

Version: 0.3.1

Release date: November 11, 2022

# Important

N/A

# New Features

* This is maintenance release. No New Features. Bumped `fastapi` and `SQLAlchemy`
  versions, updated README.

# Misc

N/A

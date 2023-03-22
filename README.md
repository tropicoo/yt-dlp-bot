## yt-dlp-bot

Simple and reliable YouTube Download Telegram Bot.

Version: 1.2.1. [Release details](RELEASES.md).

![frames](.assets/download_success.png)


## Support the development

- PayPal [![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=MA6RKYAZH9DSA)
- Bitcoin wallet `14kMRS8SvfD2ydMSMEyAmefHV3Yynf9kAd`

## 😂 Features

* Download audio and videos from any [yt-dlp](https://github.com/yt-dlp/yt-dlp) supported website
  to your storage
* Upload downloaded audio and videos to the Telegram chat
* Trigger video download by sending link to an API
* Track download tasks via API

## ⚙ Quick Setup

1. Create Telegram bot using [BotFather](https://t.me/BotFather) and get your `token`
2. [Get your Telegram API Keys](https://my.telegram.org/apps) (`api_id` and `api_hash`)
3. [Find your Telegram User ID](https://stackoverflow.com/questions/32683992/find-out-my-own-user-id-for-sending-a-message-with-telegram-api)
4. Copy `app_bot/config-example.yml` to `app_bot/config.yml`
5. Write `token`, `api_id`, `api_hash` to `app_bot/config.yml` by changing respective
   placeholders
6. Write your Telegram user id to the `allowed_users` -> `id` by replacing dummy value
   and change or remove `forward_group_id` value (if you want to forward the video to
   some group when upload is enabled)
7. Configure download media type for the user/group: `AUDIO`, `VIDEO` or `AUDIO_VIDEO` 
   in `app_bot/config.yml`'s variable `download_media_type`
8. Check the default environment variables in `envs/.env_common` and change if needed
9. Media `STORAGE_PATH` environment variable is located in
   the `envs/.env_worker` file. By default, it's `/filestorage` path inside the
   container. What you want is to map the real path to this inside
   the `docker-compose.yml` file for `worker` service, e.g. if you're on Windows, next
   strings mean container path `/filestorage` is mapped to real `D:/Videos` so your
   videos will be saved to your `Videos` folder.
   ```yml
     worker:
       ...
       volumes:
         - "D:/Videos:/filestorage"
   ```
10. If you want your downloaded video to be uploaded back to the Telegram,
   set `upload_video_file` config variable for your user in the `app_bot/config.yml`
   to `True`

## 🏃 Run

```bash
# Build base image
docker compose build base-image

# Build and run all services in detached mode
docker compose up --build -d -t 0 && docker compose logs --tail 100 -f

# Stop all services
docker compose stop -t 0
```

Your telegram bot should send you a startup message:
`✨ <YOUR_BOT_NAME> started, paste a video URL to start download` and that's it. After
pasting video URL(s) bot will send you appropriate message whether they were downloaded
or something went wrong.

## 💻 Advanced setup

1. If you want to change `yt-dlp` download options, go to the `app_worker/ytdl_opts`
   directory, copy content from `default.py` to `user.py` and modify as you wish by
   checking [available options](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L180)
   .
2. Default max simultaneous video downloads by worker service is 2. Change
   the `MAX_SIMULTANEOUS_DOWNLOADS` variable in `envs/.env_worker` to desired value but
   keep in mind that default mounted volume size is 7168m (7GB) in `docker-compose.yml`
   so it may be not enough if you download a lot of large videos at once.
3. `yt-dlp` will try to download video thumbnail if it exists. In other case Worker
   service (particularly the FFmpeg process) will make a JPEG thumbnail from the
   video. It's needed when you choose to upload the video to the Telegram chat. By
   default, it will try to make it on the 10th second of the video, but if the video is
   shorter, it will make it on `video length / 2` time point because the FFmpeg process
   will error out. Change the `THUMBNAIL_FRAME_SECOND` variable if needed in
   the `envs/.env_worker` file.
4. Max upload file size for non-premium Telegram user is 2GB (2147483648 bytes) which is
   reflected in the example config `app_bot/config-example.yml`. If the configured user
   is the premium user, you're allowed to upload files up to 4GB (4294967296 bytes) and
   can change the default value stored in the `upload_video_max_file_size` config
   variable.

## 🛑 Failed download

If your URL can't be downloaded for some reason, you will see a message with error
details

![frames](.assets/download_failed.png)

## Access

- **API**: default port is `1984` and no auth. Port can be changed
  in `docker-compose.yml`
- **RabbitMQ**: default creds are located in `envs/.env_common`
- **PostgreSQL**: default creds are located in `envs/.env_common`. Same creds are stored
  for Alembic in `app_worker/alembic.ini` on 53rd line.

## API

By default, API service will run on your `localhost` and `1984` port. API endpoint
documentations lives at `http://127.0.0.1:1984/docs`.

| Endpoint                                                           | Method   | Description                                                                                                                                |
|--------------------------------------------------------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------|
| `/status`                                                          | `GET`    | Get API healthcheck status, usually response is `{"status": "OK"}`                                                                         |
| `/v1/yt-dlp`                                                       | `GET`    | Get latest and currently installed `yt-dlp` version                                                                                        |
| `/v1/tasks/?include_meta=False&status=DONE`                        | `GET`    | Get all tasks with filtering options like to include large file metadata and by task status: `PENDING`, `PROCESSING`, `FAILED` and `DONE`. |
| `/v1/tasks/f828714a-5c50-45de-87c0-3b51b7e04039?include_meta=True` | `GET`    | Get info about task by ID                                                                                                                  |
| `/v1/tasks/latest?include_meta=True`                               | `GET`    | Get info about latest task                                                                                                                 |
| `/v1/tasks/f828714a-5c50-45de-87c0-3b51b7e04039`                   | `DELETE` | Delete task by ID                                                                                                                          |
| `/v1/tasks/latest?include_meta=True`                               | `GET`    | Get info about the latest task                                                                                                             |
| `/v1/tasks`                                                        | `POST`   | Create a download task by sending json payload `{"url": "<URL>"}`                                                                          |
| `/v1/tasks/stats`                                                  | `GET`    | Get overall tasks stats                                                                                                                    |

### API examples

1. `GET http://localhost:1984/v1/tasks/?include_meta=False&status=DONE&limit=2&offset=0`

   Response
   ```json
   [
       {
           "id": "7ab91ef7-461c-4ef6-a35b-d3704fe28e6c",
           "url": "https://youtu.be/jMetnwUZBJQ",
           "status": "DONE",
           "source": "BOT",
           "added_at": "2022-02-14T02:29:55.981622",
           "created": "2022-02-14T02:29:57.211622",
           "updated": "2022-02-14T02:29:59.595551",
           "message_id": 621,
           "file": {
               "id": "4b1c63ed-3e32-43e6-a0b7-c7fc8713b268",
               "created": "2022-02-14T02:29:59.597839",
               "updated": "2022-02-14T02:29:59.597845",
               "name": "Ana Flora Vs. Dj Brizi - Conversa Fiada",
               "ext": "mp4"
           }
       },
       {
           "id": "952bfb7f-1ab3-4db9-8114-eb9995d0cf8d",
           "url": "https://youtu.be/AWy1qiTF64M",
           "status": "DONE",
           "source": "API",
           "added_at": "2022-02-14T00:36:21.398624",
           "created": "2022-02-14T00:36:21.410999",
           "updated": "2022-02-14T00:36:23.535844",
           "message_id": null,
           "file": {
               "id": "ad1fef96-ce1c-4c5e-a426-58e2d5d3e907",
               "created": "2022-02-14T00:36:23.537706",
               "updated": "2022-02-14T00:36:23.537715",
               "name": "Rufford Ford | part 47",
               "ext": "mp4"
           }
       }
   ]
   ```
2. `POST http://localhost:1984/v1/tasks`

   Request
   ```json
   {
       "url": "https://www.youtube.com/watch?v=zGDzdps75ns",
       "download_media_type": "AUDIO_VIDEO",
       "save_to_storage": false
   }
   ```
   Response
   ```json
   {
       "id": "5ac05808-b29c-40d6-b250-07e3e769d8a6",
       "url": "https://youtu.be/AWy1qiTF64M",
       "source": "API",
       "added_at": "2022-02-14T00:35:25.419962+00:00"
   }
   ```
3. `GET http://localhost:1984/v1/tasks/stats`

   Response
   ```json
   {
       "total": 39,
       "unique_urls": 5,
       "pending": 0,
       "processing": 0,
       "failed": 26,
       "done": 13
   }
   ```

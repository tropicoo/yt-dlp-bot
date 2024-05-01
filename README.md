## yt-dlp-bot - Video Download Telegram Bot 🇺🇦

Simple and reliable self-hosted Video Download Telegram Bot.

Version: 1.6. [Release details](RELEASES.md).

![frames](.assets/download_success.png)


## Support the development

- [Buy me a coffee](https://www.buymeacoffee.com/terletsky)
- PayPal [![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=MA6RKYAZH9DSA)
- Bitcoin wallet `14kMRS8SvfD2ydMSMEyAmefHV3Yynf9kAd`

## 😂 Features

* Download audio and free videos with Creative Commons (CC) License from [yt-dlp](https://github.com/yt-dlp/yt-dlp) sites to your storage.
* Upload downloaded media to Telegram.
* Interact with the bot in private or group chats.
* Trigger video downloads via link to the API.
* Track download tasks using the API.

## Disclaimer

- Intended to use only with videos that are under Creative Commons (CC) License

## ⚙ Quick Setup

1. Create Telegram bot using [BotFather](https://t.me/BotFather) and get your `token`
2. [Get your Telegram API Keys](https://my.telegram.org/apps) (`api_id` and `api_hash`)
3. [Find your Telegram User ID](https://stackoverflow.com/questions/32683992/find-out-my-own-user-id-for-sending-a-message-with-telegram-api)
4. Copy `app_bot/config-example.yml` to `app_bot/config.yml`
5. Write `token`, `api_id`, `api_hash` to `app_bot/config.yml` by changing respective
   placeholders
6. Write your Telegram user or group ID to the `allowed_users` -> `id` by replacing dummy
   value and change `forward_group_id` value if you want to forward the video to
   some group/channel when upload is enabled. Bot should be added to the group/channel to be able to send messages.
7. Change download media type for the user/group: `AUDIO`, `VIDEO` or `AUDIO_VIDEO`
   in `app_bot/config.yml`'s variable `download_media_type`. Default `VIDEO`
8. If you want your downloaded audio/video to be uploaded back to the Telegram, set `upload_video_file` config variable 
   for your user/group in the `app_bot/config.yml` to `True`
9. Media `STORAGE_PATH` environment variable is located in
   the `envs/.env_worker` file. By default, it's `/filestorage` path inside the
   container. What you want is to map the real path to this inside
   the `docker-compose.yml` file for `worker` service, e.g. if you're on Windows, next
   strings mean container path `/filestorage` is mapped to real `D:/Videos` so your
   videos will be saved to your `Videos` folder.
   ```yml
     worker:
       volumes:
         - "D:/Videos:/filestorage"
   ```
10. Change application's `LOG_LEVEL` in `envs/.env_common` to `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` if needed

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
`✨ <YOUR_BOT_NAME> started, paste a video URL(s) to start download` and that's it. After
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
5. If the website you want to download from requires authentication you can use your cookies by putting them into
   the `app_worker/cookies/cookies.txt` file in the Netscape format.
6. If your country has an [Alpine Linux Mirror](https://mirrors.alpinelinux.org/), you can speed up the image builds by:
   1. Creating `apk_mirrors` text file and putting there your mirror urls, for example for Ukraine they are:
      ```
      https://alpine.astra.in.ua/v3.17/main
      https://alpine.astra.in.ua/v3.17/community
      ```
   2. Adding `COPY apk_mirrors /etc/apk/repositories` to the third line in `base.Dockerfile`:
      ```dockerfile
      FROM python:3.11-alpine

      COPY apk_mirrors /etc/apk/repositories
      ...
      ```
   3. Rebuild the images.

## 🛑 Failed download

If your URL can't be downloaded for some reason, you will see a message with error
details

![frames](.assets/download_failed.png)

## Access

- **API**: default port is `1984` and no auth. Port can be changed
  in `docker-compose.yml`
- **RabbitMQ**: default credentials are located in `envs/.env_common`
- **PostgreSQL**: default credentials are located in `envs/.env_common`.

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
| `/v1/tasks`                                                        | `POST`   | Create a download task by sending json payload `{"url": "<URL>"}`                                                                          |
| `/v1/tasks/stats`                                                  | `GET`    | Get overall tasks stats                                                                                                                    |

### API examples

1. `GET http://localhost:1984/v1/tasks/?include_meta=False&status=DONE&limit=2&offset=0`

   Response
   ```json
   [
       {
           "id": "7ab91ef7-461c-4ef6-a35b-d3704fe28e6c",
           "url": "https://www.youtube.com/watch?v=PavYAOpVpJI",
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
               "name": "[Drone Freestyle] Mountain Landscape With Snow | Free Stock Footage | Creative Common Video",
               "ext": "mp4"
           }
       }
   ]
   ```
2. `POST http://localhost:1984/v1/tasks`

   Request
   ```json
   {
       "url": "https://www.youtube.com/watch?v=PavYAOpVpJI",
       "download_media_type": "AUDIO_VIDEO",
       "save_to_storage": false,
       "custom_filename": "cool.mp4",
       "automatic_extension": false
   }
   ```
   Response
   ```json
   {
       "id": "5ac05808-b29c-40d6-b250-07e3e769d8a6",
       "url": "https://www.youtube.com/watch?v=PavYAOpVpJI",
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

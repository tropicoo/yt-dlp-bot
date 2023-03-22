FROM yt-base-image

RUN apk add --no-cache ffmpeg

COPY ./app_worker/requirements.txt ./

RUN apk add --no-cache --virtual .build-deps \
        build-base \
    && MAKEFLAGS="-j$(nproc)" pip install --no-cache-dir -r requirements.txt \
    && apk --purge del .build-deps

COPY ./app_worker ./start.py ./

COPY yt_shared /app/yt_shared
RUN pip install -e /app/yt_shared

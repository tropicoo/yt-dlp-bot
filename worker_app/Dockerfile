FROM yt-base-image

RUN apk add --no-cache ffmpeg

COPY ./worker_app/requirements.txt ./

RUN apk add --no-cache --virtual .build-deps \
        build-base \
    && MAKEFLAGS="-j$(nproc)" pip install --no-cache-dir -r requirements.txt \
    && apk --purge del .build-deps

COPY ./worker_app ./start.sh ./

COPY yt_shared /app/yt_shared
RUN pip install -e /app/yt_shared

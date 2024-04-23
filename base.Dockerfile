FROM python:3.12-alpine

ENV TZ=Asia/Bangkok
COPY apk_mirrors /etc/apk/repositories

RUN apk add --no-cache \
        tzdata \
        htop \
        bash \
        libstdc++

WORKDIR /app

COPY ./yt_shared/requirements_shared.txt ./

RUN apk add --no-cache --virtual .build-deps \
        build-base \
    && pip install --upgrade pip setuptools wheel \
    && MAKEFLAGS="-j$(nproc)" pip install --no-cache-dir -r requirements_shared.txt \
    && rm requirements_shared.txt \
    && apk --purge del .build-deps

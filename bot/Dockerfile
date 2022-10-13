FROM python:3.10-alpine

RUN apk add --no-cache \
        tzdata \
        htop \
        bash \
        netcat-openbsd

COPY ./bot/requirements.txt ./yt_shared/requirements_shared.txt /app/

WORKDIR /app

RUN apk add --no-cache --virtual .build-deps \
        linux-headers \
        libffi-dev \
        zlib-dev \
        build-base \
        musl-dev \
        openssl-dev \
        python3-dev  \
    && pip install --upgrade pip setuptools wheel \
    && MAKEFLAGS="-j$(nproc)" \
    && pip install --no-cache-dir -r requirements.txt -r requirements_shared.txt \
    && rm requirements_shared.txt \
    && apk --purge del .build-deps

COPY ./bot /app

COPY ./start.sh /app/start.sh
RUN chmod +x /app/start.sh

COPY yt_shared /app/yt_shared
RUN pip install -e /app/yt_shared

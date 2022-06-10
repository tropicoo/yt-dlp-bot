FROM python:3.10-slim-buster

RUN apt update \
    && apt install --yes --no-install-recommends \
        bash htop net-tools iputils-ping procps netcat ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY ./worker/requirements.txt ./yt_shared/requirements_shared.txt /app/

WORKDIR /app

RUN apt update \
    && apt install --yes gcc g++ libffi-dev libjpeg-dev zlib1g-dev python3-dev build-essential libtool automake \
    && pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt -r requirements_shared.txt \
    && apt-get autoremove --yes gcc g++ libffi-dev libjpeg-dev zlib1g-dev python3-dev build-essential libtool automake \
    && rm -rf /var/lib/apt/lists/* \
    && rm requirements_shared.txt

COPY ./worker /app
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

COPY ./start.sh /app/start.sh
RUN chmod +x /app/start.sh

COPY yt_shared /app/yt_shared
RUN pip install -e /app/yt_shared

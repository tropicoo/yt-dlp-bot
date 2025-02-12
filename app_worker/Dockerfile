FROM yt-base-image

RUN apk update && apk add --no-cache ffmpeg

COPY --from=yt-base-image /opt/venv /opt/venv

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./app_worker/uv.lock,target=uv.lock \
    --mount=type=bind,source=./app_worker/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --inexact && uv pip install --upgrade --pre yt-dlp

COPY ./app_worker ./start.py ./
COPY ./yt_shared ./yt_shared

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv pip install -e ./yt_shared

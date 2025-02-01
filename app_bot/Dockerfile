FROM yt-base-image

COPY --from=yt-base-image /opt/venv /opt/venv

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./app_bot/uv.lock,target=uv.lock \
    --mount=type=bind,source=./app_bot/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --inexact

COPY ./app_bot ./start.py ./
COPY ./yt_shared ./yt_shared

RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    uv pip install -e ./yt_shared

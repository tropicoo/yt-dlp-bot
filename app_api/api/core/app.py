from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from yt_shared.rabbit import get_rabbitmq

from api.api.api_v1.urls import v1_router
from api.api.root.endpoints.healthcheck import healthcheck_router
from api.core.config import settings
from api.core.constants import GZIP_MIN_SIZE
from api.core.log import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    app_ = FastAPI(
        title='YT DLP BOT API',
        description='API for your downloaded videos',
        debug=True,
    )
    app_.include_router(healthcheck_router)
    app_.include_router(v1_router)
    app_.add_middleware(GZipMiddleware, minimum_size=GZIP_MIN_SIZE)
    return app_


app = create_app()


@app.on_event('startup')
async def startup_event():
    redis = aioredis.from_url(
        settings.REDIS_URL, encoding='utf8', decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')
    await get_rabbitmq().register()


@app.on_event('shutdown')
async def shutdown_event():
    await get_rabbitmq().close()

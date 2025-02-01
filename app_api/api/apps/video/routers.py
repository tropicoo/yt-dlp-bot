from fastapi import APIRouter

from api.apps.video.v1.tasks.routers import tasks
from api.apps.video.v1.ytdlp.routers import ytdlp
from api.common.constants import V1_ROUTER_PATH

v1_router = APIRouter(prefix=V1_ROUTER_PATH)
v1_router.include_router(tasks.router, tags=['Tasks'])
v1_router.include_router(ytdlp.router, tags=['yt-dlp'])

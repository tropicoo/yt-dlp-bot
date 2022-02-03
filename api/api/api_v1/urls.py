from fastapi import APIRouter

from api.api_v1.endpoints import tasks
from api.api_v1.endpoints import ytdlp

v1_router = APIRouter(prefix='/v1')
v1_router.include_router(tasks.router, prefix='/tasks', tags=['tasks'])
v1_router.include_router(ytdlp.router, prefix='/yt-dlp', tags=['yt-dlp'])

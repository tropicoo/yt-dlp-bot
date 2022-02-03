import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.schemas.ytdlp import YTDLPLatestVersion
from yt_shared.db import get_db
from yt_shared.ytdlp.version_checker import VersionChecker

router = APIRouter()


@router.get('/', response_model=YTDLPLatestVersion,
            response_model_by_alias=False)
async def yt_dlp_version(db: AsyncSession = Depends(get_db)):
    version_checker = VersionChecker()
    latest, current = await asyncio.gather(
        version_checker.get_latest_version(),
        version_checker.get_current_version(db))
    return YTDLPLatestVersion(current=current, latest=latest,
                              need_upgrade=latest.version != current.version)

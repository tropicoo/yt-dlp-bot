from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.schemas.ytdlp import YTDLPLatestVersion
from yt_shared.db import get_db
from yt_shared.ytdlp.version_checker import VersionChecker

router = APIRouter()


@router.get('/', response_model=YTDLPLatestVersion, response_model_by_alias=False)
async def yt_dlp_version(db: AsyncSession = Depends(get_db)):
    version_checker = VersionChecker()
    ctx = await version_checker.get_version_context(db)
    return YTDLPLatestVersion(
        current=ctx.current, latest=ctx.latest, need_upgrade=ctx.has_new_version
    )

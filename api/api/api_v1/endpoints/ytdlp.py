from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.schemas.ytdlp import YTDLPLatestVersion
from yt_shared.db.session import get_db
from yt_shared.ytdlp.version_checker import YtdlpVersionChecker

router = APIRouter()


@router.get('/', response_model=YTDLPLatestVersion, response_model_by_alias=False)
async def yt_dlp_version(db: AsyncSession = Depends(get_db)):
    version_checker = YtdlpVersionChecker()
    ctx = await version_checker.get_version_context(db)
    return YTDLPLatestVersion(
        current=ctx.current, latest=ctx.latest, need_upgrade=ctx.has_new_version
    )

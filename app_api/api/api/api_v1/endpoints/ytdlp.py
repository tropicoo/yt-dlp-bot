from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.clients.github import YtdlpGithubClient
from yt_shared.db.session import get_db
from yt_shared.enums import YtdlpReleaseChannelType
from yt_shared.repositories.ytdlp import YtdlpRepository
from yt_shared.ytdlp.version_checker import YtdlpVersionChecker

from api.api.api_v1.schemas.ytdlp import YTDLPLatestVersion

router = APIRouter()


@router.get('/', response_model_by_alias=False)
async def yt_dlp_version(
    release_channel: YtdlpReleaseChannelType, db: AsyncSession = Depends(get_db)
) -> YTDLPLatestVersion:
    ctx = await YtdlpVersionChecker(
        client=YtdlpGithubClient(release_channel), repository=YtdlpRepository(db)
    ).get_version_context()
    return YTDLPLatestVersion(
        current=ctx.current, latest=ctx.latest, need_upgrade=ctx.has_new_version
    )

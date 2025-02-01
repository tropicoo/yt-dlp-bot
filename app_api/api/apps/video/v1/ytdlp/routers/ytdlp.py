from fastapi import APIRouter
from yt_shared.clients.github import YtdlpGithubClient
from yt_shared.enums import YtdlpReleaseChannelType
from yt_shared.repositories.ytdlp import YtdlpRepository
from yt_shared.ytdlp.version_checker import YtdlpVersionChecker

from api.apps.video.v1.ytdlp.schemas.ytdlp import YTDLPLatestVersion
from api.common.dependencies import DBDep

router = APIRouter(prefix='/yt-dlp')


@router.get('/', response_model_by_alias=False)
async def yt_dlp_version(
    release_channel: YtdlpReleaseChannelType, db: DBDep
) -> YTDLPLatestVersion:
    ctx = await YtdlpVersionChecker(
        client=YtdlpGithubClient(release_channel), repository=YtdlpRepository(db)
    ).get_version_context()
    return YTDLPLatestVersion(
        current=ctx.current, latest=ctx.latest, need_upgrade=ctx.has_new_version
    )

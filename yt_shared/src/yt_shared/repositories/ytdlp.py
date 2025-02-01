import logging

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.models import YTDLP


class YtdlpRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._db = db

    async def get_current_version(self) -> YTDLP:
        result = await self._db.execute(select(YTDLP))
        return result.scalar_one()

    async def create_or_update_version(self, current_version: str) -> None:
        row_count: int = await self._db.scalar(
            select(func.count('*')).select_from(YTDLP)
        )
        if row_count > 1:
            raise MultipleResultsFound(
                'Multiple yt-dlp version records found. Expected one.'
            )

        clause = update if row_count else insert
        insert_or_update_stmt = (
            clause(YTDLP)
            .values({'current_version': current_version})
            .execution_options(synchronize_session=False)
        )
        await self._db.execute(insert_or_update_stmt)
        await self._db.commit()

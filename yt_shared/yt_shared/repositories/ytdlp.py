import logging

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.models import YTDLP


class YtdlpRepository:
    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    @staticmethod
    async def get_current_version(db: AsyncSession) -> YTDLP:
        result = await db.execute(select(YTDLP))
        return result.scalar_one()

    @staticmethod
    async def create_or_update_version(current_version: str, db: AsyncSession) -> None:
        row_count: int = await db.scalar(select(func.count('*')).select_from(YTDLP))
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
        await db.execute(insert_or_update_stmt)
        await db.commit()

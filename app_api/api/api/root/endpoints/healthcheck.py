import logging
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from yt_shared.db.session import get_db

from api.api.root.schemas.healthcheck import HealthcheckSchema

healthcheck_router = APIRouter(tags=['Healthcheck'])

logger = logging.getLogger(__name__)


@healthcheck_router.get('/status', description='API Healthcheck')
async def healthcheck(db: AsyncSession = Depends(get_db)) -> HealthcheckSchema:
    try:
        await db.execute(text('SELECT 1'))
    except Exception:
        logger.exception('No database connection')
        raise HTTPException(HTTPStatus.SERVICE_UNAVAILABLE)
    return HealthcheckSchema()

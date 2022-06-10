import logging
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.root.schemas.healthcheck import HealthcheckSchema
from yt_shared.db import get_db

healthcheck_router = APIRouter(tags=['healthcheck'])

logger = logging.getLogger(__name__)


@healthcheck_router.get(
    '/status', response_model=HealthcheckSchema, description='API Healthcheck'
)
async def healthcheck(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute('SELECT 1')
    except Exception:
        logger.exception('No database connection')
        raise HTTPException(HTTPStatus.SERVICE_UNAVAILABLE)
    return HealthcheckSchema()

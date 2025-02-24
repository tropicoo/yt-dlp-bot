import logging
from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from api.apps.healthcheck.schemas.healthcheck import HealthcheckSchema
from api.common.dependencies import DBDep

healthcheck_router = APIRouter(tags=['Healthcheck'])

logger = logging.getLogger(__name__)


@healthcheck_router.get('/status', description='API Healthcheck')
async def healthcheck(db: DBDep) -> HealthcheckSchema:
    try:
        await db.execute(text('SELECT 1'))
    except Exception as err:
        logger.exception('No database connection')
        raise HTTPException(HTTPStatus.SERVICE_UNAVAILABLE) from err
    return HealthcheckSchema()

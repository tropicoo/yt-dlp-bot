import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response

from api.api_v1.schemas.task import (
    CreateTaskIn,
    CreateTaskOut,
    TaskSchema,
    TaskSimpleSchema,
    TasksStatsSchema,
)
from core.dependencies import get_publisher
from core.exceptions import TaskNotFoundHTTPError
from core.services.task import TaskService, TaskServiceError
from yt_shared.constants import TaskStatus
from yt_shared.db import get_db
from yt_shared.rabbit.publisher import Publisher

router = APIRouter()


@router.get('/', response_model=list[TaskSchema | TaskSimpleSchema])
async def get_tasks(
    include_meta: bool = True,
    status: Optional[list[TaskStatus]] = Query(None),
    limit: Optional[int] = Query(100, ge=1),
    offset: Optional[int] = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await TaskService(db).get_all_tasks(
        include_meta=include_meta, status=status, limit=limit, offset=offset
    )


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=CreateTaskOut)
async def create_task(
    task: CreateTaskIn,
    pb: Publisher = Depends(get_publisher),
):
    try:
        return await TaskService.create_task_non_db(task=task, publisher=pb)
    except TaskServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err)
        )


@router.get('/stats', response_model=TasksStatsSchema)
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await TaskService(db).get_stats()


@router.get('/latest', response_model=TaskSchema | TaskSimpleSchema)
async def get_latest_task(
    include_meta: bool = True,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await TaskService(db).get_latest_task(include_meta)
    except NoResultFound:
        raise TaskNotFoundHTTPError


@router.get('/{task_id}', response_model=TaskSchema | TaskSimpleSchema)
async def get_task(
    task_id: uuid.UUID,
    include_meta: bool = True,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await TaskService(db).get_task(task_id, include_meta)
    except NoResultFound:
        raise TaskNotFoundHTTPError


@router.delete(
    '/{task_id}', status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        await TaskService(db).delete_task(task_id)
    except NoResultFound:
        raise TaskNotFoundHTTPError


@router.post('/error', status_code=400)
async def post_and_get_error():
    return {'error_key': 'error data'}

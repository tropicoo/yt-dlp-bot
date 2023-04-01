import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response
from yt_shared.db.session import get_db
from yt_shared.enums import TaskStatus
from yt_shared.rabbit.publisher import RmqPublisher

from api.api.api_v1.schemas.task import (
    CreateTaskIn,
    CreateTaskOut,
    TaskSchema,
    TaskSimpleSchema,
    TasksStatsSchema,
)
from api.core.dependencies import get_rmq_publisher
from api.core.exceptions import TaskNotFoundHTTPError
from api.core.services.task import TaskService, TaskServiceError

router = APIRouter()


@router.get('/')
async def get_tasks(
    include_meta: bool = True,
    status: list[TaskStatus] | None = Query(None),
    limit: int | None = Query(100, ge=1),
    offset: int | None = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[TaskSchema | TaskSimpleSchema]:
    return await TaskService(db).get_all_tasks(
        include_meta=include_meta, status=status, limit=limit, offset=offset
    )


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_task(
    task: CreateTaskIn,
    pb: RmqPublisher = Depends(get_rmq_publisher),
) -> CreateTaskOut:
    try:
        return await TaskService.create_task_non_db(task=task, publisher=pb)
    except TaskServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err)
        )


@router.get('/stats')
async def get_stats(db: AsyncSession = Depends(get_db)) -> TasksStatsSchema:
    return await TaskService(db).get_stats()


@router.get('/latest')
async def get_latest_task(
    include_meta: bool = True,
    db: AsyncSession = Depends(get_db),
) -> TaskSchema | TaskSimpleSchema:
    try:
        return await TaskService(db).get_latest_task(include_meta)
    except NoResultFound:
        raise TaskNotFoundHTTPError


@router.get('/{task_id}')
async def get_task(
    task_id: uuid.UUID,
    include_meta: bool = True,
    db: AsyncSession = Depends(get_db),
) -> TaskSchema | TaskSimpleSchema:
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

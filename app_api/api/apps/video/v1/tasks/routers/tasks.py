import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import NoResultFound
from starlette import status
from starlette.responses import Response
from yt_shared.enums import TaskStatus

from api.apps.video.v1.tasks.schemas.task import (
    CreateTaskIn,
    CreateTaskOut,
    TaskSchema,
    TaskSimpleSchema,
    TasksStatsSchema,
)
from api.apps.video.v1.tasks.services.task import TaskService, TaskServiceError
from api.common.dependencies import DBDep, RMQDep
from api.common.exceptions import TaskNotFoundHTTPError

router = APIRouter(prefix='/tasks')


@router.get('/')
async def get_tasks(
    db: DBDep,
    include_meta: bool = True,
    status: list[TaskStatus] | None = Query(None),  # noqa: B008
    limit: int | None = Query(100, ge=1),
    offset: int | None = Query(0, ge=0),
) -> list[TaskSchema | TaskSimpleSchema]:
    return await TaskService(db).get_all_tasks(
        include_meta=include_meta, status=status, limit=limit, offset=offset
    )


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_task(task: CreateTaskIn, pb: RMQDep) -> CreateTaskOut:
    try:
        return await TaskService.create_task_non_db(task=task, publisher=pb)
    except TaskServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err)
        ) from None


@router.get('/stats')
async def get_stats(db: DBDep) -> TasksStatsSchema:
    return await TaskService(db).get_stats()


@router.get('/latest')
async def get_latest_task(
    db: DBDep,
    include_meta: bool = True,
) -> TaskSchema | TaskSimpleSchema:
    try:
        return await TaskService(db).get_latest_task(include_meta=include_meta)
    except NoResultFound:
        raise TaskNotFoundHTTPError from None


@router.get('/{task_id}')
async def get_task(
    db: DBDep, task_id: uuid.UUID, include_meta: bool = True
) -> TaskSchema | TaskSimpleSchema:
    try:
        return await TaskService(db).get_task(id_=task_id, include_meta=include_meta)
    except NoResultFound:
        raise TaskNotFoundHTTPError from None


@router.delete(
    '/{task_id}', status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_task(task_id: uuid.UUID, db: DBDep) -> None:
    try:
        await TaskService(db).delete_task(id_=task_id)
    except NoResultFound:
        raise TaskNotFoundHTTPError from None

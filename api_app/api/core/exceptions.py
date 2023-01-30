from fastapi import HTTPException
from starlette import status


class TaskNotFoundHTTPError(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')


class TaskServiceError(Exception):
    pass

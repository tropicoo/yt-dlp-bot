import uvicorn

from api.core.app import app  # noqa: F401
from api.core.config import settings

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
    )

import uvicorn

from api.core.app import app  # noqa: F401

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)

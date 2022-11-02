import uvicorn
from core.app import app  # noqa

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True, workers=2)

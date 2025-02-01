from pydantic import PositiveInt
from yt_shared.config import CommonSettings


class ApiSettings(CommonSettings):
    API_HOST: str
    API_PORT: PositiveInt
    API_WORKERS: PositiveInt


settings = ApiSettings()

from yt_shared.config import Settings


class ApiSettings(Settings):
    API_HOST: str
    API_PORT: int
    API_WORKERS: int


settings = ApiSettings()

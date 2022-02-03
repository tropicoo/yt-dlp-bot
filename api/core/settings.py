from pydantic import BaseSettings


class Settings(BaseSettings):
    title: str = 'test app title or what'


settings = Settings()

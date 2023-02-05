import logging
from typing import KeysView

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    APPLICATION_NAME: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_TEST_DB: str = 'yt_test'

    @property
    def SQLALCHEMY_DATABASE_URI_ASYNC(self) -> str:
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

    SQLALCHEMY_ECHO: bool
    SQLALCHEMY_EXPIRE_ON_COMMIT: bool

    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int

    @property
    def RABBITMQ_URI(self) -> str:
        return f'amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/'

    CONSUMER_NUMBER_OF_RETRY: int = 2
    RESEND_DELAY_MS: int = 60000

    LOG_LEVEL: str
    REDIS_HOST: str

    @property
    def REDIS_URL(self) -> str:
        return f'redis://{self.REDIS_HOST}'

    TMP_DOWNLOAD_ROOT_PATH: str
    TMP_DOWNLOAD_DIR: str
    TMP_DOWNLOADED_DIR: str

    @classmethod
    @validator('LOG_LEVEL')
    def validate_log_level_value(cls, value: str) -> str:
        valid_values: KeysView[str] = logging._nameToLevel.keys()  # noqa
        if value not in valid_values:
            raise ValueError(f'"LOG_LEVEL" must be one of {valid_values}')
        return value


settings = Settings()

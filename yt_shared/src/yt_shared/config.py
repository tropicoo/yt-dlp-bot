import logging

from pydantic import (
    ConfigDict,
    DirectoryPath,
    NewPath,
    PositiveInt,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings


class CommonSettings(BaseSettings):
    model_config = ConfigDict(
        extra='forbid', validate_default=True, validate_assignment=True
    )

    APPLICATION_NAME: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: PositiveInt
    POSTGRES_DB: str
    POSTGRES_TEST_DB: str = 'yt_test'

    @property
    def SQLALCHEMY_DATABASE_URI_ASYNC(self) -> str:  # noqa: N802
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

    SQLALCHEMY_ECHO: bool
    SQLALCHEMY_EXPIRE_ON_COMMIT: bool

    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: PositiveInt

    @property
    def RABBITMQ_URI(self) -> str:  # noqa: N802
        return f'amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/'

    CONSUMER_NUMBER_OF_RETRY: PositiveInt = 2
    RESEND_DELAY_MS: PositiveInt = 60000

    LOG_LEVEL: str
    REDIS_HOST: str

    @property
    def REDIS_URL(self) -> str:  # noqa: N802
        return f'redis://{self.REDIS_HOST}'

    TMP_DOWNLOAD_ROOT_PATH: DirectoryPath | NewPath
    TMP_DOWNLOAD_DIR: DirectoryPath | NewPath
    TMP_DOWNLOADED_DIR: DirectoryPath | NewPath

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level_value(cls, value: str, info: ValidationInfo) -> str:
        valid_values = logging.getLevelNamesMapping().keys()
        if value not in valid_values:
            raise ValueError(f'"{info.field_name}" must be one of {valid_values}')
        return value


settings = CommonSettings()

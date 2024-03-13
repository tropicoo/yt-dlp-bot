"""Config module."""

import logging
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError
from yt_shared.config import Settings

from bot.core.exceptions import ConfigError
from bot.core.schema import ConfigSchema


class ConfigLoader:
    _CONF_FILENAME = 'config.yml'

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)

    def load_config(self) -> ConfigSchema:
        data, errors = self._load_config()
        if errors:
            self._process_errors_and_exit(errors)
        return data

    def _load_config(self) -> tuple[ConfigSchema | None, ValidationError | None]:
        """Loads bot configuration from config file."""
        dir_path = Path(__file__).parent.parent.parent.parent
        conf_file_path = dir_path / self._CONF_FILENAME
        self._check_path_existence(conf_file_path)

        with open(conf_file_path, 'r') as fd_in:
            try:
                return ConfigSchema(**yaml.safe_load(fd_in)), None
            except ValidationError as err:
                return None, err

    def _check_path_existence(self, conf_file_path: Path) -> None:
        if not conf_file_path.is_file():
            err_msg = f'Cannot find {conf_file_path} configuration file'
            self._log.error(err_msg)
            raise ConfigError(err_msg)

    def _process_errors_and_exit(self, errors: ValidationError) -> None:
        sep_begin = '-' * 20
        sep_end = '-' * 18
        self._log.error(
            '%s Errors in %s %s\n%s', sep_begin, self._CONF_FILENAME, sep_begin, errors
        )
        sys.exit(f'{sep_end} Fix config and try again {sep_end}')


config_loader = ConfigLoader()

_CONF_MAIN = config_loader.load_config()


def get_main_config() -> ConfigSchema:
    return _CONF_MAIN


class BotSettings(Settings):
    TG_MAX_MSG_SIZE: int
    TG_MAX_CAPTION_SIZE: int


settings = BotSettings()

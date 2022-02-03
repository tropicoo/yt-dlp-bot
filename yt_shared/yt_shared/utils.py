from typing import Any, Union


class Singleton(type):
    """Singleton class."""

    _instances = {}

    def __call__(cls, *args, **kwargs) -> Any:
        """Check whether instance already exists.

        Return existing or create new instance and save to dict."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def get_env_bool(string: Union[str, bool]) -> bool:
    if isinstance(string, str):
        return string.lower() in ('true',)
    return string

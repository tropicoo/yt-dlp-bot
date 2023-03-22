import logging

from bot.core.config import settings


def setup_logging(suppress_asyncio: bool = True, suppress_urllib3: bool = True) -> None:
    log_format = '%(asctime)s - [%(levelname)s] - [%(name)s:%(lineno)s] - %(message)s'
    logging.basicConfig(
        format=log_format, level=logging.getLevelName(settings.LOG_LEVEL)
    )
    if suppress_asyncio:
        logging.getLogger('asyncio').setLevel(logging.WARNING)

    if suppress_urllib3:
        logging.getLogger('urllib3').setLevel(logging.WARNING)

    logging.getLogger('pyrogram').setLevel(logging.WARNING)
    try:
        logging.getLogger('sqlalchemy.engine.Engine').handlers.pop()
    except IndexError:
        pass

import logging


def setup_logging():
    log_format = '%(asctime)s - [%(levelname)s] - [%(name)s:%(lineno)s] - %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)

    log = logging.getLogger('sqlalchemy.engine.Engine')
    log.handlers.pop()

import logging
import sys
from backend.core.config import settings

# Custom formatter for consistent logs
class LogFormatter(logging.Formatter):
    def format(self, record):
        log_format = (
            f"[{record.levelname}] "
            f"{record.asctime} | "
            f"{record.name:<25} | "
            f"{record.message}"
        )
        return log_format


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger with console handler.
    All logs use the same consistent structure across the app.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.setLevel(settings.LOG_LEVEL.upper())
        logger.propagate = False

    return logger

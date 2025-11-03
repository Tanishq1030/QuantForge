# backend/core/logging.py
"""
Structured logging via loguru.
Provides a single `logger` object for consistent logging across the app.
"""

from loguru import logger as _logger
import sys
from .config import settings

# Remove default handlers and configure desired format/level
_logger.remove()

# Add a console sink with a simple structured format
_logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>"
)

# For production, you may add file sinks or aggregation (ELK / Fluentd / Cloud logging)
logger = _logger

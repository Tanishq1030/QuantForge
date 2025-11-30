# backend/engine/feeds/__init__.py
"""
Data feed connectors for QuantForge AI Engine.

Supports multiple data sources:
- RSS (financial news)
- Binance (cryptocurrency market data)
- Future: Twitter, Reddit, Discord, etc.
"""

from .base import BaseFeedConnector
from .rss_connector import RSSFeedConnector
from .binance_connector import BinanceConnector

__all__ = [
    "BaseFeedConnector",
    "RSSFeedConnector",
    "BinanceConnector",
]

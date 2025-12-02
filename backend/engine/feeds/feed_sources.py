# backend/engine/feeds/feed_sources.py
"""
Curated list of financial news RSS feeds.

Organized by category for easy management.
"""

from typing import Dict, List


class FinancialFeedSources:
    """Collection of reliable financial news RSS feeds."""
    
    # Business & Market News
    BUSINESS_NEWS = [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.reuters.com/reuters/marketsNews",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # Top News
        "https://www.cnbc.com/id/10000664/device/rss/rss.html",  # US Markets
        "https://www.cnbc.com/id/10001147/device/rss/rss.html",  # Tech
    ]
    
    # Technology
    TECHNOLOGY = [
        "https://feeds.reuters.com/reuters/technologyNews",
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
    ]
    
    # Cryptocurrency
    CRYPTO = [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed",
    ]
    
    # Stock Analysis & Investing
    INVESTING = [
        "https://seekingalpha.com/feed.xml",
        "https://www.fool.com/feeds/index.aspx",  # Motley Fool
    ]
    
    # All feeds combined
    ALL_FEEDS = BUSINESS_NEWS + TECHNOLOGY + CRYPTO + INVESTING
    
    @classmethod
    def get_by_category(cls, category: str) -> List[str]:
        """
        Get feeds by category.
        
        Args:
            category: One of 'business', 'technology', 'crypto', 'investing', 'all'
        
        Returns:
            List of RSS feed URLs
        """
        category_map = {
            "business": cls.BUSINESS_NEWS,
            "technology": cls.TECHNOLOGY,
            "crypto": cls.CRYPTO,
            "investing": cls.INVESTING,
            "all": cls.ALL_FEEDS,
        }
        
        return category_map.get(category.lower(), [])
    
    @classmethod
    def get_recommended(cls, count: int = 5) -> List[str]:
        """Get top recommended feeds."""
        return [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://feeds.reuters.com/reuters/technologyNews",
            "https://techcrunch.com/feed/",
        ][:count]

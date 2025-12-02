# backend/engine/feeds/rss_connector.py
"""
RSS Feed Connector for financial news ingestion.

Supports parsing multiple RSS/Atom feeds from financial news sources.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import feedparser
from bs4 import BeautifulSoup
import httpx

from .base import BaseFeedConnector
from backend.core.logging import get_logger

logger = get_logger(__name__)


class RSSFeedConnector(BaseFeedConnector):
    """
    RSS/Atom feed connector for financial news.
    
    Supports:
    - Multiple RSS feed URLs
    - HTML content extraction
    - Date parsing
    - Error handling with retries
    """
    
    def __init__(self, source_name: str = "RSS"):
        super().__init__(source_name)
        self.timeout = 30
        self.max_retries = 3
    
    async def fetch(
        self, 
        feed_urls: List[str],
        max_articles: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from RSS feeds.
        
        Args:
            feed_urls: List of RSS feed URLs
            max_articles: Maximum articles to fetch (None = all)
            
        Returns:
            List of normalized documents
        """
        all_documents = []
        
        for url in feed_urls:
            try:
                logger.info(f"Fetching RSS feed: {url}")
                documents = await self._fetch_single_feed(url)
                all_documents.extend(documents)
                
                if max_articles and len(all_documents) >= max_articles:
                    all_documents = all_documents[:max_articles]
                    break
                    
            except Exception as e:
                logger.error(f"Failed to fetch RSS feed {url}: {e}")
                continue
        
        logger.info(f"Fetched {len(all_documents)} articles from {len(feed_urls)} feeds")
        return all_documents
    
    async def _fetch_single_feed(self, url: str) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed with proper User-Agent."""
        
        # Fetch with proper User-Agent (many feeds block default UA)
        try:
            headers = {"User-Agent": "QuantForge/1.0 (+https://quantforge.ai)"}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                feed_content = response.text
        except Exception as e:
            logger.error(f"HTTP fetch failed for {url}: {e}")
            raise
        
        # Parse feed content
        def _parse():
            return feedparser.parse(feed_content)
        
        feed = await asyncio.to_thread(_parse)
        
        if feed.get("bozo"):  # Parse error
            logger.warning(f"RSS parse error for {url}: {feed.get('bozo_exception')}")
        
        if not feed.entries:
            logger.warning(f"No entries found in feed: {url}")
            return []
        
        logger.info(f"Found {len(feed.entries)} entries in feed: {url}")
        
        documents = []
        for entry in feed.entries:
            try:
                doc = self._parse_entry(entry, url)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Failed to parse entry: {e}")
                continue
        
        return documents
    
    def _parse_entry(self, entry: Any, feed_url: str) -> Dict[str, Any]:
        """Parse a single RSS entry."""
        # Extract content
        content = ""
        if hasattr(entry, "content"):
            content = entry.content[0].value
        elif hasattr(entry, "summary"):
            content = entry.summary
        elif hasattr(entry, "description"):
            content = entry.description
        
        # Clean HTML
        content = self._clean_html(content)
        
        # Extract title
        title = entry.get("title", "")
        
        # Extract URL
        url = entry.get("link", feed_url)
        
        # Parse timestamp
        timestamp = self._parse_timestamp(entry)
        
        # Build metadata
        metadata = {
            "feed_url": feed_url,
            "author": entry.get("author", ""),
            "tags": [tag.get("term", "") for tag in entry.get("tags", [])],
        }
        
        return self.normalize_document(
            content=content,
            title=title,
            url=url,
            timestamp=timestamp,
            **metadata
        )
    
    def _clean_html(self, html_content: str) -> str:
        """Remove HTML tags and extract clean text."""
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        return text
    
    def _parse_timestamp(self, entry: Any) -> datetime:
        """Parse entry timestamp from various RSS date fields."""
        # Try different date fields
        for field in ["published_parsed", "updated_parsed", "created_parsed"]:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        return datetime(*time_struct[:6])
                    except:
                        pass
        
        # Fallback to current time
        return datetime.utcnow()
    
    async def validate_connection(self) -> bool:
        """Test RSS feed connectivity."""
        test_url = "https://feeds.reuters.com/reuters/businessNews"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(test_url)
                return response.status_code == 200
        except:
            return False

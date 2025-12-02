# tests/unit/test_rss_connector.py
"""
Unit tests for RSSFeedConnector.

Tests:
- RSS feed parsing
- HTML content extraction
- Date parsing
- Error handling
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from backend.engine.feeds.rss_connector import RSSFeedConnector


class TestRSSFeedConnector:
    """Test suite for RSSFeedConnector"""
    
    @pytest.fixture
    def connector(self):
        """Create RSSFeedConnector instance for tests"""
        return RSSFeedConnector()
    
    # === Initialization Tests ===
    
    def test_init_default_source(self):
        """Test default source name"""
        connector = RSSFeedConnector()
        assert connector.source_name == "RSS"
    
    def test_init_custom_source(self):
        """Test custom source name"""
        connector = RSSFeedConnector(source_name="CustomRSS")
        assert connector.source_name == "CustomRSS"
    
    # === HTML Cleaning Tests ===
    
    def test_clean_html_simple(self, connector):
        """Test basic HTML tag removal"""
        html = "<p>This is <strong>bold</strong> text</p>"
        cleaned = connector._clean_html(html)
        assert cleaned == "This is bold text"
        assert "<" not in cleaned
        assert ">" not in cleaned
    
    def test_clean_html_complex(self, connector):
        """Test complex HTML with multiple tags"""
        html = """
        <div>
            <h1>Title</h1>
            <p>Paragraph with <a href="link">link</a></p>
            <ul><li>Item 1</li><li>Item 2</li></ul>
        </div>
        """
        cleaned = connector._clean_html(html)
        assert "Title" in cleaned
        assert "Paragraph" in cleaned
        assert "link" in cleaned
        assert "<div>" not in cleaned
    
    def test_clean_html_empty(self, connector):
        """Test empty HTML handling"""
        cleaned = connector._clean_html("")
        assert cleaned == ""
    
    def test_clean_html_none(self, connector):
        """Test None HTML handling"""
        cleaned = connector._clean_html(None)
        assert cleaned == ""
    
    def test_clean_html_whitespace_normalization(self, connector):
        """Test whitespace normalization"""
        html = "<p>Text   with    extra     spaces</p>"
        cleaned = connector._clean_html(html)
        assert "   " not in cleaned
        assert cleaned == "Text with extra spaces"
    
    # === Date Parsing Tests ===
    
    def test_parse_timestamp_published(self, connector):
        """Test parsing published_parsed field"""
        entry = Mock()
        entry.published_parsed = (2024, 11, 30, 12, 30, 0, 4, 335, 0)
        
        timestamp = connector._parse_timestamp(entry)
        assert isinstance(timestamp, datetime)
        assert timestamp.year == 2024
        assert timestamp.month == 11
        assert timestamp.day == 30
    
    def test_parse_timestamp_updated(self, connector):
        """Test parsing updated_parsed field"""
        entry = Mock()
        delattr(entry, 'published_parsed')  # Remove published
        entry.updated_parsed = (2024, 11, 30, 14, 0, 0, 4, 335, 0)
        
        timestamp = connector._parse_timestamp(entry)
        assert timestamp.year == 2024
    
    def test_parse_timestamp_fallback(self, connector):
        """Test fallback to current time"""
        entry = Mock()
        # Remove all date fields
        for attr in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if hasattr(entry, attr):
                delattr(entry, attr)
        
        timestamp = connector._parse_timestamp(entry)
        assert isinstance(timestamp, datetime)
        # Should be recent (within last minute)
        time_diff = (datetime.utcnow() - timestamp).total_seconds()
        assert time_diff < 60
    
    # === Entry Parsing Tests ===
    
    def test_parse_entry_full(self, connector):
        """Test parsing entry with all fields"""
        entry = Mock()
        entry.content = [Mock(value="<p>Full article content</p>")]
        entry.title = "Test Article"
        entry.link = "https://example.com/article"
        entry.author = "John Doe"
        entry.tags = [{"term": "tech"}, {"term": "finance"}]
        entry.published_parsed = (2024, 11, 30, 12, 0, 0, 4, 335, 0)
        
        doc = connector._parse_entry(entry, "https://example.com/feed")
        
        assert doc["content"] == "Full article content"
        assert doc["title"] == "Test Article"
        assert doc["url"] == "https://example.com/article"
        assert doc["metadata"]["author"] == "John Doe"
        assert "tech" in doc["metadata"]["tags"]
        assert "finance" in doc["metadata"]["tags"]
    
    def test_parse_entry_summary_fallback(self, connector):
        """Test fallback to summary when content not available"""
        entry = Mock()
        # Remove content attribute
        if hasattr(entry, 'content'):
            delattr(entry, 'content')
        entry.summary = "Summary text"
        entry.title = "Test"
        entry.link = "https://example.com"
        entry.author = ""
        entry.tags = []
        entry.published_parsed = (2024, 11, 30, 12, 0, 0, 4, 335, 0)
        
        doc = connector._parse_entry(entry, "https://feed.com")
        assert doc["content"] == "Summary text"
    
    # === Mock Feed Tests ===
    
    @pytest.mark.asyncio
    async def test_fetch_empty_urls(self, connector):
        """Test fetch with empty URL list"""
        documents = await connector.fetch(feed_urls=[])
        assert documents == []
    
    @pytest.mark.asyncio
    async def test_fetch_max_articles_limit(self, connector):
        """Test max_articles limit"""
        # Mock feedparser to return multiple entries
        mock_feed = Mock()
        mock_feed.entries = [Mock() for _ in range(20)]
        mock_feed.bozo = False
        
        with patch('feedparser.parse', return_value=mock_feed):
            with patch.object(connector, '_parse_entry', return_value={"test": "doc"}):
                documents = await connector.fetch(
                    feed_urls=["https://example.com/feed"],
                    max_articles=5
                )
                
                # Should only return 5 articles
                assert len(documents) <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# tests/unit/test_text_preprocessor.py
"""
Unit tests for TextPreprocessor.

Tests:
- Ticker extraction from various text formats
- Company name to ticker mapping
- Category classification
- Text cleaning
- Deduplication
"""

import pytest
from backend.engine.parsers.text_preprocessor import TextPreprocessor


class TestTextPreprocessor:
    """Test suite for TextPreprocessor"""
    
    @pytest.fixture
    def preprocessor(self):
        """Create TextPreprocessor instance for tests"""
        return TextPreprocessor()
    
    # === Ticker Extraction Tests ===
    
    def test_extract_ticker_explicit(self, preprocessor):
        """Test extraction of explicit ticker symbols"""
        text = "Apple Inc. (AAPL) reported strong earnings"
        tickers = preprocessor.extract_tickers(text)
        assert "AAPL" in tickers
    
    def test_extract_ticker_twitter_style(self, preprocessor):
        """Test extraction of Twitter-style $TICKER"""
        text = "Bullish on $TSLA and $NVDA today"
        tickers = preprocessor.extract_tickers(text)
        assert "TSLA" in tickers
        assert "NVDA" in tickers
    
    def test_extract_crypto_pairs(self, preprocessor):
        """Test extraction of crypto trading pairs"""
        text = "BTC-USD and ETH-USD hit new highs"
        tickers = preprocessor.extract_tickers(text)
        assert "BTC-USD" in tickers
        assert "ETH-USD" in tickers
    
    def test_company_name_mapping(self, preprocessor):
        """Test company name to ticker mapping"""
        text = "Tesla announced new Cybertruck pricing"
        tickers = preprocessor.extract_tickers(text)
        assert "TSLA" in tickers
    
    def test_case_insensitive_mapping(self, preprocessor):
        """Test case-insensitive company matching"""
        text = "Microsoft, MICROSOFT, and microsoft all mentioned"
        tickers = preprocessor.extract_tickers(text)
        assert "MSFT" in tickers
    
    def test_multiple_tickers(self, preprocessor):
        """Test extraction of multiple tickers from one text"""
        text = "Apple (AAPL), Microsoft (MSFT), and Google (GOOGL) lead tech sector"
        tickers = preprocessor.extract_tickers(text)
        assert len(tickers) >= 3
        assert all(ticker in tickers for ticker in ["AAPL", "MSFT", "GOOGL"])
    
    def test_filter_common_words(self, preprocessor):
        """Test filtering of common words that look like tickers"""
        text = "The company has NOT announced AND will FOR the"
        tickers = preprocessor.extract_tickers(text)
        # Should not extract THE, AND, NOT, FOR, etc.
        assert "THE" not in tickers
        assert "AND" not in tickers
        assert "NOT" not in tickers
    
    # === Category Classification Tests ===
    
    def test_classify_earnings(self, preprocessor):
        """Test classification of earnings-related content"""
        text = "Company reports Q3 earnings beat expectations with revenue growth"
        category = preprocessor.classify_category(text)
        assert category == "earnings"
    
    def test_classify_crypto(self, preprocessor):
        """Test classification of crypto content"""
        text = "Bitcoin surges as Ethereum blockchain sees record volume"
        category = preprocessor.classify_category(text)
        assert category == "crypto"
    
    def test_classify_regulation(self, preprocessor):
        """Test classification of regulation content"""
        text = "SEC announces new compliance rules for digital assets"
        category = preprocessor.classify_category(text)
        assert category == "regulation"
    
    def test_classify_merger(self, preprocessor):
        """Test classification of M&A content"""
        text = "Microsoft announces acquisition of gaming company in $69B deal"
        category = preprocessor.classify_category(text)
        assert category == "merger"
    
    def test_classify_general_fallback(self, preprocessor):
        """Test fallback to 'general' for uncategorized content"""
        text = "Some random news with no specific keywords"
        category = preprocessor.classify_category(text)
        assert category == "general"
    
    # === Text Cleaning Tests ===
    
    def test_clean_extra_whitespace(self, preprocessor):
        """Test removal of extra whitespace"""
        text = "Too    many     spaces"
        cleaned = preprocessor.clean_text(text)
        assert "  " not in cleaned
        assert cleaned == "Too many spaces"
    
    def test_clean_special_characters(self, preprocessor):
        """Test removal of special characters"""
        text = "Text with <html> tags & weird™ symbols©"
        cleaned = preprocessor.clean_text(text)
        # Should keep alphanumeric, spaces, basic punctuation
        assert "<" not in cleaned
        assert ">" not in cleaned
        assert "™" not in cleaned
    
    # === Content Hash Tests ===
    
    def test_generate_hash_consistency(self, preprocessor):
        """Test that same content generates same hash"""
        content = "This is test content"
        hash1 = preprocessor.generate_hash(content)
        hash2 = preprocessor.generate_hash(content)
        assert hash1 == hash2
    
    def test_generate_hash_uniqueness(self, preprocessor):
        """Test that different content generates different hashes"""
        hash1 = preprocessor.generate_hash("Content A")
        hash2 = preprocessor.generate_hash("Content B")
        assert hash1 != hash2
    
    def test_is_duplicate(self, preprocessor):
        """Test duplicate detection"""
        seen_hashes = {preprocessor.generate_hash("duplicate content")}
        
        # Same content should be detected as duplicate
        is_dup = preprocessor.is_duplicate(
            preprocessor.generate_hash("duplicate content"),
            seen_hashes
        )
        assert is_dup is True
        
        # Different content should not be duplicate
        is_dup = preprocessor.is_duplicate(
            preprocessor.generate_hash("unique content"),
            seen_hashes
        )
        assert is_dup is False
    
    # === Full Process Test ===
    
    def test_process_full_document(self, preprocessor):
        """Test full document processing pipeline"""
        document = {
            "content": "Apple Inc. (AAPL) reports record Q4 earnings    with revenue growth",
            "title": "Apple Earnings Beat",
            "source": "Reuters",
            "url": "https://example.com/article",
            "metadata": {}
        }
        
        processed = preprocessor.process(document)
        
        # Check ticker extraction
        assert processed["ticker"] == "AAPL" or "AAPL" in processed["metadata"]["tickers"]
        
        # Check category
        assert processed["category"] == "earnings"
        
        # Check content cleaning
        assert "   " not in processed["content"]  # Extra spaces removed
        
        # Check hash generation
        assert "content_hash" in processed["metadata"]
        assert len(processed["metadata"]["content_hash"]) == 32  # MD5 hash length


# === Parametrized Tests ===

@pytest.mark.parametrize("text,expected_ticker", [
    ("Tesla stock soars", "TSLA"),
    ("Microsoft earnings strong", "MSFT"),
    ("Amazon acquires company", "AMZN"),
    ("Google parent company", "GOOGL"),
    ("Meta announces layoffs", "META"),
    ("Bitcoin rallies", "BTC-USD"),
    ("Ethereum upgrade", "ETH-USD"),
])
def test_various_company_mentions(text, expected_ticker):
    """Test ticker extraction from various company mentions"""
    preprocessor = TextPreprocessor()
    tickers = preprocessor.extract_tickers(text)
    assert expected_ticker in tickers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

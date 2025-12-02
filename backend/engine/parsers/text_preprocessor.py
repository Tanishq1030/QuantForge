# backend/engine/parsers/text_preprocessor.py
"""
Text preprocessing and feature extraction for financial documents.

Extracts:
- Stock tickers (AAPL, TSLA, BTC-USD, etc.)
- Company names
- Categories (earnings, market_news, crypto, etc.)
- Sentiment (placeholder for Phase 2)
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from backend.core.logging import get_logger

logger = get_logger(__name__)


class TextPreprocessor:
    """
    Preprocessor for financial text documents.
    
    Features:
    - Ticker extraction (stock symbols)
    - Text normalization
    - Deduplication
    - Category classification
    """
    
    # Common stock ticker patterns
    TICKER_PATTERNS = [
        r'\b([A-Z]{1,5})\b',  # Standard tickers (AAPL, TSLA, MSFT)
        r'\$([A-Z]{1,5})\b',  # Twitter-style ($AAPL)
        r'\b([A-Z]+)-USD\b',  # Crypto pairs (BTC-USD, ETH-USD)
    ]
    
    # Known company to ticker mappings (expanded for better accuracy)
    COMPANY_TICKER_MAP = {
        # Tech Giants
        "apple": "AAPL",
        "microsoft": "MSFT",
        "amazon": "AMZN",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "meta": "META",
        "facebook": "META",
        "netflix": "NFLX",
        "nvidia": "NVDA",
        "amd": "AMD",
        "intel": "INTC",
        "qualcomm": "QCOM",
        
        # Electric Vehicles & Auto
        "tesla": "TSLA",
        "ford": "F",
        "general motors": "GM",
        "gm": "GM",
        "rivian": "RIVN",
        "lucid": "LCID",
        
        # Finance
        "jpmorgan": "JPM",
        "jp morgan": "JPM",
        "bank of america": "BAC",
        "wells fargo": "WFC",
        "goldman sachs": "GS",
        "morgan stanley": "MS",
        "visa": "V",
        "mastercard": "MA",
        "paypal": "PYPL",
        
        # Consumer
        "walmart": "WMT",
        "target": "TGT",
        "costco": "COST",
        "nike": "NKE",
        "starbucks": "SBUX",
        "mcdonald's": "MCD",
        "mcdonalds": "MCD",
        "coca-cola": "KO",
        "pepsi": "PEP",
        "pepsico": "PEP",
        
        # Healthcare & Pharma
        "pfizer": "PFE",
        "moderna": "MRNA",
        "johnson & johnson": "JNJ",
        "johnson and johnson": "JNJ",
        "abbvie": "ABBV",
        "merck": "MRK",
        
        # Crypto (as USD pairs)
        "bitcoin": "BTC-USD",
        "btc": "BTC-USD",
        "ethereum": "ETH-USD",
        "eth": "ETH-USD",
        "binance coin": "BNB-USD",
        "bnb": "BNB-USD",
        "cardano": "ADA-USD",
        "ada": "ADA-USD",
        "solana": "SOL-USD",
        "sol": "SOL-USD",
        "ripple": "XRP-USD",
        "xrp": "XRP-USD",
        "dogecoin": "DOGE-USD",
        "doge": "DOGE-USD",
        "polygon": "MATIC-USD",
        "matic": "MATIC-USD",
    }
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        "earnings": ["earnings", "revenue", "profit", "q1", "q2", "q3", "q4", "quarterly"],
        "market_news": ["market", "stock", "trading", "investors", "wall street"],
        "crypto": ["bitcoin", "ethereum", "crypto", "blockchain", "defi"],
        "regulation": ["sec", "regulation", "compliance", "lawsuit", "fine"],
        "merger": ["merger", "acquisition", "deal", "buyout", "takeover"],
    }
    
    def __init__(self):
        # Compile regex patterns
        self.ticker_regex = [re.compile(pattern) for pattern in self.TICKER_PATTERNS]
        logger.info("TextPreprocessor initialized")
    
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document and extract features.
        
        Args:
            document: Raw document dict
            
        Returns:
            Enhanced document with extracted features
        """
        content = document.get("content", "")
        title = document.get("title", "")
        
        # Extract tickers
        tickers = self.extract_tickers(content + " " + title)
        
        # Classify category
        category = self.classify_category(content + " " + title)
        
        # Generate content hash for dedup
        content_hash = self.generate_hash(content)
        
        # Clean text
        cleaned_content = self.clean_text(content)
        
        # Update document
        document["content"] = cleaned_content
        document["ticker"] = tickers[0] if tickers else None
        document["category"] = category
        document["metadata"] = document.get("metadata", {})
        document["metadata"]["tickers"] = tickers
        document["metadata"]["content_hash"] = content_hash
        
        return document
    
    def extract_tickers(self, text: str) -> List[str]:
        """
        Extract stock tickers from text.
        
        Returns:
            List of unique ticker symbols
        """
        tickers: Set[str] = set()
        text_lower = text.lower()
        
        # Check company name mappings
        for company, ticker in self.COMPANY_TICKER_MAP.items():
            if company in text_lower:
                tickers.add(ticker)
        
        # Extract using regex
        for regex in self.ticker_regex:
            matches = regex.findall(text)
            tickers.update(matches)
        
        # Filter invalid tickers
        valid_tickers = self._filter_tickers(list(tickers))
        
        logger.debug(f"Extracted tickers: {valid_tickers}")
        return valid_tickers
    
    def _filter_tickers(self, tickers: List[str]) -> List[str]:
        """
        Filter out invalid/common words that look like tickers.
        """
        # Common words to exclude
        BLACKLIST = {"THE", "AND", "FOR", "ARE", "WITH", "HAS", "WAS", "ITS", "NOT", "BUT", "FROM"}
        
        filtered = []
        for ticker in tickers:
            ticker = ticker.upper().strip()
            
            # Skip if in blacklist
            if ticker in BLACKLIST:
                continue
            
            # Skip if too long
            if len(ticker) > 5:
                continue
            
            # Skip if too short
            if len(ticker) < 1:
                continue
            
            filtered.append(ticker)
        
        return filtered
    
    def classify_category(self, text: str) -> Optional[str]:
        """
        Classify document category based on keywords.
        """
        text_lower = text.lower()
        
        # Count keyword matches per category
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[category] = score
        
        # Return category with highest score
        if scores:
            return max(scores, key=scores.get)
        
        return "general"
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        """
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove special characters (keep alphanumeric, spaces, basic punctuation)
        text = re.sub(r'[^\w\s.,!?$%-]', '', text)
        
        return text.strip()
    
    def generate_hash(self, content: str) -> str:
        """
        Generate content hash for deduplication.
        """
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_duplicate(self, content_hash: str, seen_hashes: Set[str]) -> bool:
        """
        Check if content is duplicate.
        """
        return content_hash in seen_hashes

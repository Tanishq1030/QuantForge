# backend/routes/analysis.py
"""
Analysis & Correlation API endpoints.

Combines:
- News/documents from vector store
- Market price data from TimescaleDB
- Ticker resolution
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.engine.memory.vector_store import QuantForgeVectorStore
from backend.engine.memory.timeseries_store import get_timeseries_store
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/analysis", tags=["Analysis & Correlation"])

# Singleton instances
vector_store = QuantForgeVectorStore()
timeseries = get_timeseries_store()


# === Pydantic Schemas ===

class ContextRequest(BaseModel):
    """Request for contextual analysis"""
    ticker: str = Field(..., description="Stock/crypto ticker symbol (e.g., AAPL, BTCUSDT)")
    date: Optional[datetime] = Field(None, description="Analysis date (default: today)")
    days_before: int = Field(default=7, description="Days of context before date", ge=1, le=90)
    days_after: int = Field(default=0, description="Days of context after date", ge=0, le=30)
    news_limit: int = Field(default=10, description="Max news articles to return", ge=1, le=50)


class NewsArticle(BaseModel):
    """News article with metadata"""
    title: str
    content: str
    source: str
    url: str
    timestamp: datetime
    ticker: Optional[str]
    category: Optional[str]
    confidence: float


class PriceData(BaseModel):
    """Price data summary"""
    symbol: str
    period_start: datetime
    period_end: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    price_change: float
    price_change_percent: float


class ContextResponse(BaseModel):
    """Contextual analysis response"""
    ticker: str
    analysis_date: datetime
    news: List[NewsArticle]
    news_count: int
    price_data: Optional[PriceData]
    has_price_data: bool
    insights: Dict[str, Any]


# === API Endpoints ===

@router.post("/context", response_model=ContextResponse)
async def get_ticker_context(request: ContextRequest):
    """
    Get comprehensive context for a ticker on a specific date.
    
    Combines:
    - Relevant news articles (vector search)
    - Price movement (TimescaleDB)
    - Basic insights
    
    Example:
        ```json
        {
            "ticker": "AAPL",
            "date": "2024-11-29",
            "days_before": 7,
            "news_limit": 10
        }
        ```
    
    Returns news articles mentioning the ticker and price data for the time period.
    """
    try:
        # Default to today if no date provided
        analysis_date = request.date or datetime.utcnow()
        
        # Calculate date range
        start_date = analysis_date - timedelta(days=request.days_before)
        end_date = analysis_date + timedelta(days=request.days_after)
        
        logger.info(f"Analyzing {request.ticker} from {start_date} to {end_date}")
        
        # Step 1: Fetch relevant news using vector search
        news_articles = await _fetch_news(
            ticker=request.ticker,
            start_date=start_date,
            end_date=end_date,
            limit=request.news_limit
        )
        
        logger.info(f"Found {len(news_articles)} news articles for {request.ticker}")
        
        # Step 2: Fetch price data from TimescaleDB
        price_data = await _fetch_price_data(
            ticker=request.ticker,
            start_date=start_date,
            end_date=end_date
        )
        
        # Step 3: Generate insights
        insights = _generate_insights(news_articles, price_data, request.ticker)
        
        return ContextResponse(
            ticker=request.ticker,
            analysis_date=analysis_date,
            news=news_articles,
            news_count=len(news_articles),
            price_data=price_data,
            has_price_data=price_data is not None,
            insights=insights
        )
        
    except Exception as e:
        logger.error(f"Failed to get context for {request.ticker}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch context: {str(e)}"
        )


@router.get("/timeline/{ticker}")
async def get_ticker_timeline(
    ticker: str,
    start_date: Optional[datetime] = Query(None, description="Timeline start"),
    end_date: Optional[datetime] = Query(None, description="Timeline end"),
    interval: str = Query("1 day", description="Time aggregation (e.g., '1 hour', '1 day')")
):
    """
    Get timeline of news + price for a ticker.
    
    Returns chronological events combining news and price movements.
    
    Example:
        ```
        GET /v1/analysis/timeline/AAPL?start_date=2024-11-01&end_date=2024-11-30&interval=1%20day
        ```
    """
    try:
        # Default date range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Fetch news
        news = await _fetch_news(ticker, start_date, end_date, limit=50)
        
        # Fetch price data with aggregation
        await timeseries.connect()
        price_history = await timeseries.get_ohlcv(
            symbol=ticker if "USDT" in ticker else f"{ticker}USDT",
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        # Combine into timeline
        timeline = []
        
        # Add news events
        for article in news:
            timeline.append({
                "timestamp": article.timestamp,
                "type": "news",
                "title": article.title,
                "category": article.category,
                "source": article.source
            })
        
        # Add price events
        for candle in price_history:
            timeline.append({
                "timestamp": candle["time"] if isinstance(candle, dict) else candle.get("bucket", candle.get("time")),
                "type": "price",
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
                "volume": float(candle["volume"])
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
            "events": timeline,
            "event_count": len(timeline)
        }
        
    except Exception as e:
        logger.error(f"Failed to get timeline for {ticker}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timeline: {str(e)}"
        )


# === Helper Functions ===

async def _fetch_news(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    limit: int = 10
) -> List[NewsArticle]:
    """Fetch news articles for a ticker using vector search."""
    try:
        # Search query
        query = f"{ticker} news stock market price"
        
        # Perform vector search
        results = await vector_store.search(
            collection_name="FinancialInsight",
            query_vector=None,  # Will embed the query text
            query_text=query,
            limit=limit,
            filters={
                "ticker": ticker
            }
        )
        
        # Convert to NewsArticle objects
        articles = []
        for result in results:
            properties = result.get("properties", {})
            
            # Check if timestamp is in date range
            timestamp = properties.get("timestamp")
            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                
                if not (start_date <= timestamp <= end_date):
                    continue
            
            articles.append(NewsArticle(
                title=properties.get("title", ""),
                content=properties.get("content", "")[:500],  # Truncate for response
                source=properties.get("source", "Unknown"),
                url=properties.get("url", ""),
                timestamp=timestamp or datetime.utcnow(),
                ticker=properties.get("ticker"),
                category=properties.get("category"),
                confidence=result.get("distance", 0.0)
            ))
        
        return articles
        
    except Exception as e:
        logger.error(f"Failed to fetch news for {ticker}: {e}")
        return []


async def _fetch_price_data(
    ticker: str,
    start_date: datetime,
    end_date: datetime
) -> Optional[PriceData]:
    """Fetch aggregated price data for a ticker."""
    try:
        await timeseries.connect()
        
        # Convert ticker to Binance format if needed
        symbol = ticker if "USDT" in ticker else f"{ticker}USDT"
        
        # Fetch OHLCV data
        data = await timeseries.get_ohlcv(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=None  # Raw data
        )
        
        if not data:
            logger.warning(f"No price data found for {ticker}")
            return None
        
        # Calculate aggregates
        first_candle = data[0]
        last_candle = data[-1]
        
        open_price = float(first_candle.get("open", 0))
        close_price = float(last_candle.get("close", 0))
        
        high_price = max(float(c.get("high", 0)) for c in data)
        low_price = min(float(c.get("low", 0)) for c in data)
        total_volume = sum(float(c.get("volume", 0)) for c in data)
        
        price_change = close_price - open_price
        price_change_percent = (price_change / open_price * 100) if open_price > 0 else 0
        
        return PriceData(
            symbol=symbol,
            period_start=start_date,
            period_end=end_date,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=total_volume,
            price_change=price_change,
            price_change_percent=price_change_percent
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch price data for {ticker}: {e}")
        return None


def _generate_insights(
    news: List[NewsArticle],
    price_data: Optional[PriceData],
    ticker: str
) -> Dict[str, Any]:
    """Generate basic insights from news and price data."""
    insights = {
        "summary": "",
        "news_sentiment": "neutral",
        "price_trend": "flat",
        "correlation_hints": []
    }
    
    # News insights
    if news:
        category_counts = {}
        for article in news:
            cat = article.category or "general"
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        dominant_category = max(category_counts, key=category_counts.get) if category_counts else "general"
        
        insights["dominant_news_category"] = dominant_category
        insights["news_categories"] = category_counts
        
        # Simple sentiment heuristic
        if dominant_category == "earnings":
            insights["news_sentiment"] = "positive" if price_data and price_data.price_change > 0 else "mixed"
        elif dominant_category == "regulation":
            insights["news_sentiment"] = "negative"
    
    # Price insights
    if price_data:
        if price_data.price_change_percent > 5:
            insights["price_trend"] = "bullish"
        elif price_data.price_change_percent < -5:
            insights["price_trend"] = "bearish"
        
        insights["price_summary"] = f"{ticker} {insights['price_trend']}: {price_data.price_change_percent:.2f}% change"
    
    # Correlation hints
    if news and price_data:
        if abs(price_data.price_change_percent) > 5 and len(news) > 0:
            insights["correlation_hints"].append(
                f"Significant price movement ({price_data.price_change_percent:.2f}%) coincides with {len(news)} news articles"
            )
    
    return insights

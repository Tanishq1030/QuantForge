# backend/engine/ai_engine.py
"""
AI Engine - The Brain of QuantForge

Orchestrates:
- Data gathering (vector store + TimescaleDB)
- LLM analysis (via multi-provider client)
- Response formatting
- Validation
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from backend.core.logging import get_logger
from backend.engine.llm.client import get_llm_client
from backend.engine.llm.prompts import get_prompt_manager, PromptType
from backend.engine.memory.vector_store import QuantForgeVectorStore
from backend.engine.memory.timeseries_store import get_timeseries_store
from backend.engine.parsers.text_preprocessor import TextPreprocessor

logger = get_logger(__name__)


class AIEngine:
    """
    Main AI orchestrator for QuantForge.
    
    Coordinates all AI operations:
    1. Gather data (news + price)
    2. Analyze with LLM
    3. Validate & format response
    
    Usage:
        engine = AIEngine()
        result = await engine.analyze_asset(
            ticker="AAPL",
            analysis_type="comprehensive"
        )
    """
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.prompt_manager = get_prompt_manager()
        self.vector_store = QuantForgeVectorStore()
        self.timeseries = get_timeseries_store()
        self.preprocessor = TextPreprocessor()
        
        logger.info("AIEngine initialized")
    
    async def analyze_asset(
        self,
        ticker: str,
        analysis_type: str = "comprehensive",
        analysis_date: Optional[datetime] = None,
        days_before: int = 7,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Perform comprehensive AI analysis of an asset.
        
        Args:
            ticker: Stock/crypto ticker (e.g., "AAPL", "BTCUSDT")
            analysis_type: "quick" | "comprehensive" | "sentiment_only" | "risk_only"
            analysis_date: Date for analysis (default: now)
            days_before: Days of historical context
            verbose: Include detailed intermediate results
            
        Returns:
            {
                "ticker": "AAPL",
                "analysis_type": "comprehensive",
                "summary": "AI-generated summary...",
                "sentiment": "bullish",
                "recommendation": "HOLD",
                "confidence": 0.85,
                "key_insights": [...],
                "meta": {...}
            }
        """
        start_time = datetime.utcnow()
        analysis_date = analysis_date or datetime.utcnow()
        
        logger.info(f"Starting analysis: {ticker} ({analysis_type})")
        
        try:
            # Step 1: Gather data
            context = await self._gather_context(
                ticker=ticker,
                start_date=analysis_date - timedelta(days=days_before),
                end_date=analysis_date
            )
            
            # Step 2: Route to appropriate analysis
            if analysis_type == "quick":
                result = await self._quick_analysis(ticker, context)
            elif analysis_type == "sentiment_only":
                result = await self._sentiment_analysis(ticker, context)
            elif analysis_type == "risk_only":
                result = await self._risk_analysis(ticker, context)
            else:  # comprehensive
                result = await self._comprehensive_analysis(ticker, context)
            
            # Step 3: Add metadata
            end_time = datetime.utcnow()
            result["meta"] = {
                "analysis_date": analysis_date.isoformat(),
                "processing_time_ms": int((end_time - start_time).total_seconds() * 1000),
                "news_count": context["news_count"],
                "has_price_data": context["has_price_data"],
                "model_used": result.get("model_used", "mock"),
                "version": "1.0"
            }
            
            if verbose:
                result["_debug"] = {
                    "raw_context": context,
                    "prompt_version": self.prompt_manager.VERSION
                }
            
            logger.info(f"Analysis complete: {ticker} ({result['meta']['processing_time_ms']}ms)")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {ticker}: {e}")
            raise
    
    async def _gather_context(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Gather all relevant data for analysis."""
        
        # Import embedder
        from backend.engine.embeddings.hybrid_embedder import HybridEmbedder
        embedder = HybridEmbedder()
        
        # Embed the search query
        query_text = f"{ticker} news stock market"
        query_vector = await embedder.embed_text(query_text)
        
        # Fetch news from vector store
        news_results = await self.vector_store.search(
            query_vector=query_vector,
            collection_name="FinancialInsight",
            limit=20,
            filters={"ticker": ticker} if ticker else None
        )
        
        # Filter by date range
        news_articles = []
        for result in news_results:
            props = result.get("properties", {})
            timestamp = props.get("timestamp")
            
            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                
                if start_date <= timestamp <= end_date:
                    news_articles.append({
                        "title": props.get("title", ""),
                        "content": props.get("content", "")[:300],  # Truncate
                        "source": props.get("source", ""),
                        "timestamp": timestamp.isoformat(),
                        "category": props.get("category", "general")
                    })
        
        # Fetch price data from TimescaleDB
        price_data = None
        try:
            await self.timeseries.connect()
            
            symbol = ticker if "USDT" in ticker else f"{ticker}USDT"
            
            ohlcv = await self.timeseries.get_ohlcv(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if ohlcv:
                first = ohlcv[0]
                last = ohlcv[-1]
                
                price_data = {
                    "open": float(first.get("open", 0)),
                    "close": float(last.get("close", 0)),
                    "high": max(float(c.get("high", 0)) for c in ohlcv),
                    "low": min(float(c.get("low", 0)) for c in ohlcv),
                    "volume": sum(float(c.get("volume", 0)) for c in ohlcv),
                    "change_percent": ((float(last.get("close", 0)) - float(first.get("open", 0))) / float(first.get("open", 0)) * 100) if float(first.get("open", 0)) > 0 else 0
                }
        except Exception as e:
            logger.warning(f"Failed to fetch price data: {e}")
        
        return {
            "ticker": ticker,
            "news_articles": news_articles,
            "news_count": len(news_articles),
            "price_data": price_data,
            "has_price_data": price_data is not None,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def _quick_analysis(self, ticker: str, context: Dict) -> Dict[str, Any]:
        """Quick analysis (<500ms target) using simple rules."""
        
        # Simple rule-based analysis (no LLM needed for quick mode)
        news_count = context["news_count"]
        has_price = context["has_price_data"]
        
        summary = f"{ticker}: "
        if news_count == 0:
            summary += "No recent news activity."
            sentiment = "neutral"
            confidence = 0.3
        else:
            # Count categories
            categories = [n["category"] for n in context["news_articles"]]
            if "earnings" in categories:
                summary += "Earnings-related news detected."
                sentiment = "bullish" if has_price and context["price_data"]["change_percent"] > 0 else "neutral"
                confidence = 0.6
            elif "regulation" in categories:
                summary += "Regulatory news detected."
                sentiment = "bearish"
                confidence = 0.5
            else:
                summary += f"{news_count} news articles found."
                sentiment = "neutral"
                confidence = 0.4
        
        if has_price:
            change = context["price_data"]["change_percent"]
            summary += f" Price: {change:+.2f}%"
        
        return {
            "ticker": ticker,
            "analysis_type": "quick",
            "summary": summary,
            "sentiment": sentiment,
            "confidence": confidence,
            "recommendation": "HOLD",  # Default for quick mode
            "key_insights": [
                f"{news_count} news articles analyzed",
                f"Price data: {'available' if has_price else 'unavailable'}"
            ],
            "model_used": "rule_based"
        }
    
    async def _sentiment_analysis(self, ticker: str, context: Dict) -> Dict[str, Any]:
        """Deep sentiment analysis using LLM."""
        
        if context["news_count"] == 0:
            return {
                "ticker": ticker,
                "analysis_type": "sentiment_only",
                "summary": "Insufficient data for sentiment analysis",
                "sentiment": "neutral",
                "confidence": 0.0,
                "model_used": "none"
            }
        
        # Prepare news text
        news_text = "\n\n".join([
            f"[{n['source']}] {n['title']}\n{n['content']}"
            for n in context["news_articles"][:10]  # Limit to 10
        ])
        
        # Get prompt
        prompt = self.prompt_manager.get_prompt(
            PromptType.SENTIMENT_ANALYSIS,
            ticker=ticker,
            news_text=news_text
        )
        
        # Call LLM
        try:
            llm_response = await self.llm_client.generate(
                prompt=prompt["user"],
                system_message=prompt["system"],
                max_tokens=300,
                temperature=0.3
            )
            
            # Parse JSON response
            analysis = self._parse_llm_json(llm_response["text"])
            
            return {
                "ticker": ticker,
                "analysis_type": "sentiment_only",
                "summary": f"Sentiment: {analysis.get('sentiment', 'neutral')}",
                "sentiment": analysis.get("sentiment", "neutral"),
                "confidence": analysis.get("confidence", 0.5),
                "key_insights": analysis.get("themes", []),
                "impact": analysis.get("impact", ""),
                "model_used": llm_response["provider"]
            }
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Fallback to rule-based
            return await self._quick_analysis(ticker, context)
    
    async def _risk_analysis(self, ticker: str, context: Dict) -> Dict[str, Any]:
        """Risk assessment using LLM."""
        # Similar to sentiment but with risk prompt
        # Implementation similar to _sentiment_analysis
        pass  # TODO: Implement
    
    async def _comprehensive_analysis(self, ticker: str, context: Dict) -> Dict[str, Any]:
        """Full comprehensive analysis combining all data."""
        
        # For now, use quick analysis as base
        # In full implementation, this would:
        # 1. Get sentiment
        # 2. Explain price movement
        # 3. Assess risks
        # 4. Generate recommendation
        
        result = await self._quick_analysis(ticker, context)
        result["analysis_type"] = "comprehensive"
        
        return result
    
    def _parse_llm_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response (handles markdown code blocks)."""
        try:
            # Remove markdown code blocks if present
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            return json.loads(text.strip())
        except:
            return {}


# Singleton instance
_ai_engine = None

def get_ai_engine() -> AIEngine:
    """Get singleton AIEngine instance."""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngine()
    return _ai_engine

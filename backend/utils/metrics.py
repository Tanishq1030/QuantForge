# backend/utils/metrics.py
"""
Usage Metrics & Analytics

Tracks API usage, token consumption, and costs for billing and analytics.
Critical for commercial SaaS operations and customer billing.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from backend.core.logging import get_logger
from backend.core.config import settings

logger = get_logger(__name__)


class MetricsCollector:
    """
    Collects and logs usage metrics for billing and analytics.
    
    Metrics tracked:
    - API calls per endpoint
    - Token usage (for LLM billing)
    - Processing time
    - Data sources accessed
    - User/organization attribution
    """
    
    def __init__(self):
        self.enabled = not settings.DEBUG  # Disable in dev
    
    def log_analysis_request(
        self,
        ticker: str,
        analysis_type: str,
        processing_time_ms: int,
        tokens_used: int,
        llm_provider: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Log AI analysis request for billing and analytics.
        
        Args:
            ticker: Asset analyzed
            analysis_type: Type of analysis
            processing_time_ms: Time taken
            tokens_used: LLM tokens consumed
            llm_provider: Provider used (ollama, openai, etc.)
            user_id: User making request
            org_id: Organization ID
            success: Whether request succeeded
            error: Error message if failed
        """
        
        if not self.enabled:
            return
        
        # Calculate cost estimate
        cost_estimate = self._estimate_cost(llm_provider, tokens_used)
        
        metric = {
            "event_type": "analysis_request",
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "analysis_type": analysis_type,
            "processing_time_ms": processing_time_ms,
            "tokens_used": tokens_used,
            "llm_provider": llm_provider,
            "cost_estimate_usd": cost_estimate,
            "user_id": user_id,
            "org_id": org_id,
            "success": success,
            "error": error
        }
        
        # Log to structured logger (can be sent to PostgreSQL/ClickHouse/etc)
        logger.info(f"METRIC: {json.dumps(metric)}")
        
        # TODO: Also store in PostgreSQL for historical analysis
        # await self._store_metric(metric)
    
    def log_llm_fallback(
        self,
        primary_provider: str,
        fallback_provider: str,
        reason: str,
        ticker: str
    ):
        """
        Log when LLM provider fallback occurs.
        
        Important for monitoring provider reliability.
        """
        
        if not self.enabled:
            return
        
        metric = {
            "event_type": "llm_fallback",
            "timestamp": datetime.utcnow().isoformat(),
            "primary_provider": primary_provider,
            "fallback_provider": fallback_provider,
            "reason": reason,
            "ticker": ticker
        }
        
        logger.warning(f"METRIC: {json.dumps(metric)}")
    
    def log_validation_failure(
        self,
        ticker: str,
        warnings: list,
        confidence_before: float,
        confidence_after: float
    ):
        """
        Log validation failures (hallucinations detected).
        
        Helps track AI quality over time.
        """
        
        if not self.enabled:
            return
        
        metric = {
            "event_type": "validation_failure",
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "warning_count": len(warnings),
            "warnings": warnings,
            "confidence_before": confidence_before,
            "confidence_after": confidence_after,
            "confidence_delta": confidence_after - confidence_before
        }
        
        logger.warning(f"METRIC: {json.dumps(metric)}")
    
    def log_data_source_usage(
        self,
        ticker: str,
        news_count: int,
        has_price_data: bool,
        vector_search_time_ms: int,
        timeseries_query_time_ms: int
    ):
        """
        Log data source usage for optimization.
        """
        
        if not self.enabled:
            return
        
        metric = {
            "event_type": "data_source_usage",
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "news_count": news_count,
            "has_price_data": has_price_data,
            "vector_search_time_ms": vector_search_time_ms,
            "timeseries_query_time_ms": timeseries_query_time_ms
        }
        
        logger.info(f"METRIC: {json.dumps(metric)}")
    
    def _estimate_cost(self, provider: str, tokens: int) -> float:
        """
        Estimate cost based on provider and token usage.
        
        Pricing (approximate):
        - OpenAI GPT-4: $0.03 / 1K tokens
        - OpenAI GPT-3.5: $0.002 / 1K tokens
        - Ollama: $0 (local)
        - HuggingFace: $0 (free tier)
        """
        
        pricing = {
            "openai": 0.002,  # Assume GPT-3.5
            "ollama": 0.0,
            "huggingface": 0.0
        }
        
        rate_per_1k = pricing.get(provider, 0.0)
        return (tokens / 1000) * rate_per_1k


# Singleton instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get singleton metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

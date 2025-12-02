# backend/core/sentry.py
"""
Sentry Error Tracking Integration

Captures errors, performance metrics, and custom events for production monitoring.
Essential for commercial SaaS to track issues and optimize performance.
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


def init_sentry():
    """
    Initialize Sentry error tracking.
    
    Only initializes if SENTRY_DSN is configured in environment.
    Integrates with FastAPI and asyncio for comprehensive tracking.
    """
    
    if not settings.SENTRY_DSN:
        logger.warning("Sentry DSN not configured - error tracking disabled")
        return
    
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            
            # Performance monitoring
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            
            # Integrations
            integrations=[
                FastApiIntegration(
                    transaction_style="url",  # Group by URL pattern
                    failed_request_status_codes=[400, 500]
                ),
                AsyncioIntegration()
            ],
            
            # Release tracking (for version comparison)
            release=f"quantforge@{settings.API_VERSION}",
            
            # Additional context
            send_default_pii=False,  # Don't send personal data
            attach_stacktrace=True,
            debug=settings.DEBUG
        )
        
        logger.info(f"✅ Sentry initialized (env: {settings.SENTRY_ENVIRONMENT})")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def capture_llm_error(
    provider: str,
    error: Exception,
    context: dict = None
):
    """
    Capture LLM provider failure with context.
    
    Args:
        provider: LLM provider name (huggingface, openai, ollama)
        error: Exception that occurred
        context: Additional context (model, prompt, etc.)
    """
    
    if not settings.SENTRY_DSN:
        return
    
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("llm_provider", provider)
        scope.set_context("llm_context", context or {})
        scope.level = "error"
        
        sentry_sdk.capture_exception(error)
        logger.debug(f"Captured LLM error to Sentry: {provider}")


def capture_validation_warning(
    warnings: list,
    response: dict,
    context: dict
):
    """
    Capture validation warnings (hallucination detection).
    
    Important for tracking AI quality issues.
    """
    
    if not settings.SENTRY_DSN or not warnings:
        return
    
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("event_type", "validation_warning")
        scope.set_context("validation", {
            "warnings": warnings,
            "ticker": context.get("ticker"),
            "analysis_type": response.get("analysis_type"),
            "confidence": response.get("confidence")
        })
        scope.level = "warning"
        
        # Send as custom event (not exception)
        sentry_sdk.capture_message(
            f"AI validation warnings: {len(warnings)} issues",
            level="warning"
        )


def capture_slow_analysis(
    ticker: str,
    analysis_type: str,
    duration_ms: int,
    threshold_ms: int = 10000
):
    """
    Capture slow API responses for performance monitoring.
    
    Args:
        ticker: Asset ticker
        analysis_type: Type of analysis
        duration_ms: Actual duration
        threshold_ms: Threshold for "slow" (default 10s)
    """
    
    if not settings.SENTRY_DSN or duration_ms < threshold_ms:
        return
    
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("event_type", "slow_analysis")
        scope.set_context("performance", {
            "ticker": ticker,
            "analysis_type": analysis_type,
            "duration_ms": duration_ms,
            "threshold_ms": threshold_ms
        })
        scope.level = "warning"
        
        sentry_sdk.capture_message(
            f"Slow analysis detected: {duration_ms}ms for {ticker}",
            level="warning"
        )


def set_user_context(user_id: str, org_id: str = None):
    """
    Set user context for error tracking.
    
    Helps identify which users are experiencing issues.
    """
    
    if not settings.SENTRY_DSN:
        return
    
    sentry_sdk.set_user({
        "id": user_id,
        "organization": org_id
    })

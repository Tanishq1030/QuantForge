# backend/middleware/rate_limiter.py
"""
Rate Limiting Middleware for API Tiers

Implements usage limits for Free, Pro, and Enterprise tiers.
Critical for preventing abuse and managing costs in commercial SaaS.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncio

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from backend.core.logging import get_logger
from backend.core.config import settings

logger = get_logger(__name__)


# Tier limits (requests per day)
TIER_LIMITS = {
    "free": {
        "requests_per_day": 50,
        "requests_per_hour": 10,
        "max_tokens": 1000
    },
    "pro": {
        "requests_per_day": 10000,
        "requests_per_hour": 500,
        "max_tokens": 2000
    },
    "enterprise": {
        "requests_per_day": -1,  # Unlimited
        "requests_per_hour": -1,
        "max_tokens": 5000
    }
}


class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    In production, use Redis for distributed rate limiting.
    This implementation is suitable for single-server deployments.
    """
    
    def __init__(self):
        # Store: {user_id: {endpoint: [(timestamp, tokens_used)]}}
        self.usage: Dict[str, Dict[str, list]] = {}
        self.cleanup_task = None
    
    async def start(self):
        """Start background cleanup task."""
        self.cleanup_task = asyncio.create_task(self._cleanup_old_entries())
        logger.info("Rate limiter started")
    
    async def stop(self):
        """Stop background cleanup task."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
    
    def check_limit(
        self,
        user_id: str,
        tier: str,
        endpoint: str,
        tokens_requested: int = 0
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limits.
        
        Returns:
            (allowed, info_dict)
        """
        
        tier_limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        
        # Get usage history
        if user_id not in self.usage:
            self.usage[user_id] = {}
        if endpoint not in self.usage[user_id]:
            self.usage[user_id][endpoint] = []
        
        usage_history = self.usage[user_id][endpoint]
        now = datetime.utcnow()
        
        # Filter to last 24 hours
        day_ago = now - timedelta(days=1)
        hour_ago = now - timedelta(hours=1)
        
        requests_today = [t for t, _ in usage_history if t > day_ago]
        requests_hour = [t for t, _ in usage_history if t > hour_ago]
        
        # Check daily limit
        daily_limit = tier_limits["requests_per_day"]
        if daily_limit > 0 and len(requests_today) >= daily_limit:
            return False, {
                "limit_type": "daily",
                "limit": daily_limit,
                "used": len(requests_today),
                "reset_at": (day_ago + timedelta(days=1)).isoformat()
            }
        
        # Check hourly limit
        hourly_limit = tier_limits["requests_per_hour"]
        if hourly_limit > 0 and len(requests_hour) >= hourly_limit:
            return False, {
                "limit_type": "hourly",
                "limit": hourly_limit,
                "used": len(requests_hour),
                "reset_at": (hour_ago + timedelta(hours=1)).isoformat()
            }
        
        # Check token limit
        max_tokens = tier_limits["max_tokens"]
        if tokens_requested > max_tokens:
            return False, {
                "limit_type": "max_tokens",
                "limit": max_tokens,
                "requested": tokens_requested
            }
        
        return True, {
            "tier": tier,
            "requests_today": len(requests_today),
            "requests_hour": len(requests_hour),
            "daily_limit": daily_limit,
            "hourly_limit": hourly_limit
        }
    
    def record_usage(
        self,
        user_id: str,
        endpoint: str,
        tokens_used: int = 0
    ):
        """Record successful API usage."""
        
        if user_id not in self.usage:
            self.usage[user_id] = {}
        if endpoint not in self.usage[user_id]:
            self.usage[user_id][endpoint] = []
        
        self.usage[user_id][endpoint].append((datetime.utcnow(), tokens_used))
    
    async def _cleanup_old_entries(self):
        """Background task to cleanup old usage entries."""
        
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff = datetime.utcnow() - timedelta(days=2)
                
                for user_id in list(self.usage.keys()):
                    for endpoint in list(self.usage[user_id].keys()):
                        # Keep only recent entries
                        self.usage[user_id][endpoint] = [
                            (t, tokens) for t, tokens in self.usage[user_id][endpoint]
                            if t > cutoff
                        ]
                        
                        if not self.usage[user_id][endpoint]:
                            del self.usage[user_id][endpoint]
                    
                    if not self.usage[user_id]:
                        del self.usage[user_id]
                
                logger.debug("Cleaned up old rate limit entries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")


# Singleton instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting.
    
    Checks rate limits before processing request.
    Returns 429 if limits exceeded.
    """
    
    # Skip rate limiting for health check and docs
    if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # Get user info from headers (in production, from JWT/Clerk)
    user_id = request.headers.get("X-User-ID", "anonymous")
    tier = request.headers.get("X-User-Tier", "free")
    
    # Check rate limit
    limiter = get_rate_limiter()
    allowed, info = limiter.check_limit(
        user_id=user_id,
        tier=tier,
        endpoint=request.url.path
    )
    
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"{info['limit_type'].title()} limit of {info['limit']} requests exceeded",
                "limit_info": info
            }
        )
    
    # Process request
    response = await call_next(request)
    
    # Record usage if successful
    if 200 <= response.status_code < 300:
        limiter.record_usage(user_id, request.url.path)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(info.get("daily_limit", "unlimited"))
    response.headers["X-RateLimit-Remaining"] = str(
        max(0, info.get("daily_limit", 0) - info.get("requests_today", 0))
    )
    
    return response

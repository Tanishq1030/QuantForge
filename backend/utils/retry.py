# backend/utils/retry.py
"""
Retry utilities with exponential backoff.

Provides:
- Async retry decorator
- Exponential backoff
- Custom retry policies
"""

import asyncio
import functools
from typing import Callable, Type, Tuple, Optional
from backend.core.logging import get_logger

logger = get_logger(__name__)


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Async retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay in seconds
        backoff: Multiplier for delay (exponential backoff)
        exceptions: Tuple of exceptions to catch
        
    Example:
        ```python
        @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
        async def fetch_data():
            # Will retry 3 times with 1s, 2s, 4s delays
            return await api.get_data()
        ```
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay}s: {e}"
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class RetryPolicy:
    """Configurable retry policy."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt."""
        import random
        
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter (0-25% of delay)
            jitter_amount = delay * 0.25 * random.random()
            delay += jitter_amount
        
        return delay

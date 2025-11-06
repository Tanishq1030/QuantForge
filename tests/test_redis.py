# tests/test_redis.py

from backend.utils.cache import RedisClient
from backend.core.logging import get_logger

logger = get_logger(__name__)


def test_redis_connection():
    redis_client = RedisClient()

    if redis_client.client:
        logger.info("✅ Redis connection successful!")

        # Basic set/get test
        redis_client.set("quantforge:test", "working", ex=10)
        value = redis_client.get("quantforge:test")

        if value == "working":
            logger.info(f"📦 Redis operational — Stored value: {value}")
        else:
            logger.error("❌ Redis set/get failed!")

    else:
        logger.error("❌ Redis connection failed — client not initialized.")


if __name__ == "__main__":
    test_redis_connection()

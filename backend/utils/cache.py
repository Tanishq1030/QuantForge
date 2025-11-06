import redis
from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """
    Redis Client for caching, pub/sub, and rate-limiting.
    Provides a unified interface to Redis operations across QuantForge.
    """

    def __init__(self):
        try:
            self.client = redis.StrictRedis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True,
            )
            # Test connection
            self.client.ping()
            logger.info(f"✅ Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.client = None

    def set(self, key: str, value: str, ex: int = None):
        """
        Set a key-value pair in Redis with an optional expiry.
        """
        if not self.client:
            logger.warning("⚠️ Redis not initialized.")
            return None

        try:
            self.client.set(name=key, value=value, ex=ex)
            logger.debug(f"🧩 Redis SET: {key} -> {value}")
        except Exception as e:
            logger.error(f"Redis SET failed for {key}: {e}")

    def get(self, key: str):
        """
        Retrieve a value by key from Redis.
        """
        if not self.client:
            logger.warning("⚠️ Redis not initialized.")
            return None

        try:
            value = self.client.get(name=key)
            logger.debug(f"📥 Redis GET: {key} -> {value}")
            return value
        except Exception as e:
            logger.error(f"Redis GET failed for {key}: {e}")
            return None

    def publish(self, channel: str, message: str):
        """
        Publish a message to a Redis channel.
        """
        if not self.client:
            logger.warning("⚠️ Redis not initialized.")
            return None

        try:
            self.client.publish(channel, message)
            logger.info(f"📢 Published to channel '{channel}': {message}")
        except Exception as e:
            logger.error(f"Redis publish failed: {e}")

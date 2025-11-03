import redis
import os

class RedisClient:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.db = int(os.getenv("REDIS_DB", 0))
        self.client = redis.StrictRedis(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            decode_responses=True
        )

    def ping(self):
        return self.client.ping()

    def set(self, key, value, expire=None):
        self.client.set(key, value, ex=expire)

    def get(self, key):
        return self.client.get(key)

    def delete(self, key):
        self.client.delete(key)

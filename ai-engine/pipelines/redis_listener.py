import redis
from utils.config import settings


class RedisListener:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
        )
        self.pubsub = self.client.pubsub()
        self.pubsub.subscribe(settings.REDIS_CHANNEL)

    def listen(self):
        print(f"Listening on redis channel: {settings.REDIS_CHANNEL}")
        for message in self.pubsub.listen():
            if message["type"] == "message":
                print("Received:", message["data"])
                # TODO: Forward to model/pipelines

from backend.utils.cache import RedisClient

def test_redis_connection():
    redis_client = RedisClient()
    try:
        if redis_client.ping():
            print("✅ Redis connection successful!")
            redis_client.set("quantforge:test", "working", expire=10)
            value = redis_client.get("quantforge:test")
            print(f"Stored value: {value}")
        else:
            print("❌ Redis ping failed.")
    except Exception as e:
        print(f"❌ Redis connection error: {e}")

if __name__ == "__main__":
    test_redis_connection()

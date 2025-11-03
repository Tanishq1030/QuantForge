import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
	PROJECT_NAME: str = "QuantForge AI Engine"
	
	# Database
	DATABASE_URL: str = os.getenv("DATABASE_URL")
	
	# Redis
	REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
	REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
	REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
	REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
	
	# Weaviate
	WEAVIATE_URL: str = os.getenv("WEAVIATE_URL")
	WEAVIATE_API_KEY: str = os.getenv("WEAVIATE_API_KEY")
	
	# MinIO
	MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
	MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "quantforge_admin")
	MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "quantforge123")
	MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "quantforge-data")


settings = Settings()

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Central configuration for QuantForge AI Engine"""

    # --- Project Metadata ---
    PROJECT_NAME: str = "QuantForge AI Engine"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- Database (Postgres / Neon / Timescale) ---
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # --- Redis ---
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))

    # --- MinIO / Object Storage ---
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_USE_SSL: bool = os.getenv("MINIO_USE_SSL", "False").lower() == "true"
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "quantforge-data")

    # --- Weaviate / Vector Memory ---
    WEAVIATE_ENDPOINT: str = os.getenv("WEAVIATE_ENDPOINT", "")
    WEAVIATE_API_KEY: str = os.getenv("WEAVIATE_API_KEY", "")

    # --- LLM / AI Providers ---
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# ✅ Global instance (import this anywhere)
settings = Settings()

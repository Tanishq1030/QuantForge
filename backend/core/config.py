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
    
    # --- Embedding Configuration ---
    EMBEDDING_BACKEND: str = os.getenv("EMBEDDING_BACKEND", "huggingface")
    HF_EMBEDDING_MODEL: str = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    HF_INFERENCE_API: str = os.getenv("HF_INFERENCE_API", "https://api-inference.huggingface.co/models")
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    APP_NAME: str = os.getenv("APP_NAME", "QuantForge AI Engine")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    
    # --- LLM Configuration (Phase 1.4) ---
    # Hugging Face LLM (Primary - Free tier)
    HF_LLM_MODEL: str = os.getenv("HF_LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    HF_LLM_ENDPOINT: str = os.getenv("HF_LLM_ENDPOINT", "https://api-inference.huggingface.co/models")
    
    # OpenAI (Paid Fallback)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    
    # Ollama LLM (Local Fallback)
    OLLAMA_LLM_MODEL: str = os.getenv("OLLAMA_LLM_MODEL", "mistral:latest")
    
    # --- Authentication (Clerk) ---
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_PUBLISHABLE_KEY: str = os.getenv("CLERK_PUBLISHABLE_KEY", "")
    CLERK_JWT_KEY: str = os.getenv("CLERK_JWT_KEY", "")
    
    # --- Error Tracking (Sentry) ---
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    
   # --- Payments (Stripe) ---
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# ✅ Global instance (import this anywhere)
settings = Settings()

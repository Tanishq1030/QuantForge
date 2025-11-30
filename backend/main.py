# backend/main.py

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.session import engine
from backend.utils.cache import RedisClient
from backend.utils.minio_client import MinioClient
from backend.routes import system, vector, feeds
# from backend.engine.memory.vector_store import WeaviateClient  # to be implemented later
import sqlalchemy

logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="QuantForge AI Engine — Core Backend Runtime",
)

# Initialize reusable clients
redis_client = RedisClient()
minio_client = MinioClient()

# Include routers
app.include_router(system.router)
app.include_router(vector.router)
app.include_router(feeds.router)

@app.get("/")
async def root():
    return {"message": "QuantForge AI Engine operational."}


@app.get("/v1/health", tags=["System"])
async def health_check():
    """
    Basic health check endpoint.
    Returns a simple OK response to verify that the FastAPI service is running.
    """
    return JSONResponse({"status": "ok", "app": settings.APP_NAME})


@app.get("/v1/system/ping", tags=["System"])
async def ping():
    """
    Simple API ping — ensures that routing and server are alive.
    """
    logger.info("Received ping request.")
    return {"message": "pong", "app": settings.APP_NAME}


@app.get("/v1/system/dependencies", tags=["System"])
async def check_dependencies():
    """
    Verify connectivity for Redis, PostgreSQL, MinIO, and Weaviate.
    Returns a structured status dictionary.
    """
    status = {}

    # --- Redis ---
    try:
        if redis_client.client:
            redis_client.set("quantforge:ping", "1", ex=5)
            val = redis_client.get("quantforge:ping")
            status["redis"] = "✅ Connected" if val == "1" else "⚠️ Read/Write issue"
        else:
            status["redis"] = "❌ Not Connected"
    except Exception as e:
        status["redis"] = f"❌ Error: {str(e)}"

    # --- PostgreSQL ---
    try:
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT NOW()")).fetchone()
            status["postgres"] = f"✅ Connected — {result[0]}"
    except Exception as e:
        status["postgres"] = f"❌ Error: {str(e)}"

    # --- MinIO ---
    try:
        bucket_name = settings.MINIO_BUCKET
        if bucket_name in [b.name for b in minio_client.client.list_buckets()]:
            status["minio"] = f"✅ Connected — bucket '{bucket_name}' found"
        else:
            status["minio"] = "⚠️ Connected but bucket missing"
    except Exception as e:
        status["minio"] = f"❌ Error: {str(e)}"

    # --- Weaviate (will be active next step) ---
    try:
        status["weaviate"] = "⏳ Pending setup"
    except Exception as e:
        status["weaviate"] = f"❌ Error: {str(e)}"

    logger.info("Dependency check results: " + str(status))
    return JSONResponse(status)

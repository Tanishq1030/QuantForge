import asyncio

import sqlalchemy
from boto3.s3.inject import download_file
from fastapi import APIRouter
from backend.db.session import get_engine
from backend.utils.cache import RedisClient
from backend.utils.minio_client import MinioClient
from backend.engine.memory.vector_store import QuantForgeVectorStore
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/system", tags=["System"])

@router.get("/dependencies", summary="Check system dependency health")
async def health_dependencies():
	"""
	Runs concurrent health checks for:
	  - PostgreSQL (Neon)
	  - Redis
	  - Minio
	  - Weaviate
	returns structured JSON with status + latency per dependency.
	"""
	results = {}
	
	async def check_postgres():
		try:
			engine = get_engine()
			with engine.connect() as conn:
				conn.execute(sqlalchemy.text("SELECT 1"))
			results["postgres"] = {"status": "✅ healthy"}
		except Exception as e:
			results["postgres"] = {"status": "❌ down", "error": str(e)}
	
	async def check_redis():
		try:
			redis = RedisClient()
			await asyncio.to_thread(redis.client.ping)
			results["redis"] = {"status": "✅ healthy"}
		except Exception as e:
			results["redis"] = {"status": " ❌ down", "error": str(e)}
			
	async def check_minio():
		try:
			minio = MinioClient()
			buckets = await asyncio.to_thread(minio.client.list_buckets)
			results["minio"] = {"status": "✅ healthy", "buckets": [b.name for b in buckets]}
			
		except Exception as e:
			results["minio"] = {"status": "❌ down", "error": str(e)}
			
	async def check_weaviate():
		try:
			weaviate_client = QuantForgeVectorStore()
			if weaviate_client.client and weaviate_client.client.is_ready():
				results["weaviate"] = {"status": "✅ healthy"}
			else:
				results["weaviate"] = {"status": "❌ down"}
			weaviate_client.client.close()
		except Exception as e:
			results["weaviate"] = {"status": "❌ down", "error": str(e)}
			
	await asyncio.gather(check_postgres(), check_redis(), check_minio(), check_weaviate())
	
	return {"dependencies": results}
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
			
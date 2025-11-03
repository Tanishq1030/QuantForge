"""
FastAPI entrypoint for QuantForge AI Engine (Phase 1)
Mounts routers, sets up middleware, and exposes health and readiness checks.

This file must live at: QuantForge/backend/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import project config & logger
from backend.core.config import settings
from backend.core.logging import logger
from backend.utils.cache import RedisCLient

redis_client = RedisCLient()

# Import routers
try:
	from backend.api.infer import router as infer_router
except Exception:
	infer_router = None
	logger.warning("infer router not mounted (backend/api/infer.py missing)")
	
try:
	from backend.api.system import router as system_router
except Exception:
	system_router = None
	logger.warning("system router not mounted (backend/api/system.py missing)")
	

def create_app() -> FastAPI:
	"""Factory to create the FastAPI app with middleware and routes."""
	app = FastAPI(
		title=settings.APP_NAME,
		version=settings.APP_VERSION,
		description="QuantForge AI Engine - Phase 1 core API",
		docs_url="/docs" if settings.ENV != "prod" else None,
		redoc_url="/redoc" if settings.ENV != "prod" else None,
	)
	
	# CORS middleware -- restricts origins in production via .env
	
	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.ALLOWED_ORIGINS,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)
	
	# Include routers (if available)
	if infer_router:
		app.include_router(infer_router, prefix="/v1")
		logger.info("Normal infer router at /v1")
	if system_router:
		app.include_router(system_router, prefix="v1/system")
		logger.info("Mounted system router at /v1/system")
		
	
	# Basic health check
	@app.get("/health", tags=["system"])
	async def health():
		"""
		Health endpoint used by load balancers, Cloudflare, and readiness probes.
		Returns service status and basic diagnostics.
		"""
		return JSONResponse({"status": "ok", "service": settings.APP_NAME, "env": settings.ENV})
	
	# Ready endpoint (can be extended to check DB, Weaviate, Ollama, etc)
	@app.get("/ready", tags=["system"])
	async def ready():
		"""
		Readiness check - currently light. Replace with full connectivity checks later.
		"""
		return JSONResponse({"ready": True})
	
	return app

app = create_app()

# When running uvicorn from project root:
# uvicorn backend.main:app --reload --port 8001
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
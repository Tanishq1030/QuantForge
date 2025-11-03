# backend/api/system.py
"""
System router: lightweight diagnostics and metadata endpoints.
Mounted at: /v1/system (main.py mounts routers under /v1 prefix).
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.logging import logger

router = APIRouter(tags=["system"])


@router.get("/info")
async def info():
    """
    Returns basic application info and environment.
    Useful for quick checks and scripts that need app metadata.
    """
    logger.info("Served /v1/system/info")
    return JSONResponse(
        {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.ENV,
            "ollama_host": f"{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"
            if settings.OLLAMA_HOST and settings.OLLAMA_PORT
            else None,
        }
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the system router.
    This is in addition to main /health; useful for internal health probes.
    """
    logger.debug("Health check ping")
    return JSONResponse({"status": "ok", "component": "system", "env": settings.ENV})

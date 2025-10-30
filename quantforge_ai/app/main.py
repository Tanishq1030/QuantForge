from fastapi import FastAPI

from ..app.config import settings
from ..app.logger import setup_logger
from ..routes import chat
from ..routes import patterns
from ..routes import predict

logger = setup_logger()

app = FastAPI(
	title=settings.PROJECT_NAME,
	version=settings.VERSION,
	description="QuantForge AI Engine — Intelligent Analysis & Forecast Microservice"
)

# Include versioned routes
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat"])
app.include_router(predict.router, prefix="/v1/predict", tags=["Prediction"])
app.include_router(patterns.router, prefix="/v1/patterns", tags=["Patterns"])


# ============= Health & Root =============
@app.get("/", tags=["Health"])
async def root():
	logger.info("Root health check pinged.")
	return {
		"status":      "QuantForge AI Engine is running",
		"version":     settings.VERSION,
		"environment": settings.ENVIRONMENT
	}


@app.get("/v1/health", tags=["Health"])
async def health_check():
	logger.info("Detailed health check requested.")
	return {
		"status":       "healthy",
		"service":      settings.PROJECT_NAME,
		"model_loaded": bool(settings.MODEL_NAME),
		"llm_provider": "Hugging Face",
		"version":      settings.VERSION
	}

# backend/routes/ai.py
"""
AI Analysis API Routes

Main endpoint: POST /v1/ai/analyze
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.engine.ai_engine import get_ai_engine
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/ai", tags=["AI Analysis"])


# === Request/Response Schemas ===

class AnalyzeRequest(BaseModel):
    """Request schema for AI analysis"""
    ticker: str = Field(..., description="Stock/crypto ticker (e.g., AAPL, BTCUSDT)")
    analysis_type: str = Field(
        default="comprehensive",
        description="Analysis type: quick | comprehensive | sentiment_only | risk_only"
    )
    as_of: Optional[datetime] = Field(None, description="Analysis date (default: now)")
    days_before: int = Field(default=7, description="Days of historical context", ge=1, le=90)
    sources: list[str] = Field(default=["news", "price"], description="Data sources to include")
    verbose: bool = Field(default=False, description="Include debug information")


class AnalyzeResponse(BaseModel):
    """Response schema for AI analysis"""
    ticker: str
    analysis_type: str
    summary: str
    sentiment: str
    recommendation: str
    confidence: float
    key_insights: list[str]
    meta: dict


# === API Endpoints ===

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_asset(request: AnalyzeRequest):
    """
    🧠 **AI-Powered Asset Analysis**
    
    Analyzes a stock or cryptocurrency using:
    - Financial news (vector search)
    - Price data (TimescaleDB)
    - LLM reasoning
    
    **Analysis Types:**
    - `quick`: Fast rule-based analysis (<500ms)
    - `comprehensive`: Deep LLM-powered analysis (5-10s)
    - `sentiment_only`: News sentiment only
    - `risk_only`: Risk assessment only
    
    **Example Request:**
    ```json
    {
        "ticker": "AAPL",
        "analysis_type": "comprehensive",
        "days_before": 7
    }
    ```
    
    **Example Response:**
    ```json
    {
        "ticker": "AAPL",
        "summary": "Apple shows bullish momentum following Q4 earnings...",
        "sentiment": "bullish",
        "recommendation": "HOLD",
        "confidence": 0.85,
        "key_insights": [
            "iPhone revenue up 12% YoY",
            "Services growth accelerating"
        ],
        "meta": {
            "processing_time_ms": 320,
            "model_used": "mistral:latest"
        }
    }
    ```
    """
    try:
        logger.info(f"AI analysis request: {request.ticker} ({request.analysis_type})")
        
        # Get AI engine
        engine = get_ai_engine()
        
        # Perform analysis
        result = await engine.analyze_asset(
            ticker=request.ticker,
            analysis_type=request.analysis_type,
            analysis_date=request.as_of,
            days_before=request.days_before,
            verbose=request.verbose
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/status")
async def ai_status():
    """
    Check AI engine status.
    
    Returns available providers and health status.
    """
    try:
        engine = get_ai_engine()
        
        return {
            "status": "healthy",
            "llm_providers": [p.value for p in engine.llm_client.providers],
            "vector_store": "connected",
            "timeseries": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI engine unhealthy: {str(e)}"
        )


@router.get("/models")
async def list_models():
    """List available LLM models and prompt templates."""
    engine = get_ai_engine()
    
    return {
        "llm_providers": [p.value for p in engine.llm_client.providers],
        "prompt_templates": engine.prompt_manager.get_available_types(),
        "prompt_version": engine.prompt_manager.VERSION
    }

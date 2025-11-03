# backend/api/infer.py
"""
Inference router: accept prompts and route them to the configured model provider.
Endpoint: POST /v1/infer
"""

from typing import Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.core.logging import logger
from backend.engine.router import route_inference

router = APIRouter(tags=["inference"])


class InferRequest(BaseModel):
    """
    Request model for inference endpoint.
    - prompt: user prompt or instruction
    - provider: which model provider to use (ollama | openai)
    - max_tokens: optional token cap for provider (provider-dependent)
    """
    prompt: str = Field(..., min_length=1, description="The user prompt")
    provider: Literal["ollama", "openai"] = Field(
        "ollama", description="Provider to use for inference"
    )
    max_tokens: Optional[int] = Field(512, description="Max tokens for model response")


class InferResponse(BaseModel):
    provider: str
    response: str
    metadata: dict = {}


@router.post("/infer", response_model=InferResponse)
async def infer(req: InferRequest):
    """
    Main inference endpoint.
    Delegates heavy lifting to backend.engine.router.route_inference.
    """
    logger.info("Received inference request", prompt=req.prompt[:80], provider=req.provider)
    try:
        text = await route_inference(prompt=req.prompt, provider=req.provider, max_tokens=req.max_tokens)
    except HTTPException:
        # re-raise FastAPI HTTP exceptions
        raise
    except Exception as e:
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

    # Response metadata can be extended (latency, provider confidence, request id)
    return InferResponse(provider=req.provider, response=text, metadata={"length": len(text)})

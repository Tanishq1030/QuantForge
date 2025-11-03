# backend/engine/router.py
"""
Model router — lightweight abstraction to send prompts to different providers.

Current providers implemented:
 - Ollama (expected local REST endpoint: http://127.0.0.1:11434/api/generate)
 - OpenAI (cloud via Chat Completions)

The functions are async and return the final text string produced by the provider.
"""

from typing import Optional
import httpx
import json
import asyncio

from backend.core.config import settings
from backend.core.logging import logger
from fastapi import HTTPException


# ---------- Ollama (local) ----------
async def infer_ollama(prompt: str, max_tokens: int = 512, timeout: int = 30) -> str:
    """
    Calls a local Ollama / similar local REST LLM server.
    Expects an endpoint: POST http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate
    The payload shape depends on the local server; this implementation uses a flexible shape.
    """
    url = f"{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}/api/generate"
    payload = {
        "model": "mistral-7b-instruct",  # adjust if different locally
        "prompt": prompt,
        "max_tokens": max_tokens,
        # add other provider-specific params if needed (temperature, top_p, etc.)
        "temperature": 0.7,
    }

    logger.debug("Calling Ollama", url=url, truncate_prompt=prompt[:120])
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # expected shape depends on Ollama server; try to adapt common patterns:
            # - return data["response"] or data["choices"][0]["text"]
            if isinstance(data, dict):
                if "response" in data:
                    return data["response"]
                if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                    # common pattern
                    first = data["choices"][0]
                    return first.get("text") or first.get("message") or json.dumps(first)
            # fallback: return raw text
            return str(data)
    except httpx.HTTPStatusError as exc:
        logger.error("Ollama returned non-2xx", status=exc.response.status_code, body=exc.response.text)
        raise HTTPException(status_code=502, detail="Local model error")
    except Exception as e:
        logger.exception("Ollama inference failed")
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")


# ---------- OpenAI (cloud) ----------
async def infer_openai(prompt: str, max_tokens: int = 512, timeout: int = 30) -> str:
    """
    Calls OpenAI Chat Completions API as a fallback or for heavy reasoning.
    Requires settings.OPENAI_API_KEY to be set.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",  # change as needed; fallback to gpt-4o-mini or gpt-4
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    logger.debug("Calling OpenAI", url=url)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            j = resp.json()
            # Standard chat completion structure
            choices = j.get("choices") or []
            if choices:
                first = choices[0]
                # Chat completion variant
                if "message" in first:
                    return first["message"].get("content", "")
                # older or other variants
                if "text" in first:
                    return first["text"]
            # fallback: return entire response
            return json.dumps(j)
    except httpx.HTTPStatusError as exc:
        logger.error("OpenAI returned non-2xx", status=exc.response.status_code, body=exc.response.text)
        raise HTTPException(status_code=502, detail="OpenAI API returned error")
    except Exception as e:
        logger.exception("OpenAI inference failed")
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")


# ---------- Router (chooses provider) ----------
async def route_inference(prompt: str, provider: str = "ollama", max_tokens: int = 512) -> str:
    """
    Top-level router that decides which provider to call.
    Strategy:
     - If provider explicitly requested, call it.
     - If provider == 'ollama' but local service is down, fall back to OpenAI (if configured).
    """
    provider = provider.lower().strip()
    logger.debug("Routing inference", provider=provider)

    if provider == "ollama":
        # try local ollama, fallback to openai if configured
        try:
            return await infer_ollama(prompt=prompt, max_tokens=max_tokens)
        except HTTPException as e:
            # if OpenAI configured, fallback, otherwise re-raise
            logger.warning("Ollama failed, attempting OpenAI fallback", reason=str(e.detail))
            if settings.OPENAI_API_KEY:
                return await infer_openai(prompt=prompt, max_tokens=max_tokens)
            raise

    if provider == "openai":
        return await infer_openai(prompt=prompt, max_tokens=max_tokens)

    # Unknown provider
    raise HTTPException(status_code=400, detail=f"Unknown provider '{provider}'")

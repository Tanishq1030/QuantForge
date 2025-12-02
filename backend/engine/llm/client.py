# backend/engine/llm/client.py
"""
Multi-Provider LLM Client with Fallback Chain

Priority Order:
1. Hugging Face Inference (FREE - 30k chars/day)
2. OpenAI (PAID - fallback)
3. Ollama (LOCAL - last resort)
"""

import httpx
import json
from typing import Dict, Any, Optional, List
from enum import Enum

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.utils.retry import async_retry

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    OLLAMA = "ollama"


class LLMClient:
    """Unified LLM client with multi-provider fallback."""
    
    def __init__(self):
        self.timeout = 30
        self.providers = self._check_available_providers()
        logger.info(f"Available LLM providers: {[p.value for p in self.providers]}")
    
    def _check_available_providers(self) -> List[LLMProvider]:
        available = []
        if settings.HF_API_KEY:
            available.append(LLMProvider.HUGGINGFACE)
        if settings.OPENAI_API_KEY:
            available.append(LLMProvider.OPENAI)
        available.append(LLMProvider.OLLAMA)
        return available
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate text using best available provider."""
        last_error = None
        
        for provider in self.providers:
            try:
                logger.info(f"Attempting generation with {provider.value}")
                
                if provider == LLMProvider.HUGGINGFACE:
                    result = await self._generate_huggingface(prompt, max_tokens, temperature, system_message)
                elif provider == LLMProvider.OPENAI:
                    result = await self._generate_openai(prompt, max_tokens, temperature, system_message)
                elif provider == LLMProvider.OLLAMA:
                    result = await self._generate_ollama(prompt, max_tokens, temperature, system_message)
                
                logger.info(f"✅ Success with {provider.value}")
                result["provider"] = provider.value
                return result
                
            except Exception as e:
                logger.warning(f"Failed with {provider.value}: {e}")
                last_error = e
                continue
        
        raise Exception(f"All LLM providers failed. Last error: {last_error}")
    
    @async_retry(max_attempts=2, delay=1.0, exceptions=(httpx.HTTPError,))
    async def _generate_huggingface(
        self, prompt: str, max_tokens: int, temperature: float, system_message: Optional[str]
    ) -> Dict[str, Any]:
        """Generate using Hugging Face Inference API (FREE)."""
        
        full_prompt = f"{system_message}\n\n{prompt}" if system_message else prompt
        
        url = f"{settings.HF_LLM_ENDPOINT}/{settings.HF_LLM_MODEL}"
        headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "return_full_text": False
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # HF returns list of generated texts
            if isinstance(data, list) and len(data) > 0:
                text = data[0].get("generated_text", "")
            else:
                text = data.get("generated_text", "")
            
            return {
                "text": text.strip(),
                "model": settings.HF_LLM_MODEL,
                "tokens_used": len(text.split())  # Approximate
            }
    
    @async_retry(max_attempts=2, delay=1.0, exceptions=(httpx.HTTPError,))
    async def _generate_openai(
        self, prompt: str, max_tokens: int, temperature: float, system_message: Optional[str]
    ) -> Dict[str, Any]:
        """Generate using OpenAI API (PAID fallback)."""
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "text": data["choices"][0]["message"]["content"].strip(),
                "model": settings.OPENAI_MODEL,
                "tokens_used": data["usage"]["total_tokens"]
            }
    
    async def _generate_ollama(
        self, prompt: str, max_tokens: int, temperature: float, system_message: Optional[str]
    ) -> Dict[str, Any]:
        """Generate using Ollama (LOCAL fallback)."""
        
        url = f"{settings.OLLAMA_URL}/api/generate"
        
        # Combine system message with prompt
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\nUser: {prompt}\nAssistant:"
        
        payload = {
            "model": settings.OLLAMA_LLM_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=60) as client:  # Longer timeout for local
            headers = {"Content-Type": "application/json"}
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "text": data["response"].strip(),
                "model": settings.OLLAMA_LLM_MODEL,
                "tokens_used": data.get("eval_count", len(data["response"].split()))
            }


# Singleton instance
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

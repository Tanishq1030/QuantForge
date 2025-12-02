# backend/engine/llm/__init__.py
"""
LLM Engine Module

Provides unified interface to multiple LLM providers:
- Hugging Face Inference (free tier)
- OpenAI (paid fallback)
- Ollama (local fallback)
"""

from .client import LLMClient
from .prompts import PromptManager

__all__ = ["LLMClient", "PromptManager"]

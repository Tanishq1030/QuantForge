# Test LLM Client Config
"""Check if config settings are correct"""

from backend.core.config import settings

print("🔍 Checking LLM Config...")
print(f"OLLAMA_URL: {settings.OLLAMA_URL}")
print(f"OLLAMA_LLM_MODEL: {settings.OLLAMA_LLM_MODEL}")
print(f"HF_API_KEY present: {bool(settings.HF_API_KEY)}")
print(f"OPENAI_API_KEY present: {bool(settings.OPENAI_API_KEY)}")

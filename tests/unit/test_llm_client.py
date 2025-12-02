# tests/unit/test_llm_client.py
"""
Unit tests for LLM Client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.engine.llm.client import LLMClient, LLMProvider


class TestLLMClient:
    """Test suite for LLM Client"""
    
    def test_check_available_providers_with_hf(self):
        """Test provider detection when HF key exists"""
        client = LLMClient()
        assert LLMProvider.HUGGINGFACE in client.providers or LLMProvider.OLLAMA in client.providers
    
    @pytest.mark.asyncio
    async def test_generate_basic(self):
        """Test basic generation (will use configured provider)"""
        client = LLMClient()
        
        # Simple test prompt
        result = await client.generate(
            prompt="Say 'Hello' in one word",
            max_tokens=10,
            temperature=0.1
        )
        
        # Check response structure
        assert "text" in result
        assert "provider" in result
        assert "model" in result
        assert "tokens_used" in result
        
        # Should have some text
        assert len(result["text"]) > 0
        
        print(f"\n✅ LLM Response: {result['text']}")
        print(f"✅ Provider: {result['provider']}")
        print(f"✅ Model: {result['model']}")


if __name__ == "__main__":
    import asyncio
    
    print("=" * 60)
    print("🧪 Testing LLM Client")
    print("=" * 60)
    
    async def run_test():
        client = LLMClient()
        print(f"\n📋 Available providers: {[p.value for p in client.providers]}")
        
        # Test generation
        print("\n🔄 Testing generation...")
        try:
            result = await client.generate(
                prompt="Explain what 'bullish' means in one sentence",
                max_tokens=50
            )
            
            print(f"\n✅ Success!")
            print(f"Provider: {result['provider']}")
            print(f"Model: {result['model']}")
            print(f"Response: {result['text']}")
            print(f"Tokens: {result['tokens_used']}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    asyncio.run(run_test())

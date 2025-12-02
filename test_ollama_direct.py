# Quick Ollama Debug Script
"""
Test direct httpx connection to Ollama API
Compare with working Postman request
"""

import asyncio
import httpx
import json

async def test_ollama_direct():
    """Test direct connection to Ollama API"""
    
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "mistral:latest",
        "prompt": "Say hello in one sentence",
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Ollama API...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            print("\n📡 Sending request...")
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"\n✅ Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n🎉 Success!")
                print(f"Response: {data.get('response', '')[:100]}...")
                print(f"Model: {data.get('model')}")
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(f"Body: {response.text}")
                
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_direct())

# Create test data for AI analysis
"""
Insert test news articles directly into Weaviate
to test comprehensive AI analysis with real data
"""

import asyncio
from datetime import datetime, timedelta
from backend.engine.memory.vector_store import QuantForgeVectorStore
from backend.engine.embeddings.hybrid_embedder import HybridEmbedder

async def create_test_data():
    """Insert test news articles for AAPL"""
    
    # Test articles about Apple
    test_articles = [
        {
            "title": "Apple (AAPL) Reports Strong Q4 Earnings Beat",
            "content": "Apple Inc reported quarterly earnings that beat Wall Street expectations, driven by strong iPhone 15 sales and growing services revenue. Revenue increased 12% year-over-year to $95 billion, with iPhone sales up significantly in key markets.",
            "source": "Reuters",
            "ticker": "AAPL",
            "category": "earnings",
            "timestamp": datetime.utcnow() - timedelta(days=2)
        },
        {
            "title": "Apple Services Revenue Accelerates, Analyst Upgrade",
            "content": "Morgan Stanley upgraded Apple to 'overweight' citing accelerating services growth. The analyst noted that App Store, iCloud, and subscription services now represent 25% of total revenue with higher margins than hardware.",
            "source": "MarketWatch",
            "ticker": "AAPL", 
            "category": "analyst",
            "timestamp": datetime.utcnow() - timedelta(days=1)
        },
        {
            "title": "Apple Vision Pro Sales Exceed Expectations in First Month",
            "content": "Apple's new Vision Pro headset has sold over 200,000 units in its first month, exceeding analyst expectations. The strong launch suggests consumer appetite for premium AR/VR devices and validates Apple's entry into spatial computing.",
            "source": "TechCrunch",
            "ticker": "AAPL",
            "category": "product",
            "timestamp": datetime.utcnow()
        }
    ]
    
    print("🔧 Initializing services...")
    embedder = HybridEmbedder()
    vector_store = QuantForgeVectorStore()
    
    # Prepare documents
    docs = []
    texts = []
    
    for article in test_articles:
        text = f"{article['title']}. {article['content']}"
        texts.append(text)
        
        docs.append({
            "content": text,
            "title": article["title"],
            "source": article["source"],
            "ticker": article["ticker"],
            "category": article["category"],
            "timestamp": article["timestamp"].isoformat(),
            "metadata": {}
        })
    
    print(f"\n📄 Embedding {len(texts)} articles...")
    vectors = await embedder.embed_texts(texts)
    
    print(f"✅ Generated {len(vectors)} embeddings")
    print(f"   Vector dimension: {len(vectors[0])}")
    
    print(f"\n💾 Inserting into Weaviate...")
    result = await vector_store.ingest(
        documents=docs,
        collection_name="FinancialInsight"
    )
    
    print(f"\n🎉 Success!")
    print(f"   Ingested: {result.get('ingested', 0)} articles")
    print(f"   Collection: FinancialInsight")
    print(f"   Ticker: AAPL")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(create_test_data())
    
    print("\n" + "="*60)
    print("✅ Test data created!")
    print("="*60)
    print("\nNow test the AI endpoint:")
    print("POST http://localhost:8000/v1/ai/analyze")
    print('{"ticker": "AAPL", "analysis_type": "comprehensive"}')

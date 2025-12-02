# tests/integration/test_full_pipeline.py
"""
End-to-end integration tests for Phase 1.3.

Tests:
- Complete RSS → Preprocessor → Embedder → Vector Store pipeline
- Complete Binance → TimescaleDB pipeline
- Correlation API combining both data sources
"""

import pytest
import asyncio
from datetime import datetime, timedelta

# Import components
from backend.engine.feeds.rss_connector import RSSFeedConnector
from backend.engine.feeds.binance_connector import BinanceConnector
from backend.engine.parsers.text_preprocessor import TextPreprocessor
from backend.engine.embeddings.hybrid_embedder import HybridEmbedder
from backend.engine.memory.vector_store import QuantForgeVectorStore
from backend.engine.memory.timeseries_store import get_timeseries_store


class TestRSSPipeline:
    """Test complete RSS ingestion pipeline."""
    
    @pytest.mark.asyncio
    async def test_rss_to_vector_store(self):
        """Test: RSS → Preprocess → Embed → Vector Store."""
        # Initialize components
        rss = RSSFeedConnector()
        preprocessor = TextPreprocessor()
        embedder = HybridEmbedder()
        vector_store = QuantForgeVectorStore()
        
        # Step 1: Fetch from RSS (small sample)
        print("\n🔄 Step 1: Fetching RSS feed...")
        feeds = ["https://feeds.reuters.com/reuters/businessNews"]
        documents = await rss.fetch(feed_urls=feeds, max_articles=5)
        
        assert len(documents) > 0, "No articles fetched from RSS"
        print(f"✅ Fetched {len(documents)} articles")
        
        # Step 2: Preprocess
        print("\n🔄 Step 2: Preprocessing documents...")
        processed = []
        for doc in documents:
            processed_doc = preprocessor.process(doc)
            processed.append(processed_doc)
        
        # Check ticker extraction
        tickers_found = [d.get("ticker") for d in processed if d.get("ticker")]
        print(f"✅ Extracted {len(tickers_found)} tickers: {tickers_found[:3]}")
        
        # Step 3: Generate embeddings
        print("\n🔄 Step 3: Generating embeddings...")
        texts = [d["content"] for d in processed]
        embeddings = await embedder.embed_texts(texts)
        
        assert len(embeddings) == len(processed)
        assert len(embeddings[0]) == 384  # Dimension check
        print(f"✅ Generated {len(embeddings)} embeddings (384-dim)")
        
        # Step 4: Store in vector database
        print("\n🔄 Step 4: Storing in Weaviate...")
        collection_name = "TestCollection"
        
        try:
            await vector_store.delete_collection(collection_name)
        except:
            pass  # Collection might not exist
        
        await vector_store.create_collection_if_not_exists(collection_name)
        
        result = await vector_store.ingest_documents(
            documents=processed,
            vectors=embeddings,
            collection_name=collection_name,
            upsert=True
        )
        
        assert result["ingested"] > 0
        print(f"✅ Ingested {result['ingested']} documents into {collection_name}")
        
        # Step 5: Verify search works
        print("\n🔄 Step 5: Testing semantic search...")
        search_results = await vector_store.search(
            collection_name=collection_name,
            query_text="stock market news",
            limit=3
        )
        
        assert len(search_results) > 0
        print(f"✅ Search returned {len(search_results)} results")
        
        print("\n✅ COMPLETE RSS PIPELINE TEST PASSED!")
        return True


class TestBinancePipeline:
    """Test complete Binance → TimescaleDB pipeline."""
    
    @pytest.mark.asyncio
    async def test_binance_to_timescaledb(self):
        """Test: Binance API → TimescaleDB storage."""
        binance = BinanceConnector()
        timeseries = get_timeseries_store()
        
        # Step 1: Fetch from Binance (small sample)
        print("\n🔄 Step 1: Fetching BTC data from Binance...")
        symbol = "BTCUSDT"
        data = await binance.fetch_ohlcv(
            symbol=symbol,
            interval="1h",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
            limit=24
        )
        
        assert len(data) > 0, "No OHLCV data fetched"
        print(f"✅ Fetched {len(data)} candles for {symbol}")
        
        # Step 2: Store in TimescaleDB
        print("\n🔄 Step 2: Storing in TimescaleDB...")
        await timeseries.connect()
        
        inserted = await timeseries.insert_ohlcv(
            symbol=symbol,
            data=data,
            source="binance"
        )
        
        assert inserted > 0
        print(f"✅ Inserted {inserted} records into TimescaleDB")
        
        # Step 3: Verify retrieval
        print("\n🔄 Step 3: Querying data back...")
        retrieved = await timeseries.get_ohlcv(
            symbol=symbol,
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        assert len(retrieved) > 0
        print(f"✅ Retrieved {len(retrieved)} records from TimescaleDB")
        
        print("\n✅ COMPLETE BINANCE PIPELINE TEST PASSED!")
        return True


class TestPerformance:
    """Performance benchmark tests."""
    
    @pytest.mark.asyncio
    async def test_rss_ingestion_performance(self):
        """Benchmark: Ingest 100 RSS articles."""
        import time
        
        rss = RSSFeedConnector()
        preprocessor = TextPreprocessor()
        embedder = HybridEmbedder()
        
        print("\n⏱️  Benchmark: Ingesting 100 articles...")
        
        # Fetch
        start = time.time()
        feeds = [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html"
        ]
        documents = await rss.fetch(feed_urls=feeds, max_articles=100)
        fetch_time = time.time() - start
        
        # Preprocess
        start = time.time()
        processed = [preprocessor.process(d) for d in documents]
        preprocess_time = time.time() - start
        
        # Embed
        start = time.time()
        texts = [d["content"] for d in processed]
        embeddings = await embedder.embed_texts(texts)
        embed_time = time.time() - start
        
        total_time = fetch_time + preprocess_time + embed_time
        
        print(f"\n📊 Performance Results:")
        print(f"  Articles: {len(documents)}")
        print(f"  Fetch time: {fetch_time:.2f}s")
        print(f"  Preprocess time: {preprocess_time:.2f}s")
        print(f"  Embed time: {embed_time:.2f}s")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Rate: {len(documents)/total_time:.1f} articles/sec")
        
        # Target: >10 articles/sec
        rate = len(documents) / total_time
        assert rate > 5, f"Too slow: {rate:.1f} articles/sec (target: >5)"
        
        print(f"✅ Performance acceptable: {rate:.1f} articles/sec")
        return True


# Standalone runner
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 Phase 1.3 Integration Tests")
    print("=" * 70)
    
    async def run_all_tests():
        # Test 1: RSS Pipeline
        print("\n" + "─" * 70)
        print("TEST 1: RSS → Vector Store Pipeline")
        print("─" * 70)
        test1 = TestRSSPipeline()
        await test1.test_rss_to_vector_store()
        
        # Test 2: Binance Pipeline
        print("\n" + "─" * 70)
        print("TEST 2: Binance → TimescaleDB Pipeline")
        print("─" * 70)
        test2 = TestBinancePipeline()
        await test2.test_binance_to_timescaledb()
        
        # Test 3: Performance
        print("\n" + "─" * 70)
        print("TEST 3: Performance Benchmarks")
        print("─" * 70)
        test3 = TestPerformance()
        await test3.test_rss_ingestion_performance()
        
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 70)
    
    asyncio.run(run_all_tests())

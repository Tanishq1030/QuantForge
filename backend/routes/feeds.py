# backend/routes/feeds.py
"""
Data feed ingestion API endpoints.

Provides endpoints for:
- RSS feed ingestion
- Binance market data sync (Phase 1.3 Day 3-4)
- Feed status monitoring
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.engine.feeds import RSSFeedConnector
from backend.engine.parsers import TextPreprocessor
from backend.engine.embeddings import HybridEmbedder
from backend.engine.memory.vector_store import QuantForgeVectorStore
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/feeds", tags=["Data Feeds"])

# Singleton instances
rss_connector = RSSFeedConnector()
preprocessor = TextPreprocessor()
embedder = HybridEmbedder()
vector_store = QuantForgeVectorStore()


# === Pydantic Schemas ===

class RSSIngestRequest(BaseModel):
    """Request for RSS feed ingestion"""
    feed_urls: List[str] = Field(..., description="List of RSS feed URLs to ingest")
    collection_name: str = Field(default="FinancialInsight", description="Target collection")
    max_articles: Optional[int] = Field(None, description="Max articles to fetch per feed")


class RSSIngestResponse(BaseModel):
    """Response from RSS ingestion"""
    success: bool
    fetched_count: int
    ingested_count: int
    failed_count: int
    tickers_extracted: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


# === API Endpoints ===

@router.post("/rss/ingest", response_model=RSSIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_rss_feeds(request: RSSIngestRequest):
    """
    Ingest financial news from RSS feeds.
    
    Pipeline:
    1. Fetch articles from RSS feeds
    2. Preprocess (extract tickers, clean text)
    3. Generate embeddings
    4. Store in vector database
    
    Example:
        ```json
        {
            "feed_urls": [
                "https://feeds.reuters.com/reuters/businessNews",
                "https://feeds.bloomberg.com/markets/news.rss"
            ],
            "collection_name": "FinancialInsight",
            "max_articles": 50
        }
        ```
    """
    try:
        # Step 1: Fetch from RSS feeds
        logger.info(f"Fetching from {len(request.feed_urls)} RSS feeds")
        raw_documents = await rss_connector.fetch(
            feed_urls=request.feed_urls,
            max_articles=request.max_articles
        )
        
        if not raw_documents:
            return RSSIngestResponse(
                success=True,
                fetched_count=0,
                ingested_count=0,
                failed_count=0,
                errors=["No articles fetched from feeds"]
            )
        
        logger.info(f"Fetched {len(raw_documents)} raw documents")
        
        # Step 2: Preprocess documents
        processed_documents = []
        all_tickers = set()
        
        for doc in raw_documents:
            try:
                processed_doc = preprocessor.process(doc)
                processed_documents.append(processed_doc)
                
                # Collect tickers
                if processed_doc.get("ticker"):
                    all_tickers.add(processed_doc["ticker"])
                    
            except Exception as e:
                logger.error(f"Failed to preprocess document: {e}")
                continue
        
        logger.info(f"Preprocessed {len(processed_documents)} documents, extracted {len(all_tickers)} tickers")
        
        # Step 3: Generate embeddings
        texts = [doc["content"] for doc in processed_documents]
        embeddings = await embedder.embed_texts(texts)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Step 4: Ingest into vector store
        await vector_store.create_collection_if_not_exists(request.collection_name)
        
        result = await vector_store.ingest_documents(
            documents=processed_documents,
            vectors=embeddings,
            collection_name=request.collection_name,
            upsert=True
        )
        
        return RSSIngestResponse(
            success=True,
            fetched_count=len(raw_documents),
            ingested_count=result["ingested"],
            failed_count=result["failed"],
            tickers_extracted=sorted(list(all_tickers)),
            errors=result.get("errors", [])
        )
        
    except Exception as e:
        logger.error(f"RSS ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RSS ingestion failed: {str(e)}"
        )


@router.get("/status")
async def get_feed_status():
    """
    Get status of all feed connectors.
    
    Returns health check for:
    - RSS connector
    - Binance connector (Phase 1.3 Day 3-4)
    """
    rss_healthy = await rss_connector.validate_connection()
    
    return {
        "connectors": {
            "rss": {
                "healthy": rss_healthy,
                "source": rss_connector.source_name
            }
        }
    }

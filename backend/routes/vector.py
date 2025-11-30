# backend/routes/vector.py
import time
from typing import List
from fastapi import APIRouter, HTTPException, status
from backend.db.schemas import (
    VectorIngestRequest, VectorIngestResponse,
    VectorSearchRequest, VectorSearchResponse, VectorSearchResult
)
from backend.engine.memory.vector_store import QuantForgeVectorStore
from backend.core.logging import get_logger
from backend.engine.embeddings import HybridEmbedder

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/vector", tags=["Vector Store"])

# Singleton instances
vector_store = QuantForgeVectorStore()
embedder = HybridEmbedder()

@router.post("/ingest", response_model=VectorIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_vectors(request: VectorIngestRequest):
    """
    Ingest documents into vector store with embeddings.
    Uses HybridEmbedder to generate real semantic embeddings.
    """
    try:
        # Ensure collection exists
        await vector_store.create_collection_if_not_exists(request.collection_name)

        # Generate real embeddings using HybridEmbedder
        logger.info(f"Generating embeddings for {len(request.documents)} documents")
        texts = [doc.content for doc in request.documents]
        vectors = await embedder.embed_texts(texts)
        logger.info(f"Generated {len(vectors)} embeddings successfully")

        docs = [doc.model_dump() for doc in request.documents]

        result = await vector_store.ingest_documents(
            documents=docs,
            vectors=vectors,
            collection_name=request.collection_name,
            upsert=request.upsert
        )

        return VectorIngestResponse(
            success=True,
            ingested_count=result.get("ingested", 0),
            updated_count=result.get("updated", 0),
            failed_count=result.get("failed", 0),
            errors=result.get("errors", []),
        )

    except Exception as e:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Vector ingestion failed: {str(e)}")


@router.post("/search", response_model=VectorSearchResponse)
async def search_vectors(request: VectorSearchRequest):
    """
    Semantic search across vector store using real embeddings.
    """
    try:
        start = time.time()

        # Generate real query embedding using HybridEmbedder
        logger.info(f"Generating query embedding for: '{request.query}'")
        query_vector = await embedder.embed_text(request.query)
        logger.info(f"Query embedding generated successfully (dim={len(query_vector)})")

        max_distance = 1.0 - request.min_confidence

        raw_results = await vector_store.search(
            query_vector=query_vector,
            limit=request.limit,
            collection_name=request.collection_name,
            filters=request.filters,
            min_distance=max_distance
        )

        results = [
            VectorSearchResult(
                content=r["content"],
                metadata=r["metadata"],
                distance=r["distance"] or 0.0,
                confidence=r["confidence"] or 0.0
            )
            for r in raw_results
        ]

        return VectorSearchResponse(
            success=True,
            query=request.query,
            results=results,
            total_results=len(results),
            execution_time_ms=round((time.time() - start) * 1000, 2)
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")


@router.delete("/collection/{collection_name}")
async def delete_collection(collection_name: str):
    """
    Delete a collection from Weaviate.
    Useful when changing vector dimensions or resetting data.
    """
    try:
        await vector_store.delete_collection(collection_name)
        return {"success": True, "message": f"Collection '{collection_name}' deleted successfully"}
    except Exception as e:
        logger.error(f"Delete collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")

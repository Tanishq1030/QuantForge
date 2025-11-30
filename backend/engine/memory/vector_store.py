# backend/engine/memory/vector_store.py
import time
import logging
from typing import List, Dict, Any, Optional
import anyio

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

# Weaviate v4 client (preferred)
try:
    import weaviate
    from weaviate.exceptions import WeaviateStartUpError
except Exception:
    weaviate = None  # we'll handle errors gracefully

class QuantForgeVectorStore:
    """
    Async-friendly wrapper around Weaviate v4 client.
    Uses manual-vector mode: we push vectors with each object explicitly.
    """

    def __init__(self):
        self.client = None
        if not weaviate:
            logger.error("weaviate library not installed. Vector store disabled.")
            return

        url = getattr(settings, "WEAVIATE_URL", None) or getattr(settings, "WEAVIATE_ENDPOINT", None) or ""
        api_key = getattr(settings, "WEAVIATE_API_KEY", None) or None

        if not url:
            logger.warning("WEAVIATE_URL/WEAVIATE_ENDPOINT empty in settings — vector store will be unavailable.")
            return

        # Ensure URL has https:// prefix
        if not url.startswith("http"):
            url = f"https://{url}"

        try:
            # Build client; include API key header if provided
            # skip_init_checks=True to avoid gRPC health check timeout on slow connections
            if api_key:
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=url,
                    auth_credentials=weaviate.auth.AuthApiKey(api_key=api_key),
                    skip_init_checks=True
                )
            else:
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=url,
                    skip_init_checks=True
                )
            
            logger.info("✅ Connected to Weaviate Cloud instance successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Weaviate client: {e}")
            self.client = None

    # Utility: run a blocking function in threadpool
    async def _run(self, func, *a, **kw):
        return await anyio.to_thread.run_sync(lambda: func(*a, **kw))

    async def create_collection_if_not_exists(self, collection_name: str = "FinancialInsight"):
        """Create Weaviate collection (class) with a minimal financial schema.
           Runs in threadpool because weaviate client is blocking.
           Note: Weaviate v4 automatically handles vector dimensions, no need to specify.
        """
        if not self.client:
            raise RuntimeError("Weaviate client not configured")

        # Check existence
        def _create():
            try:
                # Check if collection exists
                if self.client.collections.exists(collection_name):
                    logger.info(f"ℹ️ '{collection_name}' collection already exists.")
                    return False

                # Create using manual vector mode (vectorizer_config=None)
                # Weaviate v4 auto-detects vector dimensions from first insert
                from weaviate.classes.config import Property, DataType

                self.client.collections.create(
                    name=collection_name,
                    vectorizer_config=None,  # manual vectors
                    properties=[
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="source", data_type=DataType.TEXT),
                        Property(name="ticker", data_type=DataType.TEXT),
                        Property(name="category", data_type=DataType.TEXT),
                        Property(name="timestamp", data_type=DataType.DATE),
                        Property(name="metadata", data_type=DataType.TEXT),  # Store as JSON string
                    ],
                )
                logger.info(f"✅ Created collection: {collection_name}")
                return True
            except Exception as e:
                logger.error(f"Error creating collection: {e}")
                raise

        return await self._run(_create)
    
    async def delete_collection(self, collection_name: str):
        """Delete a Weaviate collection"""
        if not self.client:
            raise RuntimeError("Weaviate client not configured")
        
        def _delete():
            try:
                if self.client.collections.exists(collection_name):
                    self.client.collections.delete(collection_name)
                    logger.info(f"🗑️ Deleted collection: {collection_name}")
                    return True
                else:
                    logger.warning(f"Collection '{collection_name}' does not exist")
                    return False
            except Exception as e:
                logger.error(f"Error deleting collection: {e}")
                raise
        
        return await self._run(_delete)

    async def ingest_documents(
        self,
        documents: List[Dict[str, Any]],
        vectors: List[List[float]],
        collection_name: str = "FinancialInsight",
        upsert: bool = True
    ) -> Dict[str, int]:
        """Batch insert/update documents with explicit vectors (manual vector mode)."""

        if not self.client:
            raise RuntimeError("Weaviate client not configured")

        if len(documents) != len(vectors):
            raise ValueError("documents and vectors must be same length")

        def _ingest():
            import json
            ingested = 0
            updated = 0
            failed = 0
            errors = []

            try:
                coll = self.client.collections.get(collection_name)
            except Exception as e:
                raise RuntimeError(f"Collection {collection_name} not found: {e}")

            for doc, vec in zip(documents, vectors):
                try:
                    # If doc already has an 'id' field use it; else create new
                    obj_id = doc.get("id")
                    
                    # Convert metadata dict to JSON string for TEXT field
                    metadata_str = json.dumps(doc.get("metadata", {}))
                    
                    properties = {
                        "content": doc.get("content"),
                        "source": doc.get("source"),
                        "ticker": doc.get("ticker"),
                        "category": doc.get("category"),
                        "timestamp": doc.get("timestamp"),
                        "metadata": metadata_str,  # Store as JSON string
                    }

                    # Insert object with explicit vector
                    coll.data.insert(properties=properties, vector=vec, uuid=obj_id)
                    ingested += 1
                except Exception as ee:
                    logger.error(f"Failed to ingest doc: {ee}")
                    errors.append(str(ee))
                    failed += 1

            return {"ingested": ingested, "updated": updated, "failed": failed, "errors": errors}

        return await self._run(_ingest)

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        collection_name: str = "FinancialInsight",
        filters: Optional[Dict[str, Any]] = None,
        min_distance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Semantic search with optional filters. Returns list of {content, metadata, distance, confidence}"""

        if not self.client:
            raise RuntimeError("Weaviate client not configured")

        def _search():
            import json
            try:
                coll = self.client.collections.get(collection_name)
            except Exception as e:
                raise RuntimeError(f"Collection {collection_name} not found: {e}")

            # Build "where" filter if filters provided
            from weaviate.classes.query import Filter
            where_filter = None
            if filters:
                # Build filters using Weaviate v4 Filter API
                filter_conditions = []
                for k, v in filters.items():
                    if v is not None:
                        filter_conditions.append(Filter.by_property(k).equal(str(v)))
                
                if len(filter_conditions) == 1:
                    where_filter = filter_conditions[0]
                elif len(filter_conditions) > 1:
                    where_filter = filter_conditions[0]
                    for condition in filter_conditions[1:]:
                        where_filter = where_filter & condition

            # Run near_vector query
            resp = coll.query.near_vector(
                near_vector=query_vector, 
                limit=limit,
                filters=where_filter
            )
            
            # resp.objects holds results
            results = []
            for item in resp.objects:
                # Get distance, default to 0.0 if None
                distance = getattr(item.metadata, 'distance', None)
                if distance is None:
                    distance = 0.0
                else:
                    distance = float(distance)
                
                # Skip if distance exceeds threshold
                if distance > min_distance:
                    continue
                
                # Calculate confidence (1.0 - distance)
                confidence = max(0.0, min(1.0, 1.0 - distance))
                
                # Parse metadata JSON string back to dict
                metadata_str = item.properties.get("metadata", "{}")
                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}
                except:
                    metadata = {}
                
                results.append({
                    "content": item.properties.get("content"),
                    "metadata": metadata,
                    "distance": distance,
                    "confidence": confidence
                })
            return results

        return await self._run(_search)

    def check_health(self) -> bool:
        """Simple health check."""
        try:
            return self.client.is_ready() if self.client else False
        except Exception:
            return False

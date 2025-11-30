"""
Hybrid Embedding Engine for QuantForge
Uses local sentence-transformers for embeddings (more reliable than API)
Supports Ollama as backup
"""

from typing import List, Union, Optional
import httpx
import asyncio
from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class HybridEmbedder:
    """
    Hybrid embedding engine with local and remote options.
    Primary: Local sentence-transformers
    Fallback: Ollama local embedding
    """
    
    def __init__(self):
        self.backend = settings.EMBEDDING_BACKEND
        self.ollama_url = f"{settings.OLLAMA_URL}/api/embeddings"
        self.model = None
        
        # Initialize local model if using HuggingFace
        if self.backend == "huggingface":
            try:
                from sentence_transformers import SentenceTransformer
                model_name = settings.HF_EMBEDDING_MODEL
                logger.info(f"Loading local model: {model_name}")
                self.model = SentenceTransformer(model_name)
                logger.info(f"✅ Model loaded successfully (dim={self.model.get_sentence_embedding_dimension()})")
            except Exception as e:
                logger.error(f"Failed to load local model: {e}")
                logger.warning("Falling back to Ollama if available")
                self.backend = "ollama"
        
        logger.info(f"HybridEmbedder initialized with backend: {self.backend}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if self.backend == "huggingface" and self.model:
            # Use local sentence-transformers model
            return await self._embed_local([text])
        
        elif self.backend == "ollama":
            return await self._embed_ollama([text])
        
        else:
            raise ValueError(f"No working embedding backend available")
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        if self.backend == "huggingface" and self.model:
            # Use local model for batch
            return await self._embed_local_batch(texts)
        
        elif self.backend == "ollama":
            return await self._embed_ollama_batch(texts)
        
        else:
            raise ValueError(f"No working embedding backend available")
    
    async def _embed_local(self, texts: List[str]) -> List[float]:
        """Use local sentence-transformers model for single text"""
        # Run in thread pool to avoid blocking
        def _encode():
            embedding = self.model.encode(texts[0], convert_to_numpy=True)
            return embedding.tolist()
        
        return await asyncio.to_thread(_encode)
    
    async def _embed_local_batch(self, texts: List[str]) -> List[List[float]]:
        """Use local sentence-transformers model for batch"""
        def _encode():
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return [emb.tolist() for emb in embeddings]
        
        return await asyncio.to_thread(_encode)
    
    async def _embed_ollama(self, texts: List[str]) -> List[float]:
        """Call Ollama API for single text"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.ollama_url,
                json={
                    "model": settings.OLLAMA_EMBED_MODEL,
                    "prompt": texts[0]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}")
                raise Exception(f"Ollama API returned {response.status_code}")
            
            result = response.json()
            return result.get("embedding", [])
    
    async def _embed_ollama_batch(self, texts: List[str]) -> List[List[float]]:
        """Call Ollama API for batch of texts"""
        embeddings = []
        for text in texts:
            embedding = await self._embed_ollama([text])
            embeddings.append(embedding)
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the current model.
        
        Returns:
            Embedding dimension (e.g., 384 for all-MiniLM-L6-v2)
        """
        model_dimensions = {
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/all-mpnet-base-v2": 768,
            "nomic-embed-text": 768,
        }
        
        if self.backend == "huggingface":
            return model_dimensions.get(self.hf_model, 384)
        elif self.backend == "ollama":
            return model_dimensions.get(settings.OLLAMA_EMBED_MODEL, 768)
        
        return 384  # Default


# Singleton instance
_embedder_instance: Optional[HybridEmbedder] = None

def get_embedder() -> HybridEmbedder:
    """Get or create the singleton HybridEmbedder instance"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = HybridEmbedder()
    return _embedder_instance

# backend/engine/feeds/base.py
"""
Base class for all data feed connectors.
Provides common interface and utilities.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.logging import get_logger

logger = get_logger(__name__)


class BaseFeedConnector(ABC):
    """
    Abstract base class for data feed connectors.
    All feed implementations should inherit from this.
    """
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        logger.info(f"Initialized {self.__class__.__name__} for source: {source_name}")
    
    @abstractmethod
    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch data from the source.
        
        Returns:
            List of documents with standardized schema:
            {
                "content": str,
                "title": str,
                "source": str,
                "url": str,
                "timestamp": datetime,
                "metadata": dict
            }
        """
        pass
    
    def normalize_document(
        self, 
        content: str, 
        title: Optional[str] = None,
        url: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        **metadata
    ) -> Dict[str, Any]:
        """
        Normalize a document to standard schema.
        """
        return {
            "content": content.strip(),
            "title": title or "",
            "source": self.source_name,
            "url": url or "",
            "timestamp": timestamp or datetime.utcnow(),
            "metadata": metadata
        }
    
    async def validate_connection(self) -> bool:
        """
        Check if connection to source is valid.
        Override if needed.
        """
        return True

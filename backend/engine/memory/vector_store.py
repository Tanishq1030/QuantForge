import weaviate
from weaviate.classes.init import Auth
from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class QuantForgeVectorStore:
    """Centralized Weaviate client for QuantForge AI Engine."""

    def __init__(self):
        try:
            # ✅ Correct initialization for Weaviate Python Client v4
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=f"https://{settings.WEAVIATE_ENDPOINT}",
                auth_credentials=Auth.api_key(settings.WEAVIATE_API_KEY),
            )

            if not self.client.is_connected():
                raise ConnectionError("Could not connect to Weaviate Cloud cluster")

            logger.info("✅ Connected to Weaviate Cloud instance successfully.")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Weaviate client: {e}")
            self.client = None

    def check_health(self) -> bool:
        """Simple health check."""
        try:
            return self.client.is_connected()
        except Exception:
            return False

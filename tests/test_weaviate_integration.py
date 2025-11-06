from backend.engine.memory.vector_store import QuantForgeVectorStore
from backend.core.logging import get_logger

logger = get_logger(__name__)

def test_connection():
    logger.info("🔍 Checking Weaviate connectivity...")
    client = QuantForgeVectorStore()

    if client.client and client.client.is_connected():
        logger.info("✅ Weaviate connection is active and healthy.")

        # Test creating a collection and adding a test object
        try:
            # Create a simple collection (idempotent in Weaviate v4)
            if not client.client.collections.exists("FinancialInsight"):
                client.client.collections.create("FinancialInsight")
                logger.info("🧠 Created 'FinancialInsight' collection in Weaviate.")
            else:
                logger.info("ℹ️ 'FinancialInsight' collection already exists.")

            # Insert a small test object
            collection = client.client.collections.get("FinancialInsight")
            collection.data.insert({"source": "test", "content": "finance intelligence"})
            logger.info("📥 Stored vector entry from source: test")

            # Run a quick query
            response = collection.query.near_text("finance intelligence", limit=1)
            logger.info(f"🔍 Query 'finance intelligence' returned {len(response.objects)} matches.")

        except Exception as e:
            logger.error(f"❌ Test failed during object operations: {e}")

        finally:
            client.client.close()
            logger.info("🔒 Connection to Weaviate closed properly.")

    else:
        logger.error("❌ Weaviate unreachable.")


if __name__ == "__main__":
    test_connection()

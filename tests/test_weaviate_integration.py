from backend.engine.memory.vector_store import QuantForgeVectorStore
from backend.core.logging import get_logger
import numpy as np
from weaviate.classes.config import Property, DataType

logger = get_logger(__name__)

def test_connection():
    logger.info("🔍 Checking Weaviate connectivity...")
    client = QuantForgeVectorStore()

    if client.client and client.client.is_connected():
        logger.info("✅ Weaviate connection is active and healthy.")

        try:
            # Create non-vectorized collection if it doesn’t exist
            if not client.client.collections.exists("FinancialInsight"):
                client.client.collections.create(
                    name="FinancialInsight",
                    properties=[
                        Property(name="source", data_type=DataType.TEXT),
                        Property(name="content", data_type=DataType.TEXT),
                    ],
                    vectorizer_config=None,
                )
                logger.info("🧠 Created 'FinancialInsight' collection (manual vector mode).")
            else:
                logger.info("ℹ️ 'FinancialInsight' collection already exists.")

            collection = client.client.collections.get("FinancialInsight")

            # Generate mock embedding (128-dim)
            mock_vector = np.random.rand(128).astype(float).tolist()
            logger.info(f"🧬 Generated mock embedding (len={len(mock_vector)})")

            # ✅ Insert custom vector and object (final version)
            collection.data.insert(
                properties={"source": "test", "content": "finance intelligence"},
                vector=mock_vector,
            )
            logger.info("📥 Inserted custom vectorized record into Weaviate.")

            # Query manually using the same vector
            response = collection.query.near_vector(near_vector=mock_vector, limit=1)
            logger.info(f"🔍 Retrieved {len(response.objects)} match(es) via manual vector query.")

        except Exception as e:
            logger.error(f"❌ Test failed during object operations: {e}")

        finally:
            client.client.close()
            logger.info("🔒 Connection to Weaviate closed properly.")

    else:
        logger.error("❌ Weaviate unreachable.")


if __name__ == "__main__":
    test_connection()

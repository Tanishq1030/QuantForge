import weaviate
from weaviate.classes.init import Auth
import os

def test_connection():
    url = "https://zkinymfnraynqe1c6vjftq.c0.asia-southeast1.gcp.weaviate.cloud"  # Replace this
    api_key = "RXdMZndOY2puOWN3bktYRl9FNjUycE5vOGxUM1FEVCtEdkYxZUZQQUwvM21ZY080Zmo4Sk5PUkZxRXJNPV92MjAw"  # Create one from Weaviate Cloud Console

    # Create client with API key auth
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=url,
        auth_credentials=Auth.api_key(api_key)
    )

    try:
        meta = client.get_meta()
        print("✅ Connected to Weaviate successfully!")
        print("Cluster info:", meta)
    except Exception as e:
        print("❌ Connection failed:", e)
    finally:
        client.close()

if __name__ == "__main__":
    test_connection()

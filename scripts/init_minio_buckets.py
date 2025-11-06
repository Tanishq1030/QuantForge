"""
scripts/init_minio_buckets.py
─────────────────────────────
Ensures all required MinIO buckets exist for QuantForge AI Engine.

Buckets:
    - datasets   : For storing raw & processed data
    - models     : For AI/ML model weights and checkpoints
    - logs       : For structured logs and audit traces
    - snapshots  : For generated charts, reports, and plots
"""

import os
from minio import Minio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch MinIO configuration from .env
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
USE_SSL = os.getenv("MINIO_USE_SSL", "False").lower() == "true"

# Initialize MinIO client
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=USE_SSL,
)

# Define QuantForge buckets
REQUIRED_BUCKETS = [
    "datasets",
    "models",
    "logs",
    "snapshots",
]


def ensure_buckets():
    """Check and create missing buckets."""
    try:
        existing = {b.name for b in client.list_buckets()}

        print("🔍 Checking MinIO buckets...")
        for bucket in REQUIRED_BUCKETS:
            if bucket not in existing:
                client.make_bucket(bucket)
                print(f"✅ Created bucket: {bucket}")
            else:
                print(f"ℹ️ Bucket already exists: {bucket}")

        print("\n🚀 All required buckets verified successfully.")

    except Exception as e:
        print(f"❌ Error while initializing buckets: {e}")


if __name__ == "__main__":
    ensure_buckets()

import os
import io
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
from backend.core.logging import get_logger

# Load environment variables
load_dotenv()
logger = get_logger(__name__)


class MinioClient:
    """
    QuantForge MinIO Utility Wrapper

    Provides high-level methods to interact with MinIO for uploading datasets,
    downloading models, managing logs, and general storage operations.

    The class automatically connects to the configured MinIO instance
    defined in the .env file.
    """

    def __init__(self):
        try:
            self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
            self.access_key = os.getenv("MINIO_ACCESS_KEY")
            self.secret_key = os.getenv("MINIO_SECRET_KEY")
            self.use_ssl = os.getenv("MINIO_USE_SSL", "False").lower() == "true"

            self.client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.use_ssl,
            )
            
            logger.info(f"✅ Connected to MinIO at {self.endpoint}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize MinIO client: {e}")
            raise

    # ------------------------------------------------------------
    # 🗂️ Bucket Utilities
    # ------------------------------------------------------------

    def ensure_bucket(self, bucket_name: str):
        """Ensure a bucket exists; create it if missing."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created missing bucket: {bucket_name}")
            else:
                logger.debug(f"Bucket '{bucket_name}' already exists.")
        except S3Error as e:
            logger.error(f"S3Error while ensuring bucket '{bucket_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error ensuring bucket '{bucket_name}': {e}")
            raise

    # ------------------------------------------------------------
    # 📤 Upload Methods
    # ------------------------------------------------------------

    def upload_file(self, bucket: str, object_name: str, file_path: str):
        """Upload a local file to a MinIO bucket."""
        try:
            self.ensure_bucket(bucket)
            self.client.fput_object(bucket, object_name, file_path)
            logger.info(f"📤 Uploaded '{file_path}' → {bucket}/{object_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Upload failed for {file_path}: {e}")
            return False

    def upload_bytes(self, bucket: str, object_name: str, data: bytes, content_type="application/octet-stream"):
        """Upload in-memory data as an object."""
        try:
            self.ensure_bucket(bucket)
            self.client.put_object(
                bucket,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            logger.info(f"📤 Uploaded bytes → {bucket}/{object_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Upload bytes failed for {object_name}: {e}")
            return False

    # ------------------------------------------------------------
    # 📥 Download Methods
    # ------------------------------------------------------------

    def download_file(self, bucket: str, object_name: str, dest_path: str):
        """Download an object from MinIO to a local file."""
        try:
            self.client.fget_object(bucket, object_name, dest_path)
            logger.info(f"📥 Downloaded '{object_name}' → {dest_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Download failed for {object_name}: {e}")
            return False

    def get_object_bytes(self, bucket: str, object_name: str):
        """Retrieve an object as bytes."""
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.debug(f"📦 Retrieved object bytes: {bucket}/{object_name}")
            return data
        except Exception as e:
            logger.error(f"❌ Failed to retrieve object {object_name}: {e}")
            return None

    # ------------------------------------------------------------
    # 🧹 Management Methods
    # ------------------------------------------------------------

    def list_objects(self, bucket: str):
        """List all objects inside a bucket."""
        try:
            objects = [obj.object_name for obj in self.client.list_objects(bucket)]
            logger.info(f"📋 Objects in '{bucket}': {objects}")
            return objects
        except Exception as e:
            logger.error(f"❌ Failed to list objects in {bucket}: {e}")
            return []

    def delete_object(self, bucket: str, object_name: str):
        """Delete a specific object from a bucket."""
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"🗑️ Deleted {object_name} from {bucket}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete {object_name}: {e}")
            return False

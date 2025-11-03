import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

# Load env vars
load_dotenv()

def test_minio_connection():
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=os.getenv("MINIO_ENDPOINT"),
            aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
            aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD"),
            region_name="us-east-1",
        )

        # Create bucket if not exists
        bucket_name = os.getenv("MINIO_BUCKET")
        existing_buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
        if bucket_name not in existing_buckets:
            s3.create_bucket(Bucket=bucket_name)
            print(f"🪣 Created new bucket: {bucket_name}")
        else:
            print(f"✅ Bucket already exists: {bucket_name}")

        # Test upload
        test_key = "test_upload.txt"
        s3.put_object(Bucket=bucket_name, Key=test_key, Body=b"QuantForge test file")
        print(f"📤 Uploaded {test_key} to {bucket_name}")

        # Test download
        obj = s3.get_object(Bucket=bucket_name, Key=test_key)
        data = obj["Body"].read().decode("utf-8")
        print(f"📥 Downloaded content: {data}")

        print("✅ MinIO connection successful and operational!")

    except NoCredentialsError:
        print("❌ Credentials not found. Check MINIO_ROOT_USER / MINIO_ROOT_PASSWORD.")
    except ClientError as e:
        print(f"❌ Client error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_minio_connection()

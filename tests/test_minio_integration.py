from backend.utils.minio_client import MinioClient

client = MinioClient()

# Upload a simple test file
with open("test.txt", "w") as f:
    f.write("QuantForge MinIO integration test")

client.upload_file("datasets", "test_upload.txt", "test.txt")
print(client.list_objects("datasets"))

# Download it back
client.download_file("datasets", "test_upload.txt", "downloaded_test.txt")
print(open("downloaded_test.txt").read())

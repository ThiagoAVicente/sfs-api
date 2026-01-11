"""Integration tests for MinIO client using testcontainers."""

import pytest
from testcontainers.core.container import DockerContainer


@pytest.fixture(scope="class")
def minio_container():
    """Start MinIO container for tests."""
    container = DockerContainer("minio/minio:latest")
    container.with_exposed_ports(9000)
    container.with_env("MINIO_ROOT_USER", "minioadmin")
    container.with_env("MINIO_ROOT_PASSWORD", "minioadmin")
    container.with_command("server /data")

    container.start()
    yield container
    container.stop()


@pytest.fixture(autouse=True)
def setup_minio_client(minio_container):
    """Setup MinIO client with testcontainer."""
    import os
    from src.clients.minio_client import MinIOClient, MinIOConfig

    # Reset singleton
    MinIOClient._client = None

    # Set env vars
    host = minio_container.get_container_host_ip()
    port = minio_container.get_exposed_port(9000)

    os.environ["MINIO_HOST"] = host
    os.environ["MINIO_PORT"] = str(port)
    os.environ["MINIO_ROOT_USER"] = "minioadmin"
    os.environ["MINIO_ROOT_PASSWORD"] = "minioadmin"
    os.environ["SFS_FILE_BUCKET"] = "test-bucket"
    os.environ["MINIO_SECURE"] = "false"

    # Force reload config
    MinIOClient.config = MinIOConfig.from_env()

    yield

    MinIOClient._client = None


@pytest.mark.integration
class TestMinIOClientIntegration:
    """Integration tests for MinIO client."""

    def test_ensure_bucket_exists_creates_new(self):
        """Test creating a new bucket."""
        from src.clients import MinIOClient

        result = MinIOClient.ensure_bucket_exists("test-bucket")
        assert result is True

        # Verify bucket exists
        client = MinIOClient.get()
        assert client.bucket_exists("test-bucket")

    def test_ensure_bucket_exists_already_exists(self):
        """Test that existing bucket is not recreated."""
        from src.clients import MinIOClient

        # Create bucket
        MinIOClient.ensure_bucket_exists("existing-bucket")

        # Try again
        result = MinIOClient.ensure_bucket_exists("existing-bucket")
        assert result is True

    def test_put_and_get_object(self):
        """Test uploading and downloading an object."""
        from src.clients import MinIOClient

        MinIOClient.ensure_bucket_exists()

        # Upload
        data = b"test file content"
        success = MinIOClient.put_object(
            object_name="test-file.txt",
            data=data,
            content_type="text/plain"
        )
        assert success is True

        # Download
        retrieved = MinIOClient.get_object("test-file.txt")
        assert retrieved == data

    def test_object_exists(self):
        """Test checking if object exists."""
        from src.clients import MinIOClient

        MinIOClient.ensure_bucket_exists()

        # Upload file
        MinIOClient.put_object(
            object_name="exists.txt",
            data=b"content"
        )

        # Check exists
        assert MinIOClient.object_exists("exists.txt") is True
        assert MinIOClient.object_exists("notexists.txt") is False

    def test_delete_object(self):
        """Test deleting an object."""
        from src.clients import MinIOClient

        MinIOClient.ensure_bucket_exists()

        # Upload
        MinIOClient.put_object(
            object_name="to-delete.txt",
            data=b"delete me"
        )

        # Verify exists
        assert MinIOClient.object_exists("to-delete.txt") is True

        # Delete
        success = MinIOClient.delete_object("to-delete.txt")
        assert success is True

        # Verify deleted
        assert MinIOClient.object_exists("to-delete.txt") is False

    def test_list_objects(self):
        """Test listing objects in bucket."""
        from src.clients import MinIOClient

        MinIOClient.ensure_bucket_exists()

        # Upload multiple files
        for i in range(3):
            MinIOClient.put_object(
                object_name=f"file{i}.txt",
                data=f"content {i}".encode()
            )

        # List all
        objects = MinIOClient.list_objects()
        assert len(objects) >= 3
        assert any("file0.txt" in obj for obj in objects)

    def test_list_objects_with_prefix(self):
        """Test listing objects with prefix filter."""
        from src.clients import MinIOClient

        MinIOClient.ensure_bucket_exists()

        # Upload files with different prefixes
        MinIOClient.put_object("docs/file1.txt", b"content1")
        MinIOClient.put_object("docs/file2.txt", b"content2")
        MinIOClient.put_object("images/photo.jpg", b"imagedata")

        # List with prefix
        docs = MinIOClient.list_objects(prefix="docs/")
        assert len(docs) >= 2
        assert all("docs/" in obj for obj in docs)

    def test_put_object_large_file(self):
        """Test uploading a larger file."""
        from src.clients import MinIOClient

        MinIOClient.ensure_bucket_exists()

        # Create 1MB file
        large_data = b"x" * (1024 * 1024)
        success = MinIOClient.put_object(
            object_name="large-file.bin",
            data=large_data
        )
        assert success is True

        # Verify
        retrieved = MinIOClient.get_object("large-file.bin")
        assert len(retrieved) == len(large_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

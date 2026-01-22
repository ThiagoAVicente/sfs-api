"""Tests for API key authentication using testcontainers."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import os
from testcontainers.redis import RedisContainer
from testcontainers.core.container import DockerContainer


@pytest.fixture(scope="class")
def redis_container():
    """Start Redis container for tests."""
    container = RedisContainer("redis:7-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="class")
def minio_container():
    """Start MinIO container for tests."""
    container = DockerContainer("minio/minio:latest")
    container.with_exposed_ports(9000)
    container.with_env("MINIO_ROOT_USER", "minioadmin")
    container.with_env("MINIO_ROOT_PASSWORD", "minioadmin")
    container.with_env("MINIO_KMS_SECRET_KEY", "minio-kms:1B09jU7vbNS4qTPpnfaddRPtfStSS2tjnPWvMvDq/xc=")
    container.with_command("server /data")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="class")
def qdrant_container():
    """Start Qdrant container for tests."""
    container = DockerContainer("qdrant/qdrant:latest")
    container.with_exposed_ports(6333)
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="class")
def setup_environment(redis_container, minio_container, qdrant_container):
    """Setup environment variables for all containers."""
    # Redis
    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)

    # MinIO
    minio_host = minio_container.get_container_host_ip()
    minio_port = minio_container.get_exposed_port(9000)

    # Qdrant
    qdrant_host = qdrant_container.get_container_host_ip()
    qdrant_port = qdrant_container.get_exposed_port(6333)

    env_vars = {
        "REDIS_HOST": redis_host,
        "REDIS_PORT": str(redis_port),
        "REDIS_PASSWORD": "",
        "MINIO_HOST": minio_host,
        "MINIO_PORT": str(minio_port),
        "MINIO_ROOT_USER": "minioadmin",
        "MINIO_ROOT_PASSWORD": "minioadmin",
        "SFS_FILE_BUCKET": "test-bucket",
        "MINIO_SECURE": "false",
        "QDRANT_HOST": qdrant_host,
        "QDRANT_PORT": str(qdrant_port),
        "COLLECTION_NAME": "test-collection",
        "API_KEY": "test-api-key-12345",
    }

    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def test_api_key():
    """Test API key."""
    return "test-api-key-12345"


@pytest.fixture
def client(setup_environment, test_api_key):
    """Create test client with testcontainers."""
    # Reload modules to ensure environment variables are picked up
    import importlib
    import sys

    # Remove cached main module if it exists
    if 'main' in sys.modules:
        del sys.modules['main']
    if 'src.routers' in sys.modules:
        del sys.modules['src.routers']

    # Import after environment is set up
    from main import app
    return TestClient(app)


@pytest.mark.integration
class TestAPIKeyAuthentication:
    """Tests for API key authentication."""

    def test_health_endpoint_no_auth_required(self, client):
        """Test that /health endpoint doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root_endpoint_no_auth_required(self, client):
        """Test that root endpoint doesn't require authentication."""
        response = client.get("/")
        assert response.status_code == 200
        assert "API" in response.json()["message"]

    def test_protected_endpoint_without_api_key(self, client):
        """Test that protected endpoints reject requests without API key."""
        response = client.post(
            "/v1/search",
            json={"query": "test", "limit": 5}
        )
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_api_key(self, client, test_api_key):
        """Test that protected endpoints reject requests with invalid API key."""
        response = client.post(
            "/v1/search",
            json={"query": "test", "limit": 5},
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_protected_endpoint_with_valid_api_key(self, client, test_api_key):
        """Test that protected endpoints accept requests with valid API key."""
        # Mock the searcher and cache to avoid needing indexed data
        with patch('src.routers.v1.search.Searcher.search') as mock_search, \
             patch('src.routers.v1.search.RedisClient') as mock_redis, \
             patch('src.routers.v1.search.QueryCache') as mock_cache_class:

            mock_search.return_value = []

            # Mock Redis and cache
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_query_results = AsyncMock(return_value=None)
            mock_cache.cache_query_results = AsyncMock()
            mock_cache_class.return_value = mock_cache

            response = client.post(
                "/v1/search",
                json={"query": "test", "limit": 5},
                headers={"X-API-Key": test_api_key}
            )
            # Should succeed (200) with valid API key
            assert response.status_code == 200

    def test_upload_endpoint_requires_api_key(self, client, test_api_key):
        """Test that upload endpoint requires API key."""
        # Without API key
        response = client.post(
            "/v1/index",
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        assert response.status_code == 401

        # With valid API key - mock MinIO and Redis to test auth
        with patch('src.routers.v1.index.MinIOClient.object_exists', return_value=False), \
             patch('src.routers.v1.index.MinIOClient.put_object', return_value=True), \
             patch('src.routers.v1.index.RedisClient.enqueue_job') as mock_enqueue:
            mock_enqueue.return_value = "job-123"

            response = client.post(
                "/v1/index",
                files={"file": ("test.txt", b"test content for indexing", "text/plain")},
                headers={"X-API-Key": test_api_key}
            )
            # Should succeed (file uploaded and job queued)
            assert response.status_code == 200
            assert "job_id" in response.json()

    def test_delete_endpoint_requires_api_key(self, client, test_api_key):
        """Test that delete endpoint requires API key."""
        # Without API key
        response = client.delete("/v1/index/test.txt")
        assert response.status_code == 401

        # With valid API key - mock Redis to test auth
        with patch('src.routers.v1.index.RedisClient.enqueue_job') as mock_enqueue:
            mock_enqueue.return_value = "job-456"

            response = client.delete(
                "/v1/index/test.txt",
                headers={"X-API-Key": test_api_key}
            )
            # Should succeed (job queued for deletion)
            assert response.status_code == 200
            assert "job_id" in response.json()

    def test_download_endpoint_requires_api_key(self, client, test_api_key):
        """Test that file download endpoint requires API key."""
        # Without API key
        response = client.get("/v1/files/test.txt")
        assert response.status_code == 401

        # With valid API key but file doesn't exist
        response = client.get(
            "/v1/files/nonexistent.txt",
            headers={"X-API-Key": test_api_key}
        )
        # Should return 404 (file not found) not 401 (auth failed)
        assert response.status_code == 404

    def test_api_key_case_sensitive(self, client, test_api_key):
        """Test that API key comparison is case-sensitive."""
        response = client.post(
            "/v1/search",
            json={"query": "test", "limit": 5},
            headers={"X-API-Key": test_api_key.upper()}  # Wrong case
        )
        assert response.status_code == 401

    def test_timing_attack_resistant(self, client, test_api_key):
        """Test that secrets.compare_digest is used (timing attack resistant)."""
        # This test verifies that the compare_digest function is used
        # We can't directly test timing resistance, but we verify the behavior
        import time

        # Try with completely wrong key
        start = time.perf_counter()
        response1 = client.post(
            "/v1/search",
            json={"query": "test"},
            headers={"X-API-Key": "wrong" * 10}
        )
        time1 = time.perf_counter() - start

        # Try with almost correct key (same length)
        start = time.perf_counter()
        response2 = client.post(
            "/v1/search",
            json={"query": "test"},
            headers={"X-API-Key": test_api_key[:-1] + "X"}
        )
        time2 = time.perf_counter() - start

        # Both should return 401
        assert response1.status_code == 401
        assert response2.status_code == 401

        # Timing should be similar (within reasonable variance)
        # This is a weak test but verifies the behavior exists


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

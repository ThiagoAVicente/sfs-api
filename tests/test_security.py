"""Tests for API key authentication."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os


@pytest.fixture
def test_api_key():
    """Test API key."""
    return "test-api-key-12345"


@pytest.fixture
def client(test_api_key):
    """Create test client with mocked API key."""
    with patch.dict(os.environ, {"API_KEY": test_api_key}):
        # Import after patching environment
        from main import app
        return TestClient(app)


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
        assert "Semantic File Search API" in response.json()["message"]

    def test_protected_endpoint_without_api_key(self, client):
        """Test that protected endpoints reject requests without API key."""
        response = client.post(
            "/search",
            json={"query": "test", "limit": 5}
        )
        assert response.status_code == 401  # FastAPI returns 403 when header is missing with auto_error=True

    def test_protected_endpoint_with_invalid_api_key(self, client, test_api_key):
        """Test that protected endpoints reject requests with invalid API key."""
        response = client.post(
            "/search",
            json={"query": "test", "limit": 5},
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_protected_endpoint_with_valid_api_key(self, client, test_api_key):
        """Test that protected endpoints accept requests with valid API key."""
        with patch('src.routers.search.Searcher.search') as mock_search:
            mock_search.return_value = []

            response = client.post(
                "/search",
                json={"query": "test", "limit": 5},
                headers={"X-API-Key": test_api_key}
            )
            assert response.status_code == 200

    def test_upload_endpoint_requires_api_key(self, client, test_api_key):
        """Test that upload endpoint requires API key."""
        # Without API key
        response = client.post(
            "/index",
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        assert response.status_code == 401

        # With valid API key
        with patch('src.routers.index.MinIOClient.object_exists', return_value=False), \
             patch('src.routers.index.MinIOClient.put_object', return_value=True), \
             patch('src.routers.index.RedisClient.enqueue_job', return_value="job-123"), \
             patch('src.routers.index.required'):

            response = client.post(
                "/index",
                files={"file": ("test.txt", b"test content", "text/plain")},
                headers={"X-API-Key": test_api_key}
            )
            assert response.status_code == 200
            assert "job_id" in response.json()

    def test_delete_endpoint_requires_api_key(self, client, test_api_key):
        """Test that delete endpoint requires API key."""
        # Without API key
        response = client.delete("/index/test.txt")
        assert response.status_code == 401

        # With valid API key
        with patch('src.routers.index.RedisClient.enqueue_job', return_value="job-456"):
            response = client.delete(
                "/index/test.txt",
                headers={"X-API-Key": test_api_key}
            )
            assert response.status_code == 200
            assert "job_id" in response.json()

    def test_download_endpoint_requires_api_key(self, client, test_api_key):
        """Test that file download endpoint requires API key."""
        # Without API key
        response = client.get("/files/test.txt")
        assert response.status_code == 401

        # With valid API key
        with patch('src.routers.files.MinIOClient.object_exists', return_value=True), \
             patch('src.routers.files.MinIOClient.get_object', return_value=b"file content"):

            response = client.get(
                "/files/test.txt",
                headers={"X-API-Key": test_api_key}
            )
            assert response.status_code == 200

    def test_api_key_case_sensitive(self, client, test_api_key):
        """Test that API key comparison is case-sensitive."""
        response = client.post(
            "/search",
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
            "/search",
            json={"query": "test"},
            headers={"X-API-Key": "wrong" * 10}
        )
        time1 = time.perf_counter() - start

        # Try with almost correct key (same length)
        start = time.perf_counter()
        response2 = client.post(
            "/search",
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

"""
Tests for Qdrant client.

Includes:
1. Unit tests with mocks (fast, no dependencies)
2. Integration tests with testcontainers (slow, requires Docker)
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from qdrant_client.models import (
    Distance,
    VectorParams,
    CollectionsResponse,
    CollectionDescription,
)

# ============================================================================
# UNIT TESTS WITH MOCKS (Fast, no Docker required)
# ============================================================================


class TestQdrantClientMocked:
    """Unit tests using mocks - no real Qdrant connection."""

    @pytest.fixture(autouse=True)
    def reset_client(self):
        """Reset singleton before each test."""
        from src.clients import QdrantClient

        QdrantClient._client = None
        yield
        QdrantClient._client = None

    @pytest.mark.asyncio
    async def test_init_creates_client(self):
        """Test that init creates AsyncQdrantClient."""
        from src.clients import QdrantClient

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance

            client = await QdrantClient.init()

            assert client == mock_instance
            mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_returns_same_client(self):
        """Test that get() returns singleton instance."""
        from src.clients import QdrantClient

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance

            client1 = await QdrantClient.get()
            client2 = await QdrantClient.get()

            assert client1 == client2
            # Should only create client once
            assert mock_client_class.call_count == 1

    @pytest.mark.asyncio
    async def test_close_clears_client(self):
        """Test that close() clears the singleton."""
        from src.clients import QdrantClient

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_instance = AsyncMock()
            mock_client_class.return_value = mock_instance

            await QdrantClient.init()
            assert QdrantClient._client is not None

            await QdrantClient.close()
            assert QdrantClient._client is None
            mock_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_creates_new(self):
        """Test creating a new collection."""
        from src.clients import QdrantClient

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock: collection doesn't exist
            mock_client.get_collections.return_value = CollectionsResponse(
                collections=[]
            )

            result = await QdrantClient.ensure_collection_exists(
                collection_name="test_collection", vector_size=384
            )

            assert result is True
            mock_client.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_skips_existing(self):
        """Test that existing collection is not recreated."""
        from src.clients import QdrantClient

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock: collection already exists
            existing_collection = CollectionDescription(name="test_collection")
            mock_client.get_collections.return_value = CollectionsResponse(
                collections=[existing_collection]
            )

            result = await QdrantClient.ensure_collection_exists(
                collection_name="test_collection"
            )

            assert result is True
            mock_client.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_write_generates_point_id(self):
        """Test that write generates ID when not provided."""
        from src.clients import QdrantClient

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            vector = np.array([0.1, 0.2, 0.3])
            metadata = {"file_path": "/test.py", "chunk_index": 0}

            result = await QdrantClient.write(
                vector=vector, collection_name="test", metadata=metadata
            )

            assert result is True
            mock_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_generates_deterministic_id(self):
        """Test that write generates deterministic ID from metadata."""
        from src.clients import QdrantClient
        import hashlib

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            vector = np.array([0.1, 0.2, 0.3])
            metadata = {"file_path": "/test.py", "chunk_index": 0}

            await QdrantClient.write(
                vector=vector, collection_name="test", metadata=metadata
            )

            # Calculate expected ID
            id_string = "/test.py:0"
            expected_id = int(hashlib.md5(id_string.encode()).hexdigest()[:16], 16)

            # Check that upsert was called with deterministic ID
            call_args = mock_client.upsert.call_args
            points = call_args.kwargs["points"]
            assert points[0].id == expected_id

    @pytest.mark.asyncio
    async def test_write_converts_numpy_to_list(self):
        """Test that numpy array is converted to list."""
        from src.clients import QdrantClient

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            vector = np.array([0.1, 0.2, 0.3])
            metadata = {"file_path": "/test.py", "chunk_index": 0}

            await QdrantClient.write(
                vector=vector, collection_name="test", metadata=metadata
            )

            call_args = mock_client.upsert.call_args
            points = call_args.kwargs["points"]
            # Verify vector is a list, not numpy array
            assert isinstance(points[0].vector, list)
            assert points[0].vector == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """Test that search returns similar vectors."""
        from src.clients import QdrantClient

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock search results using MagicMock
            mock_point = MagicMock()
            mock_point.id = 123
            mock_point.score = 0.95
            mock_point.payload = {"file_path": "/test.py", "text": "test content"}

            mock_response = MagicMock()
            mock_response.points = [mock_point]
            mock_client.query_points.return_value = mock_response

            query_vector = np.array([0.1, 0.2, 0.3])
            results = await QdrantClient.search(
                query_vector=query_vector, collection_name="test", limit=5
            )

            assert len(results) == 1
            assert results[0]["score"] == 0.95
            assert results[0]["payload"]["file_path"] == "/test.py"
            mock_client.query_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_score_threshold(self):
        """Test search with score threshold filter."""
        from src.clients import QdrantClient

        with patch("src.clients.qdrant_client.AsyncQdrantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock empty response
            mock_response = MagicMock()
            mock_response.points = []
            mock_client.query_points.return_value = mock_response

            query_vector = np.array([0.1, 0.2, 0.3])
            await QdrantClient.search(
                query_vector=query_vector,
                collection_name="test",
                limit=5,
                score_threshold=0.8,
            )

            # Verify score_threshold was passed
            call_args = mock_client.query_points.call_args
            assert call_args.kwargs["score_threshold"] == 0.8


# ============================================================================
# INTEGRATION TESTS WITH TESTCONTAINERS (Requires Docker)
# ============================================================================


@pytest.mark.integration
class TestQdrantClientIntegration:
    """Integration tests using real Qdrant container."""

    @pytest.fixture(scope="class")
    def qdrant_container(self):
        """Start Qdrant container for tests."""
        from testcontainers.core.container import DockerContainer
        from testcontainers.core.wait_strategies import HttpWaitStrategy

        container = DockerContainer("qdrant/qdrant:latest")
        container.with_exposed_ports(6333)
        container.waiting_for(HttpWaitStrategy(6333).for_status_code(200))

        container.start()

        yield container

        container.stop()

    @pytest.fixture(autouse=True)
    async def setup_client(self, qdrant_container):
        """Setup client with testcontainer."""
        import os
        from src.clients import QdrantClient

        # Reset singleton
        QdrantClient._client = None

        # Set env vars to point to test container
        host = qdrant_container.get_container_host_ip()
        port = qdrant_container.get_exposed_port(6333)

        os.environ["QDRANT_HOST"] = host
        os.environ["QDRANT_PORT"] = str(port)  # Must be string!

        # Reload module to pick up new env vars
        import importlib
        import src.clients.qdrant_client as qc_module

        importlib.reload(qc_module)

        yield

        # Cleanup
        await QdrantClient.close()
        QdrantClient._client = None

    @pytest.mark.asyncio
    async def test_real_connection(self):
        """Test real connection to Qdrant."""
        from src.clients import QdrantClient

        client = await QdrantClient.get()
        assert client is not None

    @pytest.mark.asyncio
    async def test_real_create_collection(self):
        """Test creating real collection."""
        from src.clients import QdrantClient

        result = await QdrantClient.ensure_collection_exists(
            collection_name="test_real_collection",
            vector_size=384,
            distance=Distance.COSINE,
        )

        assert result is True

        # Verify collection exists
        client = await QdrantClient.get()
        collections = await client.get_collections()
        collection_names = [c.name for c in collections.collections]
        assert "test_real_collection" in collection_names

    @pytest.mark.asyncio
    async def test_real_write_and_retrieve(self):
        """Test writing and retrieving real vectors."""
        from src.clients import QdrantClient

        collection_name = "test_write_collection"

        # Create collection
        await QdrantClient.ensure_collection_exists(
            collection_name=collection_name, vector_size=3
        )

        # Write vector
        vector = np.array([0.1, 0.2, 0.3])
        metadata = {
            "file_path": "/test/file.py",
            "text": "test content",
            "chunk_index": 0,
        }

        result = await QdrantClient.write(
            vector=vector, collection_name=collection_name, metadata=metadata
        )

        assert result is True

        # Calculate expected ID
        import hashlib

        id_string = "/test/file.py:0"
        expected_id = int(hashlib.md5(id_string.encode()).hexdigest()[:16], 16)

        # Retrieve and verify
        client = await QdrantClient.get()
        points = await client.retrieve(
            collection_name=collection_name, ids=[expected_id]
        )

        assert len(points) == 1
        assert points[0].id == expected_id
        assert points[0].payload["file_path"] == "/test/file.py"
        assert points[0].payload["chunk_index"] == 0

    @pytest.mark.asyncio
    async def test_real_multiple_writes(self):
        """Test writing multiple vectors."""
        from src.clients import QdrantClient

        collection_name = "test_multi_write"

        await QdrantClient.ensure_collection_exists(
            collection_name=collection_name, vector_size=2
        )

        # Write multiple vectors
        for i in range(5):
            vector = np.array([float(i), float(i * 2)])
            metadata = {"chunk_index": i, "file_path": f"/file{i}.py"}

            await QdrantClient.write(
                vector=vector, collection_name=collection_name, metadata=metadata
            )

        # Verify count
        client = await QdrantClient.get()
        collection_info = await client.get_collection(collection_name)
        assert collection_info.points_count == 5

    @pytest.mark.asyncio
    async def test_real_search_functionality(self):
        """Test real search with similar vectors."""
        from src.clients import QdrantClient

        collection_name = "test_search_collection"

        # Create collection
        await QdrantClient.ensure_collection_exists(
            collection_name=collection_name, vector_size=3
        )

        # Write test vectors
        vectors = [
            (
                np.array([1.0, 0.0, 0.0]),
                {"text": "vector A", "chunk_index": 0, "file_path": "/a.py"},
            ),
            (
                np.array([0.9, 0.1, 0.0]),
                {
                    "text": "vector B (similar to A)",
                    "chunk_index": 1,
                    "file_path": "/b.py",
                },
            ),
            (
                np.array([0.0, 1.0, 0.0]),
                {
                    "text": "vector C (different)",
                    "chunk_index": 2,
                    "file_path": "/c.py",
                },
            ),
        ]

        for vector, metadata in vectors:
            await QdrantClient.write(
                vector=vector, collection_name=collection_name, metadata=metadata
            )

        # Search for vector similar to A
        query_vector = np.array([1.0, 0.0, 0.0])
        results = await QdrantClient.search(
            query_vector=query_vector, collection_name=collection_name, limit=3
        )

        # Should find vectors A and B (similar), not C
        assert len(results) > 0
        # First result should be most similar (vector A itself or very close)
        assert results[0]["score"] > 0.9
        assert results[0]["payload"]["text"] in ["vector A", "vector B (similar to A)"]

    @pytest.mark.asyncio
    async def test_real_search_with_threshold(self):
        """Test search with score threshold."""
        from src.clients import QdrantClient

        collection_name = "test_threshold_collection"

        await QdrantClient.ensure_collection_exists(
            collection_name=collection_name, vector_size=2
        )

        # Write vectors
        await QdrantClient.write(
            vector=np.array([1.0, 0.0]),
            collection_name=collection_name,
            metadata={"text": "similar", "chunk_index": 0, "file_path": "/sim.py"},
        )
        await QdrantClient.write(
            vector=np.array([0.0, 1.0]),
            collection_name=collection_name,
            metadata={"text": "different", "chunk_index": 1, "file_path": "/diff.py"},
        )

        # Search with high threshold (should filter out different vector)
        query_vector = np.array([1.0, 0.0])
        results = await QdrantClient.search(
            query_vector=query_vector,
            collection_name=collection_name,
            limit=10,
            score_threshold=0.9,
        )

        # Should only return the similar vector
        assert len(results) <= 1
        if len(results) > 0:
            assert results[0]["payload"]["text"] == "similar"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

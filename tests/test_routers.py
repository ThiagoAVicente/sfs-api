"""Tests for API routers using mocks."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from starlette.requests import Request


class TestIndexRouter:
    """Tests for /index endpoints."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Request object."""
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_index_file_success(self, mock_request):
        """Test successful file upload and indexing."""
        from src.routers.v1.index import index_file

        # Mock file upload
        mock_file = MagicMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"test content")

        with (
            patch("src.routers.v1.index.MinIOClient") as mock_minio,
            patch("src.routers.v1.index.RedisClient") as mock_redis,
            patch("src.routers.v1.index.required"),
        ):
            # Mock MinIO operations
            mock_minio.object_exists.return_value = False
            mock_minio.put_object.return_value = True

            # Mock Redis enqueue
            mock_redis.enqueue_job = AsyncMock(return_value="job-123")

            # Execute
            result = await index_file(mock_request, mock_file, update=False)

            # Assert
            assert result["job_id"] == "job-123"
            mock_minio.object_exists.assert_called_once_with("default/test.txt")
            # Verify put_object called with correct object name
            put_call_kwargs = mock_minio.put_object.call_args.kwargs
            assert put_call_kwargs["object_name"] == "default/test.txt"
            assert put_call_kwargs["data"] == b"test content"
            assert put_call_kwargs["content_type"] == "text/plain"
            mock_redis.enqueue_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_file_invalid(self, mock_request):
        """Test successful file upload and indexing."""
        from src.routers.v1.index import index_file
        from fastapi import HTTPException

        # Mock file upload
        mock_file = MagicMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"")

        with (
            patch("src.routers.v1.index.MinIOClient") as mock_minio,
            patch("src.routers.v1.index.RedisClient") as mock_redis,
            patch("src.routers.v1.index.required"),
        ):
            # Mock MinIO operations
            mock_minio.object_exists.return_value = False
            mock_minio.put_object.return_value = True

            # Mock Redis enqueue
            mock_redis.enqueue_job = AsyncMock(return_value="job-123")

            with pytest.raises(HTTPException) as exc_info:
                await index_file(mock_request, mock_file, update=False)

            assert exc_info.value.status_code == 415
            assert "empty" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_index_file_already_exists_no_update(self, mock_request):
        """Test file upload fails when file exists and update=False."""
        from src.routers.v1.index import index_file
        from fastapi import HTTPException

        mock_file = MagicMock()
        mock_file.filename = "existing.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"test content")

        with (
            patch("src.routers.v1.index.MinIOClient") as mock_minio,
            patch("src.routers.v1.index.required"),
        ):
            mock_minio.object_exists.return_value = True

            with pytest.raises(HTTPException) as exc_info:
                await index_file(mock_request, mock_file, update=False)

            # Router catches HTTPException and re-raises as 500
            assert exc_info.value.status_code == 400
            assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_index_file_update_existing(self, mock_request):
        """Test file upload succeeds when file exists and update=True."""
        from src.routers.v1.index import index_file

        mock_file = MagicMock()
        mock_file.filename = "existing.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"updated content")

        with (
            patch("src.routers.v1.index.MinIOClient") as mock_minio,
            patch("src.routers.v1.index.RedisClient") as mock_redis,
            patch("src.routers.v1.index.required"),
        ):
            mock_minio.object_exists.return_value = True
            mock_minio.put_object.return_value = True
            mock_redis.enqueue_job = AsyncMock(return_value="job-456")

            result = await index_file(mock_request, mock_file, update=True)

            assert result["job_id"] == "job-456"
            mock_minio.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_file_minio_upload_fails(self, mock_request):
        """Test error handling when MinIO upload fails."""
        from src.routers.v1.index import index_file
        from fastapi import HTTPException

        mock_file = MagicMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=b"test content")

        with (
            patch("src.routers.v1.index.MinIOClient") as mock_minio,
            patch("src.routers.v1.index.required"),
        ):
            mock_minio.object_exists.return_value = False
            mock_minio.put_object.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                await index_file(mock_request, mock_file, update=False)

            assert exc_info.value.status_code == 500
            assert "Failed to upload file" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_status_success(self, mock_request):
        """Test getting job status successfully."""
        from src.routers.v1.index import get_status

        with patch("src.routers.v1.index.RedisClient") as mock_redis:
            mock_redis.get_job_status = AsyncMock(return_value="complete")

            result = await get_status(mock_request, "job-123")

            assert result.job_id == "job-123"
            assert result.status == "complete"
            mock_redis.get_job_status.assert_called_once_with("job-123")

    @pytest.mark.asyncio
    async def test_get_status_job_not_found(self, mock_request):
        """Test getting status for non-existent job."""
        from src.routers.v1.index import get_status
        from fastapi import HTTPException

        with patch("src.routers.v1.index.RedisClient") as mock_redis:
            mock_redis.get_job_status = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                await get_status(mock_request, "invalid-job")

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_file_success(self, mock_request):
        """Test file deletion successfully enqueues job."""
        from src.routers.v1.index import delete_file

        with patch("src.routers.v1.index.RedisClient") as mock_redis:
            mock_redis.enqueue_job = AsyncMock(return_value="job-789")

            result = await delete_file(mock_request, "test.txt")

            assert result["job_id"] == "job-789"
            mock_redis.enqueue_job.assert_called_once()


class TestSearchRouter:
    """Tests for /search endpoint."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Request object."""
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_search_success(self, mock_request):
        """Test successful search."""
        from src.models import SearchRequest

        search_req = SearchRequest(query="test query", limit=5, score_threshold=0.5)

        mock_results = [
            {"score": 0.95, "payload": {"text": "result 1", "file_path": "/test.txt"}},
            {"score": 0.85, "payload": {"text": "result 2", "file_path": "/test2.txt"}},
        ]

        # Patch before importing to disable rate limiting and mock Redis
        with (
            patch("src.routers.v1.search.limiter.enabled", False),
            patch("src.routers.v1.search.Searcher") as mock_searcher,
            patch("src.routers.v1.search.RedisClient") as mock_redis,
            patch("src.routers.v1.search.QueryCache") as mock_cache_class,
        ):
            from src.routers.v1.search import search_files

            # Mock Redis and cache
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_query_results = AsyncMock(return_value=None)
            mock_cache.cache_query_results = AsyncMock()
            mock_cache_class.return_value = mock_cache

            mock_searcher.search = AsyncMock(return_value=mock_results)

            result = await search_files(search_req, mock_request)

            assert result.results == mock_results
            mock_searcher.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_empty_results(self, mock_request):
        """Test search with no results."""
        from src.models import SearchRequest

        search_req = SearchRequest(query="nonexistent")

        # Patch before importing to disable rate limiting and mock Redis
        with (
            patch("src.routers.v1.search.limiter.enabled", False),
            patch("src.routers.v1.search.Searcher") as mock_searcher,
            patch("src.routers.v1.search.RedisClient") as mock_redis,
            patch("src.routers.v1.search.QueryCache") as mock_cache_class,
        ):
            from src.routers.v1.search import search_files

            # Mock Redis and cache
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_query_results = AsyncMock(return_value=None)
            mock_cache.cache_query_results = AsyncMock()
            mock_cache_class.return_value = mock_cache

            mock_searcher.search = AsyncMock(return_value=[])

            result = await search_files(search_req, mock_request)

            assert result.results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

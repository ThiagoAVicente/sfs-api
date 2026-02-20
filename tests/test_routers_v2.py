"""Tests for v2 API routers with pagination."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from starlette.requests import Request


class TestFilesRouterV2:
    """Tests for /v2/files endpoints with pagination."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Request object."""
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_list_files_with_pagination(self, mock_request):
        """Test listing files with pagination."""
        from src.routers.v2.files import list_files
        from src.models.pagination import PaginationParams

        mock_files = [{"name": f"file{i}.txt", "size": 1024} for i in range(50)]

        with (
            patch("src.routers.v2.files.MinIOClient") as mock_minio,
            patch("src.routers.v2.files.RedisClient") as mock_redis,
            patch("src.routers.v2.files.FileCache") as mock_cache_class,
            patch("src.routers.v2.files.limiter.enabled", False),
        ):
            # Mock Redis
            mock_redis.get = AsyncMock(return_value=MagicMock())

            # Mock FileCache
            mock_cache = MagicMock()
            mock_cache.get_files = AsyncMock(return_value=None)  # Cache miss
            mock_cache.cache_files = AsyncMock()
            mock_cache_class.return_value = mock_cache

            # Mock MinIO
            mock_minio.list_objects.return_value = mock_files

            # Create pagination params
            pagination = PaginationParams(page=1, limit=20)

            # Execute
            result = await list_files(
                mock_request, collection="", pagination=pagination
            )

            # Assert
            assert len(result.items) == 20  # First page, 20 items
            assert result.total == 50
            assert result.page == 1
            assert result.limit == 20
            assert result.has_next is True
            assert result.has_prev is False
            assert result.total_pages == 3

    @pytest.mark.asyncio
    async def test_list_files_second_page(self, mock_request):
        """Test listing files on second page."""
        from src.routers.v2.files import list_files
        from src.models.pagination import PaginationParams

        mock_files = [{"name": f"file{i}.txt"} for i in range(30)]

        with (
            patch("src.routers.v2.files.MinIOClient") as mock_minio,
            patch("src.routers.v2.files.RedisClient") as mock_redis,
            patch("src.routers.v2.files.FileCache") as mock_cache_class,
            patch("src.routers.v2.files.limiter.enabled", False),
        ):
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_files = AsyncMock(return_value=mock_files)  # Cache hit
            mock_cache_class.return_value = mock_cache

            pagination = PaginationParams(page=2, limit=20)

            result = await list_files(
                mock_request, collection="", pagination=pagination
            )

            assert len(result.items) == 10  # Last 10 items
            assert result.page == 2
            assert result.has_next is False
            assert result.has_prev is True

    @pytest.mark.asyncio
    async def test_list_files_with_prefix(self, mock_request):
        """Test listing files with prefix filter."""
        from src.routers.v2.files import list_files
        from src.models.pagination import PaginationParams

        mock_files = [{"name": "reports/file1.txt"}, {"name": "reports/file2.txt"}]

        with (
            patch("src.routers.v2.files.MinIOClient") as mock_minio,
            patch("src.routers.v2.files.RedisClient") as mock_redis,
            patch("src.routers.v2.files.FileCache") as mock_cache_class,
            patch("src.routers.v2.files.limiter.enabled", False),
        ):
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_files = AsyncMock(return_value=None)
            mock_cache.cache_files = AsyncMock()
            mock_cache_class.return_value = mock_cache
            mock_minio.list_objects.return_value = mock_files

            pagination = PaginationParams(page=1, limit=20)

            result = await list_files(
                mock_request, collection="reports", pagination=pagination
            )

            assert len(result.items) == 2
            mock_cache.get_files.assert_called_once_with("reports")

    @pytest.mark.asyncio
    async def test_list_files_uses_cache(self, mock_request):
        """Test that cached results are used when available."""
        from src.routers.v2.files import list_files
        from src.models.pagination import PaginationParams

        cached_files = [{"name": "cached.txt"}]

        with (
            patch("src.routers.v2.files.MinIOClient") as mock_minio,
            patch("src.routers.v2.files.RedisClient") as mock_redis,
            patch("src.routers.v2.files.FileCache") as mock_cache_class,
            patch("src.routers.v2.files.limiter.enabled", False),
        ):
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_files = AsyncMock(return_value=cached_files)
            mock_cache_class.return_value = mock_cache

            pagination = PaginationParams(page=1, limit=20)

            result = await list_files(
                mock_request, collection="", pagination=pagination
            )

            # MinIO should not be called when cache hit
            mock_minio.list_objects.assert_not_called()
            assert result.items == cached_files


class TestSearchRouterV2:
    """Tests for /v2/search endpoint with pagination."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Request object."""
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, mock_request):
        """Test search with pagination."""
        from src.models import SearchRequest
        from src.models.pagination import PaginationParams
        from src.routers.v2.search import search_files

        search_req = SearchRequest(
            query="test query", score_threshold=0.5, collections=["default"]
        )

        mock_results = [
            {"score": 0.9 - i * 0.01, "text": f"result {i}"} for i in range(100)
        ]

        with (
            patch("src.routers.v2.search.Searcher") as mock_searcher,
            patch("src.routers.v2.search.RedisClient") as mock_redis,
            patch("src.routers.v2.search.QueryCache") as mock_cache_class,
            patch("src.routers.v2.search.limiter.enabled", False),
        ):
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_query_results = AsyncMock(return_value=None)  # Cache miss
            mock_cache.cache_query_results = AsyncMock()
            mock_cache_class.return_value = mock_cache

            mock_searcher.search = AsyncMock(return_value=mock_results)

            pagination = PaginationParams(page=1, limit=20)

            result = await search_files(search_req, mock_request, pagination)

            assert len(result.items) == 20  # First page
            assert result.total == 100
            assert result.page == 1
            assert result.has_next is True
            assert result.has_prev is False

    @pytest.mark.asyncio
    async def test_search_uses_cache(self, mock_request):
        """Test that cached search results are used."""
        from src.models import SearchRequest
        from src.models.pagination import PaginationParams
        from src.routers.v2.search import search_files

        search_req = SearchRequest(query="test query", collections=["default"])
        cached_results = [{"score": 0.95, "text": "cached result"}]

        with (
            patch("src.routers.v2.search.Searcher") as mock_searcher,
            patch("src.routers.v2.search.RedisClient") as mock_redis,
            patch("src.routers.v2.search.QueryCache") as mock_cache_class,
            patch("src.routers.v2.search.limiter.enabled", False),
        ):
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_query_results = AsyncMock(return_value=cached_results)
            mock_cache_class.return_value = mock_cache

            pagination = PaginationParams(page=1, limit=20)

            result = await search_files(search_req, mock_request, pagination)

            # Searcher should not be called when cache hit
            mock_searcher.search.assert_not_called()
            assert result.items == cached_results

    @pytest.mark.asyncio
    async def test_search_empty_query_fails(self, mock_request):
        """Test that empty query returns error."""
        from src.models import SearchRequest
        from src.models.pagination import PaginationParams
        from src.routers.v2.search import search_files
        from fastapi import HTTPException

        search_req = SearchRequest(query="")

        with (
            patch("src.routers.v2.search.RedisClient") as mock_redis,
            patch("src.routers.v2.search.QueryCache") as mock_cache_class,
            patch("src.routers.v2.search.limiter.enabled", False),
        ):
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_query_results = AsyncMock(return_value=None)
            mock_cache_class.return_value = mock_cache

            pagination = PaginationParams(page=1, limit=20)

            with pytest.raises(HTTPException) as exc_info:
                await search_files(search_req, mock_request, pagination)

            assert exc_info.value.status_code == 400
            assert "empty" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_search_pagination_second_page(self, mock_request):
        """Test getting second page of search results."""
        from src.models import SearchRequest
        from src.models.pagination import PaginationParams
        from src.routers.v2.search import search_files

        search_req = SearchRequest(query="test", collections=["default"])

        # Cache returns 50 results
        cached_results = [{"score": 0.9, "text": f"result {i}"} for i in range(50)]

        with (
            patch("src.routers.v2.search.RedisClient") as mock_redis,
            patch("src.routers.v2.search.QueryCache") as mock_cache_class,
            patch("src.routers.v2.search.limiter.enabled", False),
        ):
            mock_redis.get = AsyncMock(return_value=MagicMock())
            mock_cache = MagicMock()
            mock_cache.get_query_results = AsyncMock(return_value=cached_results)
            mock_cache_class.return_value = mock_cache

            pagination = PaginationParams(page=3, limit=20)

            result = await search_files(search_req, mock_request, pagination)

            assert len(result.items) == 10  # Last 10 items (40-50)
            assert result.page == 3
            assert result.has_next is False
            assert result.has_prev is True


class TestPaginationParams:
    """Tests for PaginationParams model."""

    def test_offset_calculation(self):
        """Test that offset is calculated correctly from page and limit."""
        from src.models.pagination import PaginationParams

        # Page 1
        params = PaginationParams(page=1, limit=20)
        assert params.offset == 0

        # Page 2
        params = PaginationParams(page=2, limit=20)
        assert params.offset == 20

        # Page 3 with limit 10
        params = PaginationParams(page=3, limit=10)
        assert params.offset == 20

    def test_default_values(self):
        """Test default pagination values."""
        from src.models.pagination import PaginationParams

        params = PaginationParams()
        assert params.page == 1
        assert params.limit == 20
        assert params.offset == 0

    def test_limit_validation(self):
        """Test that limit is validated."""
        from src.models.pagination import PaginationParams
        from pydantic import ValidationError

        # Limit too small
        with pytest.raises(ValidationError):
            PaginationParams(limit=0)

        # Limit too large
        with pytest.raises(ValidationError):
            PaginationParams(limit=101)

        # Valid limits
        PaginationParams(limit=1)  # Min
        PaginationParams(limit=100)  # Max


class TestPaginatedResponse:
    """Tests for PaginatedResponse model."""

    def test_create_response(self):
        """Test creating a paginated response."""
        from src.models.pagination import PaginatedResponse

        items = [1, 2, 3, 4, 5]
        response = PaginatedResponse.create(items=items, total=50, page=1, limit=5)

        assert response.items == items
        assert response.total == 50
        assert response.page == 1
        assert response.limit == 5
        assert response.total_pages == 10
        assert response.has_next is True
        assert response.has_prev is False

    def test_last_page(self):
        """Test paginated response for last page."""
        from src.models.pagination import PaginatedResponse

        response = PaginatedResponse.create(items=[1, 2], total=22, page=3, limit=10)

        assert response.total_pages == 3
        assert response.has_next is False
        assert response.has_prev is True

    def test_single_page(self):
        """Test paginated response when all items fit on one page."""
        from src.models.pagination import PaginatedResponse

        response = PaginatedResponse.create(items=[1, 2, 3], total=3, page=1, limit=10)

        assert response.total_pages == 1
        assert response.has_next is False
        assert response.has_prev is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

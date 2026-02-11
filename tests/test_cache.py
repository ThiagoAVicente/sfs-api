"""Tests for cache classes."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import json
import hashlib


class TestCacheAbs:
    """Tests for CacheAbs abstract base class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = MagicMock()
        redis.get = AsyncMock()
        redis.setex = AsyncMock()
        redis.delete = AsyncMock()
        redis.scan = AsyncMock()
        return redis

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, mock_redis):
        """Test getting cached data successfully."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        test_data = ["file1.txt", "file2.txt"]
        mock_redis.get.return_value = json.dumps(test_data)

        result = await cache.get("cache:files:list:abc123")

        assert result == test_data
        mock_redis.get.assert_called_once_with("cache:files:list:abc123")

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, mock_redis):
        """Test getting non-existent cache returns None."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        mock_redis.get.return_value = None

        result = await cache.get("cache:files:list:xyz789")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_cache(self, mock_redis):
        """Test setting cache with TTL."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        test_data = ["file1.txt", "file2.txt"]

        await cache.set("cache:files:list:abc123", test_data, ttl=1800)

        mock_redis.setex.assert_called_once_with(
            "cache:files:list:abc123", 1800, json.dumps(test_data)
        )

    @pytest.mark.asyncio
    async def test_set_cache_uses_default_ttl(self, mock_redis):
        """Test setting cache without TTL uses default."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        test_data = ["file1.txt"]

        await cache.set("cache:files:list:test", test_data)

        # FileCache has DEFAULT_TTL = 3600
        mock_redis.setex.assert_called_once_with(
            "cache:files:list:test", 3600, json.dumps(test_data)
        )

    @pytest.mark.asyncio
    async def test_delete_cache(self, mock_redis):
        """Test deleting a cache entry."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)

        await cache.delete("cache:files:list:abc123")

        mock_redis.delete.assert_called_once_with("cache:files:list:abc123")

    @pytest.mark.asyncio
    async def test_clear_cache_with_pattern(self, mock_redis):
        """Test clearing cache entries by pattern."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        # Mock scan to return keys in batches (cursor, keys)
        mock_redis.scan.return_value = (
            0,
            ["cache:files:list:abc", "cache:files:list:def"],
        )

        count = await cache.clear("cache:files:list:*")

        assert count == 2
        mock_redis.scan.assert_called_once_with(
            0, match="cache:files:list:*", count=100
        )
        mock_redis.delete.assert_called_once_with(
            "cache:files:list:abc", "cache:files:list:def"
        )

    @pytest.mark.asyncio
    async def test_clear_cache_no_pattern_uses_prefix(self, mock_redis):
        """Test clearing cache without pattern uses default prefix."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        mock_redis.scan.return_value = (0, ["cache:files:list:abc"])

        await cache.clear()

        mock_redis.scan.assert_called_once_with(
            0, match="cache:files:list:*", count=100
        )

    @pytest.mark.asyncio
    async def test_get_handles_bytes_response(self, mock_redis):
        """Test deserialization handles bytes from Redis."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        test_data = ["file1.txt"]
        mock_redis.get.return_value = json.dumps(test_data).encode("utf-8")

        result = await cache.get("cache:files:list:test")

        assert result == test_data


class TestFileCache:
    """Tests for FileCache class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = MagicMock()
        redis.get = AsyncMock()
        redis.setex = AsyncMock()
        redis.delete = AsyncMock()
        redis.scan = AsyncMock()
        return redis

    def test_cache_key_generation(self):
        """Test that cache keys are generated correctly with SHA256 hash."""
        from src.cache import FileCache

        cache = FileCache(MagicMock())

        # Test empty prefix
        key1 = cache.get_cache_key("")
        assert key1.startswith("cache:files:list:")
        assert len(key1.split(":")[-1]) == 64  # SHA256 hash length

        # Test with prefix
        prefix = "reports/2024"
        key2 = cache.get_cache_key(prefix)
        expected_hash = hashlib.sha256(prefix.encode()).hexdigest()
        assert key2 == f"cache:files:list:{expected_hash}"

        # Same prefix should generate same key
        key3 = cache.get_cache_key(prefix)
        assert key2 == key3

    @pytest.mark.asyncio
    async def test_get_files(self, mock_redis):
        """Test get_files method."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        test_files = [{"name": "file1.txt"}, {"name": "file2.txt"}]
        mock_redis.get.return_value = json.dumps(test_files)

        result = await cache.get_files("reports")

        assert result == test_files

    @pytest.mark.asyncio
    async def test_cache_files(self, mock_redis):
        """Test cache_files method."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        test_files = [{"name": "file1.txt"}]

        await cache.cache_files("reports", test_files)

        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[0].startswith("cache:files:list:")
        assert args[1] == 3600  # FileCache DEFAULT_TTL
        assert json.loads(args[2]) == test_files

    @pytest.mark.asyncio
    async def test_clear_all_files(self, mock_redis):
        """Test clear_all method."""
        from src.cache import FileCache

        cache = FileCache(mock_redis)
        mock_redis.scan.return_value = (0, ["cache:files:list:abc"])

        await cache.clear_all()

        mock_redis.scan.assert_called_once_with(
            0, match="cache:files:list:*", count=100
        )


class TestQueryCache:
    """Tests for QueryCache class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = MagicMock()
        redis.get = AsyncMock()
        redis.setex = AsyncMock()
        redis.delete = AsyncMock()
        redis.scan = AsyncMock()
        return redis

    def test_cache_key_generation(self):
        """Test that query cache keys are generated correctly."""
        from src.cache import QueryCache

        cache = QueryCache(MagicMock())

        # Test basic query
        key1 = cache.get_cache_key("test query", 0.5, 100)
        assert key1.startswith("cache:search:")
        assert len(key1.split(":")[-1]) == 32  # MD5 hash

        # Same parameters should generate same key
        key2 = cache.get_cache_key("test query", 0.5, 100)
        assert key1 == key2

        # Different parameters should generate different keys
        key3 = cache.get_cache_key("test query", 0.7, 100)
        assert key1 != key3

        key4 = cache.get_cache_key("different query", 0.5, 100)
        assert key1 != key4

    def test_cache_key_with_kwargs(self):
        """Test cache key generation includes kwargs."""
        from src.cache import QueryCache

        cache = QueryCache(MagicMock())

        key1 = cache.get_cache_key("test", 0.5, 100)
        key2 = cache.get_cache_key("test", 0.5, 100, collection="custom")

        assert key1 != key2

    @pytest.mark.asyncio
    async def test_get_query_results(self, mock_redis):
        """Test get_query_results method."""
        from src.cache import QueryCache

        cache = QueryCache(mock_redis)
        test_results = [
            {"score": 0.95, "text": "result 1"},
            {"score": 0.85, "text": "result 2"},
        ]
        mock_redis.get.return_value = json.dumps(test_results)

        result = await cache.get_query_results("test query", 0.5, 100)

        assert result == test_results

    @pytest.mark.asyncio
    async def test_cache_query_results(self, mock_redis):
        """Test cache_query_results method."""
        from src.cache import QueryCache

        cache = QueryCache(mock_redis)
        test_results = [{"score": 0.95, "text": "result 1"}]

        await cache.cache_query_results("test query", test_results, 0.5, 100)

        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[0].startswith("cache:search:")
        assert args[1] == 1800  # QueryCache DEFAULT_TTL
        assert json.loads(args[2]) == test_results

    @pytest.mark.asyncio
    async def test_cache_query_results_custom_ttl(self, mock_redis):
        """Test caching with custom TTL."""
        from src.cache import QueryCache

        cache = QueryCache(mock_redis)
        test_results = [{"score": 0.95}]

        await cache.cache_query_results("test", test_results, 0.5, 100, ttl=600)

        args = mock_redis.setex.call_args[0]
        assert args[1] == 600

    @pytest.mark.asyncio
    async def test_clear_all_queries(self, mock_redis):
        """Test clear_all method."""
        from src.cache import QueryCache

        cache = QueryCache(mock_redis)
        mock_redis.scan.return_value = (0, ["cache:search:abc", "cache:search:def"])

        await cache.clear_all()

        mock_redis.scan.assert_called_once_with(0, match="cache:search:*", count=100)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

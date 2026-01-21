"""Abstract base class for cache implementations."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class CacheAbs(ABC):
    """Abstract base class for cache operations."""

    prefix: str = "cache"
    DEFAULT_TTL: int = 1800  # 30 minutes default

    def __init__(self, redis):
        """
        Initialize cache with Redis client.

        Args:
            redis: Redis client instance (ArqRedis or redis-py client)
        """
        self.redis = redis

    @abstractmethod
    def get_cache_key(self, **kwargs) -> str:
        """
        Generate cache key from parameters.

        Args:
            **kwargs: Parameters used to generate the cache key

        Returns:
            The cache key string
        """
        raise NotImplementedError("Subclasses must implement get_cache_key method")

    async def get(self, cache_key: str) -> Any|None:
        """
        Get cached data.

        Args:
            cache_key: The cache key to retrieve

        Returns:
            Cached data if found, None otherwise
        """
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return self._deserialize(cached)
            logger.debug(f"Cache miss: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {cache_key}: {e}")
            return None

    async def set(self, cache_key: str, data: Any, ttl: int|None = None):
        """
        Set cached data with TTL.

        Args:
            cache_key: The cache key to set
            data: The data to cache
            ttl: Time to live in seconds (uses DEFAULT_TTL if not specified)
        """
        try:
            ttl = ttl or self.DEFAULT_TTL
            serialized = self._serialize(data)
            await self.redis.setex(cache_key, ttl, serialized)
            logger.debug(f"Cache set: {cache_key} with TTL {ttl}s")
        except Exception as e:
            logger.error(f"Error setting cache key {cache_key}: {e}")

    async def delete(self, cache_key: str):
        """
        Delete a specific cache entry.

        Args:
            cache_key: The cache key to delete
        """
        try:
            await self.redis.delete(cache_key)
            logger.debug(f"Cache deleted: {cache_key}")
        except Exception as e:
            logger.error(f"Error deleting cache key {cache_key}: {e}")

    async def clear(self, pattern: str|None = None):
        """
        Clear cache entries matching a pattern.

        Args:
            pattern: Pattern to match (if None, clears all cache entries of this type)

        Returns:
            Number of keys deleted
        """
        try:
            if pattern is None:
                pattern = f"{self.prefix}:*"

            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries matching pattern: {pattern}")
                return len(keys)
            logger.debug(f"No cache entries found for pattern: {pattern}")
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache with pattern {pattern}: {e}")
            return 0

    def _serialize(self, data: Any) -> str:
        """
        Serialize data for storage.

        Args:
            data: Data to serialize

        Returns:
            Serialized string
        """
        return json.dumps(data)

    def _deserialize(self, data: str) -> Any:
        """
        Deserialize data from storage.

        Args:
            data: Serialized string

        Returns:
            Deserialized data
        """
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)

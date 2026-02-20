"""Search query cache implementation."""

import hashlib
from typing import Any

from .cache_abs import CacheAbs


class QueryCache(CacheAbs):
    """Cache for semantic search query results."""

    prefix = "cache:search"
    DEFAULT_TTL = 1800  # 30 minutes for search results
    CACHE_VERSION = "v2"  # Increment when cache format changes

    def get_cache_key(
        self, query: str, score_threshold: float = 0.0, limit: int = 100, **kwargs
    ) -> str:
        """
        Generate cache key from search parameters with version.

        Args:
            query: Search query text
            score_threshold: Minimum similarity score threshold
            limit: Maximum number of results to cache
            **kwargs: Additional search parameters that affect results

        Returns:
            Cache key string with version
        """
        # Include all parameters that affect search results
        cache_input = f"{query}:{score_threshold}:{limit}"

        # Include any additional kwargs in the cache key
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = ":".join(f"{k}={v}" for k, v in sorted_kwargs)
            cache_input = f"{cache_input}:{kwargs_str}"

        # Hash to create consistent, safe cache key
        query_hash = hashlib.md5(
            cache_input.encode(), usedforsecurity=False
        ).hexdigest()
        # Include version in cache key to invalidate old format
        return f"{self.prefix}:{self.CACHE_VERSION}:{query_hash}"

    async def get_query_results(
        self, query: str, score_threshold: float = 0.0, limit: int = 100, **kwargs
    ) -> list[Any] | None:
        """
        Get cached search results.

        Args:
            query: Search query text
            score_threshold: Minimum similarity score threshold
            limit: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            Cached search results or None if not found
        """
        cache_key = self.get_cache_key(query, score_threshold, limit, **kwargs)
        return await self.get(cache_key)

    async def cache_query_results(
        self,
        query: str,
        results: list[Any],
        score_threshold: float = 0.0,
        limit: int = 100,
        ttl: int | None = None,
        **kwargs,
    ):
        """
        Cache search query results.

        Args:
            query: Search query text
            results: Search results to cache
            score_threshold: Minimum similarity score threshold used
            limit: Maximum number of results cached
            ttl: Time to live in seconds (optional)
            **kwargs: Additional search parameters
        """
        cache_key = self.get_cache_key(query, score_threshold, limit, **kwargs)
        await self.set(cache_key, results, ttl)

    async def clear_all(self):
        """Clear all search query caches."""
        return await self.clear()

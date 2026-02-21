"""File list cache implementation."""

import hashlib
from typing import Any

from .cache_abs import CacheAbs


class FileCache(CacheAbs):
    """Cache for file listing operations."""

    prefix = "cache:files:list"
    DEFAULT_TTL = 3600  # 1 hour for file lists
    CACHE_VERSION = "v2"  # Increment when cache format changes

    def get_cache_key(self, file_prefix: str = "") -> str:
        """
        Generate cache key from file prefix with version.

        Args:
            file_prefix: File path prefix for filtering files (e.g., 'reports/2024')

        Returns:
            Cache key string with version
        """
        # Hash the prefix to handle special characters and long paths
        prefix_hash = hashlib.md5(
            file_prefix.encode(), usedforsecurity=False
        ).hexdigest()  # use md5 for speed. since this is a single user app the risk of collision is low
        # Include version in cache key to invalidate old format
        return f"{self.prefix}:{self.CACHE_VERSION}:{prefix_hash}"

    async def get_files(self, file_prefix: str = "") -> list[Any] | None:
        """
        Get cached file list.

        Args:
            file_prefix: File path prefix for filtering

        Returns:
            Cached file list or None if not found
        """
        cache_key = self.get_cache_key(file_prefix)
        return await self.get(cache_key)

    async def cache_files(
        self, file_prefix: str, files: list[Any], ttl: int | None = None
    ):
        """
        Cache file list.

        Args:
            file_prefix: File path prefix used for filtering
            files: List of file objects to cache
            ttl: Time to live in seconds (optional)
        """
        cache_key = self.get_cache_key(file_prefix)
        await self.set(cache_key, files, ttl)

    async def clear_all(self):
        """Clear all file list caches."""
        return await self.clear()

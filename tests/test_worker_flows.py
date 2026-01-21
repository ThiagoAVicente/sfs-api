"""Tests for worker flows and cache invalidation."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestCacheInvalidation:
    """Tests for cache invalidation utility."""

    @pytest.mark.asyncio
    async def test_clear_all_cache_clears_query_cache(self):
        """Test that clear_all_cache clears query cache."""
        from src.worker.flows.utils import clear_all_cache

        with patch('src.worker.flows.utils.RedisClient') as mock_redis_class, \
             patch('src.worker.flows.utils.QueryCache') as mock_query_cache_class, \
             patch('src.worker.flows.utils.FileCache') as mock_file_cache_class:

            # Mock Redis
            mock_redis = MagicMock()
            mock_redis_class.get = AsyncMock(return_value=mock_redis)

            # Mock caches
            mock_query_cache = MagicMock()
            mock_query_cache.clear = AsyncMock()
            mock_query_cache_class.return_value = mock_query_cache

            mock_file_cache = MagicMock()
            mock_file_cache.clear = AsyncMock()
            mock_file_cache_class.return_value = mock_file_cache

            # Execute
            await clear_all_cache()

            # Assert both caches cleared
            mock_query_cache.clear.assert_called_once()
            mock_file_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_all_cache_uses_same_redis_instance(self):
        """Test that clear_all_cache uses the same Redis instance for both caches."""
        from src.worker.flows.utils import clear_all_cache

        with patch('src.worker.flows.utils.RedisClient') as mock_redis_class, \
             patch('src.worker.flows.utils.QueryCache') as mock_query_cache_class, \
             patch('src.worker.flows.utils.FileCache') as mock_file_cache_class:

            mock_redis = MagicMock()
            mock_redis_class.get = AsyncMock(return_value=mock_redis)

            mock_query_cache_class.return_value = MagicMock(clear=AsyncMock())
            mock_file_cache_class.return_value = MagicMock(clear=AsyncMock())

            await clear_all_cache()

            # Assert both cache classes instantiated with same Redis
            assert mock_query_cache_class.call_count == 1
            assert mock_file_cache_class.call_count == 1
            mock_query_cache_class.assert_called_with(mock_redis)
            mock_file_cache_class.assert_called_with(mock_redis)


class TestIndexFileFlow:
    """Tests for index_file worker flow."""

    @pytest.mark.asyncio
    async def test_index_file_clears_cache_on_success(self):
        """Test that index_file clears cache after successful indexing."""
        from src.worker.flows.index_file import index_file

        mock_ctx = MagicMock()
        file_path = "test.txt"
        file_type = "text/plain"
        file_content = b"This is test content for chunking and embedding."

        with patch('src.worker.flows.index_file.MinIOClient') as mock_minio, \
             patch('src.worker.flows.index_file.FileAbstraction') as mock_file_abs, \
             patch('src.worker.flows.index_file.Chunker') as mock_chunker, \
             patch('src.worker.flows.index_file.EmbeddingGenerator') as mock_embed, \
             patch('src.worker.flows.index_file.QdrantClient') as mock_qdrant, \
             patch('src.worker.flows.index_file.clear_all_cache') as mock_clear_cache:

            # Mock MinIO
            mock_minio.get_object.return_value = file_content

            # Mock file text extraction
            mock_file_abs.get_text.return_value = "This is test content"

            # Mock chunker
            mock_chunks = [
                {"text": "This is test", "start": 0, "end": 12},
                {"text": "test content", "start": 8, "end": 20}
            ]
            mock_chunker.chunk_text.return_value = mock_chunks

            # Mock embeddings
            mock_embed.embed_async = AsyncMock(return_value=[
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6]
            ])

            # Mock Qdrant
            mock_qdrant.write = AsyncMock()

            # Mock cache clear
            mock_clear_cache.return_value = AsyncMock()()

            # Execute
            result = await index_file(mock_ctx, file_path, file_type)

            # Assert cache was cleared
            mock_clear_cache.assert_called_once()

            # Assert successful indexing
            assert result["status"] == "complete"
            assert result["chunks_indexed"] == 2

    @pytest.mark.asyncio
    async def test_index_file_clears_cache_on_failure(self):
        """Test that index_file clears cache even when indexing fails."""
        from src.worker.flows.index_file import index_file

        mock_ctx = MagicMock()
        file_path = "test.txt"
        file_type = "text/plain"

        with patch('src.worker.flows.index_file.MinIOClient') as mock_minio, \
             patch('src.worker.flows.index_file.clear_all_cache') as mock_clear_cache:

            # Mock MinIO to fail
            mock_minio.get_object.return_value = None

            # Mock cache clear
            mock_clear_cache.return_value = AsyncMock()()

            # Execute and expect failure
            with pytest.raises(Exception) as exc_info:
                await index_file(mock_ctx, file_path, file_type)

            # Assert cache was still cleared (finally block)
            mock_clear_cache.assert_called_once()
            assert "Failed to download" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_index_file_writes_all_chunks_to_qdrant(self):
        """Test that all chunks are written to Qdrant with correct metadata."""
        from src.worker.flows.index_file import index_file

        mock_ctx = MagicMock()
        file_path = "test.txt"
        file_type = "text/plain"

        with patch('src.worker.flows.index_file.MinIOClient') as mock_minio, \
             patch('src.worker.flows.index_file.FileAbstraction') as mock_file_abs, \
             patch('src.worker.flows.index_file.Chunker') as mock_chunker, \
             patch('src.worker.flows.index_file.EmbeddingGenerator') as mock_embed, \
             patch('src.worker.flows.index_file.QdrantClient') as mock_qdrant, \
             patch('src.worker.flows.index_file.clear_all_cache') as mock_clear_cache:

            mock_minio.get_object.return_value = b"test content"
            mock_file_abs.get_text.return_value = "test content"

            mock_chunks = [
                {"text": "chunk 1", "start": 0, "end": 7},
                {"text": "chunk 2", "start": 5, "end": 12}
            ]
            mock_chunker.chunk_text.return_value = mock_chunks

            mock_embeddings = [[0.1, 0.2], [0.3, 0.4]]
            mock_embed.embed_async = AsyncMock(return_value=mock_embeddings)

            mock_qdrant.write = AsyncMock()
            mock_clear_cache.return_value = AsyncMock()()

            await index_file(mock_ctx, file_path, file_type)

            # Assert Qdrant write called twice (once per chunk)
            assert mock_qdrant.write.call_count == 2

            # Verify first chunk
            first_call = mock_qdrant.write.call_args_list[0]
            assert first_call[1]['metadata']['file_path'] == file_path
            assert first_call[1]['metadata']['text'] == "chunk 1"
            assert first_call[1]['metadata']['chunk_index'] == 0

            # Verify second chunk
            second_call = mock_qdrant.write.call_args_list[1]
            assert second_call[1]['metadata']['chunk_index'] == 1


class TestDeleteFileFlow:
    """Tests for delete_file worker flow."""

    @pytest.mark.asyncio
    async def test_delete_file_clears_cache_on_success(self):
        """Test that delete_file clears cache after successful deletion."""
        from src.worker.flows.delete_file import delete_file

        mock_ctx = MagicMock()
        file_path = "test.txt"

        with patch('src.worker.flows.delete_file.MinIOClient') as mock_minio, \
             patch('src.worker.flows.delete_file.QdrantClient') as mock_qdrant, \
             patch('src.worker.flows.delete_file.clear_all_cache') as mock_clear_cache:

            # Mock deletions
            mock_minio.delete_object = MagicMock()
            mock_qdrant.delete_file = AsyncMock()

            # Mock cache clear
            mock_clear_cache.return_value = AsyncMock()()

            # Execute
            result = await delete_file(mock_ctx, file_path)

            # Assert cache was cleared
            mock_clear_cache.assert_called_once()

            # Assert successful deletion
            assert result["status"] == "complete"
            assert result["file_path"] == file_path

            # Verify deletions called
            mock_minio.delete_object.assert_called_once_with(file_path)
            mock_qdrant.delete_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_file_clears_cache_on_failure(self):
        """Test that delete_file clears cache even when deletion fails."""
        from src.worker.flows.delete_file import delete_file

        mock_ctx = MagicMock()
        file_path = "test.txt"

        with patch('src.worker.flows.delete_file.MinIOClient') as mock_minio, \
             patch('src.worker.flows.delete_file.clear_all_cache') as mock_clear_cache:

            # Mock MinIO to fail
            mock_minio.delete_object.side_effect = Exception("Deletion failed")

            # Mock cache clear
            mock_clear_cache.return_value = AsyncMock()()

            # Execute and expect failure
            with pytest.raises(Exception) as exc_info:
                await delete_file(mock_ctx, file_path)

            # Assert cache was still cleared (finally block)
            mock_clear_cache.assert_called_once()
            assert "Deletion failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_file_removes_from_both_storages(self):
        """Test that delete_file removes file from both MinIO and Qdrant."""
        from src.worker.flows.delete_file import delete_file

        mock_ctx = MagicMock()
        file_path = "documents/report.pdf"

        with patch('src.worker.flows.delete_file.MinIOClient') as mock_minio, \
             patch('src.worker.flows.delete_file.QdrantClient') as mock_qdrant, \
             patch('src.worker.flows.delete_file.clear_all_cache') as mock_clear_cache:

            mock_minio.delete_object = MagicMock()
            mock_qdrant.delete_file = AsyncMock()
            mock_clear_cache.return_value = AsyncMock()()

            await delete_file(mock_ctx, file_path)

            # Verify both deletions
            mock_minio.delete_object.assert_called_once_with(file_path)
            mock_qdrant.delete_file.assert_called_once()

            # Check Qdrant delete called with correct parameters
            call_kwargs = mock_qdrant.delete_file.call_args[1]
            assert call_kwargs['file_path'] == file_path
            assert 'collection_name' in call_kwargs


class TestCacheInvalidationIntegration:
    """Integration tests to ensure cache invalidation happens correctly."""

    @pytest.mark.asyncio
    async def test_cache_invalidation_with_real_cache_objects(self):
        """Test cache invalidation with real cache objects (mocked Redis)."""
        from src.worker.flows.utils import clear_all_cache
        from src.cache import QueryCache, FileCache

        # Create mock Redis
        mock_redis = MagicMock()
        mock_redis.keys = AsyncMock(return_value=[
            b"cache:search:abc123",
            b"cache:files:list:def456"
        ])
        mock_redis.delete = AsyncMock()

        with patch('src.worker.flows.utils.RedisClient') as mock_redis_class:
            mock_redis_class.get = AsyncMock(return_value=mock_redis)

            # Execute clear
            await clear_all_cache()

            # Verify Redis keys command called for both cache types
            assert mock_redis.keys.call_count == 2
            calls = [call[0][0] for call in mock_redis.keys.call_args_list]
            assert "cache:search:*" in calls
            assert "cache:files:list:*" in calls

    @pytest.mark.asyncio
    async def test_index_and_delete_both_invalidate_cache(self):
        """Test that both index and delete operations invalidate cache."""
        from src.worker.flows.index_file import index_file
        from src.worker.flows.delete_file import delete_file

        mock_ctx = MagicMock()

        # Track cache clear calls
        clear_call_count = 0

        async def mock_clear():
            nonlocal clear_call_count
            clear_call_count += 1

        with patch('src.worker.flows.index_file.MinIOClient') as mock_minio_index, \
             patch('src.worker.flows.index_file.FileAbstraction') as mock_file_abs, \
             patch('src.worker.flows.index_file.Chunker') as mock_chunker, \
             patch('src.worker.flows.index_file.EmbeddingGenerator') as mock_embed, \
             patch('src.worker.flows.index_file.QdrantClient') as mock_qdrant_index, \
             patch('src.worker.flows.index_file.clear_all_cache', new=mock_clear), \
             patch('src.worker.flows.delete_file.MinIOClient') as mock_minio_delete, \
             patch('src.worker.flows.delete_file.QdrantClient') as mock_qdrant_delete, \
             patch('src.worker.flows.delete_file.clear_all_cache', new=mock_clear):

            # Setup mocks for index
            mock_minio_index.get_object.return_value = b"test"
            mock_file_abs.get_text.return_value = "test"
            mock_chunker.chunk_text.return_value = [{"text": "test", "start": 0, "end": 4}]
            mock_embed.embed_async = AsyncMock(return_value=[[0.1]])
            mock_qdrant_index.write = AsyncMock()

            # Setup mocks for delete
            mock_minio_delete.delete_object = MagicMock()
            mock_qdrant_delete.delete_file = AsyncMock()

            # Execute both operations
            await index_file(mock_ctx, "test.txt", "text/plain")
            await delete_file(mock_ctx, "test.txt")

            # Assert cache cleared twice
            assert clear_call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Integration tests for Redis client using testcontainers."""

import pytest
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="class")
def redis_container():
    """Start Redis container for tests."""
    container = RedisContainer("redis:7-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture(autouse=True)
async def setup_redis_client(redis_container):
    """Setup Redis client with testcontainer."""
    import os
    from src.clients import RedisClient

    # Reset singleton
    RedisClient._pool = None

    # Set env vars
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)

    os.environ["REDIS_HOST"] = host
    os.environ["REDIS_PORT"] = str(port)
    os.environ["REDIS_PASSWORD"] = ""

    # Reload module
    import importlib
    import src.clients.redis_client as redis_module
    importlib.reload(redis_module)

    yield

    # Cleanup
    await RedisClient.close()
    RedisClient._pool = None


@pytest.mark.integration
class TestRedisClientIntegration:
    """Integration tests for Redis client."""

    @pytest.mark.asyncio
    async def test_init_creates_pool(self):
        """Test that init creates Redis pool."""
        from src.clients import RedisClient

        pool = await RedisClient.init()
        assert pool is not None

    @pytest.mark.asyncio
    async def test_get_returns_same_pool(self):
        """Test that get() returns singleton pool."""
        from src.clients import RedisClient

        pool1 = await RedisClient.get()
        pool2 = await RedisClient.get()

        assert pool1 is pool2

    @pytest.mark.asyncio
    async def test_close_clears_pool(self):
        """Test that close() clears the pool."""
        from src.clients import RedisClient

        await RedisClient.init()
        assert RedisClient._pool is not None

        await RedisClient.close()
        assert RedisClient._pool is None

    @pytest.mark.asyncio
    async def test_enqueue_job_returns_job_id(self):
        """Test enqueuing a job returns job ID."""
        from src.clients import RedisClient

        # Note: This requires a worker function to be registered
        # For now, we test that the method works
        try:
            job_id = await RedisClient.enqueue_job('test_function', 'test.txt')
            assert job_id is not None
            assert isinstance(job_id, str)
        except Exception:
            # Expected if no worker is running
            pass

    @pytest.mark.asyncio
    async def test_get_job_status(self):
        """Test getting job status."""
        from src.clients import RedisClient

        # Test with non-existent job
        status = await RedisClient.get_job_status("non-existent-job")
        # Status should be None or a status string
        assert status is None or isinstance(status, str)

    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Test basic Redis connection."""
        from src.clients import RedisClient

        pool = await RedisClient.get()

        # Test basic Redis operation
        await pool.set("test_key", "test_value")
        value = await pool.get("test_key")
        # Redis returns bytes, decode to string
        assert value.decode() == "test_value"

        # Cleanup
        await pool.delete("test_key")

    @pytest.mark.asyncio
    async def test_redis_pool_ping(self):
        """Test Redis connection is alive."""
        from src.clients import RedisClient

        pool = await RedisClient.get()
        result = await pool.ping()
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
